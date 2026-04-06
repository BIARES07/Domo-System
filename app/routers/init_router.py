import uuid
import time
from fastapi import APIRouter, Request
from app.core.config import settings
from app.core.state import state
from app.core.gamemaster_v2 import gamemaster_v2

router = APIRouter(prefix="/init", tags=["Initialization"])

@router.get("/")
async def initialize_challenge(request: Request):
    """
    TSK-5.1: Nodo de Entrada y Pistas
    Delivers the base seed and initial instructions to the intern.
    """
    session_id = str(uuid.uuid4())
    state.register_session(session_id)
    
    links = {
        "self": "/api/v1/init",
        "weather": "/api/v1/intern/weather",
        "neos": "/api/v1/intern/neos",
        "satellites": "/api/v1/intern/satellites",
        "apod": "/api/v1/intern/apod",
        "launches": "/api/v1/intern/launches",
        "conjunctions": "/api/v1/intern/conjunctions"
    }

    # Apply Dynamic HATEOAS Trap if active
    trap_info = state.traps.get("dynamic_hateoas", {})
    if trap_info.get("is_active"):
        for key in ["weather", "neos", "satellites", "apod", "launches", "conjunctions"]:
            links[key] = gamemaster_v2.get_dynamic_path(links[key])

    return {
        "status": "DOMO Command Center - Secure Gateway Access",
        "session_id": session_id,
        "crypto_seed": settings.SECRET_SEED,
        "instructions": (
            "To access the satellite, mission and meteorological network endpoints, you must provide strictly formatted headers:\n"
            "1. X-Domo-Time: Current Unix UTC timestamp (integer).\n"
            "2. X-Domo-Token: SHA256 cryptographic signature derived from (SECRET_SEED + X-Domo-Time).\n"
            "3. X-Domo-Session: Reuse the session_id returned by /init to enable advanced session protocols.\n"
            "End-to-end encryption is mandatory. All requests are monitored for security compliance."
        ),
        "links": links
    }
