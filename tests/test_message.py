"""Unit tests for message module."""

import unittest
from src.meshtastic_mqtt_protobuf.message import (
    parse_node_id,
    generate_packet_id,
    build_protobuf_message,
    build_topic
)


class TestParseNodeId(unittest.TestCase):
    """Test node ID parsing functionality."""
    
    def test_parse_hex_format(self):
        """Test parsing hex format node IDs."""
        result = parse_node_id("!12345678")
        self.assertEqual(result, 0x12345678)
    
    def test_parse_broadcast(self):
        """Test parsing broadcast address."""
        result = parse_node_id("^all")
        self.assertEqual(result, 0xFFFFFFFF)
    
    def test_parse_broadcast_case_insensitive(self):
        """Test broadcast parsing is case insensitive."""
        result = parse_node_id("^ALL")
        self.assertEqual(result, 0xFFFFFFFF)
    
    def test_parse_plain_integer(self):
        """Test parsing plain integer node IDs."""
        result = parse_node_id("12345")
        self.assertEqual(result, 12345)
    
    def test_invalid_hex_format(self):
        """Test error handling for invalid hex format."""
        with self.assertRaises(ValueError):
            parse_node_id("!xyz")
    
    def test_empty_node_id(self):
        """Test error handling for empty node ID."""
        with self.assertRaises(ValueError):
            parse_node_id("")


class TestGeneratePacketId(unittest.TestCase):
    """Test packet ID generation."""
    
    def test_generates_unique_ids(self):
        """Test that multiple calls generate different IDs."""
        id1 = generate_packet_id()
        id2 = generate_packet_id()
        self.assertNotEqual(id1, id2)
    
    def test_returns_integer(self):
        """Test that packet ID is an integer."""
        packet_id = generate_packet_id()
        self.assertIsInstance(packet_id, int)


class TestBuildProtobufMessage(unittest.TestCase):
    """Test protobuf message construction."""
    
    def test_builds_message(self):
        """Test basic message construction."""
        result = build_protobuf_message(
            text="Hello",
            to_id="^all",
            gateway_id="!12345678",
            channel="LongFast",
            want_ack=False,
            hop_limit=3
        )
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)
    
    def test_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        with self.assertRaises(ValueError):
            build_protobuf_message(
                text="",
                to_id="^all",
                gateway_id="!12345678",
                channel="LongFast"
            )
    
    def test_special_characters(self):
        """Test handling of special characters in text."""
        result = build_protobuf_message(
            text="Hello 世界! 🌍",
            to_id="^all",
            gateway_id="!12345678",
            channel="LongFast"
        )
        self.assertIsInstance(result, bytes)


class TestBuildTopic(unittest.TestCase):
    """Test MQTT topic construction."""
    
    def test_builds_correct_topic(self):
        """Test topic string generation."""
        result = build_topic("US", "LongFast", "!12345678")
        self.assertEqual(result, "msh/US/2/e/LongFast/!12345678")
    
    def test_different_regions(self):
        """Test topic with different region."""
        result = build_topic("EU", "LongFast", "!abcdef12")
        self.assertEqual(result, "msh/EU/2/e/LongFast/!abcdef12")


if __name__ == '__main__':
    unittest.main()
