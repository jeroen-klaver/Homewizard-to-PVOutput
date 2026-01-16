import httpx
from typing import Optional, Dict, List
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
            - voltage_l1_v: voltage fase 1 (V)
            - voltage_l2_v: voltage fase 2 (V)
            - voltage_l3_v: voltage fase 3 (V)
            - voltage_avg_v: gemiddelde voltage (V)
            - timestamp: tijd van meting
        """
        if not data:
            return {}

        # Haal voltage data op
        voltage_l1 = data.get('voltage_sag_l1_v')
        voltage_l2 = data.get('voltage_sag_l2_v')
        voltage_l3 = data.get('voltage_sag_l3_v')

        # Bereken gemiddelde voltage van beschikbare fases
        voltages = [v for v in [voltage_l1, voltage_l2, voltage_l3] if v is not None and v > 0]
        voltage_avg = sum(voltages) / len(voltages) if voltages else None

        result = {
            'total_power_import_kwh': data.get('total_power_import_kwh', 0),
            'total_power_export_kwh': data.get('total_power_export_kwh', 0),
            'active_power_w': data.get('active_power_w', 0),
            'active_power_l1_w': data.get('active_power_l1_w', 0),
            'active_power_l2_w': data.get('active_power_l2_w', 0),
            'active_power_l3_w': data.get('active_power_l3_w', 0),
            'timestamp': datetime.now().isoformat()
        }

        # Voeg voltage data toe als beschikbaar
        if voltage_l1 is not None:
            result['voltage_l1_v'] = voltage_l1
        if voltage_l2 is not None:
            result['voltage_l2_v'] = voltage_l2
        if voltage_l3 is not None:
            result['voltage_l3_v'] = voltage_l3
        if voltage_avg is not None:
            result['voltage_avg_v'] = voltage_avg

        return result

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

    @staticmethod
    def combine_kwh_data(kwh_data_list: List[Dict]) -> Dict:
        """
        Combineer data van meerdere kWh meters

        Args:
            kwh_data_list: Lijst van verwerkte kWh meter data

        Returns:
            Dict met gecombineerde data:
            - total_power_export_kwh: som van alle meters
            - active_power_w: som van alle meters
            - meters: lijst met individuele meter data
            - timestamp: tijd van meting
        """
        if not kwh_data_list:
            return {}

        # Filter lege data
        valid_data = [d for d in kwh_data_list if d]

        if not valid_data:
            return {}

        # Combineer de data
        combined = {
            'total_power_export_kwh': sum(d.get('total_power_export_kwh', 0) for d in valid_data),
            'active_power_w': sum(d.get('active_power_w', 0) for d in valid_data),
            'timestamp': datetime.now().isoformat(),
            'meters': valid_data,  # Bewaar individuele meter data
            'meter_count': len(valid_data)
        }

        return combined
