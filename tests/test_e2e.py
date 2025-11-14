"""End-to-end tests for Meshtastic MQTT Protobuf tool.

These tests verify the complete functionality of the tool by:
1. Testing with actual Meshtastic MQTT broker (mqtt.meshtastic.org)
2. Validating protobuf message structure and compatibility
3. Testing broadcast and direct messaging scenarios
4. Testing acknowledgment requests

Note: These tests require network connectivity to mqtt.meshtastic.org
"""

import unittest
import sys
import os
from unittest.mock import patch
import time

from src.meshtastic_mqtt_protobuf.cli import main
from src.meshtastic_mqtt_protobuf.message import (
    build_protobuf_message,
    build_topic,
    parse_node_id
)
from src.meshtastic_mqtt_protobuf.mqtt_client import MeshtasticMQTTClient
from src.meshtastic_mqtt_protobuf.config import Config

# Import protobuf modules to validate message structure
from meshtastic import mesh_pb2, mqtt_pb2, portnums_pb2


class TestProtobufCompatibility(unittest.TestCase):
    """Test protobuf message compatibility with Meshtastic specification."""
    
    def test_protobuf_message_structure(self):
        """Verify protobuf message matches Meshtastic specification."""
        # Build a test message
        text = "Test message"
        to_id = "^all"
        gateway_id = "!12345678"
        channel = "LongFast"
        want_ack = True
        hop_limit = 3
        
        # Build protobuf message
        protobuf_bytes = build_protobuf_message(
            text=text,
            to_id=to_id,
            gateway_id=gateway_id,
            channel=channel,
            want_ack=want_ack,
            hop_limit=hop_limit
        )
        
        # Verify it's bytes
        self.assertIsInstance(protobuf_bytes, bytes)
        self.assertGreater(len(protobuf_bytes), 0)
        
        # Deserialize and validate structure
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.ParseFromString(protobuf_bytes)
        
        # Verify ServiceEnvelope fields
        self.assertEqual(envelope.channel_id, channel)
        self.assertEqual(envelope.gateway_id, gateway_id)
        self.assertTrue(envelope.HasField('packet'))
        
        # Verify MeshPacket fields
        packet = envelope.packet
        self.assertEqual(getattr(packet, 'from'), parse_node_id(gateway_id))
        self.assertEqual(packet.to, parse_node_id(to_id))
        self.assertGreater(packet.id, 0)
        self.assertEqual(packet.channel, 0)
        self.assertEqual(packet.hop_limit, hop_limit)
        self.assertEqual(packet.want_ack, want_ack)
        self.assertTrue(packet.HasField('decoded'))
        
        # Verify Data payload
        data = packet.decoded
        self.assertEqual(data.portnum, portnums_pb2.PortNum.TEXT_MESSAGE_APP)
        self.assertEqual(data.payload.decode('utf-8'), text)
    
    def test_protobuf_broadcast_message(self):
        """Verify broadcast message structure."""
        protobuf_bytes = build_protobuf_message(
            text="Broadcast test",
            to_id="^all",
            gateway_id="!abcdef12",
            channel="LongFast"
        )
        
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.ParseFromString(protobuf_bytes)
        
        # Verify broadcast address
        self.assertEqual(envelope.packet.to, 0xFFFFFFFF)
    
    def test_protobuf_direct_message(self):
        """Verify direct message structure."""
        target_id = "!87654321"
        protobuf_bytes = build_protobuf_message(
            text="Direct test",
            to_id=target_id,
            gateway_id="!abcdef12",
            channel="LongFast"
        )
        
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.ParseFromString(protobuf_bytes)
        
        # Verify specific recipient
        self.assertEqual(envelope.packet.to, parse_node_id(target_id))
        self.assertNotEqual(envelope.packet.to, 0xFFFFFFFF)
    
    def test_protobuf_acknowledgment_flag(self):
        """Verify want_ack flag is properly set."""
        # Test with want_ack=True
        protobuf_bytes = build_protobuf_message(
            text="Ack test",
            to_id="^all",
            gateway_id="!12345678",
            channel="LongFast",
            want_ack=True
        )
        
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.ParseFromString(protobuf_bytes)
        self.assertTrue(envelope.packet.want_ack)
        
        # Test with want_ack=False
        protobuf_bytes = build_protobuf_message(
            text="No ack test",
            to_id="^all",
            gateway_id="!12345678",
            channel="LongFast",
            want_ack=False
        )
        
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.ParseFromString(protobuf_bytes)
        self.assertFalse(envelope.packet.want_ack)
    
    def test_protobuf_hop_limit_values(self):
        """Verify hop_limit is properly encoded."""
        for hop_limit in [0, 1, 3, 5, 7]:
            protobuf_bytes = build_protobuf_message(
                text=f"Hop limit {hop_limit}",
                to_id="^all",
                gateway_id="!12345678",
                channel="LongFast",
                hop_limit=hop_limit
            )
            
            envelope = mqtt_pb2.ServiceEnvelope()
            envelope.ParseFromString(protobuf_bytes)
            self.assertEqual(envelope.packet.hop_limit, hop_limit)
    
    def test_protobuf_unicode_text(self):
        """Verify Unicode text is properly encoded."""
        unicode_text = "Hello 世界! 🌍 Émojis and spëcial çhars"
        protobuf_bytes = build_protobuf_message(
            text=unicode_text,
            to_id="^all",
            gateway_id="!12345678",
            channel="LongFast"
        )
        
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.ParseFromString(protobuf_bytes)
        decoded_text = envelope.packet.decoded.payload.decode('utf-8')
        self.assertEqual(decoded_text, unicode_text)


class TestMQTTBrokerConnection(unittest.TestCase):
    """Test connection to actual Meshtastic MQTT broker.
    
    These tests connect to mqtt.meshtastic.org to verify real-world functionality.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        cls.server = "mqtt.meshtastic.org"
        cls.port = 1883
        cls.username = "meshdev"
        cls.password = "large4cats"
        cls.gateway_id = "!12345678"  # Test gateway ID
        cls.region = "US"
        cls.channel = "LongFast"
    
    def test_mqtt_broker_connectivity(self):
        """Test connection to mqtt.meshtastic.org."""
        try:
            client = MeshtasticMQTTClient(
                server=self.server,
                port=self.port,
                username=self.username,
                password=self.password
            )
            
            # Attempt connection
            client.connect(timeout=10)
            self.assertTrue(client.connected)
            
            # Clean disconnect
            client.disconnect()
            self.assertFalse(client.connected)
            
        except (ConnectionError, TimeoutError) as e:
            self.skipTest(f"Could not connect to MQTT broker: {e}")
    
    def test_publish_broadcast_message(self):
        """Test publishing a broadcast message to actual broker."""
        try:
            # Build message
            text = f"Test broadcast message at {time.time()}"
            protobuf_bytes = build_protobuf_message(
                text=text,
                to_id="^all",
                gateway_id=self.gateway_id,
                channel=self.channel,
                want_ack=False,
                hop_limit=3
            )
            
            # Build topic
            topic = build_topic(self.region, self.channel, self.gateway_id)
            
            # Connect and publish
            client = MeshtasticMQTTClient(
                server=self.server,
                port=self.port,
                username=self.username,
                password=self.password
            )
            
            client.connect(timeout=10)
            client.publish(topic, protobuf_bytes)
            client.disconnect()
            
            # If we get here, publish was successful
            self.assertTrue(True)
            
        except (ConnectionError, TimeoutError) as e:
            self.skipTest(f"Could not connect to MQTT broker: {e}")
        except Exception as e:
            self.fail(f"Failed to publish message: {e}")
    
    def test_publish_direct_message(self):
        """Test publishing a direct message to specific node."""
        try:
            # Build message to specific node
            text = f"Test direct message at {time.time()}"
            target_id = "!87654321"  # Test target node
            
            protobuf_bytes = build_protobuf_message(
                text=text,
                to_id=target_id,
                gateway_id=self.gateway_id,
                channel=self.channel,
                want_ack=False,
                hop_limit=3
            )
            
            # Build topic
            topic = build_topic(self.region, self.channel, self.gateway_id)
            
            # Connect and publish
            client = MeshtasticMQTTClient(
                server=self.server,
                port=self.port,
                username=self.username,
                password=self.password
            )
            
            client.connect(timeout=10)
            client.publish(topic, protobuf_bytes)
            client.disconnect()
            
            # If we get here, publish was successful
            self.assertTrue(True)
            
        except (ConnectionError, TimeoutError) as e:
            self.skipTest(f"Could not connect to MQTT broker: {e}")
        except Exception as e:
            self.fail(f"Failed to publish message: {e}")
    
    def test_publish_with_acknowledgment(self):
        """Test publishing a message with acknowledgment request."""
        try:
            # Build message with want_ack=True
            text = f"Test ack message at {time.time()}"
            
            protobuf_bytes = build_protobuf_message(
                text=text,
                to_id="^all",
                gateway_id=self.gateway_id,
                channel=self.channel,
                want_ack=True,  # Request acknowledgment
                hop_limit=3
            )
            
            # Build topic
            topic = build_topic(self.region, self.channel, self.gateway_id)
            
            # Connect and publish
            client = MeshtasticMQTTClient(
                server=self.server,
                port=self.port,
                username=self.username,
                password=self.password
            )
            
            client.connect(timeout=10)
            client.publish(topic, protobuf_bytes)
            client.disconnect()
            
            # Verify message structure has want_ack set
            envelope = mqtt_pb2.ServiceEnvelope()
            envelope.ParseFromString(protobuf_bytes)
            self.assertTrue(envelope.packet.want_ack)
            
        except (ConnectionError, TimeoutError) as e:
            self.skipTest(f"Could not connect to MQTT broker: {e}")
        except Exception as e:
            self.fail(f"Failed to publish message: {e}")


class TestCLIEndToEnd(unittest.TestCase):
    """Test complete CLI workflow with actual broker."""
    
    def setUp(self):
        """Set up test configuration."""
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.yaml')
        
        # Create config with actual broker credentials
        Config.create_default_config(self.config_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cli_broadcast_message(self):
        """Test sending broadcast message via CLI."""
        test_args = [
            'meshtastic-send-pb',
            '--message', f'CLI broadcast test at {time.time()}',
            '--config', self.config_path
        ]
        
        try:
            with patch.object(sys, 'argv', test_args):
                with self.assertRaises(SystemExit) as context:
                    main()
                
                # Should exit with code 0 on success
                self.assertEqual(context.exception.code, 0)
        
        except Exception as e:
            # If connection fails, skip test
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                self.skipTest(f"Could not connect to MQTT broker: {e}")
            else:
                raise
    
    def test_cli_direct_message(self):
        """Test sending direct message via CLI."""
        test_args = [
            'meshtastic-send-pb',
            '--message', f'CLI direct test at {time.time()}',
            '--to-id', '!87654321',
            '--config', self.config_path
        ]
        
        try:
            with patch.object(sys, 'argv', test_args):
                with self.assertRaises(SystemExit) as context:
                    main()
                
                # Should exit with code 0 on success
                self.assertEqual(context.exception.code, 0)
        
        except Exception as e:
            # If connection fails, skip test
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                self.skipTest(f"Could not connect to MQTT broker: {e}")
            else:
                raise
    
    def test_cli_with_acknowledgment(self):
        """Test sending message with acknowledgment request via CLI."""
        test_args = [
            'meshtastic-send-pb',
            '--message', f'CLI ack test at {time.time()}',
            '--want-ack',
            '--config', self.config_path
        ]
        
        try:
            with patch.object(sys, 'argv', test_args):
                with self.assertRaises(SystemExit) as context:
                    main()
                
                # Should exit with code 0 on success
                self.assertEqual(context.exception.code, 0)
        
        except Exception as e:
            # If connection fails, skip test
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                self.skipTest(f"Could not connect to MQTT broker: {e}")
            else:
                raise
    
    def test_cli_custom_hop_limit(self):
        """Test sending message with custom hop limit via CLI."""
        test_args = [
            'meshtastic-send-pb',
            '--message', f'CLI hop limit test at {time.time()}',
            '--hop-limit', '5',
            '--config', self.config_path
        ]
        
        try:
            with patch.object(sys, 'argv', test_args):
                with self.assertRaises(SystemExit) as context:
                    main()
                
                # Should exit with code 0 on success
                self.assertEqual(context.exception.code, 0)
        
        except Exception as e:
            # If connection fails, skip test
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                self.skipTest(f"Could not connect to MQTT broker: {e}")
            else:
                raise


if __name__ == '__main__':
    unittest.main()
