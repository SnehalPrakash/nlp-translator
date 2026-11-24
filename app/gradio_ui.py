"""Gradio Interface for Offline Multilingual Translator.

Can run standalone or be mounted inside FastAPI at /gradio.
Provides language auto-detection, instant swap, character counts, latency metrics,
and dictionary cards for single-word translations.
"""

import gradio as gr
from core.router import LANG_DISPLAY_NAMES
from core.translator import TranslatorEngine

# Language choices for Gradio UI
SOURCE_LANG_CHOICES = [("🌐 Auto-Detect", "auto")] + [
    (name, code) for code, name in LANG_DISPLAY_NAMES.items()
]

TARGET_LANG_CHOICES = [
    (name, code) for code, name in LANG_DISPLAY_NAMES.items()
]

SAMPLE_SENTENCES = [
    ["ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ? ನಾನು ಆರಾಮಾಗಿದ್ದೇನೆ.", "auto", "en"],
    ["नमस्ते, आप कैसे हैं? मुझे भारतीय भाषाएं पसंद हैं।", "auto", "en"],
    ["வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?", "auto", "en"],
    ["నమస్కారం, మీరు ఎలా ఉన్నారు?", "auto", "en"],
    ["നമസ്കാരം, സുഖമാണോ?", "auto", "en"],
    ["Knowledge is power, and wisdom brings peace.", "en", "kn"],
    ["Hola, ¿cómo estás hoy? Este es un sistema de traducción fuera de línea.", "auto", "en"],
    ["knowledge", "en", "hi"],
]


def create_gradio_demo(translator_engine: TranslatorEngine = None):
    if translator_engine is None:
        translator_engine = TranslatorEngine.get_instance()

    def translate_handler(text, src_lang, tgt_lang):
        if not text or not text.strip():
            return "", "Enter text to translate.", "", ""

        res = translator_engine.translate(text, src_lang, tgt_lang)
        translated_text = res["translated_text"]

        # Meta info
        src_disp = LANG_DISPLAY_NAMES.get(res["source_lang"], res["source_lang"])
        tgt_disp = LANG_DISPLAY_NAMES.get(res["target_lang"], res["target_lang"])
        cache_str = "⚡ Cached (0ms model time)" if res["cached"] else "⚙️ CTranslate2 INT8"
        latency_str = f"⏱️ {res['latency_ms']} ms | {cache_str} | Detected: {src_disp} ({int(res['confidence']*100)}%)"

        # Warning
        warning_str = f"⚠️ {res['warning']}" if res.get("warning") else ""

        # Dictionary formatted card
        dict_card = ""
        entry = res.get("dictionary_entry")
        if entry:
            syn_str = ", ".join(entry["synonyms"]) if entry.get("synonyms") else "None"
            ant_str = ", ".join(entry["antonyms"]) if entry.get("antonyms") else "None"
            ex_str = "<br>• " + "<br>• ".join(entry["examples"]) if entry.get("examples") else ""
            dict_card = f"""
### 📖 Offline Lexicon: **{entry['word'].capitalize()}** *({entry.get('pos', '')})*
> {entry.get('definition', '')}

- **Synonyms**: {syn_str}
- **Antonyms**: {ant_str}
{f"- **Examples**:{ex_str}" if ex_str else ""}
"""

        return translated_text, latency_str, warning_str, dict_card

    def swap_languages(src_lang, tgt_lang):
        # Cannot swap if auto-detect is selected as source
        if src_lang == "auto":
            return "en", tgt_lang
        return tgt_lang, src_lang

    custom_css = """
    .gradio-container { max-width: 1100px !important; margin: auto !important; }
    .status-box { font-size: 0.9em; opacity: 0.85; }
    """

    with gr.Blocks(title="Offline Multilingual Translator") as demo:
        gr.Markdown(
            """
            # 🌐 Offline Multilingual Language Translator
            **Local & Private Neural Translation Engine** | Supports Kannada, Hindi, Tamil, Telugu, Malayalam, English, Spanish & French.
            *100% Offline | Powered by CTranslate2 & NLLB-200 INT8 | Apple Accelerate CPU*
            """
        )

        with gr.Row():
            src_dropdown = gr.Dropdown(
                choices=SOURCE_LANG_CHOICES,
                value="auto",
                label="Source Language",
                scale=5,
            )
            swap_btn = gr.Button("⇄ Swap", scale=1, variant="secondary")
            tgt_dropdown = gr.Dropdown(
                choices=TARGET_LANG_CHOICES,
                value="kn",
                label="Target Language",
                scale=5,
            )

        with gr.Row():
            with gr.Column():
                input_text = gr.Textbox(
                    lines=6,
                    placeholder="Type or paste text to translate... (e.g. sentences in Kannada, Hindi, Tamil, English, etc.)",
                    label="Input Text",
                )
                translate_btn = gr.Button("Translate", variant="primary", size="lg")

            with gr.Column():
                output_text = gr.Textbox(
                    lines=6,
                    placeholder="Translation will appear here...",
                    label="Translated Output",
                    interactive=False,
                )
                meta_info = gr.Markdown(value="Ready for offline translation.", elem_classes=["status-box"])
                warning_info = gr.Markdown(value="")

        # Dictionary / Lexicon Output Card
        dict_view = gr.Markdown(value="")

        # Sample test sentences
        gr.Markdown("### 💡 Quick Sample Phrases")
        gr.Examples(
            examples=SAMPLE_SENTENCES,
            inputs=[input_text, src_dropdown, tgt_dropdown],
            label="Click an example to test",
        )

        # Wire handlers
        translate_btn.click(
            fn=translate_handler,
            inputs=[input_text, src_dropdown, tgt_dropdown],
            outputs=[output_text, meta_info, warning_info, dict_view],
        )

        # Live translate on enter
        input_text.submit(
            fn=translate_handler,
            inputs=[input_text, src_dropdown, tgt_dropdown],
            outputs=[output_text, meta_info, warning_info, dict_view],
        )

        swap_btn.click(
            fn=swap_languages,
            inputs=[src_dropdown, tgt_dropdown],
            outputs=[src_dropdown, tgt_dropdown],
        )

    return demo


if __name__ == "__main__":
    demo = create_gradio_demo()
    demo.launch(server_port=7860, inbrowser=False)
