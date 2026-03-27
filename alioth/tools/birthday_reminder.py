import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.utils.session_waiter import (
    SessionController,
    session_waiter,
)
from utils.initialize import initialize


@initialize()
async def _initialize_birthday_reminder():
    logger.info("生日提醒初始化成功...")


@session_waiter(
    timeout=60, record_history_chains=False
)  # 注册一个会话控制器，设置超时时间为 60 秒，不记录历史消息链
async def add_birthday_reminder(controller: SessionController, event: AstrMessageEvent):
    idiom = event.message_str  # 用户发来的成语，假设是 "一马当先"

    if idiom == "退出":  # 假设用户想主动退出成语接龙，输入了 "退出"
        await event.send(event.plain_result("已退出成语接龙~"))
        controller.stop()  # 停止会话控制器，会立即结束。
        return

    if len(idiom) != 4:  # 假设用户输入的不是4字成语
        await event.send(
            event.plain_result("成语必须是四个字的呢~")
        )  # 发送回复，不能使用 yield
        return
        # 退出当前方法，不执行后续逻辑，但此会话并未中断，后续的用户输入仍然会进入当前会话

    # ...
    message_result = event.make_result()
    message_result.chain = [
        Comp.Plain("先见之明")
    ]  # import astrbot.api.message_components as Comp
    await event.send(message_result)  # 发送回复，不能使用 yield

    controller.keep(
        timeout=60, reset_timeout=True
    )  # 重置超时时间为 60s，如果不重置，则会继续之前的超时时间计时。

    # controller.stop() # 停止会话控制器，会立即结束。
    # 如果记录了历史消息链，可以通过 controller.get_history_chains() 获取历史消息链
