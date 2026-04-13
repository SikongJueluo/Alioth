import sys
from pathlib import Path
from typing import cast

# pyright: reportMissingImports=false
from astrbot.api import AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

PLUGIN_ROOT = Path(__file__).resolve().parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from alioth.birthday_reminder import (
    handle_birthday_reminder_create_command,
    handle_birthday_reminder_delete_command,
    handle_birthday_reminder_list_command,
)
from alioth.infrastructure import (
    InitializationContext,
    initialize_plugin_context,
    parse_plugin_config,
    register_all_llm_tools,
    run_initializations_async,
    run_terminations_async,
)
from alioth.infrastructure.config import PluginConfig


class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.context = cast(Context, self.context)
        self.config: PluginConfig = parse_plugin_config(config)

        initialize_plugin_context(self.context, self.config)
        register_all_llm_tools(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        self.context = cast(Context, self.context)
        init_ctx = InitializationContext(star_context=self.context, config=self.config)
        await run_initializations_async(init_ctx)

    @filter.command_group("birthday", alias={"bday"})
    def birthday(self) -> None:
        """生日提醒管理"""

    @birthday.command("add")
    async def birthday_add(self, event: AstrMessageEvent) -> None:
        await handle_birthday_reminder_create_command(event)

    @birthday.command("list")
    async def birthday_list(self, event: AstrMessageEvent) -> None:
        await handle_birthday_reminder_list_command(event)

    @birthday.command("delete")
    async def birthday_delete(
        self,
        event: AstrMessageEvent,
        birthday_id: int,
    ) -> None:
        await handle_birthday_reminder_delete_command(event, birthday_id)

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        await run_terminations_async()
