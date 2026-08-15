# -*- coding: utf-8 -*-
import argparse
import sqlite3
import time
from pathlib import Path


def score(value):
    return f"{float(value or 0):.1f}"


def main():
    parser = argparse.ArgumentParser(description="只读查看 QQ 机器人群统计与互动画像")
    parser.add_argument("--db", default="data/context-cache.sqlite3")
    parser.add_argument("--group", default="1057604880")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--pause", action="store_true")
    args = parser.parse_args()
    database = Path(args.db).expanduser().resolve()
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        group = connection.execute("""
            SELECT group_name, member_count, max_member_count, active_24h,
                   message_24h, updated_at
            FROM group_stats WHERE group_id = ?
        """, (str(args.group),)).fetchone()
        print("===== 群统计 =====")
        if group:
            print(f"群名：{group[0] or '(未获取)'}")
            print(f"成员：{group[1]} / {group[2] or '?'}")
            print(f"近24小时：{group[3]} 人活跃，{group[4]} 条消息")
            print("更新时间：" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(group[5])))
        else:
            print("尚无群人数快照。")

        print("\n===== 用户画像 =====")
        profiles = connection.execute("""
            SELECT user_id, current_name, message_count, question_count, sticker_count,
                   quote_count, positive_signals, negative_signals, helpful_signals,
                   profile_summary
            FROM user_profiles WHERE conversation_id = ?
            ORDER BY message_count DESC, last_seen DESC LIMIT ?
        """, (str(args.group), max(1, args.limit))).fetchall()
        if not profiles:
            print("尚无画像。")
        for row in profiles:
            print(f"- {row[1]} ({row[0]})：{row[2]} 条；提问 {row[3]}，表情 {row[4]}，"
                  f"引用 {row[5]}；正向 {row[6]}，冲突 {row[7]}，帮助 {row[8]}；{row[9]}")

        print("\n===== 关系边（按置信度） =====")
        relationships = connection.execute("""
            SELECT r.source_user_id, COALESCE(ps.current_name, r.source_user_id),
                   r.target_user_id, COALESCE(pt.current_name, r.target_user_id),
                   r.interactions, r.familiarity_score, r.warmth_score,
                   r.reciprocity_score, r.tension_score, r.overall_score, r.confidence
            FROM relationship_edges r
            LEFT JOIN user_profiles ps ON ps.conversation_id = r.conversation_id
                                      AND ps.user_id = r.source_user_id
            LEFT JOIN user_profiles pt ON pt.conversation_id = r.conversation_id
                                      AND pt.user_id = r.target_user_id
            WHERE r.conversation_id = ?
            ORDER BY r.confidence DESC, r.interactions DESC LIMIT ?
        """, (str(args.group), max(1, args.limit))).fetchall()
        if not relationships:
            print("尚无引用或 @ 形成的关系样本。")
        for row in relationships:
            print(f"- {row[1]} → {row[3]}：互动 {row[4]}；熟悉 {score(row[5])}，"
                  f"温度 {score(row[6])}，互惠 {score(row[7])}，冲突 {score(row[8])}，"
                  f"综合 {score(row[9])}，置信度 {float(row[10] or 0):.0%}")
    finally:
        connection.close()
    if args.pause:
        input("\n按回车关闭……")


if __name__ == "__main__":
    main()
