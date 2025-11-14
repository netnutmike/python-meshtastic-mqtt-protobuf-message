# Requirements Document

## Introduction

This document specifies the requirements for a Python command-line tool that enables users to send protobuf-encoded messages to a Meshtastic MQTT server. The tool provides configuration management through YAML files and command-line argument overrides, following the native Meshtastic MQTT protocol using Protocol Buffers as documented at https://meshtastic.org/docs/software/integrations/mqtt/. Unlike JSON-based implementations that require special gateway configuration, this tool uses the standard protobuf format that all Meshtastic devices natively support.

## Glossary

- **CLI Tool**: The command-line interface application being developed
- **MQTT Server**: A message broker that implements the MQTT protocol for publish/subscribe messaging
- **Meshtastic**: A mesh networking platform that supports MQTT integration
- **YAML Config File**: A YAML-formatted configuration file containing default connection and message parameters
- **Protobuf Message**: A binary message payload encoded using Protocol Buffers according to the Meshtastic protocol specification
- **ServiceEnvelope**: The outer protobuf message wrapper used by Meshtastic for MQTT transport
- **Command-Line Override**: A parameter provided via command-line arguments that supersedes the corresponding YAML config value
- **Meshtastic Protobufs**: The Protocol Buffer definitions from the official Meshtastic project

## Requirements

### Requirement 1

**User Story:** As a user, I want to send a message to a Meshtastic MQTT server using the native protobuf format, so that my messages work with any standard Meshtastic gateway without requiring special JSON configuration.

#### Acceptance Criteria

1. WHEN the user executes the CLI Tool with message content via command-line argument, THE CLI Tool SHALL construct a properly formatted protobuf message according to the Meshtastic protocol specification
2. THE CLI Tool SHALL encode messages using the ServiceEnvelope protobuf format as defined in the official Meshtastic protobufs
3. THE CLI Tool SHALL publish protobuf messages to the MQTT topic pattern `msh/[region]/2/e/[channel]/[gateway_id]`
4. WHEN the message is successfully published, THE CLI Tool SHALL display a confirmation message and terminate with exit code zero
5. IF the MQTT connection fails, THEN THE CLI Tool SHALL display an error message with connection details and terminate with a non-zero exit code

### Requirement 2

**User Story:** As a user, I want to store my MQTT connection settings in a YAML configuration file, so that I don't have to specify them every time I run the tool.

#### Acceptance Criteria

1. THE CLI Tool SHALL read configuration parameters from a YAML Config File located in a standard configuration directory
2. THE YAML Config File SHALL contain fields for MQTT Server address, username, password, gateway identifier, channel identifier, and region
3. WHEN the YAML Config File does not exist, THE CLI Tool SHALL create a default configuration file with placeholder values
4. WHEN the YAML Config File contains invalid YAML syntax, THE CLI Tool SHALL display an error message indicating the syntax error location and terminate with a non-zero exit code
5. THE CLI Tool SHALL validate that required configuration fields (MQTT Server address, username, password, gateway identifier) are present in the YAML Config File

### Requirement 3

**User Story:** As a user, I want to override configuration file settings with command-line arguments, so that I can use different settings for specific invocations without modifying the config file.

#### Acceptance Criteria

1. WHEN the user provides an MQTT Server address via command-line argument, THE CLI Tool SHALL use that address instead of the YAML Config File value
2. WHEN the user provides username or password via command-line argument, THE CLI Tool SHALL use those credentials instead of the YAML Config File values
3. WHEN the user provides gateway, channel, or region identifiers via command-line argument, THE CLI Tool SHALL use those values instead of the YAML Config File values
4. THE CLI Tool SHALL apply command-line overrides after loading the YAML Config File values
5. WHEN both YAML Config File and command-line arguments are absent for a required parameter, THE CLI Tool SHALL display an error message listing the missing parameters and terminate with a non-zero exit code

### Requirement 4

**User Story:** As a user, I want clear help documentation for the command-line tool, so that I can understand how to use it without referring to external documentation.

#### Acceptance Criteria

1. WHEN the user executes the CLI Tool with a help flag, THE CLI Tool SHALL display usage information including all available command-line arguments
2. THE CLI Tool SHALL display descriptions for each command-line argument in the help output
3. THE CLI Tool SHALL display the location of the YAML Config File in the help output
4. THE CLI Tool SHALL display example usage commands in the help output
5. WHEN the user executes the CLI Tool without required arguments, THE CLI Tool SHALL display a brief usage message and terminate with a non-zero exit code

### Requirement 5

**User Story:** As a user, I want the tool to use the official Meshtastic protobuf definitions, so that my messages are guaranteed to be compatible with all Meshtastic devices and firmware versions.

#### Acceptance Criteria

1. THE CLI Tool SHALL use the official Meshtastic protobuf definitions from the meshtastic Python package
2. THE CLI Tool SHALL construct ServiceEnvelope messages containing properly formatted Data protobuf payloads
3. THE CLI Tool SHALL encode text messages as TEXT_MESSAGE_APP portnum within the Data payload
4. THE CLI Tool SHALL set appropriate packet identifiers, hop limits, and want_ack flags according to Meshtastic protocol standards
5. THE CLI Tool SHALL serialize protobuf messages to binary format before publishing to MQTT

### Requirement 6

**User Story:** As a user, I want to specify message delivery options like acknowledgment requests and hop limits, so that I can control how my messages are transmitted through the mesh network.

#### Acceptance Criteria

1. THE CLI Tool SHALL support a command-line argument to request message acknowledgment (want_ack flag)
2. THE CLI Tool SHALL support a command-line argument to set the hop limit for message propagation
3. WHEN acknowledgment is not explicitly requested, THE CLI Tool SHALL default to want_ack=False for efficiency
4. WHEN hop limit is not specified, THE CLI Tool SHALL use the Meshtastic default hop limit value
5. THE CLI Tool SHALL include these options in the protobuf message packet configuration

### Requirement 7

**User Story:** As a user, I want to send messages to specific nodes or broadcast to all nodes, so that I can control message recipients.

#### Acceptance Criteria

1. THE CLI Tool SHALL support specifying a destination node ID via command-line argument or configuration file
2. WHEN destination is set to "^all" or not specified, THE CLI Tool SHALL encode the message as a broadcast to all nodes
3. WHEN destination is a specific node ID, THE CLI Tool SHALL encode the message for direct delivery to that node
4. THE CLI Tool SHALL validate node ID format before encoding into the protobuf message
5. THE CLI Tool SHALL convert node ID strings (e.g., "!12345678") to the appropriate integer format for protobuf encoding

### Requirement 8

**User Story:** As a developer, I want the project to have proper repository setup with version control and dependency management, so that the tool can be easily maintained and distributed.

#### Acceptance Criteria

1. THE project SHALL include a .gitignore file that excludes Python cache files, virtual environments, and sensitive configuration files
2. THE project SHALL include a requirements.txt file listing all Python package dependencies including meshtastic and paho-mqtt with version specifications
3. THE project SHALL include a README.md file with installation instructions, usage examples, and configuration documentation
4. THE project SHALL use a standard Python project structure with appropriate directories for source code and configuration
5. THE project SHALL include a setup.py or pyproject.toml file for package installation and distribution
