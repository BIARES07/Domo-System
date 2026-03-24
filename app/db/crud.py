from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, desc
from typing import List, Optional

from app.db import models, schemas

# Trainee Metric CRUD
async def create_trainee_metric(db: AsyncSession, metric: schemas.TraineeMetricCreate) -> models.TraineeMetric:
    db_metric = models.TraineeMetric(**metric.model_dump())
    db.add(db_metric)
    await db.commit()
    await db.refresh(db_metric)
    return db_metric

async def get_trainee_metrics(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.TraineeMetric]:
    result = await db.execute(
        select(models.TraineeMetric)
        .order_by(desc(models.TraineeMetric.timestamp))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

# Chaos Config CRUD
async def get_chaos_config(db: AsyncSession, trap_name: str) -> Optional[models.ChaosConfig]:
    result = await db.execute(select(models.ChaosConfig).filter(models.ChaosConfig.trap_name == trap_name))
    return result.scalars().first()

async def get_all_chaos_configs(db: AsyncSession) -> List[models.ChaosConfig]:
    result = await db.execute(select(models.ChaosConfig))
    return result.scalars().all()

async def create_chaos_config(db: AsyncSession, config: schemas.ChaosConfigCreate) -> models.ChaosConfig:
    db_config = models.ChaosConfig(**config.model_dump())
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)
    return db_config

async def update_chaos_config(db: AsyncSession, trap_name: str, config_update: schemas.ChaosConfigUpdate) -> Optional[models.ChaosConfig]:
    db_config = await get_chaos_config(db, trap_name)
    if not db_config:
        return None
    
    update_data = config_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
        
    await db.commit()
    await db.refresh(db_config)
    return db_config
