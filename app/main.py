import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.database import engine, Base
from app.db import crud
from app.core.state import state

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup actions before app starts accepting requests
    logger.info("Initializing database...")
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
        
    # Load initial trap states from SQLite to Memory
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        traps_in_db = await crud.get_all_chaos_configs(session)
        for t in traps_in_db:
            state.traps[t.trap_name] = {
                "is_active": t.is_active,
                "severity": t.severity
            }
        
    yield
    
    # Cleanup actions when app is shutting down
    await engine.dispose()

from app.core.auth_middleware import DomoAuthMiddleware
from app.core.chaos_middleware import ChaosMiddleware
from app.core.metrics_middleware import MetricsMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import init_router, intern_router, admin_router

app = FastAPI(
    title="Sistema DOMO API",
    description="Hostile API Gateway for Intern Challenge and Admin Control Panel",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files for the Game Master Dashboard
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Los middlewares se ejecutan de abajo hacia arriba (el último añadido es el primero en recibir el request)
app.add_middleware(ChaosMiddleware)
app.add_middleware(DomoAuthMiddleware)
app.add_middleware(MetricsMiddleware)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(init_router.router, prefix="/api/v1")
app.include_router(intern_router.router, prefix="/api/v1")
app.include_router(admin_router.router, prefix="/api/v1")

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "message": "DOMO Gateway is running"}
