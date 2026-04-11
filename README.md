# Alioth

**玉衡** —— 北斗七星之一，位于斗柄与斗勺连接处，主掌平衡与秩序。

[![License](https://img.shields.io/github/license/SikongJueluo/Alioth)](LICENSE)
[![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D4.22.1-blue)](https://github.com/AstrBotDevs/AstrBot)

AstrBot 生日提醒插件。通过交互式对话设置生日记录，每日定时自动向指定会话发送祝福消息。

## 功能特性

- **交互式设置** — 通过多轮对话引导用户逐步输入寿星姓名、目标会话 unified_msg_origin、生日日期和祝福语
- **每日定时提醒** — 每天早上 8:00 自动检查并发送生日祝福（基于 APScheduler CronTrigger）
- **持久化存储** — 使用 SQLite 数据库保存所有生日记录，重启不丢失
- **闰年处理** — 正确处理 2 月 29 日生日：非闰年自动改为 2 月 28 日发送
- **去重机制** — 通过 `last_sent_date` 字段防止同一天重复发送
- **超时保护** — 设置过程中 120 秒无输入自动退出

## 安装

在 AstrBot 管理面板的插件市场中搜索 `alioth` 安装，或手动安装：

```bash
# 克隆到 AstrBot 插件目录
git clone https://github.com/SikongJueluo/Alioth.gitastrbot_plugin_alioth
```

### 要求

- AstrBot >= 4.22.1
- Python >= 3.13

## 使用方法

发送 `/BirthdayReminder` 命令，按照提示依次输入：

1. **寿星姓名** — 要提醒的生日对应的人名
2. **目标会话 unified_msg_origin** — 接收提醒消息的会话标识，格式如 `aiocqhttp:GroupMessage:123456`
3. **月份** — 生日月份（1–12）
4. **日期** — 生日日期（1–31）
5. **祝福语** — 生日当天发送的祝福内容

设置过程中随时可发送「退出」取消操作。

## 项目结构

```
alioth/
├── configs/
│   ├── __init__.py
│   └── config.py          # Pydantic 配置模型，管理插件数据路径
├── tools/
│   ├── __init__.py
│   └── birthday_reminder.py  # 核心逻辑：交互设置、每日检查、通知发送
└── utils/
    ├── __init__.py
    ├── common.py           # 全局插件上下文
    ├── database.py         # SQLite CRUD（aiosqlite）
    ├── initialize.py       # 初始化注册表
    ├── message.py          # 消息发送工具
    └── terminate.py        # 终止注册表
```

## 许可证

[AGPL-3.0](LICENSE)

## 相关链接

- [AstrBot](https://github.com/AstrBotDevs/AstrBot)
- [AstrBot 插件开发文档](https://docs.astrbot.app/dev/star/plugin-new.html)
- [AstrBot Plugin Development Docs](https://docs.astrbot.app/en/dev/star/plugin-new.html)
