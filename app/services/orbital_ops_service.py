from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence

from app.services.celestrak_client import celestrak_client


class OrbitalOpsService:
    def __init__(self):
        self._cache_ttl = timedelta(minutes=10)
        self._conjunction_cache: Optional[List[Dict[str, Any]]] = None
        self._conjunction_cache_time: Optional[datetime] = None
        self._launch_templates = [
            {
                "mission_name": "Aquila Relay",
                "provider": "DOMO Strategic Launch",
                "vehicle": "Aquila Heavy",
                "launch_site": "Guiana Maritime Complex",
                "orbit_class": "MEO Communications",
                "payload": "Quantum relay pair",
                "window_offset_hours": 2,
                "window_minutes": 95,
                "readiness": "GREEN",
                "mission_brief": "Deploy dual relays to reinforce deep-space comms redundancy.",
            },
            {
                "mission_name": "Helios Surveyor",
                "provider": "NASA Partner Grid",
                "vehicle": "Atlas Nova",
                "launch_site": "Vandenberg SLC-8",
                "orbit_class": "Sun-Synchronous",
                "payload": "Solar weather mapper",
                "window_offset_hours": 9,
                "window_minutes": 70,
                "readiness": "AMBER",
                "mission_brief": "Inject heliophysics mapper into dawn-dusk orbit for flare response.",
            },
            {
                "mission_name": "Perseus Cargo-12",
                "provider": "Orbital Freight Union",
                "vehicle": "Perseus Cargo",
                "launch_site": "Tanegashima Pad 2",
                "orbit_class": "LEO Logistics",
                "payload": "Station consumables and avionics spares",
                "window_offset_hours": 20,
                "window_minutes": 120,
                "readiness": "GREEN",
                "mission_brief": "Routine resupply mission with high-value avionics hardware.",
            },
            {
                "mission_name": "Nyx Pathfinder",
                "provider": "ESA Expeditionary Ops",
                "vehicle": "Ariane NX",
                "launch_site": "Kourou ELA-4",
                "orbit_class": "Trans-Lunar Injection",
                "payload": "Autonomous nav beacon demonstrator",
                "window_offset_hours": 34,
                "window_minutes": 45,
                "readiness": "AMBER",
                "mission_brief": "Test precision navigation beacons for cislunar transfer lanes.",
            },
        ]
        self._fallback_satellites = [
            {
                "name": "DOMO-SENTINEL-1",
                "norad_id": 91001,
                "inclination": 53.2,
                "raan": 14.5,
                "eccentricity": 0.00031,
                "mean_motion": 15.12,
            },
            {
                "name": "DOMO-SENTINEL-2",
                "norad_id": 91002,
                "inclination": 54.1,
                "raan": 18.3,
                "eccentricity": 0.00029,
                "mean_motion": 15.09,
            },
            {
                "name": "AURORA-LINK-A",
                "norad_id": 91003,
                "inclination": 97.8,
                "raan": 122.2,
                "eccentricity": 0.00112,
                "mean_motion": 14.84,
            },
            {
                "name": "AURORA-LINK-B",
                "norad_id": 91004,
                "inclination": 97.3,
                "raan": 127.4,
                "eccentricity": 0.00108,
                "mean_motion": 14.87,
            },
            {
                "name": "KESTREL-NAV-4",
                "norad_id": 91005,
                "inclination": 65.6,
                "raan": 201.9,
                "eccentricity": 0.00074,
                "mean_motion": 14.31,
            },
            {
                "name": "KESTREL-NAV-8",
                "norad_id": 91006,
                "inclination": 66.0,
                "raan": 208.7,
                "eccentricity": 0.00079,
                "mean_motion": 14.27,
            },
        ]

    async def get_launch_windows(self) -> List[Dict[str, Any]]:
        return self.build_launch_manifest()

    async def get_conjunction_alerts(self) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        if self._conjunction_cache and self._conjunction_cache_time:
            if (now - self._conjunction_cache_time) < self._cache_ttl:
                return self._conjunction_cache

        try:
            satellites = await celestrak_client.get_active_satellites()
        except Exception:
            satellites = []

        alerts = self.build_conjunction_feed(satellites, now=now)
        self._conjunction_cache = alerts
        self._conjunction_cache_time = now
        return alerts

    def build_launch_manifest(self, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        now = (now or datetime.now(timezone.utc)).replace(microsecond=0)
        launches: List[Dict[str, Any]] = []

        for index, template in enumerate(self._launch_templates, start=1):
            window_open = now + timedelta(hours=template["window_offset_hours"])
            window_close = window_open + timedelta(minutes=template["window_minutes"])
            launches.append(
                {
                    "mission_id": f"LCH-{now.strftime('%Y%m%d')}-{index:02d}",
                    "mission_name": template["mission_name"],
                    "provider": template["provider"],
                    "vehicle": template["vehicle"],
                    "launch_site": template["launch_site"],
                    "orbit_class": template["orbit_class"],
                    "payload": template["payload"],
                    "window_open_utc": window_open.isoformat(),
                    "window_close_utc": window_close.isoformat(),
                    "countdown": self._format_countdown(now, window_open, window_close),
                    "status": self._launch_status(now, window_open, window_close),
                    "readiness": template["readiness"],
                    "mission_brief": template["mission_brief"],
                }
            )

        return launches

    def build_conjunction_feed(
        self,
        satellites: Sequence[Dict[str, Any]],
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        now = (now or datetime.now(timezone.utc)).replace(microsecond=0)
        candidates = [
            sat
            for sat in satellites
            if sat.get("name") and sat.get("norad_id") is not None
        ]
        if len(candidates) < 4:
            candidates = list(self._fallback_satellites)

        pool = list(candidates[:8])
        if len(pool) < 4:
            pool = list(self._fallback_satellites)

        alerts: List[Dict[str, Any]] = []
        max_pairs = max(2, min(4, len(pool) // 2))

        for index in range(max_pairs):
            primary = pool[index]
            secondary = pool[-(index + 1)]
            if primary["norad_id"] == secondary["norad_id"]:
                continue

            inclination_gap = abs(float(primary.get("inclination", 0.0)) - float(secondary.get("inclination", 0.0)))
            raan_gap_raw = abs(float(primary.get("raan", 0.0)) - float(secondary.get("raan", 0.0)))
            raan_gap = min(raan_gap_raw, 360.0 - raan_gap_raw)
            mean_motion_gap = abs(float(primary.get("mean_motion", 0.0)) - float(secondary.get("mean_motion", 0.0)))
            eccentricity_gap = abs(float(primary.get("eccentricity", 0.0)) - float(secondary.get("eccentricity", 0.0)))

            miss_distance_km = round(
                max(
                    1.4,
                    inclination_gap * 4.1 + raan_gap * 0.22 + mean_motion_gap * 26.0 + eccentricity_gap * 9000.0,
                ),
                2,
            )
            relative_velocity_kms = round(7.1 + mean_motion_gap * 0.95 + inclination_gap * 0.05, 2)
            risk_score = int(
                max(
                    18,
                    min(
                        98,
                        round(100 - miss_distance_km * 1.35 + mean_motion_gap * 12 + eccentricity_gap * 3500),
                    ),
                )
            )
            alert_level = self._conjunction_level(risk_score)
            tca = now + timedelta(minutes=25 + index * 47)

            alerts.append(
                {
                    "event_id": f"CNJ-{primary['norad_id']}-{secondary['norad_id']}",
                    "primary_name": primary["name"],
                    "primary_norad_id": primary["norad_id"],
                    "secondary_name": secondary["name"],
                    "secondary_norad_id": secondary["norad_id"],
                    "tca_utc": tca.isoformat(),
                    "miss_distance_km": miss_distance_km,
                    "relative_velocity_kms": relative_velocity_kms,
                    "risk_score": risk_score,
                    "alert_level": alert_level,
                    "recommended_action": self._conjunction_action(alert_level),
                }
            )

        alerts.sort(key=lambda item: (-item["risk_score"], item["miss_distance_km"]))
        return alerts

    def _format_countdown(self, now: datetime, window_open: datetime, window_close: datetime) -> str:
        if now > window_close:
            elapsed = now - window_close
            total_minutes = int(elapsed.total_seconds() // 60)
            return f"T+{total_minutes // 60:02d}H {total_minutes % 60:02d}M"

        if window_open <= now <= window_close:
            return "WINDOW OPEN"

        remaining = window_open - now
        total_minutes = int(remaining.total_seconds() // 60)
        return f"T-{total_minutes // 60:02d}H {total_minutes % 60:02d}M"

    def _launch_status(self, now: datetime, window_open: datetime, window_close: datetime) -> str:
        if now > window_close:
            return "LAUNCHED"
        if window_open <= now <= window_close:
            return "WINDOW OPEN"

        hours_to_launch = (window_open - now).total_seconds() / 3600
        if hours_to_launch <= 4:
            return "FINAL POLL"
        if hours_to_launch <= 12:
            return "GO/NO-GO"
        return "SCHEDULED"

    def _conjunction_level(self, risk_score: int) -> str:
        if risk_score >= 85:
            return "CRITICAL"
        if risk_score >= 65:
            return "HIGH"
        if risk_score >= 45:
            return "ELEVATED"
        return "MONITOR"

    def _conjunction_action(self, alert_level: str) -> str:
        if alert_level == "CRITICAL":
            return "Prepare immediate collision-avoidance burn review."
        if alert_level == "HIGH":
            return "Escalate to flight dynamics and verify covariance updates."
        if alert_level == "ELEVATED":
            return "Track next ephemeris refresh and confirm geometry trend."
        return "Continue passive monitoring with scheduled refresh."


orbital_ops_service = OrbitalOpsService()