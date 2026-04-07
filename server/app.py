"""
TR-143-kompatibel speedtest-server — FastAPI backend.
Endepunkter:
  GET  /download?size=10MB
  POST /upload
  GET  /ping
  GET  /speedtest/status
  GET  /           → index.html
"""

import os
import time
import socket
import logging
import json
from typing import Generator

from fastapi import FastAPI, Request, Response, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ── Config ────────────────────────────────────────────────────────────
PORT        = int(os.getenv("PORT", 8080))
MAX_SIZE_MB = int(os.getenv("MAX_SIZE_MB", 100))
SERVER_NAME = os.getenv("SERVER_NAME", "Heimnett SpeedTest")

START_TIME  = time.time()

# ── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("speedtest")

def log_event(client_ip: str, test_type: str, result: dict):
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "client_ip": client_ip,
        "test_type": test_type,
        **result,
    }
    logger.info(json.dumps(entry))

# ── App ─────────────────────────────────────────────────────────────
app = FastAPI(title="TR-143 SpeedTest Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# ── Helpers ───────────────────────────────────────────────────────────
SIZE_MAP = {
    "1mb":   1,
    "5mb":   5,
    "10mb":  10,
    "25mb":  25,
    "50mb":  50,
    "100mb": 100,
}

CHUNK = 64 * 1024  # 64 KiB streaming chunk

def parse_size(size_str: str) -> int:
    """Return size in bytes; raises HTTPException on invalid/too-large input."""
    key = size_str.lower()
    if key not in SIZE_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Ugyldig størrelse '{size_str}'. Støttede verdier: "
                   + ", ".join(k.upper() for k in SIZE_MAP),
        )
    mb = SIZE_MAP[key]
    if mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"Maks tillatt størrelse er {MAX_SIZE_MB} MB.",
        )
    return mb * 1024 * 1024

def random_stream(total_bytes: int) -> Generator[bytes, None, None]:
    """Yield pseudo-random bytes in CHUNK-sized pieces."""
    remaining = total_bytes
    block = os.urandom(CHUNK)
    while remaining > 0:
        send = min(CHUNK, remaining)
        yield block[:send]
        remaining -= send

# ── Endepunkter ──────────────────────────────────────────────────────────
@app.get("/ping")
async def ping(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    ts = int(time.time() * 1000)
    log_event(client_ip, "ping", {"latency_ms": None})
    return JSONResponse({"status": "ok", "timestamp": ts})

@app.get("/download")
async def download(request: Request, size: str = "10MB"):
    client_ip = request.client.host if request.client else "unknown"
    total = parse_size(size)
    t_start = time.perf_counter()

    def stream_and_log():
        for chunk in random_stream(total):
            yield chunk
        elapsed = time.perf_counter() - t_start
        mbps = (total * 8 / elapsed) / 1e6 if elapsed > 0 else 0
        log_event(client_ip, "download", {"size_bytes": total, "elapsed_s": round(elapsed, 3), "mbps": round(mbps, 2)})

    return StreamingResponse(
        stream_and_log(),
        media_type="application/octet-stream",
        headers={
            "Content-Length": str(total),
            "Cache-Control": "no-store",
            "Content-Disposition": f"attachment; filename=speedtest_{size}.bin",
        },
    )

@app.post("/upload")
async def upload(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    t_start = time.perf_counter()
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
    elapsed = time.perf_counter() - t_start
    mbps = (total * 8 / elapsed) / 1e6 if elapsed > 0 else 0
    log_event(client_ip, "upload", {"size_bytes": total, "elapsed_s": round(elapsed, 3), "mbps": round(mbps, 2)})
    return JSONResponse({
        "status": "ok",
        "bytes_received": total,
        "elapsed_s": round(elapsed, 3),
        "mbps": round(mbps, 2),
    })

@app.put("/upload")
async def upload_put(request: Request):
    return await upload(request)

@app.get("/speedtest/status")
async def status(request: Request):
    uptime = int(time.time() - START_TIME)
    try:
        hostname = socket.gethostname()
        server_ip = socket.gethostbyname(hostname)
    except Exception:
        hostname = "unknown"
        server_ip = "unknown"
    return JSONResponse({
        "server_name": SERVER_NAME,
        "version": "1.0.0",
        "uptime_s": uptime,
        "hostname": hostname,
        "server_ip": server_ip,
        "max_size_mb": MAX_SIZE_MB,
    })

# Static files (served last so API routes take priority)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# ── Main entry point for the application handling the static files, APIs, and functionality."""