"""API and Endpoint Test using FastAPI TestClient."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.server import app

client = TestClient(app)

def test_endpoints():
    print("=== Testing FastAPI Endpoints ===")

    # 1. Test /api/languages
    res = client.get("/api/languages")
    assert res.status_code == 200, f"Languages failed: {res.text}"
    langs = res.json()["languages"]
    print(f"✓ /api/languages returned {len(langs)} languages: {[l['code'] for l in langs]}")

    # 2. Test / (Root Web UI HTML)
    res = client.get("/")
    assert res.status_code == 200
    assert "Offline Multilingual Language Translator" in res.text
    print("✓ GET / returned Web UI HTML")

    # 3. Test /static/css/styles.css
    res = client.get("/static/css/styles.css")
    assert res.status_code == 200
    assert "Noto Sans Kannada" in res.text
    print("✓ GET /static/css/styles.css served local CSS")

    # 4. Test /api/translate (Kannada to English)
    payload = {
        "text": "ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?",
        "source_lang": "kn",
        "target_lang": "en",
        "use_cache": True
    }
    res = client.post("/api/translate", json=payload)
    assert res.status_code == 200, f"Translate failed: {res.text}"
    data = res.json()
    print(f"✓ POST /api/translate: {payload['text']} -> {data['translated_text']} ({data['latency_ms']}ms)")

    # 5. Test /api/translate auto-detect (Hindi to English)
    payload_auto = {
        "text": "नमस्ते, आप कैसे हैं?",
        "source_lang": "auto",
        "target_lang": "en",
        "use_cache": True
    }
    res_auto = client.post("/api/translate", json=payload_auto)
    assert res_auto.status_code == 200
    data_auto = res_auto.json()
    print(f"✓ POST /api/translate (auto-detect): Detected {data_auto['source_lang']} -> {data_auto['translated_text']}")
    assert data_auto["source_lang"] == "hi"

    # 6. Test /api/dictionary
    res_dict = client.get("/api/dictionary/knowledge")
    assert res_dict.status_code == 200
    dict_data = res_dict.json()
    assert dict_data["found"] is True
    print(f"✓ GET /api/dictionary/knowledge: {dict_data['word']} -> {dict_data['definition'][:40]}...")

    # 7. Test /api/history
    res_hist = client.get("/api/history")
    assert res_hist.status_code == 200
    hist = res_hist.json()["history"]
    assert len(hist) > 0
    print(f"✓ GET /api/history returned {len(hist)} items")

    print("\n✓ ALL 7 API ENDPOINTS VALIDATED SUCCESSFULLY!")

if __name__ == "__main__":
    test_endpoints()
