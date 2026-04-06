import hashlib
import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.state import state

class DomoAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Exclude specific paths from auth
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json") or request.url.path == "/health":
            return await call_next(request)
            
        # Admin routes might have a different auth, for now we let them pass or check a different token
        # but let's assume we protect /api/v1/intern endpoints
        if request.url.path.startswith("/api/v1/intern"):
            domo_time = request.headers.get("X-Domo-Time")
            domo_token = request.headers.get("X-Domo-Token")

            if not domo_time or not domo_token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Missing X-Domo-Time or X-Domo-Token headers"}
                )

            try:
                request_time = int(domo_time)
                current_time = int(time.time())
                
                # Replay attack protection (e.g., max 30 seconds diff)
                if abs(current_time - request_time) > 30:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Timestamp expired or too far in the future"}
                    )
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid X-Domo-Time format"}
                )

            # Calculate expected hash
            payload = f"{settings.SECRET_SEED}{domo_time}".encode('utf-8')
            expected_hash = hashlib.sha256(payload).hexdigest()

            if expected_hash != domo_token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid cryptographic token"}
                )

            explicit_session_id = request.headers.get("X-Domo-Session")
            if explicit_session_id:
                session_started_at = state.get_session_started_at(explicit_session_id)
                if session_started_at is None:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Invalid or unknown X-Domo-Session"}
                    )
                request.state.domo_session_id = explicit_session_id
                request.state.domo_session_started_at = session_started_at
            else:
                client_ip = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("User-Agent", "unknown-agent")
                fingerprint = hashlib.sha256(f"{client_ip}:{user_agent}".encode("utf-8")).hexdigest()[:16]
                fallback_session_id, session_started_at = state.get_or_create_fallback_session(
                    fingerprint,
                    created_at=current_time,
                )
                request.state.domo_session_id = fallback_session_id
                request.state.domo_session_started_at = session_started_at

            request.state.domo_request_time = request_time

        return await call_next(request)
