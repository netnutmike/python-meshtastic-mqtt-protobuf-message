"""Integration tests for CLI module."""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from io import StringIO

from src.meshtastic_mqtt_protobuf.cli import (
    parse_arguments,
    validate_inputs,
    setup_logging,
    main
)
from src.meshtastic_mqtt_protobuf.config import Config


class TestParseArguments(unittest.TestCase):
    """Test command-line argument parsing."""
    
    def test_parse_minimal_args(self):
        """Test parsing with minimal required arguments."""
        test_args = ['meshtastic-send-pb', '--message', 'Test message']
        with patch.object(sys, 'argv', test_args):
            args = parse_arguments()
            self.assertEqual(args.message, 'Test message')
            self.assertIsNone(args.server)
            self.assertFalse(args.verbose)
    
    def test_parse_all_args(self):
        """Test parsing with all arguments."""
        test_args = [
            'meshtastic-send-pb',
            '--message', 'Hello',
            '--server', 'mqtt.example.com',
            '--port', '1883',
            '--username', 'user',
            '--password', 'pass',
            '--gateway-id', '!12345678',
            '--to-id', '!abcdef12',
            '--channel', 'LongFast',
            '--region', 'US',
            '--want-ack',
            '--hop-limit', '5',
            '--config', '/path/to/config.yaml',
            '--verbose'
        ]
        with patch.object(sys, 'argv', test_args):
            args = parse_arguments()
            self.assertEqual(args.message, 'Hello')
            self.assertEqual(args.server, 'mqtt.example.com')
            self.assertEqual(args.port, 1883)
            self.assertEqual(args.username, 'user')
            self.assertEqual(args.password, 'pass')
            self.assertEqual(args.gateway_id, '!12345678')
            self.assertEqual(args.to_id, '!abcdef12')
            self.assertEqual(args.channel, 'LongFast')
            self.assertEqual(args.region, 'US')
            self.assertTrue(args.want_ack)
            self.assertEqual(args.hop_limit, 5)
            self.assertEqual(args.config, '/path/to/config.yaml')
            self.assertTrue(args.verbose)


class TestValidateInputs(unittest.TestCase):
    """Test input validation."""
    
    def test_valid_hop_limit(self):
        """Test validation passes with valid hop limit."""
        config = Config()
        config.config.meshtastic.hop_limit = 3
        # Should not raise
        validate_inputs(config)
    
    def test_invalid_hop_limit_too_high(self):
        """Test validation fails with hop limit too high."""
        config = Config()
        config.config.meshtastic.hop_limit = 10
        with self.assertRaises(ValueError) as context:
            validate_inputs(config)
        self.assertIn("hop_limit", str(context.exception))
    
    def test_invalid_hop_limit_negative(self):
        """Test validation fails with negative hop limit."""
        config = Config()
        config.config.meshtastic.hop_limit = -1
        with self.assertRaises(ValueError) as context:
            validate_inputs(config)
        self.assertIn("hop_limit", str(context.exception))


class TestSetupLogging(unittest.TestCase):
    """Test logging configuration."""
    
    def test_setup_logging_info_level(self):
        """Test logging setup with INFO level."""
        import logging
        # Clear any existing handlers
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        setup_logging(verbose=False)
        self.assertEqual(logger.level, logging.INFO)
    
    def test_setup_logging_debug_level(self):
        """Test logging setup with DEBUG level."""
        import logging
        # Clear any existing handlers
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        setup_logging(verbose=True)
        self.assertEqual(logger.level, logging.DEBUG)


class TestMainFunction(unittest.TestCase):
    """Test main CLI orchestration flow."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.yaml')
        
        # Create test config
        Config.create_default_config(self.config_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('src.meshtastic_mqtt_protobuf.cli.MeshtasticMQTTClient')
    def test_main_success_flow(self, mock_mqtt_client):
        """Test successful end-to-end flow."""
        # Mock MQTT client
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        # Test arguments
        test_args = [
            'meshtastic-send-pb',
            '--message', 'Test message',
            '--config', self.config_path
        ]
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # Should exit with code 0 on success
            self.assertEqual(context.exception.code, 0)
            
            # Verify MQTT client was used
            mock_client_instance.connect.assert_called_once()
            mock_client_instance.publish.assert_called_once()
            mock_client_instance.disconnect.assert_called_once()
    
    def test_main_missing_message(self):
        """Test error when message is missing."""
        test_args = [
            'meshtastic-send-pb',
            '--config', self.config_path
        ]
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # Should exit with non-zero code
            self.assertNotEqual(context.exception.code, 0)
    
    def test_main_empty_message(self):
        """Test error when message is empty."""
        test_args = [
            'meshtastic-send-pb',
            '--message', '',
            '--config', self.config_path
        ]
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # Should exit with code 3 (message validation error)
            self.assertEqual(context.exception.code, 3)
    
    def test_main_config_not_found_creates_default(self):
        """Test that missing config file creates default."""
        nonexistent_config = os.path.join(self.temp_dir, 'nonexistent.yaml')
        
        test_args = [
            'meshtastic-send-pb',
            '--message', 'Test',
            '--config', nonexistent_config
        ]
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # Should exit with code 1 and create config
            self.assertEqual(context.exception.code, 1)
            self.assertTrue(os.path.exists(nonexistent_config))
    
    @patch('src.meshtastic_mqtt_protobuf.cli.MeshtasticMQTTClient')
    def test_main_cli_overrides(self, mock_mqtt_client):
        """Test CLI arguments override config file."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        test_args = [
            'meshtastic-send-pb',
            '--message', 'Override test',
            '--config', self.config_path,
            '--server', 'custom.mqtt.com',
            '--gateway-id', '!99999999',
            '--want-ack'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as context:
                main()
            
            self.assertEqual(context.exception.code, 0)
            
            # Verify custom server was used
            call_args = mock_mqtt_client.call_args
            self.assertEqual(call_args[1]['server'], 'custom.mqtt.com')
    
    @patch('src.meshtastic_mqtt_protobuf.cli.MeshtasticMQTTClient')
    def test_main_connection_error(self, mock_mqtt_client):
        """Test handling of MQTT connection errors."""
        mock_client_instance = MagicMock()
        mock_client_instance.connect.side_effect = ConnectionError("Connection refused")
        mock_mqtt_client.return_value = mock_client_instance
        
        test_args = [
            'meshtastic-send-pb',
            '--message', 'Test',
            '--config', self.config_path
        ]
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # Should exit with code 2 (connection error)
            self.assertEqual(context.exception.code, 2)
    
    @patch('src.meshtastic_mqtt_protobuf.cli.MeshtasticMQTTClient')
    def test_main_invalid_hop_limit(self, mock_mqtt_client):
        """Test error with invalid hop limit."""
        test_args = [
            'meshtastic-send-pb',
            '--message', 'Test',
            '--config', self.config_path,
            '--hop-limit', '10'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as context:
                main()
            
            # Should exit with code 3 (validation error)
            self.assertEqual(context.exception.code, 3)


if __name__ == '__main__':
    unittest.main()
