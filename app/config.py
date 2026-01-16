import yaml
from pathlib import Path
from typing import Optional

class Config:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.data = self._load_config()

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
            'homewizard_kwh': {'host': '', 'enabled': False},
            'pvoutput': {'api_key': '', 'system_id': ''},
            'update_interval': 300,
            'webserver': {'port': 8080, 'host': '0.0.0.0'}
        }

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
    def homewizard_kwh_host(self) -> Optional[str]:
        return self.data.get('homewizard_kwh', {}).get('host')

    @property
    def homewizard_kwh_enabled(self) -> bool:
        return self.data.get('homewizard_kwh', {}).get('enabled', False)

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
