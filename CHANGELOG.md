# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-11-16

### Added
- Initial release of meshtastic-mqtt-protobuf CLI tool
- Licensed under GNU General Public License v3.0 or later (GPL-3.0-or-later)
- Command-line interface for sending protobuf-encoded messages to Meshtastic MQTT servers
- Support for broadcast and direct messaging
- Acknowledgment request functionality
- Configurable hop limit for message propagation
- YAML configuration file support with CLI argument overrides
- Comprehensive error handling with specific exit codes
- Verbose logging mode for debugging
- Full protobuf compatibility with Meshtastic specification
- End-to-end tests with actual MQTT broker
- Protobuf compatibility validation tests
- Complete documentation in README.md

### Features
- Connect to any Meshtastic MQTT broker
- Send text messages using native protobuf format
- Configure via YAML file or command-line arguments
- Support for multiple regions and channels
- Automatic packet ID generation
- UTF-8 text encoding with Unicode support
- QoS 1 message delivery for reliability

### Dependencies
- meshtastic>=2.2.0
- paho-mqtt>=1.6.1
- PyYAML>=6.0

## [Unreleased]

### Planned
- Support for additional message types (position, telemetry)
- Message subscription and listening capabilities
- Interactive mode for continuous messaging
- Message history and logging
- Configuration validation command
- Shell completion support

[1.0.0]: https://github.com/yourusername/meshtastic-mqtt-protobuf/releases/tag/v1.0.0
