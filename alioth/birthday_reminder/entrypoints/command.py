from astrbot.api.event import AstrMessageEvent

from alioth.birthday_reminder.application.session_flow import start_birthday_reminder


async def handle_birthday_reminder_command(event: AstrMessageEvent) -> None:
    await start_birthday_reminder(event)
