from typing import Dict, List
from datetime import datetime, timedelta, date
from collections import deque

class DataManager:
    """Beheer en opslag van historische data"""

    def __init__(self, max_history_hours: int = 24):
        self.max_history_hours = max_history_hours
        self.p1_history = deque(maxlen=max_history_hours * 60)  # Per minuut
        self.kwh_history = deque(maxlen=max_history_hours * 60)
        self.latest_p1_data = {}
        self.latest_kwh_data = {}
        self.last_update = None

        # Voor dagelijkse cumulatieve berekeningen (PVOutput)
        self.daily_start_values = {}
        self.current_date = None
        self._check_and_reset_daily_values()

    def _check_and_reset_daily_values(self):
        """Check of we een nieuwe dag zijn en reset dagelijkse start waarden"""
        today = date.today()

        if self.current_date != today:
            print(f"Nieuwe dag gedetecteerd, reset dagelijkse waarden. Oude datum: {self.current_date}, Nieuwe: {today}")
            self.current_date = today
            self.daily_start_values = {}

    def _set_daily_start_value(self, key: str, value: float):
        """Sla dagelijkse start waarde op als deze nog niet bestaat"""
        if key not in self.daily_start_values:
            self.daily_start_values[key] = value
            print(f"Dagelijkse start waarde ingesteld: {key} = {value}")

    def add_p1_data(self, data: Dict):
        """Voeg P1 meter data toe aan geschiedenis"""
        if data:
            self._check_and_reset_daily_values()

            # Sla dagelijkse start waarden op
            if 'total_power_import_kwh' in data:
                self._set_daily_start_value('p1_import_kwh', data['total_power_import_kwh'])
            if 'total_power_export_kwh' in data:
                self._set_daily_start_value('p1_export_kwh', data['total_power_export_kwh'])

            data['_timestamp'] = datetime.now()
            self.p1_history.append(data)
            self.latest_p1_data = data
            self.last_update = datetime.now()

    def add_kwh_data(self, data: Dict):
        """Voeg kWh meter data toe aan geschiedenis"""
        if data:
            self._check_and_reset_daily_values()

            # Sla dagelijkse start waarde op
            if 'total_power_export_kwh' in data:
                self._set_daily_start_value('kwh_export_kwh', data['total_power_export_kwh'])

            data['_timestamp'] = datetime.now()
            self.kwh_history.append(data)
            self.latest_kwh_data = data
            self.last_update = datetime.now()

    def get_latest_data(self) -> Dict:
        """Haal nieuwste data op"""
        return {
            'p1': self.latest_p1_data,
            'kwh': self.latest_kwh_data,
            'last_update': self.last_update.isoformat() if self.last_update else None
        }

    def get_history(self, hours: int = 1) -> Dict:
        """
        Haal historische data op voor de laatste X uren

        Args:
            hours: Aantal uren geschiedenis

        Returns:
            Dict met p1 en kwh geschiedenis
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        p1_filtered = [
            item for item in self.p1_history
            if item.get('_timestamp', datetime.min) > cutoff_time
        ]

        kwh_filtered = [
            item for item in self.kwh_history
            if item.get('_timestamp', datetime.min) > cutoff_time
        ]

        return {
            'p1': p1_filtered,
            'kwh': kwh_filtered
        }

    def get_daily_totals(self) -> Dict:
        """
        Bereken totalen voor vandaag (voor PVOutput)

        Returns:
            Dict met:
            - energy_generation_wh: Totaal opgewekt vandaag in Wh
            - energy_consumption_wh: Totaal verbruikt vandaag in Wh
            - energy_import_wh: Totaal geïmporteerd vandaag in Wh
            - energy_export_wh: Totaal geëxporteerd vandaag in Wh
        """
        self._check_and_reset_daily_values()

        totals = {
            'energy_generation_wh': 0,
            'energy_consumption_wh': 0,
            'energy_import_wh': 0,
            'energy_export_wh': 0
        }

        # Bereken opwekking vandaag (kWh meters)
        if self.latest_kwh_data and 'total_power_export_kwh' in self.latest_kwh_data:
            current_kwh = self.latest_kwh_data['total_power_export_kwh']
            start_kwh = self.daily_start_values.get('kwh_export_kwh', current_kwh)
            totals['energy_generation_wh'] = int((current_kwh - start_kwh) * 1000)

        # Bereken import/export vandaag (P1 meter)
        if self.latest_p1_data:
            if 'total_power_import_kwh' in self.latest_p1_data:
                current_import = self.latest_p1_data['total_power_import_kwh']
                start_import = self.daily_start_values.get('p1_import_kwh', current_import)
                totals['energy_import_wh'] = int((current_import - start_import) * 1000)

            if 'total_power_export_kwh' in self.latest_p1_data:
                current_export = self.latest_p1_data['total_power_export_kwh']
                start_export = self.daily_start_values.get('p1_export_kwh', current_export)
                totals['energy_export_wh'] = int((current_export - start_export) * 1000)

        # Bereken totaal verbruik vandaag
        # Verbruik = Opwekking + Import - Export
        totals['energy_consumption_wh'] = (
            totals['energy_generation_wh'] +
            totals['energy_import_wh'] -
            totals['energy_export_wh']
        )

        return totals

    def get_statistics(self) -> Dict:
        """Bereken statistieken over de data"""
        stats = {
            'p1': {},
            'kwh': {},
            'totals': {}
        }

        # P1 statistieken
        if self.latest_p1_data:
            stats['p1'] = {
                'current_power_w': self.latest_p1_data.get('active_power_w', 0),
                'total_import_kwh': self.latest_p1_data.get('total_power_import_kwh', 0),
                'total_export_kwh': self.latest_p1_data.get('total_power_export_kwh', 0),
                'is_importing': self.latest_p1_data.get('active_power_w', 0) > 0,
                'is_exporting': self.latest_p1_data.get('active_power_w', 0) < 0
            }

        # kWh statistieken
        if self.latest_kwh_data:
            stats['kwh'] = {
                'current_power_w': self.latest_kwh_data.get('active_power_w', 0),
                'total_generated_kwh': self.latest_kwh_data.get('total_power_export_kwh', 0)
            }

        # Totalen
        generation = self.latest_kwh_data.get('active_power_w', 0)
        grid_power = self.latest_p1_data.get('active_power_w', 0)

        stats['totals'] = {
            'generation_w': generation,
            'consumption_w': generation + grid_power,  # Als grid_power negatief is (export), dan verbruik = gen - export
            'grid_power_w': grid_power,
            'self_consumption_w': min(generation, generation + grid_power) if grid_power >= 0 else generation
        }

        return stats
