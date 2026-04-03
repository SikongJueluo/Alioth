from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from astrbot.api.star import Star
from astrbot.core.utils.astrbot_path import get_astrbot_data_path
from returns.maybe import Maybe


@dataclass
class PluginContext:
    star_context: Star._ContextLike
    plugin_repo: str
    plugin_name: str
    plugin_author: str
    plugin_version: str
    plugin_description: str
    plugin_displayname: str
    plugin_astrbot_version: str


_plugin_context: Optional[PluginContext] = None


def initialize_utils_common(context: Star._ContextLike):
    metadata_filepath = (
        Path(get_astrbot_data_path())
        / "plugin_data"
        / "astrbot_plugin_alioth"
        / "metadata.yaml"
    )
    if not metadata_filepath.exists():
        raise FileNotFoundError(f"metadata.yaml not found at {metadata_filepath}")

    with open(metadata_filepath, "r") as f:
        metadata = yaml.load(f, yaml.SafeLoader)

        global _plugin_context
        _plugin_context = PluginContext(
            star_context=context,
            plugin_repo=metadata["repo"],
            plugin_name=metadata["name"],
            plugin_author=metadata["author"],
            plugin_version=metadata["version"],
            plugin_description=metadata["description"],
            plugin_displayname=metadata["displayname"],
            plugin_astrbot_version=metadata["astrbot_version"],
        )


def get_plugin_context() -> Maybe[PluginContext]:
    """
    Get the plugin context.
    """
    return Maybe.from_optional(_plugin_context)


def get_plugin_context_unsafe() -> PluginContext:
    """
    Usually use in initialize function
    Raise ValueError when common utils are not initialized
    """
    if _plugin_context is None:
        raise ValueError("plugin context not initialized")
    return _plugin_context
