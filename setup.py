"""Setup configuration for meshtastic-mqtt-protobuf package."""

from setuptools import setup, find_packages
from pathlib import Path
import re

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

# Read version from __version__.py
version = "0.1.0"  # fallback
version_file = this_directory / "src" / "meshtastic_mqtt_protobuf" / "__version__.py"
if version_file.exists():
    version_content = version_file.read_text(encoding="utf-8")
    version_match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', version_content, re.MULTILINE)
    if version_match:
        version = version_match.group(1)

setup(
    name="meshtastic-mqtt-protobuf",
    version=version,
    author="Meshtastic MQTT Protobuf Contributors",
    description="A CLI tool for sending protobuf-encoded messages to Meshtastic MQTT servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/meshtastic-mqtt-protobuf",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    license="GPL-3.0-or-later",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications",
        "Topic :: Communications :: Ham Radio",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "meshtastic-send-pb=meshtastic_mqtt_protobuf.cli:main",
        ],
    },
)
