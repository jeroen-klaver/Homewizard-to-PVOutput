import httpx
from typing import Optional, Dict
from datetime import datetime

class HomeWizardClient:
    """Client voor HomeWizard API communicatie"""

    def __init__(self, host: str):
        self.host = host
        self.base_url = f"http://{host}/api/v1"

    async def get_data(self) -> Optional[Dict]:
        """Haal actuele data op van HomeWizard apparaat"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/data")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Fout bij ophalen HomeWizard data van {self.host}: {e}")
            return None

    async def get_info(self) -> Optional[Dict]:
        """Haal apparaat informatie op"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Fout bij ophalen HomeWizard info van {self.host}: {e}")
            return None

class HomeWizardDataProcessor:
    """Verwerk HomeWizard data voor gebruik in de applicatie"""

    @staticmethod
    def process_p1_data(data: Dict) -> Dict:
        """
        Verwerk P1 meter data

        Returns:
            Dict met:
            - total_power_import_kwh: totaal geïmporteerd (kWh)
            - total_power_export_kwh: totaal geëxporteerd (kWh)
            - active_power_w: actief vermogen (W, positief = import, negatief = export)
            - active_power_l1_w: actief vermogen fase 1
            - active_power_l2_w: actief vermogen fase 2
            - active_power_l3_w: actief vermogen fase 3
            - timestamp: tijd van meting
        """
        if not data:
            return {}

        return {
            'total_power_import_kwh': data.get('total_power_import_kwh', 0),
            'total_power_export_kwh': data.get('total_power_export_kwh', 0),
            'active_power_w': data.get('active_power_w', 0),
            'active_power_l1_w': data.get('active_power_l1_w', 0),
            'active_power_l2_w': data.get('active_power_l2_w', 0),
            'active_power_l3_w': data.get('active_power_l3_w', 0),
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def process_kwh_data(data: Dict) -> Dict:
        """
        Verwerk kWh meter data (zonnepanelen)

        Returns:
            Dict met:
            - total_power_export_kwh: totaal opgewekt (kWh)
            - active_power_w: actief vermogen (W)
            - timestamp: tijd van meting
        """
        if not data:
            return {}

        return {
            'total_power_export_kwh': data.get('total_power_export_kwh', 0),
            'active_power_w': data.get('active_power_w', 0),
            'timestamp': datetime.now().isoformat()
        }
