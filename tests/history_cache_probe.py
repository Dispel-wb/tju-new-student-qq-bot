# -*- coding: utf-8 -*-
import asyncio
import os
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR if (SCRIPT_DIR / "bot.py").exists() else SCRIPT_DIR.parent
SOURCE_DIR = PROJECT_DIR / "src" if (PROJECT_DIR / "src" / "bot.py").exists() else PROJECT_DIR
sys.path.insert(0, str(SOURCE_DIR))

from bot import Bot


async def main():
    cache_path = os.environ.get("BOT_HISTORY_PROBE_CACHE")
    if not cache_path:
        raise SystemExit("缺少 BOT_HISTORY_PROBE_CACHE")
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise SystemExit("缺少 DEEPSEEK_API_KEY")

    bot = Bot(SOURCE_DIR / "bot.md", cache_path=cache_path)
    conversation_id = "private:2450036920"
    cases = (
        (
            "你知道我为什么昨晚熬那么晚吗？",
            ("没说", "没有说", "没讲", "没有讲", "没写", "没有写", "无法确定", "不能确定"),
        ),
        (
            "你是不会看我和你的聊天记录吗？",
            ("能看", "看得到", "有记录", "可以看", "会看"),
        ),
    )
    failures = []
    for question, expected_any in cases:
        decision = await bot.llm_decide(conversation_id, question, "测试员", mentioned=True)
        answer = str((decision or {}).get("content") or "")
        print(f"\n问：{question}\n答：{answer}")
        if not answer or bot.response_is_bad(question, answer):
            failures.append((question, "回答未通过质量检查", answer))
        elif not any(marker in answer for marker in expected_any):
            failures.append((question, f"未命中历史证据表达 {expected_any}", answer))
    if failures:
        print("\n历史缓存真实 API 测试失败：")
        for question, reason, answer in failures:
            print(f"- {question}: {reason}: {answer}")
        raise SystemExit(1)
    print("\n历史缓存真实 API 测试通过。")


if __name__ == "__main__":
    asyncio.run(main())
