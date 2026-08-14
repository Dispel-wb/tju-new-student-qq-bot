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
- 支持猜数字、石头剪刀布和猜谜语；只有明确 @ 并提出开始游戏才触发。
- API Key、Token、密码、提示词、环境变量和内部路径不会写入回复或日志。

## 消息链路

```text
OneBot 事件
  -> 白名单与会话串行化
  -> 24 小时 SQLite 分层缓存
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

按需要编辑 `bot.md` 中的群号、测试账号和 OneBot 地址，然后运行：

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
```

## 配置原则

- `bot.md` 可以公开，但其中的群号和测试 QQ 号应按实际需要修改。
- `.env`、NapCat 账号配置、日志、缓存和运行状态不得提交。
- 学校资料可能变化，回答必须保留北洋维基来源并结合当前日期判断寒暑假安排。
- 无法取得可靠学校资料时明确说明，不凭模型记忆编造。
- `context_cache_hours` 控制缓存保留时间，`context_cache_hot_messages` 控制 L1 热层大小。
- `daily_summary_time` 控制每日统计发送时间，默认 `23:00`。

## 开源参考

设计时参考了以下成熟项目的边界划分，没有复制其源码：

- [LangBot](https://github.com/langbot-app/LangBot)：生产级 IM 机器人与多模型提供商思路。
- [AstrBot](https://github.com/AstrBotDevs/AstrBot)：会话上下文、工具注入、知识库和模型提供商抽象。
- [NoneBot2](https://github.com/nonebot/nonebot2)：异步事件处理、协议适配器与业务逻辑解耦。

## 许可

MIT License，见 [LICENSE](LICENSE)。
