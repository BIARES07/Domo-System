from typing import Dict, Any

class AppState:
    def __init__(self):
        # In-memory storage for active traps to completely eliminate Redis
        # format: {"trap_name": {"is_active": bool, "severity": float}}
        self.traps: Dict[str, Dict[str, Any]] = {
            "json_mutation": {"is_active": False, "severity": 1.0},
            "random_failures": {"is_active": False, "severity": 0.2},
            "latency": {"is_active": False, "severity": 0.5},
            "binary_tle": {"is_active": False, "severity": 1.0},
            # Advanced Traps (V2)
            "schema_drift": {"is_active": False, "severity": 1.0},
            "inconsistent_paging": {"is_active": False, "severity": 1.0},
            "seed_rotation": {"is_active": False, "severity": 1.0},
            "dynamic_hateoas": {"is_active": False, "severity": 1.0}
        }

# Global state instance
state = AppState()
