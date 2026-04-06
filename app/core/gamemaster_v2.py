import base64
import json
from typing import Any, Dict, List
from datetime import datetime
import time

class GamemasterV2:
    @staticmethod
    def apply_schema_drift(data: Any) -> Any:
        """
        Trap: Schema Drift.
        Changes numeric types to strings with units to break strict type checking.
        Example: 120.5 -> "120.5 km/s"
        """
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    # Deterministically add units based on key name
                    unit = " units"
                    if "vel" in k.lower() or "motion" in k.lower(): unit = " km/s"
                    elif "alt" in k.lower(): unit = " km"
                    elif "lat" in k.lower() or "lon" in k.lower() or "inc" in k.lower(): unit = " deg"
                    new_dict[k] = f"{v}{unit}"
                else:
                    new_dict[k] = GamemasterV2.apply_schema_drift(v)
            return new_dict
        elif isinstance(data, list):
            return [GamemasterV2.apply_schema_drift(item) for item in data]
        else:
            return data

    @staticmethod
    def apply_inconsistent_paging(data: List[Any], range_header: str) -> Dict[str, Any]:
        """
        Trap: Inconsistent Paging.
        Only returns a slice of data if X-Domo-Range header is not present or incorrect.
        """
        # Expected format: "items=0-4"
        limit = 3 # Very small limit to be annoying
        start = 0
        
        if range_header and range_header.startswith("items="):
            try:
                parts = range_header.replace("items=", "").split("-")
                start = int(parts[0])
                end = int(parts[1])
                limit = (end - start) + 1
            except:
                pass

        total = len(data)
        sliced_data = data[start:start+limit]
        
        return {
            "items": sliced_data,
            "total_count": total,
            "range": f"{start}-{start+len(sliced_data)-1}",
            "next_range": f"{start+limit}-{start+limit+limit-1}" if start+limit < total else None
        }

    @staticmethod
    def apply_seed_rotation(data: Any, session_started_at: float = None) -> Any:
        """
        Trap: Seed Rotation.
        If the authenticated session is older than 1 hour,
        return the data as a Base64 string instead of JSON.
        """
        if session_started_at is None:
            return data

        current_time = int(time.time())
        if abs(current_time - int(session_started_at)) > 3600:
            json_str = json.dumps(data)
            encoded = base64.b64encode(json_str.encode()).decode()
            return {
                "status": "SESSION_ENCRYPTED_UPGRADE_REQUIRED",
                "payload_buffer": encoded,
                "hint": "Cryptographic security handshake required. Re-authenticate to decrypt stream."
            }
        return data

    @staticmethod
    def get_dynamic_path(base_path: str) -> str:
        """
        Trap: Dynamic HATEOAS.
        Appends the current date to the path to break hardcoded clients.
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"{base_path}/{date_str}"

    @staticmethod
    def apply_launch_window_fragmentation(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Trap: Launch Window Fragmentation.
        Converts flat launch rows into a manifest packet with nested timing data.
        """
        manifest = []
        for launch in data:
            manifest.append(
                {
                    "mission_id": launch.get("mission_id"),
                    "mission_name": launch.get("mission_name"),
                    "provider": launch.get("provider"),
                    "vehicle": launch.get("vehicle"),
                    "launch_site": launch.get("launch_site"),
                    "orbit_class": launch.get("orbit_class"),
                    "payload": launch.get("payload"),
                    "readiness": launch.get("readiness"),
                    "mission_brief": launch.get("mission_brief"),
                    "window_packet": {
                        "open": launch.get("window_open_utc"),
                        "close": launch.get("window_close_utc"),
                    },
                    "launch_vector": f"{launch.get('status', 'UNKNOWN')}|{launch.get('countdown', 'T-00H 00M')}",
                }
            )

        return {
            "manifest": manifest,
            "window_count": len(manifest),
            "sync_mode": "fragmented",
        }

    @staticmethod
    def apply_conjunction_signal_scramble(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Trap: Conjunction Signal Scramble.
        Wraps conjunctions in a packet, flattens ranking into a string band and reorders by TCA.
        """
        alerts = []
        for alert in sorted(data, key=lambda item: item.get("tca_utc", "")):
            alerts.append(
                {
                    "event_id": alert.get("event_id"),
                    "primary_name": alert.get("primary_name"),
                    "primary_norad_id": alert.get("primary_norad_id"),
                    "secondary_name": alert.get("secondary_name"),
                    "secondary_norad_id": alert.get("secondary_norad_id"),
                    "tca_utc": alert.get("tca_utc"),
                    "threat_band": f"R-{int(alert.get('risk_score', 0)):03d}",
                    "geometry": {
                        "miss_km": alert.get("miss_distance_km"),
                        "rel_vel_kms": alert.get("relative_velocity_kms"),
                    },
                    "alert_level": alert.get("alert_level"),
                    "recommended_action": alert.get("recommended_action"),
                }
            )

        return {
            "alerts": alerts,
            "ordering": "chronological",
            "operator_hint": "Normalize threat_band and geometry before ranking.",
        }

gamemaster_v2 = GamemasterV2()
