from __future__ import annotations

# pyright: reportMissingImports=false
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from astrbot.api import logger

from alioth.birthday_reminder.application.reminder_service import run_daily_check
from alioth.infrastructure import InitializationContext, initialize, terminate

_scheduler: Optional[AsyncIOScheduler] = None


@initialize(priority=3)
async def initialize_birthday_reminder(ctx: InitializationContext) -> None:
    global _scheduler
    hour = ctx.config.get("check_hour", 8)
    minute = ctx.config.get("check_minute", 0)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_daily_check,
        CronTrigger(hour=hour, minute=minute),
        id="daily_birthday_check",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("生日提醒初始化成功...")


@terminate(priority=3)
async def terminate_birthday_reminder() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None
