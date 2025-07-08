import threading
import time
from typing import Callable

from fastapi import Depends, HTTPException, Request, status

# In-memory store for rate limiting (per IP)
RATE_LIMIT = 20  # requests
RATE_PERIOD = 60  # seconds
rate_limit_store = {}
rate_limit_lock = threading.Lock()

API_KEYS = {"supersecretapikey123"}  # Replace with your real keys or load from config


async def rate_limiter(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    with rate_limit_lock:
        entry = rate_limit_store.get(ip, {"count": 0, "start": now})
        if now - entry["start"] > RATE_PERIOD:
            # Reset window
            entry = {"count": 1, "start": now}
        else:
            entry["count"] += 1
        rate_limit_store[ip] = entry
        if entry["count"] > RATE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {RATE_LIMIT} requests per {RATE_PERIOD} seconds",
            )


async def api_key_auth(request: Request):
    api_key = request.headers.get("x-api-key")
    if not api_key or api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key"
        )
