from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class TraineeMetricCreate(BaseModel):
    endpoint_accessed: str
    response_time_ms: float
    status_code: int
    client_ip: Optional[str] = None

class TraineeMetricResponse(TraineeMetricCreate):
    id: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ChaosConfigCreate(BaseModel):
    trap_name: str
    is_active: bool = False
    severity: float = Field(default=0.0, ge=0.0, le=1.0)

class ChaosConfigUpdate(BaseModel):
    is_active: Optional[bool] = None
    severity: Optional[float] = Field(default=None, ge=0.0, le=1.0)

class ChaosConfigResponse(ChaosConfigCreate):
    id: int
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)
