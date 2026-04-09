import httpx
from datetime import date, timedelta, datetime
from typing import Dict, Any, Optional
from app.core.config import settings

class NasaClient:
    def __init__(self):
        self.base_url = "https://api.nasa.gov"
        self.api_key = settings.NASA_API_KEY
        self.timeout = httpx.Timeout(10.0)
        self.limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        
        # Simple memory cache
        self._cache_neows: Optional[Dict[str, Any]] = None
        self._cache_neows_time: Optional[datetime] = None
        self._cache_flares: Optional[Any] = None
        self._cache_flares_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=15) # Cache for 15 minutes to save DEMO_KEY limit

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self.timeout, limits=self.limits)

    async def get_apod(self) -> Dict[str, Any]:
        """Fetch Astronomy Picture of the Day"""
        url = f"{self.base_url}/planetary/apod"
        params = {"api_key": self.api_key}
        async with self._get_client() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_neows(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Fetch Near Earth Object Web Service"""
        if self._cache_neows and self._cache_neows_time and (datetime.now() - self._cache_neows_time) < self._cache_ttl:
            return self._cache_neows

        if not start_date:
            start_date = str(date.today())
        if not end_date:
            end_date = str(date.today() + timedelta(days=2))
            
        url = f"{self.base_url}/neo/rest/v1/feed"
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "api_key": self.api_key
        }
        async with self._get_client() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                self._cache_neows = data
                self._cache_neows_time = datetime.now()
                return data
            except Exception as e:
                if getattr(e, "response", None) and e.response.status_code == 429:
                    if self._cache_neows: return self._cache_neows
                    return {"element_count": 0, "near_earth_objects": {}, "error": "NASA API Rate Limit Exceeded"}
                if self._cache_neows: return self._cache_neows
                # Fallback static data to prevent 500 errors if NASA API is down or timing out
                return {
                    "element_count": 1,
                    "near_earth_objects": {
                        start_date: [
                            {
                                "id": "999999",
                                "name": "MOCK-NEO-DOMO",
                                "absolute_magnitude_h": 20.5,
                                "is_potentially_hazardous_asteroid": True,
                                "close_approach_data": [{"close_approach_date": start_date}]
                            }
                        ]
                    }
                }

    async def get_donki_flares(self, start_date: str = None) -> Any:
        """Fetch Solar Flares from DONKI"""
        if self._cache_flares and self._cache_flares_time and (datetime.now() - self._cache_flares_time) < self._cache_ttl:
            return self._cache_flares

        if not start_date:
            start_date = str(date.today() - timedelta(days=30))
            
        url = f"{self.base_url}/DONKI/FLR"
        params = {
            "startDate": start_date,
            "api_key": self.api_key
        }
        async with self._get_client() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                self._cache_flares = data
                self._cache_flares_time = datetime.now()
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    if self._cache_flares: return self._cache_flares
                    return [] # Fallback to empty list on rate limit
                raise e

nasa_client = NasaClient()
