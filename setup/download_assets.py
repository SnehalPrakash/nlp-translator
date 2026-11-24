"""Download offline auxiliary assets:
1. FastText lid.176.ftz language identification model (900KB)
2. Noto Sans font files for Indian scripts (Kannada, Devanagari, Tamil, Telugu, Malayalam)
"""

import os
import sys
import ssl
import certifi
import urllib.request

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "static", "fonts")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

# 1. FastText lid.176.ftz
FASTTEXT_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz"
fasttext_path = os.path.join(MODELS_DIR, "lid.176.ftz")

ssl_ctx = ssl.create_default_context(cafile=certifi.where())

def download_file(url: str, dest_path: str, desc: str):
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"✓ {desc} already exists ({os.path.getsize(dest_path)} bytes).")
        return
    print(f"Downloading {desc} from {url}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ssl_ctx) as resp, open(dest_path, "wb") as f:
            f.write(resp.read())
        print(f"✓ Downloaded {desc} ({os.path.getsize(dest_path)} bytes).")
    except Exception as e:
        print(f"⚠ Warning: Failed to download {desc}: {e}")


def main():
    print("=== Downloading Offline Auxiliary Assets ===")
    download_file(FASTTEXT_URL, fasttext_path, "FastText lid.176.ftz")

    # Download Noto Sans WOFF2 / TTF font subsets for offline Indian language rendering
    # Using raw fonts from Google Fonts repository / GitHub
    font_urls = {
        "NotoSansKannada-Regular.ttf": "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansKannada/NotoSansKannada-Regular.ttf",
        "NotoSansDevanagari-Regular.ttf": "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf",
        "NotoSansTamil-Regular.ttf": "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansTamil/NotoSansTamil-Regular.ttf",
        "NotoSansTelugu-Regular.ttf": "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansTelugu/NotoSansTelugu-Regular.ttf",
        "NotoSansMalayalam-Regular.ttf": "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansMalayalam/NotoSansMalayalam-Regular.ttf",
    }

    for filename, url in font_urls.items():
        dest = os.path.join(FONTS_DIR, filename)
        download_file(url, dest, filename)

    print("=== Asset download complete ===")


if __name__ == "__main__":
    main()
