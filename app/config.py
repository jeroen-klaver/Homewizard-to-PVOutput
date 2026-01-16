import yaml
from pathlib import Path
from typing import Optional, List, Dict

class Config:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.data = self._load_config()
        self._migrate_old_config()

    def _load_config(self) -> dict:
        """Laad configuratie uit YAML bestand"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Als config niet bestaat, gebruik example
            example_path = "config/config.example.yaml"
            if Path(example_path).exists():
                with open(example_path, 'r') as f:
                    return yaml.safe_load(f)
            return self._default_config()

    def _default_config(self) -> dict:
        """Default configuratie als er geen bestand is"""
        return {
            'homewizard_p1': {'host': '', 'enabled': False},
            'homewizard_kwh_meters': [],
            'pvoutput': {'api_key': '', 'system_id': ''},
            'update_interval': 300,
            'webserver': {'port': 8080, 'host': '0.0.0.0'}
        }

    def _migrate_old_config(self):
        """Migreer oude single kWh meter config naar nieuwe lijst formaat"""
        # Check of oude 'homewizard_kwh' formaat bestaat
        if 'homewizard_kwh' in self.data and 'homewizard_kwh_meters' not in self.data:
            old_kwh = self.data.get('homewizard_kwh', {})
            if old_kwh.get('host'):
                # Converteer naar nieuwe lijst formaat
                self.data['homewizard_kwh_meters'] = [{
                    'name': 'Omvormer 1',
                    'host': old_kwh.get('host'),
                    'enabled': old_kwh.get('enabled', True)
                }]
                # Verwijder oude config
                del self.data['homewizard_kwh']
                print("Config gemigreerd: oude 'homewizard_kwh' naar nieuwe 'homewizard_kwh_meters' formaat")

        # Zorg dat homewizard_kwh_meters altijd bestaat
        if 'homewizard_kwh_meters' not in self.data:
            self.data['homewizard_kwh_meters'] = []

    def save(self):
        """Sla configuratie op naar YAML bestand"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False)

    @property
    def homewizard_p1_host(self) -> Optional[str]:
        return self.data.get('homewizard_p1', {}).get('host')

    @property
    def homewizard_p1_enabled(self) -> bool:
        return self.data.get('homewizard_p1', {}).get('enabled', False)

    @property
    def homewizard_kwh_meters(self) -> List[Dict]:
        """Haal lijst van geconfigureerde kWh meters op"""
        return self.data.get('homewizard_kwh_meters', [])

    @property
    def homewizard_kwh_meters_enabled(self) -> List[Dict]:
        """Haal alleen ingeschakelde kWh meters op"""
        return [meter for meter in self.homewizard_kwh_meters if meter.get('enabled', False)]

    # Backwards compatibility - deprecated maar beschikbaar voor oude code
    @property
    def homewizard_kwh_host(self) -> Optional[str]:
        """Deprecated: gebruik homewizard_kwh_meters"""
        meters = self.homewizard_kwh_meters_enabled
        return meters[0].get('host') if meters else None

    @property
    def homewizard_kwh_enabled(self) -> bool:
        """Deprecated: gebruik homewizard_kwh_meters_enabled"""
        return len(self.homewizard_kwh_meters_enabled) > 0

    @property
    def pvoutput_api_key(self) -> Optional[str]:
        return self.data.get('pvoutput', {}).get('api_key')

    @property
    def pvoutput_system_id(self) -> Optional[str]:
        return self.data.get('pvoutput', {}).get('system_id')

    @property
    def update_interval(self) -> int:
        return self.data.get('update_interval', 300)

    @property
    def webserver_port(self) -> int:
        return self.data.get('webserver', {}).get('port', 8080)

    @property
    def webserver_host(self) -> str:
        return self.data.get('webserver', {}).get('host', '0.0.0.0')
