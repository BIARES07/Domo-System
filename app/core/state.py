import time
from typing import Dict, Any, Optional, Tuple

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
            "dynamic_hateoas": {"is_active": False, "severity": 1.0},
            "launch_window_fragmentation": {"is_active": False, "severity": 1.0},
            "conjunction_signal_scramble": {"is_active": False, "severity": 1.0}
        }
        # Session registry used by advanced auth-sensitive traps like seed rotation.
        self.sessions: Dict[str, float] = {}
        self.session_ttl_seconds = 6 * 3600

    def register_session(self, session_id: str, created_at: Optional[float] = None) -> float:
        self.prune_sessions()
        started_at = float(created_at if created_at is not None else time.time())
        self.sessions[session_id] = started_at
        return started_at

    def get_session_started_at(self, session_id: str) -> Optional[float]:
        return self.sessions.get(session_id)

    def get_or_create_fallback_session(self, fingerprint: str, created_at: Optional[float] = None) -> Tuple[str, float]:
        session_id = f"fallback:{fingerprint}"
        started_at = self.get_session_started_at(session_id)
        if started_at is None:
            started_at = self.register_session(session_id, created_at=created_at)
        return session_id, started_at

    def prune_sessions(self) -> None:
        cutoff = time.time() - self.session_ttl_seconds
        expired_sessions = [session_id for session_id, started_at in self.sessions.items() if started_at < cutoff]
        for session_id in expired_sessions:
            self.sessions.pop(session_id, None)

# Global state instance
state = AppState()
