import httpx
from typing import Optional, Dict
from datetime import datetime, timedelta

class WeatherCache:
    """In-memory cache met TTL voor weather data"""

    def __init__(self, ttl_minutes: int = 15):
        self.cache = {}  # {(lat, lon): (data, expiry_timestamp)}
        self.ttl_seconds = ttl_minutes * 60

    def get(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Haal cached weather data op als deze niet expired is"""
        key = (round(latitude, 4), round(longitude, 4))  # Round naar ~10m precisie

        if key in self.cache:
            data, expiry = self.cache[key]
            if datetime.now() < expiry:
                return data
            else:
                del self.cache[key]  # Cleanup expired entry

        return None

    def get_even_if_expired(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Haal cached data op, zelfs als expired (fallback bij API failure)"""
        key = (round(latitude, 4), round(longitude, 4))
        if key in self.cache:
            data, _ = self.cache[key]
            return data
        return None

    def set(self, latitude: float, longitude: float, data: Dict):
        """Cache weather data met TTL"""
        key = (round(latitude, 4), round(longitude, 4))
        expiry = datetime.now() + timedelta(seconds=self.ttl_seconds)
        self.cache[key] = (data, expiry)


class OpenMeteoClient:
    """Weather client voor Open-Meteo API (geen authenticatie vereist)"""

    def __init__(self, latitude: float, longitude: float, cache_duration: int = 15):
        # Valideer coordinates
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitude moet tussen -90 en 90 zijn, got {latitude}")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitude moet tussen -180 en 180 zijn, got {longitude}")

        self.latitude = latitude
        self.longitude = longitude
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.cache = WeatherCache(ttl_minutes=cache_duration)

    async def get_weather(self) -> Dict:
        """
        Haal actuele weather data op

        Returns:
            Dict met:
            - temperature_c: Temperatuur in Celsius
            - weather_code: WMO weather code
            - timestamp: ISO timestamp
        """
        # Check cache eerst
        cached_data = self.cache.get(self.latitude, self.longitude)
        if cached_data:
            print(f"Weather data uit cache gebruikt (lat={self.latitude}, lon={self.longitude})")
            return cached_data

        # Haal data op van API
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        'latitude': self.latitude,
                        'longitude': self.longitude,
                        'current': 'temperature_2m,weather_code'
                    }
                )
                response.raise_for_status()
                data = response.json()

                # Parse response
                weather_data = WeatherDataProcessor.process_openmeteo_data(data)

                # Cache de data
                self.cache.set(self.latitude, self.longitude, weather_data)

                print(f"Weather data opgehaald van Open-Meteo: {weather_data.get('temperature_c')}°C")
                return weather_data

        except httpx.RequestError as e:
            print(f"Network error bij ophalen weather data: {e}")
            # Probeer expired cache als fallback
            expired_data = self.cache.get_even_if_expired(self.latitude, self.longitude)
            if expired_data:
                print("Gebruik expired cache als fallback")
                return expired_data
            raise

        except Exception as e:
            print(f"Fout bij ophalen weather data van Open-Meteo: {e}")
            # Probeer expired cache als fallback
            expired_data = self.cache.get_even_if_expired(self.latitude, self.longitude)
            if expired_data:
                print("Gebruik expired cache als fallback")
                return expired_data
            raise


class WeatherDataProcessor:
    """Process en normalizeer weather data van verschillende providers"""

    @staticmethod
    def wmo_to_pvoutput_condition(wmo_code: int) -> str:
        """
        Map WMO weather code naar PVOutput condition string

        Args:
            wmo_code: WMO code (0-99)

        Returns:
            PVOutput condition string (Fine, Cloudy, Showers, etc.)
        """
        # Mapping table gebaseerd op WMO codes
        if wmo_code == 0 or wmo_code == 1:
            return "Fine"
        elif wmo_code == 2:
            return "Partly Cloudy"
        elif wmo_code == 3:
            return "Cloudy"
        elif wmo_code in (45, 48):
            return "Fog"
        elif 51 <= wmo_code <= 67:  # Drizzle and rain
            return "Showers"
        elif 71 <= wmo_code <= 77:  # Snow
            return "Snow"
        elif 80 <= wmo_code <= 82:  # Rain showers
            return "Showers"
        elif 85 <= wmo_code <= 86:  # Snow showers
            return "Snow"
        elif wmo_code >= 95:  # Thunderstorm
            return "Storm"
        else:
            return "Fine"  # Default fallback

    @staticmethod
    def process_openmeteo_data(data: Dict) -> Dict:
        """
        Process Open-Meteo API response

        Args:
            data: Raw JSON response van Open-Meteo API

        Returns:
            Genormaliseerd dict met:
            - temperature_c: float
            - weather_code: int
            - weather_condition: str (PVOutput format)
            - timestamp: str (ISO format)
        """
        if not data or 'current' not in data:
            raise ValueError("Invalid Open-Meteo response: missing 'current' data")

        current = data.get('current', {})

        temperature = current.get('temperature_2m')
        if temperature is None:
            raise ValueError("Invalid Open-Meteo response: missing temperature_2m")

        wmo_code = current.get('weather_code', 0)

        return {
            'temperature_c': float(temperature),
            'weather_code': wmo_code,
            'weather_condition': WeatherDataProcessor.wmo_to_pvoutput_condition(wmo_code),
            'timestamp': datetime.now().isoformat()
        }
