import inspect
from typing import Any

from astrbot.api.event import MessageChain
from astrbot.core.platform.message_session import MessageSession
from returns.result import Failure, Result, Success


async def sendMessage(
    context: Any, session: MessageSession, msg: MessageChain
) -> Result[bool, str]:
    if not inspect.isfunction(context.send_message):
        return Failure("Context send_message is not a function")

    await context.send_message(str(session), msg)
    return Success(True)
