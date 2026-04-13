import sys
from pathlib import Path
from typing import cast

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

PLUGIN_ROOT = Path(__file__).resolve().parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from alioth.birthday_reminder import (
    handle_birthday_reminder_command,
    register_llm_tools,
)

from alioth.infrastructure import (
    InitializationContext,
    initialize_plugin_context,
    run_initializations_async,
    run_terminations_async,
)


class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        register_llm_tools(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        self.context = cast(Context, self.context)
        initialize_plugin_context(self.context, self.config)

        init_ctx = InitializationContext(star_context=self.context, config=self.config)
        await run_initializations_async(init_ctx)

    @filter.command("BirthdayReminder")
    async def birthday_reminder(self, event: AstrMessageEvent):
        """生日提醒"""
        try:
            await handle_birthday_reminder_command(event)
        except TimeoutError:
            yield event.plain_result("设置超时，已退出生日提醒设置~")
        except Exception as e:
            logger.exception("生日提醒设置异常")
            yield event.plain_result(f"发生错误: {e}")
        finally:
            event.stop_event()

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        await run_terminations_async()
