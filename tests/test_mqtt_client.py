"""Unit tests for MQTT client module."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import paho.mqtt.client as mqtt
from src.meshtastic_mqtt_protobuf.mqtt_client import MeshtasticMQTTClient


class TestMeshtasticMQTTClient(unittest.TestCase):
    """Test MQTT client functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.server = "mqtt.example.com"
        self.port = 1883
        self.username = "testuser"
        self.password = "testpass"
    
    def test_init(self):
        """Test client initialization."""
        client = MeshtasticMQTTClient(
            self.server, self.port, self.username, self.password
        )
        self.assertEqual(client.server, self.server)
        self.assertEqual(client.port, self.port)
        self.assertEqual(client.username, self.username)
        self.assertEqual(client.password, self.password)
        self.assertFalse(client.connected)
        self.assertIsNone(client.client)
    
    @patch('paho.mqtt.client.Client')
    def test_connect_success(self, mock_mqtt_client):
        """Test successful connection to MQTT broker."""
        # Create mock client instance
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        # Create client and connect
        client = MeshtasticMQTTClient(
            self.server, self.port, self.username, self.password
        )
        
        # Simulate successful connection by calling the callback
        def simulate_connect(*args, **kwargs):
            # Trigger the on_connect callback with success code
            if client.client and client.client.on_connect:
                client.client.on_connect(None, None, None, 0)
        
        mock_client_instance.connect.side_effect = simulate_connect
        
        client.connect(timeout=1)
        
        # Verify connection was attempted
        mock_client_instance.username_pw_set.assert_called_once_with(
            self.username, self.password
        )
        mock_client_instance.connect.assert_called_once()
        mock_client_instance.loop_start.assert_called_once()
        self.assertTrue(client.connected)
    
    @patch('paho.mqtt.client.Client')
    def test_connect_bad_credentials(self, mock_mqtt_client):
        """Test connection failure with bad credentials."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        client = MeshtasticMQTTClient(
            self.server, self.port, self.username, self.password
        )
        
        # Simulate connection failure with bad credentials (rc=4)
        def simulate_connect_fail(*args, **kwargs):
            if client.client and client.client.on_connect:
                client.client.on_connect(None, None, None, 4)
        
        mock_client_instance.connect.side_effect = simulate_connect_fail
        
        with self.assertRaises(ConnectionError) as context:
            client.connect(timeout=1)
        
        self.assertIn("bad username or password", str(context.exception))
        self.assertFalse(client.connected)
    
    @patch('paho.mqtt.client.Client')
    def test_connect_timeout(self, mock_mqtt_client):
        """Test connection timeout."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        client = MeshtasticMQTTClient(
            self.server, self.port, self.username, self.password
        )
        
        # Don't trigger callback to simulate timeout
        with self.assertRaises(TimeoutError) as context:
            client.connect(timeout=0.2)
        
        self.assertIn("timed out", str(context.exception))
    
    @patch('paho.mqtt.client.Client')
    def test_publish_success(self, mock_mqtt_client):
        """Test successful message publishing."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        # Mock publish result
        mock_result = MagicMock()
        mock_result.rc = mqtt.MQTT_ERR_SUCCESS
        mock_client_instance.publish.return_value = mock_result
        
        client = MeshtasticMQTTClient(
            self.server, self.port, self.username, self.password
        )
        
        # Simulate connection
        def simulate_connect(*args, **kwargs):
            if client.client and client.client.on_connect:
                client.client.on_connect(None, None, None, 0)
        
        mock_client_instance.connect.side_effect = simulate_connect
        client.connect(timeout=1)
        
        # Publish message
        topic = "msh/US/2/e/LongFast/!12345678"
        payload = b"test binary payload"
        
        client.publish(topic, payload)
        
        # Verify publish was called with correct parameters
        mock_client_instance.publish.assert_called_once_with(topic, payload, qos=1)
        mock_result.wait_for_publish.assert_called_once()
    
    @patch('paho.mqtt.client.Client')
    def test_publish_not_connected(self, mock_mqtt_client):
        """Test publishing without connection raises error."""
        client = MeshtasticMQTTClient(
            self.server, self.port, self.username, self.password
        )
        
        with self.assertRaises(RuntimeError) as context:
            client.publish("test/topic", b"payload")
        
        self.assertIn("Not connected", str(context.exception))
    
    @patch('paho.mqtt.client.Client')
    def test_publish_invalid_payload(self, mock_mqtt_client):
        """Test publishing non-bytes payload raises error."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        client = MeshtasticMQTTClient(
            self.server, self.port, self.username, self.password
        )
        
        # Simulate connection
        def simulate_connect(*args, **kwargs):
            if client.client and client.client.on_connect:
                client.client.on_connect(None, None, None, 0)
        
        mock_client_instance.connect.side_effect = simulate_connect
        client.connect(timeout=1)
        
        # Try to publish string instead of bytes
        with self.assertRaises(ValueError) as context:
            client.publish("test/topic", "string payload")
        
        self.assertIn("must be bytes", str(context.exception))
    
    @patch('paho.mqtt.client.Client')
    def test_disconnect(self, mock_mqtt_client):
        """Test clean disconnect from broker."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        client = MeshtasticMQTTClient(
            self.server, self.port, self.username, self.password
        )
        
        # Simulate connection
        def simulate_connect(*args, **kwargs):
            if client.client and client.client.on_connect:
                client.client.on_connect(None, None, None, 0)
        
        mock_client_instance.connect.side_effect = simulate_connect
        client.connect(timeout=1)
        
        # Disconnect
        client.disconnect()
        
        # Verify disconnect was called
        mock_client_instance.loop_stop.assert_called_once()
        mock_client_instance.disconnect.assert_called_once()
        self.assertFalse(client.connected)
        self.assertIsNone(client.client)


if __name__ == '__main__':
    unittest.main()
