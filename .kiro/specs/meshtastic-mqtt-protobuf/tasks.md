# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create directory structure: src/meshtastic_mqtt_protobuf/ with __init__.py, cli.py, config.py, mqtt_client.py, message.py
  - Create requirements.txt with meshtastic>=2.2.0, paho-mqtt>=1.6.1, PyYAML>=6.0
  - Create setup.py with package metadata and entry point for meshtastic-send-pb command
  - Create .gitignore excluding Python cache, virtual environments, and config files
  - _Requirements: 8.1, 8.2, 8.4, 8.5_

- [x] 2. Implement configuration management module
  - [x] 2.1 Create Config class with data models for MQTT and Meshtastic settings
    - Define MQTTConfig and MeshtasticConfig dataclasses
    - Define AppConfig dataclass combining both configs
    - Implement Config class with load_from_file, merge_with_cli_args, validate, and get methods
    - _Requirements: 2.1, 2.2, 2.5_
  
  - [x] 2.2 Implement YAML configuration file loading and validation
    - Implement load_from_file to parse YAML and populate config objects
    - Add error handling for invalid YAML syntax with line number reporting
    - Implement validation for required fields (server, username, password, gateway_id)
    - _Requirements: 2.1, 2.2, 2.4, 2.5_
  
  - [x] 2.3 Implement default configuration file creation
    - Implement create_default_config to generate template YAML file
    - Use platform-appropriate config directory (~/.config on Linux/macOS, %APPDATA% on Windows)
    - Set file permissions to 0600 on Unix-like systems for security
    - _Requirements: 2.3_
  
  - [x] 2.4 Implement CLI argument override merging
    - Implement merge_with_cli_args to apply command-line overrides
    - Ensure CLI arguments take precedence over config file values
    - Handle missing parameters with clear error messages
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Implement protobuf message construction module
  - [x] 3.1 Create node ID parsing utilities
    - Implement parse_node_id to convert "!12345678" hex format to integer
    - Handle "^all" broadcast address (0xFFFFFFFF = 4294967295)
    - Add validation for node ID format
    - _Requirements: 7.4, 7.5_
  
  - [x] 3.2 Implement packet ID generation
    - Create generate_packet_id function for unique packet identifiers
    - Use timestamp-based or random generation for uniqueness
    - _Requirements: 5.4_
  
  - [x] 3.3 Implement protobuf message construction
    - Import meshtastic protobuf modules (mesh_pb2, mqtt_pb2, portnums_pb2)
    - Implement build_protobuf_message to create ServiceEnvelope with MeshPacket and Data
    - Set TEXT_MESSAGE_APP portnum for text messages
    - Encode message text as UTF-8 bytes in Data payload
    - Configure packet with from, to, id, channel, hop_limit, want_ack fields
    - Serialize protobuf to binary format
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3_
  
  - [x] 3.4 Implement MQTT topic construction
    - Create build_topic function following pattern msh/[region]/2/e/[channel]/[gateway_id]
    - _Requirements: 1.3_
  
  - [x] 3.5 Write unit tests for message module
    - Test node ID parsing for hex format and broadcast
    - Test packet ID generation uniqueness
    - Test protobuf message structure and serialization
    - Test topic string generation
    - Test handling of special characters in text
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 4. Implement MQTT client module
  - [x] 4.1 Create MeshtasticMQTTClient class with connection management
    - Implement __init__ with server, port, username, password parameters
    - Implement connect method with paho-mqtt client setup
    - Add _on_connect callback with connection result code handling
    - Implement connection timeout and error handling
    - _Requirements: 1.4_
  
  - [x] 4.2 Implement binary message publishing
    - Implement publish method to send binary protobuf payload
    - Use QoS 1 for reliable delivery
    - Add _on_publish callback for confirmation
    - Handle publish errors with descriptive messages
    - _Requirements: 1.3_
  
  - [x] 4.3 Implement disconnect and cleanup
    - Implement disconnect method to cleanly close MQTT connection
    - Stop network loop and release resources
    - _Requirements: 1.4_
  
  - [x] 4.4 Write unit tests for MQTT client
    - Test connection establishment with mock broker
    - Test binary message publishing
    - Test error handling for connection failures
    - Test clean disconnect
    - _Requirements: 1.3, 1.4_

- [x] 5. Implement command-line interface module
  - [x] 5.1 Create argument parser with all CLI options
    - Use argparse to define --message, --server, --port, --username, --password arguments
    - Add --gateway-id, --to-id, --channel, --region arguments
    - Add --want-ack flag and --hop-limit integer argument
    - Add --config, --verbose, --help arguments
    - Provide descriptions and examples in help text
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 5.2 Implement input validation
    - Create validate_inputs function to check required parameters
    - Validate message text is not empty
    - Validate hop_limit is within valid range
    - Display clear error messages for missing or invalid inputs
    - _Requirements: 3.5, 4.5_
  
  - [x] 5.3 Implement main orchestration flow
    - Create main function as entry point
    - Load configuration from file or create default
    - Parse command-line arguments
    - Merge config with CLI overrides
    - Validate inputs
    - Construct protobuf message
    - Connect to MQTT broker
    - Publish message
    - Display confirmation and exit with code 0 on success
    - Handle errors with appropriate exit codes (1-4, 99)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 5.4 Implement logging configuration
    - Set up logging with INFO level by default
    - Enable DEBUG level when --verbose flag is used
    - Log to stdout for success messages, stderr for errors
    - In verbose mode, log protobuf message hex dump
    - _Requirements: 1.3, 1.4_
  
  - [x] 5.5 Write integration tests for CLI
    - Test end-to-end flow with test MQTT broker
    - Test config file and CLI override combinations
    - Test error scenarios (missing config, bad credentials)
    - Verify protobuf message structure
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 6. Create documentation and examples
  - [x] 6.1 Write comprehensive README.md
    - Document installation instructions (from source and pip)
    - Provide configuration file format and location
    - Include usage examples for common scenarios
    - Document all command-line arguments
    - Add troubleshooting section
    - Explain differences from JSON implementation
    - Include links to Meshtastic documentation
    - _Requirements: 8.3_
  
  - [x] 6.2 Add inline code documentation
    - Add docstrings to all classes and functions
    - Document protobuf message structure
    - Add comments explaining protocol-specific logic
    - _Requirements: 8.3_

- [x] 7. Verify end-to-end functionality
  - [x] 7.1 Test with actual Meshtastic MQTT broker
    - Send test messages to mqtt.meshtastic.org
    - Verify messages appear on Meshtastic devices
    - Test broadcast and direct messaging
    - Test acknowledgment requests
    - _Requirements: 1.1, 1.2, 1.3, 5.1, 5.2, 5.3, 5.4, 5.5, 7.1, 7.2, 7.3_
  
  - [x] 7.2 Validate protobuf compatibility
    - Verify protobuf messages match Meshtastic specification
    - Test with different meshtastic package versions
    - Confirm compatibility with current Meshtastic firmware
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
