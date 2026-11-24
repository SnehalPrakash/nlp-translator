import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import ctranslate2
import sentencepiece

model_dir = "models/nllb-200-ct2-int8"
sp_path = os.path.join(model_dir, "sentencepiece.bpe.model")

translator = ctranslate2.Translator(model_dir, device="cpu", compute_type="int8")
sp = sentencepiece.SentencePieceProcessor()
sp.load(sp_path)

test_sentence = "Hello, how are you?"
tokens = sp.encode_as_pieces(test_sentence)

print("Raw pieces:", tokens)

# Format A (HuggingFace NLLB): tokens + ["</s>", "eng_Latn"]
tokens_a = tokens + ["</s>", "eng_Latn"]
res_a = translator.translate_batch([tokens_a], target_prefix=[["kan_Knda"]], beam_size=4)
out_a = res_a[0].hypotheses[0]
clean_a = [t for t in out_a if t not in ("kan_Knda", "</s>")]
print("\nFormat A (tokens + [</s>, src_lang]):")
print("Output tokens:", out_a)
print("Decoded text:", sp.decode_pieces(clean_a))

# Format B: ["eng_Latn"] + tokens + ["</s>"]
tokens_b = ["eng_Latn"] + tokens + ["</s>"]
res_b = translator.translate_batch([tokens_b], target_prefix=[["kan_Knda"]], beam_size=4)
out_b = res_b[0].hypotheses[0]
clean_b = [t for t in out_b if t not in ("kan_Knda", "</s>")]
print("\nFormat B ([src_lang] + tokens + [</s>]):")
print("Output tokens:", out_b)
print("Decoded text:", sp.decode_pieces(clean_b))
