import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.database import Base
from app.core.config import settings
from app.db import crud, schemas

async def seed_db():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with SessionLocal() as db:
        traps = [
            {"name": "json_mutation", "severity": 1.0, "active": False},
            {"name": "random_failures", "severity": 0.2, "active": False},
            {"name": "latency", "severity": 0.5, "active": False},
            {"name": "binary_tle", "severity": 1.0, "active": False},
            {"name": "schema_drift", "severity": 1.0, "active": False},
            {"name": "inconsistent_paging", "severity": 1.0, "active": False},
            {"name": "seed_rotation", "severity": 1.0, "active": False},
            {"name": "dynamic_hateoas", "severity": 1.0, "active": False},
            {"name": "launch_window_fragmentation", "severity": 1.0, "active": False},
            {"name": "conjunction_signal_scramble", "severity": 1.0, "active": False}
        ]
        
        for t in traps:
            existing = await crud.get_chaos_config(db, t["name"])
            if not existing:
                config = schemas.ChaosConfigCreate(
                    trap_name=t["name"],
                    severity=t["severity"],
                    is_active=t["active"]
                )
                await crud.create_chaos_config(db, config)
                print(f"Created trap: {t['name']}")
            else:
                print(f"Trap already exists: {t['name']}")
                
if __name__ == "__main__":
    asyncio.run(seed_db())
