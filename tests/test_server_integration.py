"""Integration test for unified FastAPI + Gradio server."""

import os
import sys
import time
import urllib.request
import json
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uvicorn
from app.server import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

def run_client_checks():
    # Wait for server to come up
    for _ in range(20):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/api/languages") as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.5)

    print("--- 1. Testing GET /api/languages ---")
    with urllib.request.urlopen("http://127.0.0.1:8000/api/languages") as r:
        data = json.loads(r.read())
        print(f"Languages available: {len(data['languages'])} -> {[l['code'] for l in data['languages']]}")
        assert len(data["languages"]) >= 7

    print("--- 2. Testing GET / (Standalone Web App HTML) ---")
    with urllib.request.urlopen("http://127.0.0.1:8000/") as r:
        html = r.read().decode("utf-8")
        assert "Offline Multilingual Language Translator" in html
        assert "/static/css/styles.css" in html
        print(f"HTML served successfully ({len(html)} bytes).")

    print("--- 3. Testing POST /api/translate ---")
    req_body = json.dumps({
        "text": "Hello, how are you?",
        "source_lang": "en",
        "target_lang": "kn",
        "use_cache": True
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/translate",
        data=req_body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read())
        print(f"Translation Output: {res['translated_text']}")
        print(f"Latency: {res['latency_ms']}ms | Cached: {res['cached']}")
        assert len(res["translated_text"]) > 0

    print("--- 4. Testing GET /gradio (Mounted Gradio App) ---")
    with urllib.request.urlopen("http://127.0.0.1:8000/gradio") as r:
        assert r.status == 200
        print("Gradio UI mounted and serving at /gradio!")

    print("\n✓ ALL INTEGRATION CHECKS PASSED!")
    os._exit(0)

if __name__ == "__main__":
    t = threading.Thread(target=run_client_checks, daemon=True)
    t.start()
    run_server()
