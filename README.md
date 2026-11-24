# 🌐 Offline Multilingual NLP Translator

A private, high-performance neural machine translation system focused on Indian & global languages that runs **100% offline**—no cloud APIs, no telemetry, and no internet connection required after setup.

Supports **Kannada, Hindi, Tamil, Telugu, Malayalam, English, Spanish, and French** with sub-second CPU inference on Apple Silicon and modern PCs, plus a **Web UI**, **Gradio UI**, and **Flutter Mobile App**.

---

## ⚡ Key Features

- **100% Offline & Private**: Zero external API calls or background polling (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`).
- **Lean INT8 Inference**: Powered by Meta's **NLLB-200-distilled-600M** quantized to **INT8 (~600 MB)** via **CTranslate2** (no `torch` or `transformers` loaded at runtime).
- **Three Interfaces in One Project**:
  - **Standalone Web App** (`http://localhost:8000`): Dual-pane translator UI with light/dark theme, local Noto Sans fonts, dictionary lookup, and history drawer.
  - **Gradio UI** (`http://localhost:8000/gradio`): Mounted directly inside FastAPI sharing the same model in RAM.
  - **Flutter Mobile App** (`mobile/`): Native Android/iOS client with offline TTS (`flutter_tts`) and local Wi-Fi connection.
- **Zero-Config LAN Discovery**: Broadcasts via mDNS (`http://translator.local:8000`) so phones on the same Wi-Fi/hotspot can connect immediately.
- **Microsecond Script Routing**: Deterministic Unicode codepoint router for Indic scripts and FastText (`lid.176.ftz`) for Latin script disambiguation.
- **Indic-Aware Sentence Splitter**: Handles `.`, `?`, `!`, and Indic danda (`।`, `॥`) with batched `translate_batch()` to prevent 512-token truncation.
- **Sub-Millisecond Cache & Offline Lexicon**: SQLite SHA-256 translation cache (`< 1 ms` on repeat queries) plus English-pivot definitions, parts of speech, synonyms, and antonyms.

---

## 🗺️ Supported Languages

| Language | Script | ISO Code | NLLB-200 Tag |
| :--- | :--- | :--- | :--- |
| **Kannada** (ಕನ್ನಡ) | Kannada | `kn` | `kan_Knda` |
| **Hindi** (हिन्दी) | Devanagari | `hi` | `hin_Deva` |
| **Tamil** (தமிழ்) | Tamil | `ta` | `tam_Taml` |
| **Telugu** (తెలుగు) | Telugu | `te` | `tel_Telu` |
| **Malayalam** (മലയാളം) | Malayalam | `ml` | `mal_Mlym` |
| **English** | Latin | `en` | `eng_Latn` |
| **Spanish** (Español) | Latin | `es` | `spa_Latn` |
| **French** (Français) | Latin | `fr` | `fra_Latn` |

---

## 🚀 Easy Installation & Setup

### Prerequisites
- **Python 3.10 – 3.12** (Python 3.12 recommended)
- **~2.5 GB free disk space** during initial model download & INT8 conversion (final runtime footprint is ~604 MB for the model)
- *(Optional, for Mobile App)* **Flutter SDK** + **Android SDK** (for building the Android APK)

### 1. Clone the Repository
```bash
git clone https://github.com/SnehalPrakash/nlp-translator.git
cd nlp-translator
```

### 2. Run One-Command Setup
This creates a `.venv`, installs Python dependencies, downloads the FastText language ID model and local Noto Sans fonts, and converts `facebook/nllb-200-distilled-600M` to CTranslate2 INT8:

```bash
chmod +x setup.sh run.sh
./setup.sh
```

> **Note (Manual Setup / Windows):**
> ```bash
> python -m venv .venv
> # Activate: source .venv/bin/activate (macOS/Linux) or .venv\Scripts\activate (Windows)
> pip install -r requirements.txt -r requirements-setup.txt
> python setup/download_assets.py
> python setup/convert_model.py
> ```

### 3. Launch the Server
```bash
./run.sh
```

Once running, open:
- **Web App**: [http://localhost:8000](http://localhost:8000)
- **Gradio Interface**: [http://localhost:8000/gradio](http://localhost:8000/gradio)
- **Mobile Browser on Local Wi-Fi**: `http://translator.local:8000` (or `http://<YOUR-COMPUTER-LAN-IP>:8000`)

---

## 📱 Mobile App (Flutter)

The `mobile/` directory contains a native Flutter client that connects to your local translation server over Wi-Fi.

```bash
cd mobile
flutter pub get

# Run on a connected device/emulator
flutter run

# Or build an Android APK
flutter build apk --debug
```

In the app, it connects to `http://translator.local:8000` by default, or you can tap the host/settings icon to enter your computer's local IP address (e.g., `192.168.1.42`).

---

## 🧪 Running Tests

Run the 12-case golden test suite covering Indic/European translation pairs, paragraph splitting, cache latency, and dictionary lookups:

```bash
.venv/bin/python tests/test_golden_suite.py
```

Run API integration tests (with the server running):
```bash
.venv/bin/python tests/test_api_client.py
```

---

## 🏛️ Project Structure

```text
nlp-translator/
├── app/
│   ├── gradio_ui.py            # Embedded Gradio Blocks UI (/gradio)
│   └── server.py               # FastAPI server, mDNS broadcaster & static files
├── core/
│   ├── router.py               # Unicode script + FastText language detector
│   ├── splitter.py             # Indic-aware sentence splitter (। / .)
│   └── translator.py           # CTranslate2 + SentencePiece inference engine
├── data/
│   └── db.py                   # SQLite cache, history & offline lexicon manager
├── mobile/                     # Flutter Android/iOS client
├── setup/
│   ├── convert_model.py        # NLLB-200 -> CTranslate2 INT8 converter
│   └── download_assets.py      # FastText & Noto Sans font downloader
├── tests/                      # Golden suite & API integration tests
├── web/                        # Standalone HTML/CSS/JS Web UI
├── requirements.txt            # Lean runtime dependencies
├── requirements-setup.txt      # One-time model conversion dependencies
├── run.sh                      # Server launch script
└── setup.sh                    # Automated setup script
```

---

## 🔒 Privacy & Offline Guarantees
- `torch` and `transformers` are **never imported at runtime**—only during one-time conversion in `setup/convert_model.py`.
- `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` are set in `run.sh`.
- All Noto Sans fonts (Kannada, Devanagari, Tamil, Telugu, Malayalam) are bundled locally in `web/static/fonts/` so scripts render cleanly without internet access.
