# 📱 IndicTranslate - Mobile Application (Flutter)

A native mobile client for the **Offline Multilingual Language Translator** built with **Flutter** and **Material 3**.

---

## ⚡ Features

- **Google Translate Mobile UX**: Modern dual-pane interface with responsive cards, character counters, and live debounced translation.
- **Zero-Config mDNS Auto-Discovery**: Automatically discovers and connects to `http://translator.local:8000` on the local Wi-Fi / hotspot.
- **Offline Text-to-Speech (TTS)**: Built-in speaker button using device-native offline speech engines (`flutter_tts`).
- **One-Tap Clipboard Copying**: Native OS clipboard copy with visual toast/snackbar feedback.
- **Offline Dictionary Drawer**: Automatically reveals word definitions, parts of speech, and synonyms for single-word queries.
- **Light & Dark Themes**: Follows system dark mode with high-contrast accessibility.
- **Host Switcher**: Quick dialog on the top-right to customize the host IP if your Wi-Fi router blocks mDNS multicast.

---

## 🚀 Running on Your Phone

### 1. Prerequisites
If you don't have Flutter installed yet:
```bash
brew install --cask flutter
```

### 2. Launch on Connected Device (Android / iOS)
1. Make sure the translator server is running on your Mac (`./run.sh`).
2. Connect your phone via USB (with USB debugging enabled on Android or trusted on iOS) or connect to the same Wi-Fi.
3. Run:
```bash
cd mobile
flutter pub get
flutter run
```

### 3. Build Standalone Android APK
To install directly on your Android phone without needing a computer connection:
```bash
cd mobile
flutter build apk --release
```
The installable APK will be generated at:
```text
mobile/build/app/outputs/flutter-apk/app-release.apk
```
You can AirDrop, email, or USB-transfer this APK directly to any Android smartphone!

---

## 📡 Connecting to Your Mac Node

1. Turn on your phone's Wi-Fi and connect to the **same Wi-Fi router** as your Mac, OR turn on your phone's **Personal Hotspot** and connect your Mac to it (no mobile data / internet needed!).
2. By default, the app automatically connects to `http://translator.local:8000`.
3. If your router has AP-isolation enabled, tap **"Setup Host"** in the top-right corner of the app and enter your Mac's local IP (e.g. `http://192.168.1.15:8000`).
