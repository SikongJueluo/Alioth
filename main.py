from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from alioth.tools import add_birthday_reminder
from alioth.utils.initialize import initialize, run_initializations_async


@initialize(priority=1)
async def load_configs():
    """Load configuration files."""
    logger.info("Loading configurations...")


@initialize()
def register_commands():
    """Register custom commands."""
    logger.info("Commands registered")


@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        await run_initializations_async()

    @filter.command("BirthdayReminder")
    async def birthday_reminder(self, event: AstrMessageEvent):
        """生日提醒"""
        try:
            await add_birthday_reminder(event)
        except TimeoutError:
            yield event.plain_result("设置超时，已退出生日提醒设置~")
        except Exception as e:
            logger.exception("生日提醒设置异常")
            yield event.plain_result(f"发生错误: {e}")
        finally:
            event.stop_event()

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        pass
