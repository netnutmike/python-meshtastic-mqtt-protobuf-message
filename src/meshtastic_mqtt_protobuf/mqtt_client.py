"""MQTT client module for connecting and publishing to Meshtastic MQTT brokers.

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

This module provides an MQTT client specifically designed for publishing
binary protobuf messages to Meshtastic MQTT brokers. It handles connection
management, authentication, and reliable message delivery.

MQTT Protocol Details:
---------------------
- Uses MQTT v3.1.1 protocol via paho-mqtt library
- QoS 1 (at least once delivery) for reliable message transmission
- Binary payload format (protobuf serialized bytes)
- Standard MQTT authentication with username/password

Connection Flow:
---------------
1. Create client instance with broker credentials
2. Set username/password for authentication
3. Connect to broker (async with callback)
4. Wait for connection confirmation
5. Publish binary protobuf messages
6. Disconnect cleanly when done

Error Handling:
--------------
The client provides detailed error messages for common failure scenarios:
- Connection refused (network, authentication, authorization)
- Publish failures (no connection, queue full)
- Timeout errors (slow network, unresponsive broker)
"""

import logging
import paho.mqtt.client as mqtt


logger = logging.getLogger(__name__)


class MeshtasticMQTTClient:
    """MQTT client for publishing protobuf messages to Meshtastic brokers."""
    
    def __init__(self, server, port, username, password):
        """Initialize MQTT client with connection parameters.
        
        Args:
            server: MQTT broker address
            port: MQTT broker port
            username: MQTT username
            password: MQTT password
        """
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.connected = False
        self.connection_error = None
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker.
        
        Args:
            client: MQTT client instance
            userdata: User data
            flags: Connection flags
            rc: Connection result code
        """
        if rc == 0:
            self.connected = True
            self.connection_error = None
            logger.info(f"Connected to MQTT broker at {self.server}:{self.port}")
        else:
            self.connected = False
            # Map result codes to error messages
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            self.connection_error = error_messages.get(rc, f"Connection refused - unknown error (code {rc})")
            logger.error(f"Failed to connect to MQTT broker: {self.connection_error}")
    
    def connect(self, timeout=10):
        """Establish connection to MQTT broker.
        
        Args:
            timeout: Connection timeout in seconds (default: 10)
            
        Raises:
            ConnectionError: If connection fails
            TimeoutError: If connection times out
        """
        try:
            # Create MQTT client instance
            self.client = mqtt.Client()
            
            # Set username and password
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            
            # Connect to broker
            logger.debug(f"Connecting to MQTT broker at {self.server}:{self.port}")
            self.client.connect(self.server, self.port, keepalive=60)
            
            # Start network loop in background
            self.client.loop_start()
            
            # Wait for connection with timeout
            import time
            elapsed = 0
            while not self.connected and self.connection_error is None and elapsed < timeout:
                time.sleep(0.1)
                elapsed += 0.1
            
            # Check connection status
            if self.connected:
                return
            elif self.connection_error:
                raise ConnectionError(f"Failed to connect to MQTT broker at {self.server}:{self.port}: {self.connection_error}")
            else:
                raise TimeoutError(f"Connection to MQTT broker at {self.server}:{self.port} timed out after {timeout} seconds")
        
        except TimeoutError:
            # Re-raise TimeoutError without wrapping
            raise
        except (OSError, ConnectionRefusedError) as e:
            raise ConnectionError(f"Failed to connect to MQTT broker at {self.server}:{self.port}: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for when a message is published.
        
        Args:
            client: MQTT client instance
            userdata: User data
            mid: Message ID
        """
        logger.debug(f"Message published successfully (mid: {mid})")
    
    def publish(self, topic, payload):
        """Publish binary protobuf message to MQTT topic.
        
        Publishes a binary protobuf message using QoS 1 (at least once delivery)
        to ensure reliable transmission. The message is sent as raw bytes without
        any encoding or content-type headers.
        
        QoS Level Explanation:
        ---------------------
        QoS 1 (at least once): The broker acknowledges receipt of the message.
        If the acknowledgment is not received, the message is retransmitted.
        This provides a good balance between reliability and performance for
        Meshtastic messages.
        
        Binary Format:
        -------------
        The payload must be raw bytes (protobuf serialized). MQTT brokers
        handle binary data natively, so no base64 encoding or other
        transformation is needed. This is more efficient than JSON text format.
        
        Args:
            topic: MQTT topic string (e.g., "msh/US/2/e/LongFast/!12345678")
            payload: Binary protobuf message bytes (ServiceEnvelope serialized)
            
        Raises:
            RuntimeError: If not connected to broker
            ValueError: If payload is not bytes
            Exception: If publish fails
        """
        if not self.connected or self.client is None:
            raise RuntimeError("Not connected to MQTT broker. Call connect() first.")
        
        if not isinstance(payload, bytes):
            raise ValueError("Payload must be bytes")
        
        try:
            # Set publish callback
            self.client.on_publish = self._on_publish
            
            # Publish with QoS 1 for reliable delivery
            # QoS 1 ensures the broker acknowledges receipt
            logger.debug(f"Publishing message to topic: {topic}")
            logger.debug(f"Payload size: {len(payload)} bytes")
            
            result = self.client.publish(topic, payload, qos=1)
            
            # Check if publish was successful
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                error_messages = {
                    mqtt.MQTT_ERR_NO_CONN: "No connection to broker",
                    mqtt.MQTT_ERR_QUEUE_SIZE: "Message queue is full"
                }
                error_msg = error_messages.get(result.rc, f"Publish failed with error code {result.rc}")
                raise Exception(f"Failed to publish message: {error_msg}")
            
            # Wait for message to be sent and acknowledged by broker
            result.wait_for_publish()
            
            logger.info(f"Message published successfully to {topic}")
            
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            raise
    
    def disconnect(self):
        """Cleanly disconnect from MQTT broker and release resources."""
        if self.client is not None:
            try:
                logger.debug("Disconnecting from MQTT broker")
                self.client.loop_stop()
                self.client.disconnect()
                self.connected = False
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.client = None
