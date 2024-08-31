import os
from typing import Any, Dict

import yaml


class ConfigurationError(Exception):
    pass


class Config:
    def __init__(self, config_file: str = "config_example.yaml"):
        self._config = self._load_config(config_file)
        self._validate_config()

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        if not os.path.exists(config_file):
            raise ConfigurationError(f"Configuration file not found: {config_file}")

        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        for key, value in config.items():
            env_value = os.getenv(key.upper())
            if env_value is not None:
                config[key] = self._parse_env_value(env_value)

        return config

    def _parse_env_value(self, value: str) -> Any:
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def _validate_config(self):
        required_keys = [
            "database_host",
            "database_port",
            "database_name",
            "database_user",
            "bmp_i2c_address",
            "gps_serial_port",
            "ebimu_serial_port",
            "parachute_servo_pin",
            "parachute_relay_pin",
        ]
        for key in required_keys:
            if key not in self._config:
                raise ConfigurationError(f"Missing required configuration key: {key}")

    def __getattr__(self, name: str) -> Any:
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"Configuration has no attribute '{name}'")


config = Config()

DB_CONFIG = {
    "host": config.database_host,
    "port": config.database_port,
    "database": config.database_name,
    "user": config.database_user,
    "password": config.database_password,
}

BMP_CONFIG = {
    "i2c_address": config.bmp_i2c_address,
}

GPS_CONFIG = {
    "serial_port": config.gps_serial_port,
    "baud_rate": config.gps_baud_rate,
}

EBIMU_CONFIG = {
    "serial_port": config.ebimu_serial_port,
    "baud_rate": config.ebimu_baud_rate,
}

PARACHUTE_CONFIG = {
    "servo_pin": config.parachute_servo_pin,
    "relay_pin": config.parachute_relay_pin,
}

DECISION_MAKER_CONFIG = {
    "window_size": config.decision_maker_window_size,
    "falling_confirmation_threshold": config.decision_maker_falling_confirmation_threshold,
    "no_deploy_altitude": config.decision_maker_no_deploy_altitude,
    "estimated_max_altitude": config.decision_maker_estimated_max_altitude,
    "estimated_min_altitude": config.decision_maker_estimated_min_altitude,
    "initial_theta": config.decision_maker_initial_theta,
    "critical_angle_threshold": config.decision_maker_critical_angle_threshold,
}
