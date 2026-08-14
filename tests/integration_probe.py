# -*- coding: utf-8 -*-
import argparse
import asyncio
import sys
import tempfile
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from bot import Bot


def check_wiki(bot):
    failures = 0
    for question in ("天津大学校史馆开放时间", "学校宿舍床铺大小"):
        result = bot.wiki_search(question)
        passed = bool(result and "来源：https://wiki.tjubot.cn/" in result)
        print(f"[{'PASS' if passed else 'FAIL'}] 北洋维基：{question}")
        print((result or "无结果")[:700])
        failures += 0 if passed else 1
    return failures


def check_model(bot):
    config = dict(bot.llm_cfg())
    for key in ("api_key", "base_url", "model", "fallback_model"):
        config[key] = bot.llm_value(key, "")
    result = bot.llm_chat(
        config,
        "你是简洁自然的中文聊天助手。",
        "只回答这句话：我支持猜数字、石头剪刀布和猜谜语。",
        80,
    )
    passed = bool(result and "猜数字" in result)
    print(f"[{'PASS' if passed else 'FAIL'}] DeepSeek 主备模型链路")
    print(result or "无结果")
    return 0 if passed else 1


async def check_conversation(bot):
    failures = 0
    cases = (
        ("你好，你看见我了吗", False),
        ("你刚才答非所问，真笨", False),
        ("天津大学校史馆今天开放吗", True),
    )
    for question, needs_source in cases:
        bot.add_history("private:2450036920", "测试员", question)
        decision = await bot.llm_decide("private:2450036920", question, "测试员", mentioned=True)
        answer = str((decision or {}).get("content") or "")
        passed = bool(answer and "正常返回" not in answer)
        if needs_source:
            passed = passed and "https://wiki.tjubot.cn/" in answer
        print(f"[{'PASS' if passed else 'FAIL'}] 完整对话：{question}")
        print(answer or "无结果")
        failures += 0 if passed else 1
    return failures


def main():
    parser = argparse.ArgumentParser(description="真实外部依赖探测，不启动 QQ 机器人")
    parser.add_argument("--wiki", action="store_true", help="检查北洋维基")
    parser.add_argument("--model", action="store_true", help="检查 DeepSeek")
    parser.add_argument("--conversation", action="store_true", help="检查完整对话链路")
    args = parser.parse_args()
    if not args.wiki and not args.model and not args.conversation:
        args.wiki = args.model = True
    with tempfile.TemporaryDirectory() as cache_dir:
        bot = Bot(PROJECT_DIR / "bot.md", cache_path=Path(cache_dir) / "probe-cache.sqlite3")
        failures = 0
        if args.wiki:
            failures += check_wiki(bot)
        if args.model:
            failures += check_model(bot)
        if args.conversation:
            failures += asyncio.run(check_conversation(bot))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
