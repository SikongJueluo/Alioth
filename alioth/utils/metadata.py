from dataclasses import dataclass
from pathlib import Path

import yaml
from astrbot.core.utils.astrbot_path import get_astrbot_data_path


@dataclass
class PluginMetadata:
    repo: str
    name: str
    author: str
    version: str
    description: str
    displayname: str
    astrbot_version: str


def initialize_plugin_metadata() -> PluginMetadata:
    metadata_filepath = (
        Path(get_astrbot_data_path())
        / "plugins"
        / "astrbot_plugin_alioth"
        / "metadata.yaml"
    )
    if not metadata_filepath.exists():
        raise FileNotFoundError(f"metadata.yaml not found at {metadata_filepath}")

    with open(metadata_filepath, "r") as f:
        metadata = yaml.load(f, yaml.SafeLoader)

        plugin_metadata = PluginMetadata(
            repo=metadata["repo"],
            name=metadata["name"],
            author=metadata["author"],
            version=metadata["version"],
            description=metadata["description"],
            displayname=metadata["displayname"],
            astrbot_version=metadata["astrbot_version"],
        )
        return plugin_metadata


plugin_metadata: PluginMetadata = initialize_plugin_metadata()
