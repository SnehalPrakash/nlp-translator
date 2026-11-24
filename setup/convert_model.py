"""One-time conversion script:
Downloads facebook/nllb-200-distilled-600M and converts to CTranslate2 INT8 model.
Copies sentencepiece.bpe.model and metadata for lean offline runtime.
"""

import os
import sys
import subprocess
from huggingface_hub import hf_hub_download

MODEL_ID = "facebook/nllb-200-distilled-600M"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "nllb-200-ct2-int8")


def convert():
    print(f"=== Converting {MODEL_ID} to CTranslate2 INT8 ===")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Download SentencePiece tokenizer model
    print("Downloading SentencePiece tokenizer model...")
    sp_path = hf_hub_download(
        repo_id=MODEL_ID,
        filename="sentencepiece.bpe.model",
        local_dir=OUTPUT_DIR,
    )
    print(f"✓ Saved sentencepiece.bpe.model to {sp_path}")

    # 2. Run CTranslate2 converter CLI
    cmd = [
        sys.executable,
        "-m", "ctranslate2.converters.transformers",
        "--model", MODEL_ID,
        "--output_dir", OUTPUT_DIR,
        "--quantization", "int8",
        "--copy_files", "sentencepiece.bpe.model",
        "--low_cpu_mem_usage",
        "--force",
    ]
    print(f"Running conversion: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True)
    if result.returncode == 0:
        print("✓ Conversion completed successfully!")
        # Print file sizes in output dir
        total_size = 0
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for f in files:
                fp = os.path.join(root, f)
                sz = os.path.getsize(fp)
                total_size += sz
                print(f"  - {f}: {sz / (1024*1024):.2f} MB")
        print(f"Total model footprint: {total_size / (1024*1024):.2f} MB")
    else:
        print("Conversion failed.")


if __name__ == "__main__":
    convert()
