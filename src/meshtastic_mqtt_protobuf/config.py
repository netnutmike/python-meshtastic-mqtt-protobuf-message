"""Configuration management module for YAML config files and CLI overrides.

Copyright (C) 2024 Meshtastic MQTT Protobuf Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This module handles loading configuration from YAML files, merging with
command-line argument overrides, and validating required parameters.

Configuration Hierarchy:
-----------------------
1. Default values (defined in dataclasses)
2. YAML configuration file values (override defaults)
3. Command-line arguments (override both defaults and YAML)

This allows users to set common values in the config file while still
being able to override specific parameters for individual invocations.

Configuration Structure:
-----------------------
The configuration is organized into two main sections:
- mqtt: MQTT broker connection settings
- meshtastic: Meshtastic protocol parameters

Security Considerations:
-----------------------
- Config files are created with 0600 permissions (owner read/write only)
- Passwords should be stored in config file, not passed via CLI
- Config files should be excluded from version control (.gitignore)
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, Any
from pathlib import Path


@dataclass
class MQTTConfig:
    """MQTT connection configuration."""
    server: str = ""
    port: int = 1883
    username: str = ""
    password: str = ""


@dataclass
class MeshtasticConfig:
    """Meshtastic protocol configuration."""
    gateway_id: str = ""
    to_id: str = "^all"
    channel: str = "LongFast"
    region: str = "US"
    want_ack: bool = False
    hop_limit: int = 3


@dataclass
class AppConfig:
    """Combined application configuration."""
    mqtt: MQTTConfig = field(default_factory=MQTTConfig)
    meshtastic: MeshtasticConfig = field(default_factory=MeshtasticConfig)


class Config:
    """Manages configuration from YAML files and command-line arguments."""
    
    def __init__(self):
        """Initialize empty configuration."""
        self.config = AppConfig()
    
    def load_from_file(self, path: str) -> None:
        """Load configuration from YAML file.
        
        Args:
            path: Path to YAML configuration file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML syntax is invalid
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                data = {}
            
            # Load MQTT config
            if 'mqtt' in data:
                mqtt_data = data['mqtt']
                self.config.mqtt = MQTTConfig(
                    server=mqtt_data.get('server', ''),
                    port=mqtt_data.get('port', 1883),
                    username=mqtt_data.get('username', ''),
                    password=mqtt_data.get('password', '')
                )
            
            # Load Meshtastic config
            if 'meshtastic' in data:
                mesh_data = data['meshtastic']
                self.config.meshtastic = MeshtasticConfig(
                    gateway_id=mesh_data.get('gateway_id', ''),
                    to_id=mesh_data.get('to_id', '^all'),
                    channel=mesh_data.get('channel', 'LongFast'),
                    region=mesh_data.get('region', 'US'),
                    want_ack=mesh_data.get('want_ack', False),
                    hop_limit=mesh_data.get('hop_limit', 3)
                )
        
        except yaml.YAMLError as e:
            # Extract line number if available
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                raise yaml.YAMLError(
                    f"Invalid YAML syntax at line {mark.line + 1}, column {mark.column + 1}: {e.problem}"
                )
            else:
                raise yaml.YAMLError(f"Invalid YAML syntax: {e}")
    
    def merge_with_cli_args(self, args) -> None:
        """Merge command-line arguments with configuration.
        
        CLI arguments take precedence over config file values.
        
        Args:
            args: Parsed command-line arguments (argparse.Namespace or dict-like)
        """
        # Handle both argparse.Namespace and dict
        if hasattr(args, '__dict__'):
            args_dict = vars(args)
        else:
            args_dict = args
        
        # Override MQTT settings
        if args_dict.get('server'):
            self.config.mqtt.server = args_dict['server']
        if args_dict.get('port'):
            self.config.mqtt.port = args_dict['port']
        if args_dict.get('username'):
            self.config.mqtt.username = args_dict['username']
        if args_dict.get('password'):
            self.config.mqtt.password = args_dict['password']
        
        # Override Meshtastic settings
        if args_dict.get('gateway_id'):
            self.config.meshtastic.gateway_id = args_dict['gateway_id']
        if args_dict.get('to_id'):
            self.config.meshtastic.to_id = args_dict['to_id']
        if args_dict.get('channel'):
            self.config.meshtastic.channel = args_dict['channel']
        if args_dict.get('region'):
            self.config.meshtastic.region = args_dict['region']
        if args_dict.get('want_ack') is not None:
            self.config.meshtastic.want_ack = args_dict['want_ack']
        if args_dict.get('hop_limit') is not None:
            self.config.meshtastic.hop_limit = args_dict['hop_limit']
    
    def validate(self) -> None:
        """Validate that required configuration fields are present.
        
        Raises:
            ValueError: If required fields are missing
        """
        missing = []
        
        if not self.config.mqtt.server:
            missing.append('mqtt.server')
        if not self.config.mqtt.username:
            missing.append('mqtt.username')
        if not self.config.mqtt.password:
            missing.append('mqtt.password')
        if not self.config.meshtastic.gateway_id:
            missing.append('meshtastic.gateway_id')
        
        if missing:
            raise ValueError(
                f"Missing required configuration parameters: {', '.join(missing)}"
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.
        
        Args:
            key: Configuration key in dot notation (e.g., 'mqtt.server')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        parts = key.split('.')
        
        if len(parts) != 2:
            return default
        
        section, field = parts
        
        if section == 'mqtt':
            return getattr(self.config.mqtt, field, default)
        elif section == 'meshtastic':
            return getattr(self.config.meshtastic, field, default)
        
        return default
    
    @staticmethod
    def create_default_config(path: str) -> None:
        """Create a default configuration file.
        
        Args:
            path: Path where config file should be created
        """
        # Create directory if it doesn't exist
        config_dir = os.path.dirname(path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
        
        # Default configuration template
        default_config = {
            'mqtt': {
                'server': 'mqtt.meshtastic.org',
                'port': 1883,
                'username': 'meshdev',
                'password': 'large4cats'
            },
            'meshtastic': {
                'gateway_id': '!12345678',
                'to_id': '^all',
                'channel': 'LongFast',
                'region': 'US',
                'want_ack': False,
                'hop_limit': 3
            }
        }
        
        # Write YAML file
        with open(path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
        
        # Set restrictive permissions on Unix-like systems
        if os.name != 'nt':  # Not Windows
            os.chmod(path, 0o600)
    
    @staticmethod
    def get_default_config_path() -> str:
        """Get the platform-appropriate default config file path.
        
        Returns:
            Default configuration file path
        """
        if os.name == 'nt':  # Windows
            config_dir = os.path.join(os.environ.get('APPDATA', ''), 'meshtastic-mqtt-protobuf')
        else:  # Linux/macOS
            config_dir = os.path.join(os.path.expanduser('~'), '.config', 'meshtastic-mqtt-protobuf')
        
        return os.path.join(config_dir, 'config.yaml')
