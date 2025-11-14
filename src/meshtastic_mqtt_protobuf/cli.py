"""Command-line interface module for Meshtastic MQTT Protobuf tool.

This module provides the main entry point and orchestration logic for the
command-line tool. It coordinates configuration loading, message construction,
MQTT connection, and message publishing.

Execution Flow:
--------------
1. Parse command-line arguments
2. Setup logging (INFO or DEBUG based on --verbose)
3. Load configuration from YAML file (or create default)
4. Merge CLI arguments with config (CLI takes precedence)
5. Validate all required parameters are present
6. Build protobuf message from text and parameters
7. Construct MQTT topic string
8. Connect to MQTT broker
9. Publish binary protobuf message
10. Disconnect and exit

Exit Codes:
----------
- 0: Success
- 1: Configuration error (missing file, invalid YAML, missing required fields)
- 2: MQTT error (connection failed, publish failed)
- 3: Message construction error (empty message, invalid parameters)
- 4: Protobuf error (missing package, version mismatch)
- 99: Unexpected error
- 130: User cancelled (Ctrl+C)

Error Handling Strategy:
-----------------------
Errors are caught at each stage and reported with clear, actionable messages.
In verbose mode, full stack traces are logged for debugging. The tool always
attempts to disconnect from MQTT cleanly, even on error.
"""

import argparse
import logging
import sys
import os

from .config import Config
from .message import build_protobuf_message, build_topic
from .mqtt_client import MeshtasticMQTTClient


# Configure logging
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='meshtastic-send-pb',
        description='Send protobuf-encoded messages to Meshtastic MQTT server',
        epilog='''
Examples:
  # Send a message using config file defaults
  meshtastic-send-pb --message "Hello Mesh!"
  
  # Override MQTT server
  meshtastic-send-pb -m "Test message" --server mqtt.example.com
  
  # Send to specific node with acknowledgment
  meshtastic-send-pb -m "Direct message" --to-id "!a1b2c3d4" --want-ack
  
  # Use custom config file with verbose logging
  meshtastic-send-pb -m "Debug test" --config /path/to/config.yaml --verbose

Configuration file location: ~/.config/meshtastic-mqtt-protobuf/config.yaml (Linux/macOS)
                            %APPDATA%\\meshtastic-mqtt-protobuf\\config.yaml (Windows)
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Message argument (required)
    parser.add_argument(
        '--message', '-m',
        type=str,
        required=True,
        help='Message text to send (required)'
    )
    
    # MQTT connection arguments
    parser.add_argument(
        '--server',
        type=str,
        help='MQTT server address (overrides config file)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        help='MQTT server port (default: 1883, overrides config file)'
    )
    
    parser.add_argument(
        '--username', '-u',
        type=str,
        help='MQTT username (overrides config file)'
    )
    
    parser.add_argument(
        '--password', '-p',
        type=str,
        help='MQTT password (overrides config file)'
    )
    
    # Meshtastic protocol arguments
    parser.add_argument(
        '--gateway-id',
        type=str,
        help='Gateway node ID for MQTT topic (e.g., "!12345678", overrides config file)'
    )
    
    parser.add_argument(
        '--to-id',
        type=str,
        help='Recipient node ID (e.g., "!a1b2c3d4" or "^all" for broadcast, overrides config file)'
    )
    
    parser.add_argument(
        '--channel',
        type=str,
        help='Meshtastic channel name (e.g., "LongFast", overrides config file)'
    )
    
    parser.add_argument(
        '--region',
        type=str,
        help='Meshtastic region (e.g., "US", "EU", overrides config file)'
    )
    
    parser.add_argument(
        '--want-ack',
        action='store_true',
        help='Request message acknowledgment'
    )
    
    parser.add_argument(
        '--hop-limit',
        type=int,
        help='Maximum hops for message propagation (default: 3, overrides config file)'
    )
    
    # Configuration and utility arguments
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (default: platform-specific config directory)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    
    return parser.parse_args()


def validate_inputs(config):
    """Validate input parameters.
    
    Args:
        config: Config object with merged configuration
        
    Raises:
        ValueError: If validation fails
    """
    # Validate message text (should be checked before this, but double-check)
    # Message is validated in main() before calling this
    
    # Validate hop_limit is within valid range
    hop_limit = config.config.meshtastic.hop_limit
    if hop_limit is not None:
        if not isinstance(hop_limit, int) or hop_limit < 0 or hop_limit > 7:
            raise ValueError(
                f"Invalid hop_limit: {hop_limit}. Must be an integer between 0 and 7."
            )
    
    # Config.validate() already checks required fields (server, username, password, gateway_id)
    # No additional validation needed here


def setup_logging(verbose=False):
    """Configure logging for the application.
    
    Args:
        verbose: If True, enable DEBUG level logging
    """
    # Set log level
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set paho-mqtt logger to WARNING to reduce noise
    logging.getLogger('paho').setLevel(logging.WARNING)


def main():
    """Entry point for the CLI application.
    
    Orchestrates the complete flow from argument parsing to message delivery.
    This function coordinates all modules (config, message, mqtt_client) to
    send a protobuf-encoded message to a Meshtastic MQTT broker.
    
    The function uses a try-except-finally pattern to ensure clean resource
    cleanup (MQTT disconnection) even when errors occur. Exit codes are set
    based on the type of error encountered.
    """
    exit_code = 0
    client = None
    
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Setup logging
        setup_logging(args.verbose)
        
        # Validate message is not empty
        if not args.message or not args.message.strip():
            logger.error("Message text cannot be empty")
            sys.exit(3)
        
        # Determine config file path
        config_path = args.config if args.config else Config.get_default_config_path()
        
        # Load configuration
        config = Config()
        
        # Create default config if it doesn't exist
        if not os.path.exists(config_path):
            logger.info(f"Configuration file not found. Creating default config at: {config_path}")
            Config.create_default_config(config_path)
            logger.info("Please edit the configuration file with your MQTT credentials and gateway ID")
            sys.exit(1)
        
        try:
            config.load_from_file(config_path)
            logger.debug(f"Loaded configuration from: {config_path}")
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
        
        # Merge CLI arguments with config
        config.merge_with_cli_args(args)
        
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            sys.exit(1)
        
        # Validate inputs
        try:
            validate_inputs(config)
        except ValueError as e:
            logger.error(f"Input validation failed: {e}")
            sys.exit(3)
        
        # Build protobuf message
        try:
            logger.debug("Building protobuf message")
            protobuf_payload = build_protobuf_message(
                text=args.message,
                to_id=config.config.meshtastic.to_id,
                gateway_id=config.config.meshtastic.gateway_id,
                channel=config.config.meshtastic.channel,
                want_ack=config.config.meshtastic.want_ack,
                hop_limit=config.config.meshtastic.hop_limit
            )
            
            # Log hex dump in verbose mode
            if args.verbose:
                hex_dump = protobuf_payload.hex()
                logger.debug(f"Protobuf message hex dump ({len(protobuf_payload)} bytes):")
                # Format hex dump in readable chunks
                for i in range(0, len(hex_dump), 64):
                    logger.debug(f"  {hex_dump[i:i+64]}")
            
        except ValueError as e:
            logger.error(f"Failed to build protobuf message: {e}")
            sys.exit(3)
        except Exception as e:
            logger.error(f"Unexpected error building message: {e}")
            sys.exit(99)
        
        # Build MQTT topic
        topic = build_topic(
            region=config.config.meshtastic.region,
            channel=config.config.meshtastic.channel,
            gateway_id=config.config.meshtastic.gateway_id
        )
        logger.debug(f"MQTT topic: {topic}")
        
        # Connect to MQTT broker
        try:
            logger.debug("Connecting to MQTT broker")
            client = MeshtasticMQTTClient(
                server=config.config.mqtt.server,
                port=config.config.mqtt.port,
                username=config.config.mqtt.username,
                password=config.config.mqtt.password
            )
            client.connect()
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"MQTT connection failed: {e}")
            sys.exit(2)
        except Exception as e:
            logger.error(f"Unexpected error connecting to MQTT broker: {e}")
            sys.exit(99)
        
        # Publish message
        try:
            logger.debug("Publishing message")
            client.publish(topic, protobuf_payload)
            logger.info(f"Message sent successfully to {config.config.meshtastic.to_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            sys.exit(2)
        
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        exit_code = 130
    
    except SystemExit as e:
        # Re-raise SystemExit to preserve exit code
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose if 'args' in locals() else False:
            import traceback
            logger.debug(traceback.format_exc())
        exit_code = 99
    
    finally:
        # Clean up MQTT connection
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass
    
    sys.exit(exit_code)
