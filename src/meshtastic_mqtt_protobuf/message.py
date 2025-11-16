"""Protobuf message construction module for Meshtastic messages.

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

This module handles the construction of Meshtastic protocol buffer messages
for transmission over MQTT. It uses the official Meshtastic protobuf definitions
from the meshtastic Python package to ensure protocol compatibility.

Protocol Overview:
-----------------
Meshtastic uses Protocol Buffers (protobuf) as its native message format.
Messages sent via MQTT are wrapped in a ServiceEnvelope that contains:
  1. A MeshPacket with routing information (from, to, hop_limit, etc.)
  2. A Data payload with the actual message content
  3. Channel and gateway metadata for MQTT routing

The protobuf format is more efficient than JSON and is natively supported
by all Meshtastic devices without requiring special gateway configuration.

Key Protobuf Types:
------------------
- ServiceEnvelope (mqtt_pb2): Outer wrapper for MQTT transport
- MeshPacket (mesh_pb2): Packet with routing and delivery information
- Data (mesh_pb2): Payload containing the actual message
- PortNum (portnums_pb2): Application port numbers (e.g., TEXT_MESSAGE_APP)

References:
----------
- Meshtastic MQTT Documentation: https://meshtastic.org/docs/software/integrations/mqtt/
- Meshtastic Protobufs: https://buf.build/meshtastic/protobufs
"""

import time
import random

from meshtastic import mesh_pb2, mqtt_pb2, portnums_pb2


def parse_node_id(node_id):
    """Parse a node ID string to integer format.
    
    Converts Meshtastic node ID formats to integer:
    - "!12345678" hex format -> integer
    - "^all" broadcast -> 0xFFFFFFFF (4294967295)
    
    Args:
        node_id: Node ID string (e.g., "!12345678" or "^all")
        
    Returns:
        Integer node ID
        
    Raises:
        ValueError: If node ID format is invalid
    """
    if not node_id:
        raise ValueError("Node ID cannot be empty")
    
    # Handle broadcast address
    if node_id.lower() == "^all":
        return 0xFFFFFFFF  # 4294967295
    
    # Handle hex format with ! prefix
    if node_id.startswith("!"):
        hex_str = node_id[1:]
        if not hex_str:
            raise ValueError("Node ID hex string cannot be empty after '!'")
        try:
            return int(hex_str, 16)
        except ValueError:
            raise ValueError(f"Invalid hex format in node ID: {node_id}")
    
    # Try parsing as plain integer
    try:
        return int(node_id)
    except ValueError:
        raise ValueError(f"Invalid node ID format: {node_id}. Expected '!<hex>', '^all', or integer")


def generate_packet_id():
    """Generate a unique packet identifier.
    
    Uses a combination of timestamp and random value to ensure uniqueness.
    
    Returns:
        Integer packet ID
    """
    # Use lower 32 bits of timestamp in milliseconds plus random component
    timestamp_ms = int(time.time() * 1000)
    random_component = random.randint(0, 0xFFFF)
    # Combine timestamp and random for uniqueness, keep within 32-bit range
    packet_id = ((timestamp_ms & 0xFFFF) << 16) | random_component
    return packet_id & 0xFFFFFFFF


def build_protobuf_message(text, to_id, gateway_id, channel, want_ack=False, hop_limit=3):
    """Build a Meshtastic protobuf message.
    
    Constructs a ServiceEnvelope containing a MeshPacket with Data payload
    following the Meshtastic MQTT protocol specification.
    
    Protobuf Message Structure:
    ---------------------------
    ServiceEnvelope (mqtt_pb2.ServiceEnvelope)
      ├── packet (MeshPacket) - The actual mesh packet
      │   ├── from - Sender node ID (gateway in this case)
      │   ├── to - Recipient node ID (or 0xFFFFFFFF for broadcast)
      │   ├── id - Unique packet identifier
      │   ├── channel - Channel index (0 for default)
      │   ├── hop_limit - Maximum hops before packet is dropped
      │   ├── want_ack - Whether sender wants acknowledgment
      │   └── decoded (Data) - The payload
      │       ├── portnum - Application port (TEXT_MESSAGE_APP for text)
      │       └── payload - UTF-8 encoded message bytes
      ├── channel_id - Channel name string (e.g., "LongFast")
      └── gateway_id - Gateway node ID string (e.g., "!12345678")
    
    This structure follows the official Meshtastic MQTT protocol and ensures
    compatibility with all Meshtastic devices and firmware versions.
    
    Args:
        text: Message text to send
        to_id: Recipient node ID (e.g., "!12345678" or "^all")
        gateway_id: Gateway node ID (e.g., "!12345678")
        channel: Channel name (e.g., "LongFast")
        want_ack: Whether to request acknowledgment (default: False)
        hop_limit: Maximum number of hops (default: 3)
        
    Returns:
        Serialized protobuf message bytes
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not text:
        raise ValueError("Message text cannot be empty")
    
    # Parse node IDs from string format to integer format
    # Gateway is the sender (from), recipient is the destination (to)
    from_node = parse_node_id(gateway_id)
    to_node = parse_node_id(to_id)
    
    # Step 1: Create the Data payload
    # This is the innermost layer containing the actual message content
    data = mesh_pb2.Data()
    data.portnum = portnums_pb2.PortNum.TEXT_MESSAGE_APP  # Port 1 = text messages
    data.payload = text.encode('utf-8')  # Encode text as UTF-8 bytes
    
    # Step 2: Create the MeshPacket
    # This wraps the Data payload with routing and delivery information
    packet = mesh_pb2.MeshPacket()
    setattr(packet, 'from', from_node)  # 'from' is a Python keyword, use setattr
    packet.to = to_node
    packet.id = generate_packet_id()  # Unique ID for tracking and deduplication
    packet.channel = 0  # Channel index (0 = default/primary channel)
    packet.hop_limit = hop_limit  # Max hops before packet expires
    packet.want_ack = want_ack  # Request acknowledgment from recipient
    packet.decoded.CopyFrom(data)  # Embed the Data payload
    
    # Step 3: Create the ServiceEnvelope
    # This is the outer wrapper used for MQTT transport
    # It contains the packet plus metadata for MQTT routing
    envelope = mqtt_pb2.ServiceEnvelope()
    envelope.packet.CopyFrom(packet)  # Embed the MeshPacket
    envelope.channel_id = channel  # Channel name string for topic routing
    envelope.gateway_id = gateway_id  # Gateway ID string for topic routing
    
    # Step 4: Serialize to binary format
    # The protobuf is converted to binary bytes for MQTT transmission
    return envelope.SerializeToString()


def build_topic(region, channel, gateway_id):
    """Build MQTT topic string for Meshtastic.
    
    Constructs topic following pattern: msh/[region]/2/e/[channel]/[gateway_id]
    
    Topic Structure Explanation:
    ----------------------------
    - msh: Meshtastic prefix (identifies Meshtastic MQTT messages)
    - [region]: Geographic region code (e.g., "US", "EU", "ANZ")
    - 2: Protocol version (version 2 is current)
    - e: Envelope format indicator (protobuf ServiceEnvelope)
         Note: JSON format uses 'json' instead of 'e'
    - [channel]: Channel name (e.g., "LongFast", "ShortSlow")
    - [gateway_id]: Gateway node ID that will relay the message
    
    Example: msh/US/2/e/LongFast/!12345678
    
    This topic format ensures messages are routed to the correct gateway
    and channel within the Meshtastic mesh network.
    
    Args:
        region: Region code (e.g., "US", "EU")
        channel: Channel name (e.g., "LongFast")
        gateway_id: Gateway node ID (e.g., "!12345678")
        
    Returns:
        MQTT topic string
    """
    return f"msh/{region}/2/e/{channel}/{gateway_id}"
