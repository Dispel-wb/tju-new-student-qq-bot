# -*- coding: utf-8 -*-
import asyncio
import os
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR if (SCRIPT_DIR / "bot.py").exists() else SCRIPT_DIR.parent
SOURCE_DIR = PROJECT_DIR / "src" if (PROJECT_DIR / "src" / "bot.py").exists() else PROJECT_DIR
sys.path.insert(0, str(SOURCE_DIR))

from bot import Bot


FORBIDDEN = (
    "模型没有正常返回",
    "模型没正常返回",
    "没有生成出可靠答案",
    "稍后重发",
    "北洋维基这次没有成功打开",
    "北洋维基尚未连接",
    "北洋维基未连接",
    "检索暂时失败",
    "响应卡了一下",
    "别急",
    "别生气",
    "希望对你有帮助",
    "有问题随时问我",
    "尽管说",
)


async def ask(bot, conversation_id, text):
    bot.add_history(conversation_id, "测试员", text, user_id=2450036920)
    public = bot.public_answer_for(text)
    if public:
        answer = public
    else:
        decision = await bot.llm_decide(conversation_id, text, "测试员", mentioned=True)
        answer = str((decision or {}).get("content") or bot.fallback_answer_for(conversation_id, text))
    bot.add_bot_history(conversation_id, answer)
    return answer


async def main():
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise SystemExit("缺少 DEEPSEEK_API_KEY，未执行真实 API 测试")
    cases = (
        ("你还在线吗？", ("在",)),
        ("我想知道学校床铺的大小", ("190", "83.5")),
        ("北洋园一般是几人间？", ("人间",)),
        ("你会干啥呀？", ("新生", "聊天")),
        ("我说的是你会干啥呀？", ("新生", "聊天")),
        ("你有病吧？", ("收到", "抱歉", "确实", "问题", "没接住", "改")),
        ("所以说你会干啥呀？", ("新生", "聊天")),
        ("你能不能不要检索北洋维基？", ("不查", "可以", "行")),
        ("量子纠缠是什么？", ("量子",)),
    )
    failures = []
    with tempfile.TemporaryDirectory() as cache_dir:
        bot = Bot(SOURCE_DIR / "bot.md", cache_path=Path(cache_dir) / "live-cache.sqlite3")
        conversation_id = "private:2450036920"
        for question, expected_any in cases:
            answer = await ask(bot, conversation_id, question)
            print(f"\n问：{question}\n答：{answer}")
            if not answer or any(marker in answer for marker in FORBIDDEN):
                failures.append((question, "出现故障话术", answer))
                continue
            school_question = bool(bot.school_wiki_query(conversation_id, question))
            if bot.response_is_bad(question, answer, school_question=school_question):
                failures.append((question, "未通过自然表达质检", answer))
                continue
            if not any(marker in answer for marker in expected_any):
                failures.append((question, f"未命中相关内容 {expected_any}", answer))
    if failures:
        print("\n真实对话失败项：")
        for question, reason, answer in failures:
            print(f"- {question}: {reason}: {answer}")
        raise SystemExit(1)
    print("\n真实 DeepSeek + 北洋维基连续对话全部通过。")


if __name__ == "__main__":
    asyncio.run(main())
