import httpx
from typing import Optional
from datetime import datetime

class PVOutputClient:
    """Client voor PVOutput API communicatie"""

    def __init__(self, api_key: str, system_id: str):
        self.api_key = api_key
        self.system_id = system_id
        self.base_url = "https://pvoutput.org/service/r2"

    def _get_headers(self) -> dict:
        """Genereer headers voor API requests"""
        return {
            'X-Pvoutput-Apikey': self.api_key,
            'X-Pvoutput-SystemId': self.system_id
        }

    async def add_status(
        self,
        energy_generation: Optional[int] = None,
        power_generation: Optional[int] = None,
        energy_consumption: Optional[int] = None,
        power_consumption: Optional[int] = None,
        temperature: Optional[float] = None,
        voltage: Optional[float] = None
    ) -> bool:
        """
        Voeg status toe aan PVOutput

        Args:
            energy_generation: Totaal opgewekte energie in Wh (cumulatief voor de dag)
            power_generation: Actueel opgewekt vermogen in W
            energy_consumption: Totaal verbruikte energie in Wh (cumulatief voor de dag)
            power_consumption: Actueel verbruikt vermogen in W
            temperature: Temperatuur in C
            voltage: Voltage in V

        Returns:
            True als succesvol, False bij fout
        """
        now = datetime.now()
        date_str = now.strftime('%Y%m%d')
        time_str = now.strftime('%H:%M')

        params = {
            'd': date_str,
            't': time_str
        }

        if energy_generation is not None:
            params['v1'] = int(energy_generation)
        if power_generation is not None:
            params['v2'] = int(power_generation)
        if energy_consumption is not None:
            params['v3'] = int(energy_consumption)
        if power_consumption is not None:
            params['v4'] = int(power_consumption)
        if temperature is not None:
            params['v5'] = temperature
        if voltage is not None:
            params['v6'] = voltage

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/addstatus.jsp",
                    headers=self._get_headers(),
                    data=params
                )
                response.raise_for_status()
                print(f"PVOutput status toegevoegd: {params}")
                return True
        except Exception as e:
            print(f"Fout bij toevoegen PVOutput status: {e}")
            return False

    async def get_status(self) -> Optional[dict]:
        """Haal laatste status op van PVOutput"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/getstatus.jsp",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Fout bij ophalen PVOutput status: {e}")
            return None

class PVOutputDataConverter:
    """Converteer HomeWizard data naar PVOutput formaat"""

    @staticmethod
    def convert_to_pvoutput(
        p1_data: dict,
        kwh_data: dict,
        daily_totals: dict = None,
        weather_data: dict = None
    ) -> dict:
        """
        Converteer HomeWizard data naar PVOutput formaat

        Args:
            p1_data: Data van P1 meter (import/export)
            kwh_data: Data van kWh meter(s) (zonnepanelen) - kan gecombineerde data zijn
            daily_totals: Dagelijkse totalen (optioneel, voor cumulatieve data)
            weather_data: Weather data (optioneel, voor temperatuur)

        Returns:
            Dict met PVOutput parameters:
            - energy_generation: Totaal opgewekt vandaag (Wh)
            - power_generation: Actueel opgewekt vermogen (W)
            - energy_consumption: Totaal verbruikt vandaag (Wh)
            - power_consumption: Actueel verbruik (W)
            - temperature: Temperatuur (°C)
            - voltage: Voltage (V)

        PVOutput API parameters:
        - v1: Energy Generation (Wh) - cumulatief vandaag
        - v2: Power Generation (W) - actueel
        - v3: Energy Consumption (Wh) - cumulatief vandaag
        - v4: Power Consumption (W) - actueel
        - v5: Temperature (°C) - optioneel
        - v6: Voltage (V) - optioneel
        """
        result = {}

        # v2: Actuele opwekking (van kWh meter(s) als beschikbaar)
        if kwh_data and kwh_data.get('active_power_w') is not None:
            result['power_generation'] = abs(int(kwh_data.get('active_power_w', 0)))

        # v4: Actueel verbruik berekenen
        # Verbruik = Opwekking + Grid power
        # Als grid power negatief is (export), dan is verbruik lager
        # Als grid power positief is (import), dan is verbruik hoger
        if p1_data and p1_data.get('active_power_w') is not None:
            generation = result.get('power_generation', 0)
            grid_power = p1_data.get('active_power_w', 0)
            result['power_consumption'] = abs(int(generation + grid_power))

        # v5: Temperature (van weather data)
        if weather_data and weather_data.get('temperature_c') is not None:
            result['temperature'] = round(weather_data.get('temperature_c'), 1)

        # v6: Voltage (gemiddelde van alle fases)
        if p1_data and p1_data.get('voltage_avg_v') is not None:
            result['voltage'] = round(p1_data.get('voltage_avg_v'), 1)

        # v1 & v3: Dagelijkse totalen (cumulatief voor vandaag)
        if daily_totals:
            # v1: Totaal opgewekt vandaag
            if 'energy_generation_wh' in daily_totals:
                result['energy_generation'] = daily_totals['energy_generation_wh']

            # v3: Totaal verbruikt vandaag
            if 'energy_consumption_wh' in daily_totals:
                result['energy_consumption'] = daily_totals['energy_consumption_wh']

        return result
