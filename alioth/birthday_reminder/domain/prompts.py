INITIAL_PROMPT = "请提供寿星的名字："
TARGET_SESSION_PROMPT = "请提供发送提醒的会话标识（unified_msg_origin，例如 aiocqhttp:GroupMessage:123456）："


def build_creation_confirmation(
    name: str,
    target_session: str,
    month: int,
    day: int,
    message: str,
) -> str:
    return (
        "生日提醒已设置完成！\n"
        f"名字: {name}\n"
        f"发送至: {target_session}\n"
        f"生日: {month}月{day}日\n"
        f"祝福: {message}"
    )
