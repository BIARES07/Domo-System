from datetime import datetime, timezone

from app.services.orbital_ops_service import OrbitalOpsService


def test_build_launch_manifest_has_expected_fields():
    service = OrbitalOpsService()
    now = datetime(2026, 4, 5, 12, 0, 0, tzinfo=timezone.utc)

    launches = service.build_launch_manifest(now=now)

    assert len(launches) == 4
    first_launch = launches[0]
    assert first_launch["mission_id"] == "LCH-20260405-01"
    assert first_launch["status"] == "FINAL POLL"
    assert first_launch["countdown"] == "T-02H 00M"
    assert first_launch["mission_name"] == "Aquila Relay"
    assert first_launch["window_open_utc"].startswith("2026-04-05T14:00:00")


def test_build_conjunction_feed_prioritizes_risk_order():
    service = OrbitalOpsService()
    now = datetime(2026, 4, 5, 12, 0, 0, tzinfo=timezone.utc)
    satellites = [
        {
            "name": "ALPHA-1",
            "norad_id": 10001,
            "inclination": 53.0,
            "raan": 10.0,
            "eccentricity": 0.00010,
            "mean_motion": 15.10,
        },
        {
            "name": "ALPHA-2",
            "norad_id": 10002,
            "inclination": 53.4,
            "raan": 12.2,
            "eccentricity": 0.00011,
            "mean_motion": 15.04,
        },
        {
            "name": "BETA-1",
            "norad_id": 10003,
            "inclination": 97.6,
            "raan": 118.0,
            "eccentricity": 0.00105,
            "mean_motion": 14.88,
        },
        {
            "name": "BETA-2",
            "norad_id": 10004,
            "inclination": 97.9,
            "raan": 122.4,
            "eccentricity": 0.00110,
            "mean_motion": 14.82,
        },
        {
            "name": "GAMMA-1",
            "norad_id": 10005,
            "inclination": 66.4,
            "raan": 200.3,
            "eccentricity": 0.00070,
            "mean_motion": 14.35,
        },
        {
            "name": "GAMMA-2",
            "norad_id": 10006,
            "inclination": 66.0,
            "raan": 206.8,
            "eccentricity": 0.00074,
            "mean_motion": 14.29,
        },
    ]

    alerts = service.build_conjunction_feed(satellites, now=now)

    assert len(alerts) >= 2
    assert alerts[0]["risk_score"] >= alerts[-1]["risk_score"]
    assert alerts[0]["event_id"].startswith("CNJ-")
    assert alerts[0]["alert_level"] in {"CRITICAL", "HIGH", "ELEVATED", "MONITOR"}
    assert "recommended_action" in alerts[0]
