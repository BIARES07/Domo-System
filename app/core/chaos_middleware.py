import asyncio
import random
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.state import state

class ChaosMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Chaos only affects intern endpoints
        if not request.url.path.startswith("/api/v1/intern"):
            return await call_next(request)

        # Rate Limit / Random Failures trap
        trap_info = state.traps.get("random_failures", {})
        is_active = trap_info.get("is_active", False)
        
        if is_active:
            severity = trap_info.get("severity", 0.1)
            
            if random.random() < severity:
                error_types = [
                    (status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error"),
                    (status.HTTP_429_TOO_MANY_REQUESTS, "Too Many Requests"),
                    (status.HTTP_503_SERVICE_UNAVAILABLE, "Service Unavailable")
                ]
                err_code, err_msg = random.choice(error_types)
                return JSONResponse(
                    status_code=err_code,
                    content={"detail": err_msg}
                )

        # Delay trap
        delay_info = state.traps.get("latency", {})
        is_delay_active = delay_info.get("is_active", False)
        
        if is_delay_active:
            severity = delay_info.get("severity", 0.5)
            
            if random.random() < severity:
                # Sleep between 1 to 5 seconds
                delay = random.uniform(1.0, 5.0)
                await asyncio.sleep(delay)

        return await call_next(request)
