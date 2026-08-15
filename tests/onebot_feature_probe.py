# -*- coding: utf-8 -*-
import asyncio
import json
import sys
import tempfile
from pathlib import Path

import websockets


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR if (SCRIPT_DIR / "bot.py").exists() else SCRIPT_DIR.parent
SOURCE_DIR = PROJECT_DIR / "src" if (PROJECT_DIR / "src" / "bot.py").exists() else PROJECT_DIR
sys.path.insert(0, str(SOURCE_DIR))

from bot import Bot


async def pump(bot, websocket):
    async for payload in websocket:
        event = json.loads(payload)
        echo = event.get("echo")
        future = bot.api_waiters.get(str(echo)) if echo is not None else None
        if future and not future.done():
            future.set_result(event)


async def main():
    with tempfile.TemporaryDirectory() as cache_dir:
        bot = Bot(SOURCE_DIR / "bot.md", cache_path=Path(cache_dir) / "probe.sqlite3")
        async with websockets.connect(bot.ws_url, ping_interval=20, ping_timeout=20) as websocket:
            receiver = asyncio.create_task(pump(bot, websocket))
            try:
                group = await bot.call_onebot(
                    websocket, "get_group_info", {"group_id": 1057604880, "no_cache": True}
                )
                if not isinstance(group, dict) or int(group.get("member_count") or 0) <= 0:
                    raise RuntimeError(f"群信息异常：{group}")
                bot.save_group_stats(
                    1057604880, group.get("member_count"), group.get("max_member_count"),
                    group.get("group_name"),
                )
                print(f"群人数：{group.get('member_count')} / {group.get('max_member_count')}")

                history = await bot.call_onebot(
                    websocket, "get_friend_msg_history", {"user_id": 2450036920, "count": 20}
                )
                messages = []
                if isinstance(history, dict):
                    messages = history.get("messages") or history.get("message") or []
                elif isinstance(history, list):
                    messages = history
                messages = [item for item in messages if isinstance(item, dict)]
                if not messages:
                    raise RuntimeError(f"私聊历史为空：{history}")
                latest = messages[-1]
                message_id = latest.get("message_id") or latest.get("id")
                if message_id is None:
                    raise RuntimeError("私聊历史缺少 message_id")
                fetched = await bot.call_onebot(websocket, "get_msg", {"message_id": message_id})
                if not isinstance(fetched, dict):
                    raise RuntimeError(f"get_msg 失败：{fetched}")
                recognized = bot.norm_text(fetched)
                if not recognized:
                    raise RuntimeError("消息识别结果为空")
                quoted, resolved_id, _ = await bot.quoted_context(websocket, {
                    "message": [{"type": "reply", "data": {"id": str(message_id)}}]
                })
                if not quoted or str(resolved_id) != str(message_id):
                    raise RuntimeError("引用解析失败")
                print(f"引用解析：{quoted[:120]}")
                print("OneBot 引用、历史与群人数真实探针通过。")
            finally:
                receiver.cancel()
                await asyncio.gather(receiver, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
