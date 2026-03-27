import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.utils.session_waiter import (
    SessionController,
    session_waiter,
)
from utils.initialize import initialize

# 会话状态存储
_reminder_state = {
    "remindee_id": None,
    "group_id": None,
    "send_time": None,
    "message_content": None,
}


@initialize()
async def _initialize_birthday_reminder():
    logger.info("生日提醒初始化成功...")


@session_waiter(timeout=120, record_history_chains=False)
async def add_birthday_reminder(controller: SessionController, event: AstrMessageEvent):
    """
    添加生日提醒的步骤：
    1. 被提醒人的id
    2. 发送消息的群聊的id
    3. 发送消息的具体时间
    4. 发送消息的内容
    5. 随时输入"退出"终止流程
    """
    user_input = event.message_str.strip()

    # 退出控制词
    if user_input == "退出":
        await event.send(event.plain_result("已退出生日提醒设置~"))
        controller.stop()
        return

    # 步骤1: 收集被提醒人ID
    if _reminder_state["remindee_id"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供被提醒人的ID："))
        else:
            _reminder_state["remindee_id"] = user_input
            await event.send(
                event.plain_result(
                    f"已记录被提醒人ID: {user_input}\n请提供发送消息的群聊ID："
                )
            )
        controller.keep(timeout=120, reset_timeout=True)
        return

    # 步骤2: 收集群聊ID
    if _reminder_state["group_id"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供发送消息的群聊ID："))
        else:
            _reminder_state["group_id"] = user_input
            await event.send(
                event.plain_result(
                    f"已记录群聊ID: {user_input}\n请提供发送消息的具体时间（如 2024-05-01 09:00）："
                )
            )
        controller.keep(timeout=120, reset_timeout=True)
        return

    # 步骤3: 收集发送时间
    if _reminder_state["send_time"] is None:
        if not user_input:
            await event.send(
                event.plain_result("请提供发送消息的具体时间（如 2024-05-01 09:00）：")
            )
        else:
            _reminder_state["send_time"] = user_input
            await event.send(
                event.plain_result(
                    f"已记录发送时间: {user_input}\n请提供发送消息的内容："
                )
            )
        controller.keep(timeout=120, reset_timeout=True)
        return

    # 步骤4: 收集消息内容并完成设置
    if _reminder_state["message_content"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供发送消息的内容："))
        else:
            _reminder_state["message_content"] = user_input

            # 占位输出：打印收集到的所有信息
            logger.info("=" * 50)
            logger.info("【生日提醒占位实现】")
            logger.info(f"被提醒人ID: {_reminder_state['remindee_id']}")
            logger.info(f"群聊ID: {_reminder_state['group_id']}")
            logger.info(f"发送时间: {_reminder_state['send_time']}")
            logger.info(f"消息内容: {_reminder_state['message_content']}")
            logger.info("=" * 50)

            # 发送确认消息
            confirm_msg = (
                f"生日提醒已设置完成！\n"
                f"被提醒人ID: {_reminder_state['remindee_id']}\n"
                f"群聊ID: {_reminder_state['group_id']}\n"
                f"发送时间: {_reminder_state['send_time']}\n"
                f"消息内容: {_reminder_state['message_content']}\n\n"
                f"（当前为占位实现，具体定时发送功能待后续开发）"
            )
            await event.send(event.plain_result(confirm_msg))

            # 重置状态
            _reminder_state["remindee_id"] = None
            _reminder_state["group_id"] = None
            _reminder_state["send_time"] = None
            _reminder_state["message_content"] = None

            controller.stop()
