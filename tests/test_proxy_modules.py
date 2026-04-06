import hashlib
import time

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.state import state
from app.main import app
from app.services.celestrak_client import celestrak_client
from app.services.nasa_client import nasa_client
from app.services.orbital_ops_service import orbital_ops_service


def build_auth_headers():
    domo_time = str(int(time.time()))
    domo_token = hashlib.sha256(f"{settings.SECRET_SEED}{domo_time}".encode("utf-8")).hexdigest()
    return {
        "X-Domo-Time": domo_time,
        "X-Domo-Token": domo_token,
    }


def build_session_headers(session_id: str):
    headers = build_auth_headers()
    headers["X-Domo-Session"] = session_id
    return headers


@pytest.mark.asyncio
async def test_init_exposes_launch_and_conjunction_links():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/init/")

    assert response.status_code == 200
    body = response.json()
    links = body["links"]
    assert body["session_id"]
    assert links["launches"].endswith("/launches")
    assert links["conjunctions"].endswith("/conjunctions")


@pytest.mark.asyncio
async def test_explicit_unknown_session_is_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/intern/apod",
            headers=build_session_headers("missing-session-id"),
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or unknown X-Domo-Session"


@pytest.mark.asyncio
async def test_launches_endpoint_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/intern/launches")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_launches_endpoint_returns_manifest(monkeypatch):
    async def fake_get_launch_windows():
        return [
            {
                "mission_id": "LCH-TEST-01",
                "mission_name": "Test Mission",
                "provider": "DOMO Test Range",
                "vehicle": "Vector-9",
                "launch_site": "Pad 7",
                "orbit_class": "LEO",
                "payload": "Test payload",
                "window_open_utc": "2026-04-05T14:00:00+00:00",
                "window_close_utc": "2026-04-05T15:30:00+00:00",
                "countdown": "T-02H 00M",
                "status": "FINAL POLL",
                "readiness": "GREEN",
                "mission_brief": "Dry-run manifest",
            }
        ]

    monkeypatch.setattr(orbital_ops_service, "get_launch_windows", fake_get_launch_windows)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/intern/launches", headers=build_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body[0]["mission_name"] == "Test Mission"
    assert body[0]["status"] == "FINAL POLL"


@pytest.mark.asyncio
async def test_launches_endpoint_fragments_manifest_when_trap_active(monkeypatch):
    async def fake_get_launch_windows():
        return [
            {
                "mission_id": "LCH-TEST-01",
                "mission_name": "Test Mission",
                "provider": "DOMO Test Range",
                "vehicle": "Vector-9",
                "launch_site": "Pad 7",
                "orbit_class": "LEO",
                "payload": "Test payload",
                "window_open_utc": "2026-04-05T14:00:00+00:00",
                "window_close_utc": "2026-04-05T15:30:00+00:00",
                "countdown": "T-02H 00M",
                "status": "FINAL POLL",
                "readiness": "GREEN",
                "mission_brief": "Dry-run manifest",
            }
        ]

    monkeypatch.setattr(orbital_ops_service, "get_launch_windows", fake_get_launch_windows)
    monkeypatch.setitem(state.traps["launch_window_fragmentation"], "is_active", True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/intern/launches", headers=build_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["window_count"] == 1
    assert body["manifest"][0]["window_packet"]["open"] == "2026-04-05T14:00:00+00:00"
    assert body["manifest"][0]["launch_vector"] == "FINAL POLL|T-02H 00M"


@pytest.mark.asyncio
async def test_conjunctions_endpoint_returns_alerts(monkeypatch):
    async def fake_get_conjunction_alerts():
        return [
            {
                "event_id": "CNJ-10001-10002",
                "primary_name": "SAT-A",
                "primary_norad_id": 10001,
                "secondary_name": "SAT-B",
                "secondary_norad_id": 10002,
                "tca_utc": "2026-04-05T13:20:00+00:00",
                "miss_distance_km": 4.8,
                "relative_velocity_kms": 8.2,
                "risk_score": 81,
                "alert_level": "HIGH",
                "recommended_action": "Escalate to flight dynamics and verify covariance updates.",
            }
        ]

    monkeypatch.setattr(orbital_ops_service, "get_conjunction_alerts", fake_get_conjunction_alerts)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/intern/conjunctions", headers=build_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body[0]["event_id"] == "CNJ-10001-10002"
    assert body[0]["alert_level"] == "HIGH"


@pytest.mark.asyncio
async def test_conjunctions_endpoint_scrambles_signal_when_trap_active(monkeypatch):
    async def fake_get_conjunction_alerts():
        return [
            {
                "event_id": "CNJ-10001-10002",
                "primary_name": "SAT-A",
                "primary_norad_id": 10001,
                "secondary_name": "SAT-B",
                "secondary_norad_id": 10002,
                "tca_utc": "2026-04-05T13:20:00+00:00",
                "miss_distance_km": 4.8,
                "relative_velocity_kms": 8.2,
                "risk_score": 81,
                "alert_level": "HIGH",
                "recommended_action": "Escalate to flight dynamics and verify covariance updates.",
            }
        ]

    monkeypatch.setattr(orbital_ops_service, "get_conjunction_alerts", fake_get_conjunction_alerts)
    monkeypatch.setitem(state.traps["conjunction_signal_scramble"], "is_active", True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/intern/conjunctions", headers=build_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["ordering"] == "chronological"
    assert body["alerts"][0]["threat_band"] == "R-081"
    assert body["alerts"][0]["geometry"]["miss_km"] == 4.8


@pytest.mark.asyncio
async def test_admin_dashboard_data_includes_orbital_modules(monkeypatch):
    async def fake_get_donki_flares():
        return [{"flrID": "FLR-1"}]

    async def fake_get_neows():
        return {"element_count": 1, "near_earth_objects": {}}

    async def fake_get_active_satellites():
        return [{"name": "SAT-A", "norad_id": 10001}]

    async def fake_get_apod():
        return {"title": "Mock APOD"}

    async def fake_get_launch_windows():
        return [{"mission_id": "LCH-TEST-01", "mission_name": "Test Mission"}]

    def fake_build_conjunction_feed(_satellites):
        return [{"event_id": "CNJ-10001-10002", "alert_level": "HIGH"}]

    monkeypatch.setattr(nasa_client, "get_donki_flares", fake_get_donki_flares)
    monkeypatch.setattr(nasa_client, "get_neows", fake_get_neows)
    monkeypatch.setattr(celestrak_client, "get_active_satellites", fake_get_active_satellites)
    monkeypatch.setattr(nasa_client, "get_apod", fake_get_apod)
    monkeypatch.setattr(orbital_ops_service, "get_launch_windows", fake_get_launch_windows)
    monkeypatch.setattr(orbital_ops_service, "build_conjunction_feed", fake_build_conjunction_feed)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/admin/dashboard/data")

    assert response.status_code == 200
    body = response.json()
    assert body["launches"][0]["mission_id"] == "LCH-TEST-01"
    assert body["conjunctions"][0]["event_id"] == "CNJ-10001-10002"
    assert body["apod"]["title"] == "Mock APOD"


@pytest.mark.asyncio
async def test_seed_rotation_uses_session_age_with_fresh_request(monkeypatch):
    async def fake_get_apod():
        return {"title": "Encrypted APOD", "media_type": "image", "url": "https://example.com/apod.jpg"}

    monkeypatch.setattr(nasa_client, "get_apod", fake_get_apod)
    monkeypatch.setitem(state.traps["seed_rotation"], "is_active", True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        init_response = await ac.get("/api/v1/init/")
        session_id = init_response.json()["session_id"]
        state.sessions[session_id] = time.time() - 7200

        response = await ac.get(
            "/api/v1/intern/apod",
            headers=build_session_headers(session_id),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SESSION_ENCRYPTED_UPGRADE_REQUIRED"
    assert body["payload_buffer"]