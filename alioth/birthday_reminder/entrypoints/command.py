# pyright: reportMissingImports=false

from collections.abc import Awaitable, Callable

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from alioth.birthday_reminder.application.reminder_service import (
    delete_birthday_reminder,
    list_birthday_reminders,
)
from alioth.birthday_reminder.application.session_flow import start_birthday_reminder
from alioth.birthday_reminder.domain.prompts import (
    build_birthday_delete_confirmation,
    build_birthday_list_message,
)


async def _run_birthday_command(
    event: AstrMessageEvent,
    handler: Callable[[], Awaitable[None]],
    *,
    operation_name: str,
    timeout_message: str = "操作超时，请稍后重试。",
) -> None:
    try:
        await handler()
    except TimeoutError:
        await event.send(event.plain_result(timeout_message))
    except ValueError as exc:
        await event.send(event.plain_result(str(exc)))
    except Exception:
        logger.exception("%s时发生异常", operation_name)
        await event.send(event.plain_result(f"{operation_name}失败，请稍后重试。"))
    finally:
        event.stop_event()


async def handle_birthday_reminder_create_command(event: AstrMessageEvent) -> None:
    await _run_birthday_command(
        event,
        lambda: start_birthday_reminder(event),
        operation_name="创建生日提醒",
        timeout_message="设置超时，已退出生日提醒设置~",
    )


async def handle_birthday_reminder_list_command(event: AstrMessageEvent) -> None:
    async def run() -> None:
        birthdays = await list_birthday_reminders()
        await event.send(event.plain_result(build_birthday_list_message(birthdays)))

    await _run_birthday_command(
        event,
        run,
        operation_name="查询生日提醒列表",
    )


async def handle_birthday_reminder_delete_command(
    event: AstrMessageEvent,
    birthday_id: int,
) -> None:
    async def run() -> None:
        birthday = await delete_birthday_reminder(birthday_id)
        await event.send(
            event.plain_result(build_birthday_delete_confirmation(birthday))
        )

    await _run_birthday_command(
        event,
        run,
        operation_name="删除生日提醒",
    )
