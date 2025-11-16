# Meshtastic MQTT Protobuf CLI

A Python command-line tool for sending messages to Meshtastic devices via MQTT using the native Protocol Buffer format. Unlike JSON-based implementations that require special gateway configuration, this tool uses the standard protobuf encoding that all Meshtastic devices natively support.

## Features

- Native protobuf message encoding using official Meshtastic protocol definitions
- YAML configuration file for storing connection settings
- Command-line argument overrides for flexible usage
- Support for broadcast and direct messaging
- Message acknowledgment requests and hop limit control
- Compatible with any standard Meshtastic MQTT gateway
- No special gateway configuration required

## Installation

### From Source

```bash
git clone https://github.com/yourusername/meshtastic-mqtt-protobuf.git
cd meshtastic-mqtt-protobuf
pip install -e .
```

### Using pip (future)

```bash
pip install meshtastic-mqtt-protobuf
```

### Requirements

- Python 3.7 or higher
- Dependencies (automatically installed):
  - meshtastic >= 2.2.0
  - paho-mqtt >= 1.6.1
  - PyYAML >= 6.0

## Configuration

### Configuration File

The tool uses a YAML configuration file to store default connection settings. On first run, a default configuration file is created at:

- **Linux/macOS**: `~/.config/meshtastic-mqtt-protobuf/config.yaml`
- **Windows**: `%APPDATA%\meshtastic-mqtt-protobuf\config.yaml`

### Configuration Format

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

### Required Fields

- `mqtt.server`: MQTT broker address
- `mqtt.username`: MQTT username
- `mqtt.password`: MQTT password
- `meshtastic.gateway_id`: Your gateway's node ID (format: `!12345678`)

### Optional Fields

- `mqtt.port`: MQTT broker port (default: 1883)
- `meshtastic.to_id`: Recipient node ID or `^all` for broadcast (default: `^all`)
- `meshtastic.channel`: Meshtastic channel name (default: `LongFast`)
- `meshtastic.region`: Region code (default: `US`)
- `meshtastic.want_ack`: Request message acknowledgment (default: false)
- `meshtastic.hop_limit`: Maximum hops for message propagation (default: 3)

## Usage

### Basic Usage

Send a broadcast message using configuration file settings:

```bash
meshtastic-send-pb --message "Hello Meshtastic!"
```

### Send to Specific Node

Send a message to a specific node:

```bash
meshtastic-send-pb --message "Hello Node!" --to-id "!87654321"
```

### Override Configuration

Override MQTT server and credentials:

```bash
meshtastic-send-pb --message "Test message" \
  --server mqtt.example.com \
  --username myuser \
  --password mypass
```

### Request Acknowledgment

Send a message with acknowledgment request:

```bash
meshtastic-send-pb --message "Important message" --want-ack
```

### Set Hop Limit

Control message propagation distance:

```bash
meshtastic-send-pb --message "Local message" --hop-limit 1
```

### Verbose Mode

Enable detailed logging for debugging:

```bash
meshtastic-send-pb --message "Debug test" --verbose
```

### Custom Configuration File

Use a different configuration file:

```bash
meshtastic-send-pb --message "Test" --config /path/to/config.yaml
```

## Command-Line Arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--message` | `-m` | Message text to send | Yes |
| `--server` | | MQTT server address | No* |
| `--port` | | MQTT server port (default: 1883) | No |
| `--username` | `-u` | MQTT username | No* |
| `--password` | `-p` | MQTT password | No* |
| `--gateway-id` | | Gateway node ID for MQTT topic | No* |
| `--to-id` | | Recipient node ID (default: broadcast) | No |
| `--channel` | | Meshtastic channel name | No |
| `--region` | | Meshtastic region code | No |
| `--want-ack` | | Request message acknowledgment | No |
| `--hop-limit` | | Maximum hops (1-7) | No |
| `--config` | | Path to config file | No |
| `--verbose` | `-v` | Enable verbose logging | No |
| `--help` | `-h` | Show help message | No |

*Required if not specified in configuration file

## Examples

### Example 1: Quick Broadcast

```bash
meshtastic-send-pb -m "Hello everyone!"
```

### Example 2: Direct Message with Acknowledgment

```bash
meshtastic-send-pb \
  --message "Are you there?" \
  --to-id "!12345678" \
  --want-ack
```

### Example 3: Local Network Message

```bash
meshtastic-send-pb \
  --message "Testing local mesh" \
  --hop-limit 2 \
  --channel "LongFast"
```

### Example 4: Custom MQTT Broker

```bash
meshtastic-send-pb \
  --message "Private network test" \
  --server mqtt.private.local \
  --username admin \
  --password secret123 \
  --gateway-id "!ABCDEF01"
```

## Troubleshooting

### Connection Refused

**Error**: `Connection refused` or `Connection timeout`

**Solutions**:
- Verify MQTT server address and port are correct
- Check network connectivity to the MQTT broker
- Ensure firewall allows outbound connections on port 1883
- Try using verbose mode (`--verbose`) to see detailed connection logs

### Authentication Failed

**Error**: `Authentication failed` or `Not authorized`

**Solutions**:
- Verify username and password are correct
- Check that credentials match your MQTT broker configuration
- For mqtt.meshtastic.org, use username `meshdev` and password `large4cats`

### Invalid Node ID Format

**Error**: `Invalid node ID format`

**Solutions**:
- Node IDs should be in format `!12345678` (8 hex characters with `!` prefix)
- Use `^all` for broadcast messages
- Check your gateway's node ID in the Meshtastic app

### Configuration File Not Found

**Error**: `Configuration file not found`

**Solutions**:
- Run the tool once to create a default configuration file
- Specify a custom config file path with `--config`
- Manually create the config directory and file

### Missing Required Parameters

**Error**: `Missing required parameter: server`

**Solutions**:
- Ensure all required fields are in your configuration file
- Provide missing parameters via command-line arguments
- Check configuration file syntax is valid YAML

### Protobuf Serialization Error

**Error**: `Failed to serialize protobuf message`

**Solutions**:
- Update the meshtastic package: `pip install --upgrade meshtastic`
- Check that message text doesn't contain invalid characters
- Verify hop_limit is within valid range (1-7)

## Differences from JSON Implementation

This tool uses the native Meshtastic protobuf format instead of JSON, which provides several advantages:

| Feature | Protobuf (This Tool) | JSON Implementation |
|---------|---------------------|---------------------|
| Gateway Config | No special config needed | Requires JSON plugin enabled |
| Message Format | Binary protobuf | JSON text |
| Topic Pattern | `msh/[region]/2/e/[channel]/[gateway_id]` | `msh/[region]/2/json/[channel]/[gateway_id]` |
| Compatibility | All standard gateways | Only JSON-enabled gateways |
| Protocol | Official Meshtastic protobufs | Custom JSON format |
| Message Size | Smaller (binary) | Larger (text) |
| Features | Full protocol support | Limited to JSON fields |

### Why Use Protobuf?

- **Universal Compatibility**: Works with any Meshtastic gateway without special configuration
- **Official Protocol**: Uses the same format as Meshtastic devices internally
- **Future-Proof**: Automatically compatible with new protocol features
- **Efficient**: Binary format is more compact than JSON
- **Type-Safe**: Protocol Buffers provide strong typing and validation

## Protocol Details

### Message Structure

Messages are encoded using the Meshtastic Protocol Buffer definitions:

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

### MQTT Topic Format

Topics follow the pattern: `msh/[region]/2/e/[channel]/[gateway_id]`

- `msh`: Meshtastic prefix
- `[region]`: Region code (e.g., "US", "EU")
- `2`: Protocol version
- `e`: Envelope format (protobuf)
- `[channel]`: Channel name (e.g., "LongFast")
- `[gateway_id]`: Gateway node ID (e.g., "!12345678")

## Security Considerations

- Configuration files are created with restricted permissions (0600 on Unix-like systems)
- Avoid passing passwords via command-line arguments (visible in process list)
- Store credentials in the configuration file instead
- Ensure `.gitignore` excludes configuration files to prevent credential commits
- Consider using environment variables for sensitive data in automated scripts

## Links and Resources

- [Meshtastic Official Documentation](https://meshtastic.org/docs/)
- [Meshtastic MQTT Integration Guide](https://meshtastic.org/docs/software/integrations/mqtt/)
- [Meshtastic Protocol Buffers](https://buf.build/meshtastic/protobufs)
- [Meshtastic Python Package](https://pypi.org/project/meshtastic/)
- [MQTT Protocol](https://mqtt.org/)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later).

See the [LICENSE](LICENSE) file for the full license text.

### What this means:

- You are free to use, modify, and distribute this software
- If you distribute modified versions, you must also license them under GPL v3
- You must make the source code available when distributing the software
- There is NO WARRANTY for this software

For more information, visit: https://www.gnu.org/licenses/gpl-3.0.html

## Acknowledgments

- Meshtastic project for the excellent mesh networking platform
- Official Meshtastic Python package for protobuf definitions
