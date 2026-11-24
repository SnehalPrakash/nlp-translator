"""Unified FastAPI Application Server.

Features:
- Mounts Gradio UI at /gradio (Single process, shared model in RAM).
- REST API endpoints for translation, detection, lexicon, and history.
- Non-blocking threadpool inference with Semaphore concurrency protection.
- Zeroconf mDNS advertisement for http://translator.local:8000 on LAN.
- Static file serving for standalone offline Web UI.
"""

import asyncio
import os
import sys
import socket
from contextlib import asynccontextmanager
from typing import Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import gradio as gr
from zeroconf import IPVersion, ServiceInfo, Zeroconf

from app.gradio_ui import create_gradio_demo
from core.router import LANG_DISPLAY_NAMES, detect_language
from core.translator import TranslatorEngine
from data.db import HistoryService, LexiconService

# Concurrency limit for CPU-bound inference
INFERENCE_SEMAPHORE = asyncio.Semaphore(2)

# Zeroconf state
zc: Optional[Zeroconf] = None
service_info: Optional[ServiceInfo] = None


def get_local_ip() -> str:
    """Find the local network IP for mDNS advertisement."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't need to be reachable; triggers OS routing lookup
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global zc, service_info
    print("Initializing Offline Multilingual Translator Engine...")
    engine = TranslatorEngine.get_instance()
    app.state.engine = engine

    # Start mDNS Broadcaster for http://translator.local:8000
    local_ip = get_local_ip()
    port = 8000
    try:
        zc = Zeroconf(ip_version=IPVersion.V4Only)
        service_info = ServiceInfo(
            "_http._tcp.local.",
            "Offline Translator._http._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties={"path": "/"},
            server="translator.local.",
        )
        zc.register_service(service_info)
        print(f"📡 mDNS Active: Broadcasted on http://translator.local:{port} ({local_ip})")
    except Exception as e:
        print(f"⚠️ mDNS registration warning: {e}")

    yield

    # Cleanup mDNS on shutdown
    if zc and service_info:
        print("Unregistering mDNS service...")
        zc.unregister_service(service_info)
        zc.close()


app = FastAPI(
    title="Offline Multilingual Translator API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static web files
static_dir = os.path.join(os.path.dirname(__file__), "..", "web", "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Pydantic Schemas
class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "kn"
    use_cache: bool = True
    save_history: bool = True


class DetectRequest(BaseModel):
    text: str


# REST Endpoints
@app.get("/")
async def serve_index():
    index_file = os.path.join(os.path.dirname(__file__), "..", "web", "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)
    return {"message": "Offline Translator API is online. Visit /gradio for interactive UI."}


@app.get("/api/languages")
async def get_languages():
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in LANG_DISPLAY_NAMES.items()
        ]
    }


@app.post("/api/translate")
async def api_translate(req: TranslationRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    engine: TranslatorEngine = getattr(app.state, "engine", None)
    if engine is None:
        engine = TranslatorEngine.get_instance()

    # Concurrency control: prevent event-loop freeze & memory thrashing
    async with INFERENCE_SEMAPHORE:
        res = await asyncio.to_thread(
            engine.translate,
            req.text,
            req.source_lang,
            req.target_lang,
            req.use_cache,
            req.save_history,
        )
    return res


@app.post("/api/detect")
async def api_detect(req: DetectRequest):
    lang_code, confidence = detect_language(req.text)
    return {
        "detected_lang": lang_code,
        "name": LANG_DISPLAY_NAMES.get(lang_code, lang_code),
        "confidence": round(confidence, 2),
    }


@app.get("/api/dictionary/{word}")
async def api_dictionary(word: str):
    entry = LexiconService.lookup(word)
    if not entry:
        return {"found": False, "word": word}
    return {"found": True, **entry}


@app.get("/api/history")
async def api_history(limit: int = 50):
    return {"history": HistoryService.list_recent(limit)}


@app.post("/api/history/favorite/{record_id}")
async def api_toggle_favorite(record_id: int):
    HistoryService.toggle_favorite(record_id)
    return {"status": "ok", "record_id": record_id}


@app.post("/api/history/clear")
async def api_clear_history():
    HistoryService.clear()
    return {"status": "cleared"}


# Mount Gradio into FastAPI at /gradio
gradio_demo = create_gradio_demo()
app = gr.mount_gradio_app(app, gradio_demo, path="/gradio")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=False)
