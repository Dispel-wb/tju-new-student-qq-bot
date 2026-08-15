# 第三方来源与许可说明

本仓库的机器人业务源码为独立实现，没有复制、修改或打包下列参考项目的源码。
它们只用于理解成熟机器人项目的架构边界、事件处理方式和模型提供商设计。

## 架构参考

| 项目 | 审计版本 | 许可证 | 本项目的使用方式 |
| --- | --- | --- | --- |
| [LangBot](https://github.com/langbot-app/LangBot) | `1f1a3af` | [Apache-2.0](https://github.com/langbot-app/LangBot/blob/1f1a3af/LICENSE) | 仅参考 IM 平台、会话与模型提供商的分层思路；未复制源码 |
| [AstrBot](https://github.com/AstrBotDevs/AstrBot) | `0fceeb3` | [AGPL-3.0](https://github.com/AstrBotDevs/AstrBot/blob/0fceeb3/LICENSE) | 仅参考上下文、知识库与工具边界；未复制源码，也不依赖或分发 AstrBot |
| [NoneBot2](https://github.com/nonebot/nonebot2) | `623abb2` | [MIT](https://github.com/nonebot/nonebot2/blob/623abb2/LICENSE) | 仅参考异步事件与协议适配解耦思路；未复制源码 |

## 运行时边界

- 本仓库通过公开的 OneBot 11 接口与协议端通信，不包含 NapCat、Lagrange 或 QQ 客户端文件。
- `websockets` 是通过包管理器安装的运行时依赖，适用其自身许可证。
- DeepSeek 作为外部 API 服务调用，不在本仓库中分发其模型或服务端代码。

## 审计记录

2026-08-15 对 `bot.py` 与上述三个审计版本的共 1,522 个 Python 文件进行了连续 6 个有效代码行的精确匹配检查，未发现相同代码块。该检查用于辅助确认代码来源，不替代专业法律意见。

因此，本仓库自身代码继续采用 [MIT License](LICENSE)。如果以后复制或修改第三方源码，提交者必须同时保留原版权声明，并按对应许可证更新本文件和仓库许可边界。
