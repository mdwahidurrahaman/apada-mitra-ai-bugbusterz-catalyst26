"""
In-memory Rate Limiter
Simple fixed-window limiter suitable for one-process deployments.
"""

import os
import time
import threading
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        self.max_requests = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "120"))
        self.requests = defaultdict(deque)
        self._lock = threading.Lock()
        
        # Cleanup thread to prevent memory leak
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def _cleanup_loop(self):
        """Periodically removes old entries from the requests dictionary to prevent memory leak."""
        while True:
            time.sleep(self.window_seconds * 2)
            now = time.time()
            with self._lock:
                keys_to_delete = []
                for key, bucket in self.requests.items():
                    while bucket and bucket[0] <= now - self.window_seconds:
                        bucket.popleft()
                    if not bucket:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self.requests[key]

    async def dispatch(self, request, call_next):
        if request.url.path in {"/", "/health"}:
            return await call_next(request)

        client_host = request.client.host if request.client else "unknown"
        key = f"{client_host}:{request.url.path}"
        now = time.time()
        
        with self._lock:
            bucket = self.requests[key]

            while bucket and bucket[0] <= now - self.window_seconds:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "message": "Too many requests. Please try again later.",
                        "data": None,
                        "error": {
                            "code": "RATE_LIMITED",
                            "details": {
                                "window_seconds": self.window_seconds,
                                "max_requests": self.max_requests
                            }
                        }
                    }
                )

            bucket.append(now)
        
        return await call_next(request)
