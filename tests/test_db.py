import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.database import Base
from app.db import crud, schemas

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_and_get_metric():
    async with TestingSessionLocal() as session:
        metric_in = schemas.TraineeMetricCreate(
            endpoint_accessed="/api/v1/test",
            response_time_ms=120.5,
            status_code=200,
            client_ip="127.0.0.1"
        )
        metric = await crud.create_trainee_metric(session, metric_in)
        assert metric.id is not None
        assert metric.endpoint_accessed == "/api/v1/test"

        metrics = await crud.get_trainee_metrics(session)
        assert len(metrics) == 1
        assert metrics[0].response_time_ms == 120.5

@pytest.mark.asyncio
async def test_chaos_config_crud():
    async with TestingSessionLocal() as session:
        config_in = schemas.ChaosConfigCreate(
            trap_name="level_1_json_mutation",
            is_active=True,
            severity=0.5
        )
        config = await crud.create_chaos_config(session, config_in)
        assert config.trap_name == "level_1_json_mutation"
        assert config.is_active is True

        fetched_config = await crud.get_chaos_config(session, "level_1_json_mutation")
        assert fetched_config is not None
        assert fetched_config.severity == 0.5

        update_in = schemas.ChaosConfigUpdate(is_active=False, severity=0.8)
        updated_config = await crud.update_chaos_config(session, "level_1_json_mutation", update_in)
        assert updated_config.is_active is False
        assert updated_config.severity == 0.8
