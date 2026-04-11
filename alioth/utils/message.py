from typing import Union

from astrbot.api.event import MessageChain
from astrbot.core.platform.message_session import MessageSession
from returns.maybe import Nothing
from returns.result import Failure, Result, Success

from .common import get_plugin_context


async def send_message(
    session: Union[MessageSession, str], msg: MessageChain
) -> Result[bool, str]:
    context = get_plugin_context()
    if context is Nothing:
        return Failure("No plugin context available")

    star_context = context.unwrap().star_context
    try:
        delivered = await star_context.send_message(session, msg)
    except ValueError as exc:
        return Failure(f"Invalid session: {exc}")
    except Exception as exc:
        return Failure(f"Send message failed: {exc}")

    if not delivered:
        return Failure(f"No platform found for session: {session}")

    return Success(True)
