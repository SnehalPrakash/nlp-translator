"""Core Offline Translation Engine.

Uses ONLY CTranslate2 and SentencePiece at runtime (no PyTorch, no Transformers).
Enforces zero-network offline mode via environment flags.
Integrates sentence chunking, SHA-256 caching, Unicode routing, and lexicon lookups.
"""

import os
import time
from typing import Any, Dict, List, Optional, Tuple

# Enforce complete offline operation
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import ctranslate2
import sentencepiece

from core.router import (
    LANG_DISPLAY_NAMES,
    NLLB_LANG_CODES,
    detect_language,
    get_nllb_code,
    is_romanized_indic,
)
from core.splitter import split_sentences
from data.db import CacheService, HistoryService, LexiconService

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "nllb-200-ct2-int8")
SP_MODEL_PATH = os.path.join(MODEL_DIR, "sentencepiece.bpe.model")


class TranslatorEngine:
    _instance = None

    def __init__(self, model_dir: str = MODEL_DIR):
        if not os.path.isdir(model_dir):
            raise FileNotFoundError(f"Model directory not found at: {model_dir}")
        if not os.path.isfile(SP_MODEL_PATH):
            raise FileNotFoundError(f"SentencePiece model not found at: {SP_MODEL_PATH}")

        print(f"Loading CTranslate2 INT8 model from {model_dir} (CPU execution)...")
        start_t = time.time()
        self.translator = ctranslate2.Translator(
            model_dir,
            device="cpu",
            compute_type="int8",
            intra_threads=4,
            inter_threads=1,
        )
        self.sp = sentencepiece.SentencePieceProcessor()
        self.sp.load(SP_MODEL_PATH)
        print(f"✓ CTranslate2 engine initialized in {time.time() - start_t:.2f}s.")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def tokenize_sentence(self, sentence: str, src_lang: str) -> List[str]:
        """Tokenize a sentence for NLLB-200 encoder.
        
        NLLB-200 HuggingFace convention: [tokens] + ['</s>', src_lang_code]
        """
        src_tag = get_nllb_code(src_lang)
        subwords = self.sp.encode_as_pieces(sentence)
        return subwords + ["</s>", src_tag]

    def detokenize_sentence(self, tokens: List[str], tgt_lang: str) -> str:
        """Detokenize generated tokens back to readable text."""
        tgt_tag = get_nllb_code(tgt_lang)
        # Filter out target language prefix, EOS, and special tokens
        cleaned = [
            t for t in tokens
            if t != tgt_tag and t != "</s>" and not t.startswith("__")
        ]
        return self.sp.decode_pieces(cleaned).strip()

    def translate(
        self,
        text: str,
        src_lang: str = "auto",
        tgt_lang: str = "en",
        use_cache: bool = True,
        save_history: bool = True,
    ) -> Dict[str, Any]:
        """Translate text with automatic detection, chunking, caching, and lexicon lookup."""
        if not text or not text.strip():
            return {
                "translated_text": "",
                "source_lang": src_lang,
                "target_lang": tgt_lang,
                "confidence": 0.0,
                "cached": False,
                "latency_ms": 0.0,
                "dictionary_entry": None,
                "warning": None,
            }

        start_time = time.perf_counter()
        raw_text = text.strip()

        # 1. Resolve source language (auto-detect via Unicode router)
        confidence = 1.0
        detected_lang = src_lang
        if src_lang == "auto" or not src_lang:
            detected_lang, confidence = detect_language(raw_text)

        # Transliteration warning check (e.g. Kanglish/Hinglish entered with native Indic target)
        warning = None
        if is_romanized_indic(raw_text, tgt_lang):
            warning = f"Romanized text detected. For best accuracy in {LANG_DISPLAY_NAMES.get(tgt_lang, tgt_lang)}, please type in native script."

        # 2. Check SHA-256 Translation Cache
        if use_cache:
            cached_translation = CacheService.get(raw_text, detected_lang, tgt_lang)
            if cached_translation:
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                dict_entry = self._check_dictionary(raw_text, cached_translation, detected_lang, tgt_lang)
                return {
                    "translated_text": cached_translation,
                    "source_lang": detected_lang,
                    "target_lang": tgt_lang,
                    "confidence": confidence,
                    "cached": True,
                    "latency_ms": round(latency_ms, 2),
                    "dictionary_entry": dict_entry,
                    "warning": warning,
                }

        # 3. Sentence Splitting (prevents 512-token truncation on paragraphs)
        sentences = split_sentences(raw_text)
        tgt_tag = get_nllb_code(tgt_lang)

        # 4. Batch Tokenization
        tokenized_batch = [self.tokenize_sentence(s, detected_lang) for s in sentences]
        target_prefixes = [[tgt_tag]] * len(sentences)

        # 5. Parallel Batch Inference via CTranslate2
        results = self.translator.translate_batch(
            tokenized_batch,
            target_prefix=target_prefixes,
            beam_size=4,
            max_batch_size=32,
            batch_type="examples",
        )

        # 6. Detokenization and Reconstruction
        translated_sentences = []
        for res in results:
            hypo_tokens = res.hypotheses[0]
            translated_sent = self.detokenize_sentence(hypo_tokens, tgt_lang)
            translated_sentences.append(translated_sent)

        # Join sentences preserving natural spacing
        translated_text = " ".join(translated_sentences).strip()

        # 7. Update Cache and History
        if use_cache:
            CacheService.set(raw_text, translated_text, detected_lang, tgt_lang)
        if save_history:
            HistoryService.add(raw_text, translated_text, detected_lang, tgt_lang)

        # 8. Single-word Dictionary / Lexicon Check (English pivot)
        dict_entry = self._check_dictionary(raw_text, translated_text, detected_lang, tgt_lang)

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "translated_text": translated_text,
            "source_lang": detected_lang,
            "target_lang": tgt_lang,
            "confidence": round(confidence, 2),
            "cached": False,
            "latency_ms": round(latency_ms, 2),
            "sentences_count": len(sentences),
            "dictionary_entry": dict_entry,
            "warning": warning,
        }

    def _check_dictionary(
        self, source_text: str, translated_text: str, src_lang: str, tgt_lang: str
    ) -> Optional[Dict[str, Any]]:
        """Look up dictionary entry if input is a single word."""
        words = source_text.strip().split()
        if len(words) > 2:
            return None

        # Try source word directly (if English)
        entry = LexiconService.lookup(source_text)
        if entry:
            return entry

        # If source is non-English, try English translated word as pivot
        if tgt_lang == "en":
            entry = LexiconService.lookup(translated_text)
            if entry:
                return entry

        return None
