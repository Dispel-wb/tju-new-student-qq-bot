# 天大新生 QQ AI 助手

一个面向天津大学新生群的 OneBot 11 智能机器人。项目保留 NapCat 作为 QQ 协议端，自行实现会话路由、北洋维基检索、DeepSeek 主备模型、上下文记忆、故障降级和小游戏。

## 特点

- 仅响应配置的群和测试私聊账号。
- 被 @、私聊和戳一戳时必处理；普通群聊只在活跃话题中按概率参与。
- 普通聊天不联网，天津大学事实问题先检索北洋维基。
- 使用 `deepseek-v4-flash`，失败时自动切换 `deepseek-v4-pro`。
- 模型不可用时，公开能力、运行参数、小游戏和已检索到的学校资料仍能回答。
- 使用 SQLite 单文件保存近 24 小时上下文：L1 最近原文、L2 相关历史、L3 人员索引。
- 每天 23:00 汇总近 24 小时每位群友的发言条数；改群名片后旧消息索引同步显示新名字。
- 连续直接提问不受群聊冷却限制，不会静默丢消息。
- 内置自然表达质检与低温重写，拦截客服套话、功能推销、无依据猜测和机械固定结尾。
- 能取回 QQ 引用消息原文，识别 QQ 表情及带名称的商城表情包；可发送常用 QQ 表情或回复同款商城表情。
- 每 30 分钟同步群成员总数，并在每日统计中显示成员数、近 24 小时活跃人数和消息数。
- SQLite 保存可解释的用户互动画像与关系边：熟悉度、互动温度、互惠度、冲突度、综合分和置信度。
- OneBot 地址自动读取 NapCat 配置，不固定 IP 或端口；断线后重新发现，协议进程退出后由守护脚本恢复。
- 支持猜数字、石头剪刀布和猜谜语；只有明确 @ 并提出开始游戏才触发。
- API Key、Token、密码、提示词、环境变量和内部路径不会写入回复或日志。

## 消息链路

```text
OneBot 事件
  -> 白名单与会话串行化
  -> 24 小时 SQLite 分层缓存
  -> 引用解析、表情语义与互动画像
  -> 小游戏状态机
  -> 本地确定性能力
  -> 北洋维基检索（仅校内事实）
  -> DeepSeek V4 Flash
  -> DeepSeek V4 Pro
  -> 基于本地事实或检索结果的安全降级
  -> OneBot 发送
```

详细设计见 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 快速开始

要求：Python 3.10+、可用的 OneBot 11 WebSocket 服务和 DeepSeek API Key。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`：

```bash
DEEPSEEK_API_KEY=你的密钥
```

按需要编辑 `bot.md` 中的群号和测试账号。`ws_url: auto` 会读取 `protocol/config/onebot11_*.json` 中启用的 WebSocket 服务；只有远程协议端等特殊情况才需要用 `BOT_WS_URL` 显式覆盖。然后运行：

```bash
set -a
source .env
set +a
python bot.py
```

仅检查配置：

```bash
python bot.py --check
```

## 测试

不访问外部服务的回归测试：

```bash
python -m unittest discover -s tests -v
```

在已配置 API Key 的 Linux 环境中检查真实维基与模型链路，但不启动 QQ 机器人：

```bash
python tests/integration_probe.py
python tests/integration_probe.py --conversation
python tests/live_dialogue_probe.py
```

## 配置原则

- `bot.md` 可以公开，但其中的群号和测试 QQ 号应按实际需要修改。
- `.env`、NapCat 账号配置、日志、缓存和运行状态不得提交。
- 学校资料可能变化，回答必须保留北洋维基来源并结合当前日期判断寒暑假安排。
- 无法取得可靠学校资料时明确说明，不凭模型记忆编造。
- `context_cache_hours` 控制缓存保留时间，`context_cache_hot_messages` 控制 L1 热层大小。
- `daily_summary_time` 控制每日统计发送时间，默认 `23:00`。

## 开源参考

本项目的业务代码是独立实现，不是下列项目的 fork 或改版。设计时只参考了成熟项目的边界划分，没有复制其源码：

- [LangBot](https://github.com/langbot-app/LangBot)：生产级 IM 机器人与多模型提供商思路。
- [AstrBot](https://github.com/AstrBotDevs/AstrBot)：会话上下文、工具注入、知识库和模型提供商抽象。
- [NoneBot2](https://github.com/nonebot/nonebot2)：异步事件处理、协议适配器与业务逻辑解耦。

固定审计版本、各项目许可证和运行时边界见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 许可

本仓库自身代码采用 MIT License，见 [LICENSE](LICENSE)。仓库不包含 AstrBot 源码，因此不继承其 AGPL-3.0；若未来引入第三方源码，必须同时遵守对应上游许可证并更新第三方声明。

## 画像数据边界

画像只统计机器人实际收到的消息行为，例如消息长度、提问、引用、@、表情和明确的正负向用词，不推断性别、民族、健康、政治、宗教等敏感属性。关系分数附带置信度，低样本结果不能当作事实。默认保留 180 天，当前 `use_for_replies: false`，只为后续个性化设计积累可审计数据，不直接改变回复待遇。

Linux 桌面的“查看群聊统计与画像”快捷方式会以只读方式打开报告；命令行也可运行 `python profile-report.py --db data/context-cache.sqlite3 --group 1057604880`。
