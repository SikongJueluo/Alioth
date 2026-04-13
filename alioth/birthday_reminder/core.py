from __future__ import annotations

# pyright: reportMissingImports=false
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from astrbot.api import logger

from alioth.utils import (
    get_plugin_context_unsafe,
    initialize,
    terminate,
)

from .common import run_daily_check

_scheduler: Optional[AsyncIOScheduler] = None


@initialize(priority=3)
async def _initialize_birthday_reminder():
    global _scheduler
    ctx = get_plugin_context_unsafe()
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
async def _terminate_birthday_reminder():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None
