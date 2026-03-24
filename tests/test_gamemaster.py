import struct
import math
from app.core.gamemaster import gamemaster

def test_pack_satellite_data():
    lat, lon, alt, vel = 10.5, -45.2, 400.0, 7.6
    packed = gamemaster.pack_satellite_data(lat, lon, alt, vel)
    assert len(packed) == 16
    
    unpacked = gamemaster.unpack_satellite_data(packed)
    assert math.isclose(unpacked[0], lat, rel_tol=1e-5)
    assert math.isclose(unpacked[1], lon, rel_tol=1e-5)
    assert math.isclose(unpacked[2], alt, rel_tol=1e-5)
    assert math.isclose(unpacked[3], vel, rel_tol=1e-5)

def test_mutate_json():
    original = {"velocidad": 100, "datos": {"altitud": 400}}
    mutated = gamemaster.mutate_json(original)
    
    assert "velocidad_cruda" in mutated
    assert mutated["velocidad_cruda"] == 100
    assert "datos_cruda" in mutated
    assert "altitud_cruda" in mutated["datos_cruda"]
    assert mutated["datos_cruda"]["altitud_cruda"] == 400
