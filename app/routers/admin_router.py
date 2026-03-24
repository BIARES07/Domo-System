from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

from app.services.nasa_client import nasa_client
from app.services.celestrak_client import celestrak_client
from app.core.state import state
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import crud, schemas

router = APIRouter(prefix="/admin", tags=["Admin - Command Center"])

# No Chaos or Auth middlewares will block this because they are scoped to /intern

@router.get("/dashboard/data")
async def get_dashboard_data():
    """Aggregated endpoint for the Admin UI"""
    try:
        weather = await nasa_client.get_donki_flares()
        neos = await nasa_client.get_neows()
        satellites = await celestrak_client.get_active_satellites()
        apod = await nasa_client.get_apod()
        
        return {
            "weather": weather,
            "neos": neos,
            "satellites": satellites[:50], # Send more data to admin
            "apod": apod
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", response_model=List[schemas.TraineeMetricResponse])
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """Get latest metrics from the trainee accessing the intern API"""
    return await crud.get_trainee_metrics(db, limit=50)

@router.get("/traps", response_model=List[schemas.ChaosConfigResponse])
async def get_all_traps(db: AsyncSession = Depends(get_db)):
    """Get all trap configurations from DB"""
    return await crud.get_all_chaos_configs(db)

@router.post("/traps/{trap_name}", response_model=schemas.ChaosConfigResponse)
async def update_trap(trap_name: str, config: schemas.ChaosConfigUpdate, db: AsyncSession = Depends(get_db)):
    """Update trap state and sync to in-memory state for fast access by middleware"""
    updated_config = await crud.update_chaos_config(db, trap_name, config)
    if not updated_config:
        # Create it if it doesn't exist
        new_config = schemas.ChaosConfigCreate(
            trap_name=trap_name,
            is_active=config.is_active if config.is_active is not None else False,
            severity=config.severity if config.severity is not None else 0.0
        )
        updated_config = await crud.create_chaos_config(db, new_config)
    
    # Sync to In-Memory State
    state.traps[trap_name] = {
        "is_active": updated_config.is_active,
        "severity": updated_config.severity
    }
    
    return updated_config
