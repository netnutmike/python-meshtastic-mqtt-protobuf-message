"""Setup configuration for meshtastic-mqtt-protobuf package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = ""
readme_path = this_directory / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

# Read requirements
requirements = []
requirements_path = this_directory / "requirements.txt"
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding="utf-8").splitlines()

setup(
    name="meshtastic-mqtt-protobuf",
    version="0.1.0",
    author="Meshtastic MQTT Protobuf Contributors",
    description="A CLI tool for sending protobuf-encoded messages to Meshtastic MQTT servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/meshtastic-mqtt-protobuf",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Communications",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "meshtastic-send-pb=meshtastic_mqtt_protobuf.cli:main",
        ],
    },
)
