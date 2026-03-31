import inspect
from typing import Any, Union, cast

from astrbot.api.event import MessageChain
from astrbot.core.platform.message_session import MessageSession
from returns.result import Failure, Result, Success

from alioth.utils import global_plugin_context


async def send_message(
    session: Union[MessageSession, str], msg: MessageChain
) -> Result[bool, str]:
    context = cast(Any, global_plugin_context)

    if not inspect.isfunction(context.send_message):
        return Failure("Context send_message is not a function")

    await context.send_message(str(session), msg)
    return Success(True)
