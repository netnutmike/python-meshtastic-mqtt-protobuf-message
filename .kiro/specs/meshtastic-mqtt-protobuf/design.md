# Design Document

## Overview

The Meshtastic MQTT Protobuf CLI tool is a Python command-line application that sends messages to Meshtastic devices via MQTT using the native Protocol Buffer format. Unlike JSON-based implementations that require special gateway configuration, this tool uses the standard protobuf encoding that all Meshtastic devices natively support, ensuring compatibility with any standard Meshtastic MQTT gateway.

The tool leverages the official `meshtastic` Python package which includes the compiled protobuf definitions, ensuring protocol compatibility across firmware versions. Messages are encoded as ServiceEnvelope protobufs and published to topics following the pattern `msh/[region]/2/e/[channel]/[gateway_id]`.

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
meshtastic-mqtt-protobuf/
├── src/
│   └── meshtastic_mqtt_protobuf/
│       ├── __init__.py
│       ├── cli.py           # Command-line interface and argument parsing
│       ├── config.py        # Configuration management (YAML loading/saving)
│       ├── mqtt_client.py   # MQTT connection and publishing logic
│       └── message.py       # Meshtastic protobuf message construction
├── .gitignore
├── requirements.txt
├── setup.py
└── README.md
```

### Component Responsibilities

1. **CLI Module**: Handles argument parsing, validates user input, orchestrates the flow
2. **Config Module**: Manages YAML configuration file reading, writing, and merging with CLI overrides
3. **MQTT Client Module**: Establishes MQTT connections and publishes binary protobuf messages
4. **Message Module**: Constructs Meshtastic-compliant protobuf messages using the official meshtastic package

## Components and Interfaces

### CLI Module (`cli.py`)

**Purpose**: Entry point for the application, handles command-line argument parsing and orchestration.

**Key Functions**:
- `main()`: Entry point that coordinates all operations
- `parse_arguments()`: Uses argparse to define and parse command-line arguments
- `validate_inputs()`: Validates that required parameters are present after merging config and CLI args

**Command-Line Arguments**:
- `--message` or `-m`: Message text to send (required)
- `--server`: MQTT server address (optional, overrides config)
- `--port`: MQTT server port (optional, overrides config, default: 1883)
- `--username` or `-u`: MQTT username (optional, overrides config)
- `--password` or `-p`: MQTT password (optional, overrides config)
- `--gateway-id`: Gateway node ID for MQTT topic (optional, overrides config)
- `--to-id`: Recipient node ID (optional, overrides config, default: broadcast)
- `--channel`: Meshtastic channel name (optional, overrides config)
- `--region`: Meshtastic region (optional, overrides config)
- `--want-ack`: Request message acknowledgment (optional, flag)
- `--hop-limit`: Maximum hops for message propagation (optional, integer)
- `--config`: Path to config file (optional, default: ~/.config/meshtastic-mqtt-protobuf/config.yaml)
- `--verbose` or `-v`: Enable verbose logging (optional, flag)
- `--help` or `-h`: Display help information

### Config Module (`config.py`)

**Purpose**: Manages configuration file operations and merging with command-line overrides.

**Key Classes/Functions**:
- `Config` class: Represents configuration state
  - `load_from_file(path)`: Loads YAML configuration
  - `merge_with_cli_args(args)`: Merges CLI arguments, giving them priority
  - `validate()`: Ensures required fields are present
  - `create_default_config(path)`: Creates a default config file if none exists
  - `get(key, default=None)`: Retrieves configuration value

**YAML Configuration Structure**:
```yaml
mqtt:
  server: "mqtt.meshtastic.org"
  port: 1883
  username: "meshdev"
  password: "large4cats"
  
meshtastic:
  gateway_id: "!12345678"  # Your gateway's node ID
  to_id: "^all"            # Broadcast by default
  channel: "LongFast"
  region: "US"
  want_ack: false
  hop_limit: 3
```

### MQTT Client Module (`mqtt_client.py`)

**Purpose**: Handles MQTT connection establishment and binary message publishing.

**Key Classes/Functions**:
- `MeshtasticMQTTClient` class:
  - `__init__(server, port, username, password)`: Initialize client with connection parameters
  - `connect()`: Establish connection to MQTT broker
  - `publish(topic, payload)`: Publish binary protobuf message to specified topic
  - `disconnect()`: Clean disconnect from broker
  - `_on_connect(client, userdata, flags, rc)`: Connection callback
  - `_on_publish(client, userdata, mid)`: Publish callback

**Dependencies**: Uses `paho-mqtt` library for MQTT protocol implementation.

**Key Differences from JSON Version**:
- Publishes binary data instead of JSON strings
- Uses topic pattern with `/e/` instead of `/json/`
- No content-type headers needed (binary is default)

### Message Module (`message.py`)

**Purpose**: Constructs Meshtastic-compliant protobuf messages using the official meshtastic package.

**Key Functions**:
- `build_protobuf_message(text, to_id, gateway_id, want_ack, hop_limit)`: Creates ServiceEnvelope protobuf
- `build_topic(region, channel, gateway_id)`: Constructs MQTT topic string
- `parse_node_id(node_id)`: Converts node ID strings to integers
- `generate_packet_id()`: Generates unique packet identifiers

**Protobuf Message Construction**:

The message construction follows this hierarchy:
1. **ServiceEnvelope** (outer wrapper for MQTT)
   - Contains the packet and channel information
   - Gateway ID for routing
   
2. **MeshPacket** (the actual packet)
   - from: sender node ID (gateway)
   - to: recipient node ID (or broadcast)
   - id: unique packet identifier
   - channel: channel index
   - hop_limit: maximum hops
   - want_ack: acknowledgment request flag
   - decoded: contains the Data payload
   
3. **Data** (the payload)
   - portnum: TEXT_MESSAGE_APP (for text messages)
   - payload: UTF-8 encoded text bytes

**Example Construction**:
```python
from meshtastic import mesh_pb2, mqtt_pb2, portnums_pb2
import time

# Create the Data payload
data = mesh_pb2.Data()
data.portnum = portnums_pb2.PortNum.TEXT_MESSAGE_APP
data.payload = text.encode('utf-8')

# Create the MeshPacket
packet = mesh_pb2.MeshPacket()
packet.from_node = parse_node_id(gateway_id)
packet.to = parse_node_id(to_id)
packet.id = generate_packet_id()
packet.channel = 0  # Default channel index
packet.hop_limit = hop_limit
packet.want_ack = want_ack
packet.decoded.CopyFrom(data)

# Create the ServiceEnvelope
envelope = mqtt_pb2.ServiceEnvelope()
envelope.packet.CopyFrom(packet)
envelope.channel_id = channel
envelope.gateway_id = gateway_id

# Serialize to binary
return envelope.SerializeToString()
```

**Topic Format**: `msh/[region]/2/e/[channel]/[gateway_id]`
- `msh`: Meshtastic prefix
- `[region]`: Region code (e.g., "US", "EU")
- `2`: Protocol version
- `e`: Envelope format (protobuf)
- `[channel]`: Channel name (e.g., "LongFast")
- `[gateway_id]`: Gateway node ID (e.g., "!12345678")

## Data Models

### Configuration Data Model

```python
from dataclasses import dataclass

@dataclass
class MQTTConfig:
    server: str
    port: int = 1883
    username: str = ""
    password: str = ""

@dataclass
class MeshtasticConfig:
    gateway_id: str = ""      # Gateway node ID for MQTT topic
    to_id: str = "^all"       # Recipient (broadcast by default)
    channel: str = "LongFast"
    region: str = "US"
    want_ack: bool = False
    hop_limit: int = 3

@dataclass
class AppConfig:
    mqtt: MQTTConfig
    meshtastic: MeshtasticConfig
```

### Message Parameters

```python
@dataclass
class MessageParams:
    """Parameters for constructing a Meshtastic message."""
    text: str
    to_id: str
    gateway_id: str
    channel: str
    region: str
    want_ack: bool = False
    hop_limit: int = 3
```

## Error Handling

### Error Categories and Handling Strategy

1. **Configuration Errors**:
   - Missing required configuration: Display clear error message listing missing fields, exit code 1
   - Invalid YAML syntax: Display parse error with line number, exit code 1
   - Invalid file permissions: Display permission error, exit code 1

2. **MQTT Connection Errors**:
   - Connection refused: Display server/port details and suggest checking connectivity, exit code 2
   - Authentication failure: Display authentication error, suggest checking credentials, exit code 2
   - Timeout: Display timeout error with server details, exit code 2

3. **Message Construction Errors**:
   - Empty message: Display error requiring message content, exit code 3
   - Invalid node ID format: Display format requirements, exit code 3
   - Protobuf serialization error: Display error details, exit code 3
   - Invalid hop limit: Display valid range, exit code 3

4. **Protobuf Errors**:
   - Missing meshtastic package: Display installation instructions, exit code 4
   - Protobuf version mismatch: Display version requirements, exit code 4

5. **General Errors**:
   - Unexpected exceptions: Log full traceback, display user-friendly error, exit code 99

### Logging Strategy

- Use Python's `logging` module with configurable verbosity
- Default: INFO level (connection status, publish confirmation)
- Verbose mode (`--verbose` flag): DEBUG level (full MQTT protocol details, protobuf message contents)
- All errors logged to stderr
- Success messages logged to stdout
- In verbose mode, log hex dump of protobuf binary for debugging

## Testing Strategy

### Unit Tests

1. **Config Module Tests**:
   - Test YAML parsing with valid configuration
   - Test handling of missing configuration file
   - Test CLI argument override logic
   - Test validation of required fields
   - Test default config file creation

2. **Message Module Tests**:
   - Test protobuf message construction with various inputs
   - Test node ID parsing (hex format, broadcast)
   - Test topic string generation
   - Test packet ID generation uniqueness
   - Test protobuf serialization
   - Test handling of special characters in text
   - Test want_ack and hop_limit encoding

3. **MQTT Client Module Tests**:
   - Test connection establishment (using mock broker)
   - Test binary message publish operation
   - Test error handling for connection failures
   - Test clean disconnect

### Integration Tests

1. **End-to-End Flow**:
   - Test complete flow from CLI args to protobuf message publish (using test MQTT broker)
   - Test config file + CLI override combination
   - Test error scenarios (missing config, bad credentials)
   - Verify protobuf message structure matches Meshtastic specification

### Manual Testing

1. Test against actual Meshtastic MQTT broker (mqtt.meshtastic.org)
2. Verify messages are received by Meshtastic devices
3. Test with Meshtastic mobile app to confirm message delivery
4. Test various command-line argument combinations
5. Verify help documentation clarity
6. Test broadcast vs. direct messaging
7. Test acknowledgment requests

## Dependencies

### Required Python Packages

- `meshtastic>=2.2.0`: Official Meshtastic Python package with protobuf definitions
- `paho-mqtt>=1.6.1`: MQTT client library
- `PyYAML>=6.0`: YAML configuration file parsing
- `protobuf>=3.20.0`: Protocol Buffers runtime (dependency of meshtastic)
- `argparse`: Command-line argument parsing (standard library)
- `dataclasses`: Data models (standard library, Python 3.7+)
- `logging`: Logging functionality (standard library)

### Python Version

- Minimum: Python 3.7 (for dataclasses support)
- Recommended: Python 3.9+

## Installation and Distribution

### Installation Methods

1. **From source**:
   ```bash
   git clone <repository>
   cd meshtastic-mqtt-protobuf
   pip install -e .
   ```

2. **Using pip** (future):
   ```bash
   pip install meshtastic-mqtt-protobuf
   ```

### Entry Point

The tool will be installed as a command-line executable `meshtastic-send-pb` using setuptools entry_points.

## Configuration File Location

Default configuration file location follows platform conventions:
- Linux/macOS: `~/.config/meshtastic-mqtt-protobuf/config.yaml`
- Windows: `%APPDATA%\meshtastic-mqtt-protobuf\config.yaml`

The tool creates the directory and default config file on first run if they don't exist.

## Security Considerations

1. **Credential Storage**: YAML config file should have restricted permissions (0600 on Unix-like systems)
2. **Password Handling**: Passwords in CLI arguments visible in process list - config file preferred
3. **Config File Exclusion**: .gitignore must exclude config files to prevent credential commits
4. **Input Validation**: Sanitize all user inputs before constructing protobuf messages
5. **Binary Data**: Protobuf binary format prevents injection attacks
6. **Connection Security**: Support for TLS/SSL connections to MQTT broker (future enhancement)

## Key Differences from JSON Implementation

1. **Message Format**: Binary protobuf instead of JSON text
2. **Topic Pattern**: Uses `/e/` (envelope) instead of `/json/`
3. **Gateway ID**: Uses gateway_id instead of from_id (messages originate from gateway)
4. **Protocol Compliance**: Uses official meshtastic package ensuring compatibility
5. **No Special Gateway Config**: Works with standard Meshtastic MQTT gateways
6. **Message Structure**: ServiceEnvelope → MeshPacket → Data hierarchy
7. **Additional Options**: Supports want_ack and hop_limit flags
8. **Node ID Handling**: Gateway ID for topic, to_id for recipient

## Protobuf Version Compatibility

The tool uses the `meshtastic` Python package which includes versioned protobuf definitions. The package is regularly updated to match Meshtastic firmware releases. Users should:
- Keep the meshtastic package updated for latest protocol features
- Check compatibility with their Meshtastic firmware version
- Refer to Meshtastic release notes for protocol changes

## Future Enhancements

1. Support for TLS/SSL encrypted MQTT connections
2. Support for additional message types (position, telemetry)
3. Message receiving/subscribing functionality
4. Batch message sending from file input
5. Support for encrypted channels (PSK)
6. Interactive mode for sending multiple messages
7. Message status tracking and acknowledgment monitoring
8. Support for admin messages and device configuration
