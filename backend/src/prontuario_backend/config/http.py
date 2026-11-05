import hashlib
import json
import logging
import time
from uuid import uuid4

from prometheus_client import CollectorRegistry, Counter, Histogram
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("prontuario.requests")


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings):
        super().__init__(app)
        self.settings = settings
        self.windows = {}
        self.redis = None
        if settings.redis_url:
            options = {
                "socket_connect_timeout": settings.redis_connect_timeout,
                "socket_timeout": settings.redis_socket_timeout,
                "retry": Retry(NoBackoff(), 0),
            }
            if settings.redis_url.get_secret_value().startswith("rediss://"):
                options.update(ssl_cert_reqs="required", ssl_check_hostname=True)
                if settings.redis_ssl_ca:
                    options["ssl_ca_certs"] = settings.redis_ssl_ca
            self.redis = Redis.from_url(settings.redis_url.get_secret_value(), **options)
        self.registry = CollectorRegistry()
        self.count = Counter("http_requests_total", "Requests", ["route", "status"], registry=self.registry)
        self.duration = Histogram("http_duration_seconds", "Duration", ["route"], registry=self.registry)

    async def dispatch(self, request, call_next):
        started = time.monotonic()
        request_id = str(uuid4())
        request.state.request_id = request_id
        response = None
        if request.url.path.startswith("/api/"):
            client = request.client.host if request.client else "unknown"
            key = hashlib.sha256(client.encode()).hexdigest()
            try:
                if self.redis:
                    count = await self.redis.eval("local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n", 1, "rate:" + key)
                else:
                    now = time.monotonic()
                    self.windows = {k: v for k, v in self.windows.items() if now - v[0] < 60}
                    start, count = self.windows.get(key, (now, 0))
                    count += 1
                    if key not in self.windows and len(self.windows) >= 10000:
                        raise RuntimeError("limiter capacity")
                    self.windows[key] = (start, count)
                if count > self.settings.rate_limit:
                    response = JSONResponse({"error": {"code": "rate_limited", "request_id": request_id}}, 429, headers={"Retry-After": "60"})
            except (RedisError, RuntimeError):
                response = JSONResponse({"error": {"code": "temporarily_unavailable", "request_id": request_id}}, 503)
        if response is None:
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > self.settings.max_body_bytes:
                    response = JSONResponse({"error": {"code": "body_too_large", "request_id": request_id}}, 413)
                    break
                body.extend(chunk)
            if response is None:
                request._body = bytes(body)
                try:
                    response = await call_next(request)
                except Exception:  # noqa: BLE001 - sanitize unhandled errors at the HTTP boundary
                    response = JSONResponse({"error": {"code": "internal_error", "request_id": request_id}}, 500)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store"
        if self.settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        route = request.scope.get("route")
        label = getattr(route, "path", "unmatched")
        elapsed = time.monotonic() - started
        self.count.labels(label, str(response.status_code)).inc()
        self.duration.labels(label).observe(elapsed)
        logger.info(json.dumps({"request_id": request_id, "method": request.method, "route": label,
                                "status": response.status_code, "duration_ms": round(elapsed * 1000, 2)}))
        request.app.state.metrics = self.registry
        return response
