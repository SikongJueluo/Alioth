import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from alioth.utils.initialize import initialize


class AliothConfig(BaseModel):
    plugin_name: str = "alioth"

    @property
    def plugin_data_path(self) -> Path:
        from astrbot.core.utils.astrbot_path import get_astrbot_data_path

        return Path(get_astrbot_data_path()) / "plugin_data" / self.plugin_name

    @property
    def config_file_path(self) -> Path:
        return self.plugin_data_path / "config.json"

    @property
    def database_file_path(self) -> Path:
        return self.plugin_data_path / "database.db"


config: AliothConfig = AliothConfig()


@initialize(priority=1)
async def init_config():
    global config

    config_file = config.config_file_path

    if not config_file.exists():
        with open(config_file, "rb") as f:
            data: dict[str, Any] = json.load(f)
        config = AliothConfig.model_validate_json(data)
    else:
        with open(config_file, "w") as f:
            f.write(config.model_dump_json(indent=2))

    config.plugin_data_path.mkdir(parents=True, exist_ok=True)
