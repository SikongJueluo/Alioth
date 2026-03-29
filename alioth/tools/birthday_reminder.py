from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.utils.session_waiter import (
    SessionController,
    session_waiter,
)
from alioth.utils.database import add_birthday_reminder as db_add_reminder
from alioth.utils.initialize import initialize

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
    user_input = event.message_str.strip()

    if user_input == "退出":
        await event.send(event.plain_result("已退出生日提醒设置~"))
        controller.stop()
        return

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

    if _reminder_state["message_content"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供发送消息的内容："))
        else:
            _reminder_state["message_content"] = user_input

            try:
                row_id = await db_add_reminder(
                    remindee_id=_reminder_state["remindee_id"],  # type: ignore[arg-type]
                    group_id=_reminder_state["group_id"],  # type: ignore[arg-type]
                    send_time=_reminder_state["send_time"],  # type: ignore[arg-type]
                    message_content=_reminder_state["message_content"],
                )
            except Exception:
                logger.exception("保存生日提醒到数据库失败")
                await event.send(event.plain_result("保存失败，请稍后重试。"))
                _reset_state()
                controller.stop()
                return

            logger.info(
                "生日提醒已保存: remindee=%s group=%s time=%s (row_id=%d)",
                _reminder_state["remindee_id"],
                _reminder_state["group_id"],
                _reminder_state["send_time"],
                row_id,
            )

            confirm_msg = (
                f"生日提醒已设置完成！\n"
                f"被提醒人ID: {_reminder_state['remindee_id']}\n"
                f"群聊ID: {_reminder_state['group_id']}\n"
                f"发送时间: {_reminder_state['send_time']}\n"
                f"消息内容: {_reminder_state['message_content']}"
            )
            await event.send(event.plain_result(confirm_msg))

            _reset_state()
            controller.stop()


def _reset_state():
    _reminder_state["remindee_id"] = None
    _reminder_state["group_id"] = None
    _reminder_state["send_time"] = None
    _reminder_state["message_content"] = None
