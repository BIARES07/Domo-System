import httpx
from typing import List, Dict, Any
from datetime import datetime, timedelta

class CelesTrakClient:
    def __init__(self):
        # We use active satellites for the intern challenges
        self.active_satellites_url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
        self.timeout = httpx.Timeout(15.0)
        self._cache = []
        self._last_fetch = None
        self._cache_ttl = timedelta(minutes=15) # Cache for 15 minutes

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self.timeout)

    def parse_tle(self, tle_data: str) -> List[Dict[str, Any]]:
        """
        Parses raw TLE text into a structured list of dictionaries.
        """
        lines = tle_data.strip().split('\n')
        satellites = []
        
        # Process every 3 lines (Name, Line 1, Line 2)
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break
                
            name = lines[i].strip()
            line1 = lines[i+1].strip()
            line2 = lines[i+2].strip()
            
            if not line1.startswith('1 ') or not line2.startswith('2 '):
                continue

            try:
                # Extracting NORAD ID and basic parameters as an example structure
                sat_dict = {
                    "name": name,
                    "norad_id": int(line1[2:7]),
                    "classification": line1[7],
                    "designator": line1[9:17].strip(),
                    "epoch_year": int(line1[18:20]),
                    "epoch_day": float(line1[20:32]),
                    "inclination": float(line2[8:16]),
                    "raan": float(line2[17:25]),
                    "eccentricity": float("0." + line2[26:33]),
                    "arg_perigee": float(line2[34:42]),
                    "mean_anomaly": float(line2[43:51]),
                    "mean_motion": float(line2[52:63]),
                    "rev_number": int(line2[63:68]),
                    "raw_tle": {
                        "line1": line1,
                        "line2": line2
                    }
                }
                satellites.append(sat_dict)
            except (ValueError, IndexError):
                # Skip malformed lines
                continue
                
        return satellites

    async def get_active_satellites(self) -> List[Dict[str, Any]]:
        """Fetch and parse active satellites TLE data"""
        if self._cache and self._last_fetch and (datetime.now() - self._last_fetch) < self._cache_ttl:
            return self._cache
            
        async with self._get_client() as client:
            try:
                response = await client.get(self.active_satellites_url)
                response.raise_for_status()
                raw_text = response.text
                self._cache = self.parse_tle(raw_text)
                self._last_fetch = datetime.now()
                return self._cache
            except Exception as e:
                if self._cache: # Return stale cache if error occurs
                    return self._cache
                raise e

celestrak_client = CelesTrakClient()
