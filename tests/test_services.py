import pytest
from app.services.celestrak_client import CelesTrakClient

def test_parse_tle():
    sample_tle = """ISS (ZARYA)
1 25544U 98067A   23338.50000000  .00010505  00000+0  19000-3 0  9997
2 25544  51.6425 151.7853 0001476 348.6508 135.2917 15.50085186428135"""
    
    client = CelesTrakClient()
    parsed = client.parse_tle(sample_tle)
    
    assert len(parsed) == 1
    iss = parsed[0]
    assert iss["name"] == "ISS (ZARYA)"
    assert iss["norad_id"] == 25544
    assert iss["classification"] == "U"
    assert iss["designator"] == "98067A"
    assert iss["epoch_year"] == 23
    assert iss["epoch_day"] == 338.5
    assert iss["inclination"] == 51.6425
    assert iss["raan"] == 151.7853
    assert iss["eccentricity"] == 0.0001476
    assert iss["arg_perigee"] == 348.6508
    assert iss["mean_anomaly"] == 135.2917
    assert iss["mean_motion"] == 15.50085186
    assert iss["rev_number"] == 42813
