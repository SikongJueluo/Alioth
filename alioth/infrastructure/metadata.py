from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class PluginMetadata:
    repo: str
    name: str
    author: str
    version: str
    description: str
    displayname: str
    astrbot_version: str


def _plugin_root_path() -> Path:
    return Path(__file__).resolve().parents[2]


def initialize_plugin_metadata() -> PluginMetadata:
    metadata_filepath = _plugin_root_path() / "metadata.yaml"
    if not metadata_filepath.exists():
        raise FileNotFoundError(f"metadata.yaml not found at {metadata_filepath}")

    with open(metadata_filepath, "r") as f:
        metadata = yaml.load(f, yaml.SafeLoader)

        plugin_metadata = PluginMetadata(
            repo=metadata["repo"],
            name=metadata["name"],
            author=metadata["author"],
            version=metadata["version"],
            description=metadata["desc"],
            displayname=metadata["display_name"],
            astrbot_version=metadata["astrbot_version"],
        )
        return plugin_metadata


plugin_metadata: PluginMetadata = initialize_plugin_metadata()
