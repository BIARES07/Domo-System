import base64
import json
from typing import Any, Dict, List
from datetime import datetime
import hashlib

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
    def apply_seed_rotation(data: Any, request_time: int) -> Any:
        """
        Trap: Seed Rotation.
        If the request_time is "too old" relative to now (e.g. session > 1 hour),
        return the data as a Base64 string instead of JSON.
        """
        current_time = int(datetime.now().timestamp())
        # We simulate that the session started at 'request_time'
        # In this trap, if the diff is > 3600 seconds (1 hour), we "corrupt" the data
        if abs(current_time - request_time) > 3600:
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

gamemaster_v2 = GamemasterV2()
