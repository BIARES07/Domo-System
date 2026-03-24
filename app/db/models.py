from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.sql import func
from app.db.database import Base

class TraineeMetric(Base):
    __tablename__ = "trainee_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint_accessed = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    response_time_ms = Column(Float, nullable=False)
    status_code = Column(Integer, nullable=False)
    client_ip = Column(String, nullable=True)

class ChaosConfig(Base):
    __tablename__ = "chaos_config"
    
    id = Column(Integer, primary_key=True, index=True)
    trap_name = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    severity = Column(Float, default=0.0, nullable=False) # 0.0 to 1.0 representing percentage
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
