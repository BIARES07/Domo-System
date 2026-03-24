import time
import asyncio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.database import AsyncSessionLocal
from app.db import crud, schemas

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Solo monitoreamos las rutas del pasante
        if not request.url.path.startswith("/api/v1/intern"):
            return await call_next(request)
            
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Disparamos la tarea de guardado en base de datos sin bloquear la respuesta
        async def save_metric():
            try:
                async with AsyncSessionLocal() as db:
                    metric = schemas.TraineeMetricCreate(
                        endpoint_accessed=request.url.path,
                        response_time_ms=process_time,
                        status_code=response.status_code,
                        client_ip=request.client.host if request.client else "unknown"
                    )
                    await crud.create_trainee_metric(db, metric)
            except Exception as e:
                print(f"Failed to save metric: {e}")
                
        asyncio.create_task(save_metric())
        
        return response
