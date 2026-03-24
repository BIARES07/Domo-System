from fastapi import APIRouter, Depends, HTTPException, Response, Request
from typing import Dict, Any, List, Optional
import json

from app.services.nasa_client import nasa_client
from app.services.celestrak_client import celestrak_client
from app.core.gamemaster import gamemaster
from app.core.gamemaster_v2 import gamemaster_v2
from app.core.state import state

router = APIRouter(prefix="/intern", tags=["Intern - Hostile API"])

async def is_trap_active(trap_name: str) -> bool:
    trap_info = state.traps.get(trap_name, {})
    return trap_info.get("is_active", False)

async def apply_v2_traps(data: Any, request: Request) -> Any:
    # 1. Seed Rotation Trap (Requires X-Domo-Time)
    if await is_trap_active("seed_rotation"):
        domo_time = request.headers.get("X-Domo-Time")
        if domo_time:
            data = gamemaster_v2.apply_seed_rotation(data, int(domo_time))
            
    # 2. Schema Drift Trap
    if await is_trap_active("schema_drift"):
        data = gamemaster_v2.apply_schema_drift(data)
        
    return data

@router.get("/weather")
@router.get("/weather/{date_str}")
async def get_space_weather(request: Request, date_str: Optional[str] = None):
    try:
        data = await nasa_client.get_donki_flares()
        
        # Original Mutation Trap
        if await is_trap_active("json_mutation"):
            data = gamemaster.mutate_json(data)
            
        return await apply_v2_traps(data, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/neos")
@router.get("/neos/{date_str}")
async def get_near_earth_objects(request: Request, date_str: Optional[str] = None):
    try:
        data = await nasa_client.get_neows()
        
        if await is_trap_active("json_mutation"):
            data = gamemaster.mutate_json(data)
            
        return await apply_v2_traps(data, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/satellites")
@router.get("/satellites/{date_str}")
async def get_satellites(request: Request, date_str: Optional[str] = None):
    try:
        satellites = await celestrak_client.get_active_satellites()
        satellites = satellites[:20] # Return more to make paging useful
        
        # 1. Binary TLE Trap (Takes priority)
        if await is_trap_active("binary_tle"):
            binary_payload = bytearray()
            for sat in satellites[:10]:
                lat, lon, alt, vel = sat.get("inclination", 0.0), sat.get("raan", 0.0), sat.get("mean_motion", 0.0), sat.get("eccentricity", 0.0)
                import struct
                norad_bytes = struct.pack('<I', sat["norad_id"])
                packed_data = gamemaster.pack_satellite_data(lat, lon, alt, vel)
                binary_payload.extend(norad_bytes + packed_data)
            return Response(content=bytes(binary_payload), media_type="application/octet-stream")

        # 2. Inconsistent Paging Trap
        if await is_trap_active("inconsistent_paging"):
            range_header = request.headers.get("X-Domo-Range", "")
            data_dict = gamemaster_v2.apply_inconsistent_paging(satellites, range_header)
            
            # Apply common transformations to items inside the paging response
            data_dict["items"] = await apply_v2_traps(data_dict["items"], request)
            if await is_trap_active("json_mutation"):
                data_dict["items"] = gamemaster.mutate_json(data_dict["items"])
            return data_dict

        # 3. Normal Flow
        if await is_trap_active("json_mutation"):
             satellites = gamemaster.mutate_json(satellites)
             
        return await apply_v2_traps(satellites, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/apod")
@router.get("/apod/{date_str}")
async def get_apod(request: Request, date_str: Optional[str] = None):
    try:
        data = await nasa_client.get_apod()
        if await is_trap_active("json_mutation"):
            data = gamemaster.mutate_json(data)
        return await apply_v2_traps(data, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

