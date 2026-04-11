from pathlib import Path

from astrbot.core.utils.astrbot_path import get_astrbot_plugin_data_path

from .metadata import plugin_metadata


def get_plugin_data_path() -> Path:
    return Path(get_astrbot_plugin_data_path()) / plugin_metadata.name


def get_database_file_path() -> Path:
    return get_plugin_data_path() / "database.db"
