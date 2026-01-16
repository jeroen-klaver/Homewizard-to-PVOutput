from typing import Dict, List
from datetime import datetime, timedelta
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

    def add_p1_data(self, data: Dict):
        """Voeg P1 meter data toe aan geschiedenis"""
        if data:
            data['_timestamp'] = datetime.now()
            self.p1_history.append(data)
            self.latest_p1_data = data
            self.last_update = datetime.now()

    def add_kwh_data(self, data: Dict):
        """Voeg kWh meter data toe aan geschiedenis"""
        if data:
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
