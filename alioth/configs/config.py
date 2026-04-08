import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from alioth.utils.initialize import initialize


class AliothConfig(BaseModel):
    @property
    def plugin_data_path(self) -> Path:
        from astrbot.core.utils.astrbot_path import get_astrbot_plugin_data_path

        from alioth.utils import plugin_metadata

        return Path(get_astrbot_plugin_data_path()) / plugin_metadata.name

    @property
    def config_file_path(self) -> Path:
        return self.plugin_data_path / "config.json"

    @property
    def database_file_path(self) -> Path:
        return self.plugin_data_path / "database.db"


config: AliothConfig = AliothConfig()


def _update_config(target: AliothConfig, source: AliothConfig) -> None:
    for field_name in type(source).model_fields:
        setattr(target, field_name, getattr(source, field_name))


@initialize(priority=1)
async def init_config():
    plugin_data_path = config.plugin_data_path
    plugin_data_path.mkdir(parents=True, exist_ok=True)
    config_file = config.config_file_path

    if config_file.exists():
        with open(config_file, "rb") as f:
            data: dict[str, Any] = json.load(f)
        loaded_config = AliothConfig.model_validate(data)
        _update_config(config, loaded_config)
    else:
        with open(config_file, "w") as f:
            f.write(config.model_dump_json(indent=2))
