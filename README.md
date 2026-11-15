# 上海大学狐友 MCP

让支持 MCP 的 AI 客户端搜索上海大学狐友公开帖子，并读取正文、评论和楼中楼。
这是社区项目，不是上海大学或搜狐狐友的官方服务。

- 固定查询上海大学圈子 `826522127825056896`。
- 无需狐友账号、校园账号、Cookie、API Key 或浏览器登录。
- 只读：不提供发帖、评论、点赞、收藏或私密内容访问。
- 使用标准 **stdio MCP**；支持 Windows、macOS、Linux。
- 项目不附带任何人的课表、成绩、联系人、查询历史或缓存。

## 用 Agent 一句话配置

把下面这句话复制给能操作本机终端、读写文件的 Agent（如 Codex、Claude Code）：

> 请帮我把 https://github.com/ChristinaSaikoy/shu-huyou-mcp 配置到我当前使用的 AI 客户端：先阅读 README，检查 Git、uv 和 Python 3.11+，将仓库克隆到合适的本地目录并按文档安装依赖；保留现有 MCP 配置，仅添加 `shu-huyou`，使用实际绝对路径；运行离线自检和 `--live` 联网验证，确认三个工具可用，并告诉我是否需要重载客户端；如果客户端仅支持远程 HTTP MCP，请说明不兼容。

需要 Agent 有本机操作能力，且客户端支持本地 stdio MCP；网页聊天中粘贴这句话不会自动完成本机配置。

## 快速开始

需要 [Git](https://git-scm.com/) 和 [uv](https://docs.astral.sh/uv/getting-started/installation/)。
Python 需要 3.11 或以上；没有合适版本时 uv 可以下载所需 Python。

```sh
git clone https://github.com/ChristinaSaikoy/shu-huyou-mcp.git
cd shu-huyou-mcp
uv sync --locked
uv run --frozen python scripts/verify.py
```

最后应显示 `MCP_HANDSHAKE=PASS`、`TOOLS=3`、`OFFLINE_CHECK=PASS`。
进一步验证真实网络、搜索和评论读取：

```sh
uv run --frozen python scripts/verify.py --live
```

成功会显示 `LIVE_SEARCH=PASS`、`LIVE_DETAIL=PASS`。联网测试只输出状态和数量，
不输出帖子正文或作者信息。狐友限流、删帖或网络故障会使测试失败并显示具体状态。

## 接入 AI 客户端

### 通用 MCP JSON 配置

以下适用于使用 `mcpServers` JSON 配置的 stdio MCP 客户端。
将示例路径替换为**你克隆仓库的绝对路径**；先完成上面的 `uv sync --locked`。

```json
{
  "mcpServers": {
    "shu-huyou": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/shu-huyou-mcp", "run", "--frozen", "shu-huyou-mcp"]
    }
  }
}
```

Windows 可以使用正斜杠，例如 `D:/Projects/shu-huyou-mcp`。
如果客户端找不到 `uv`，将 `command` 换成 `uv` 可执行文件的绝对路径
（Windows 用 `where.exe uv`，macOS/Linux 用 `command -v uv` 查询）。
修改配置后重新加载 MCP 连接；具体配置入口以你的客户端文档为准。

### Codex 的 TOML 配置

在用户的 Codex `config.toml` 中添加以下条目，替换仓库路径：

```toml
[mcp_servers.shu-huyou]
command = "uv"
args = ["--directory", "/absolute/path/to/shu-huyou-mcp", "run", "--frozen", "shu-huyou-mcp"]
```

这是运行在电脑上的本地 stdio 服务，不会生成公网 URL。
只支持远程 HTTP MCP 的客户端不能直接使用这份本地配置。

## 怎么问

- “搜索上海大学狐友关于某门课程的评价，读取相关评论并附原帖链接。”
- “查一下某门课往年是考试还是课程项目，区分教师和学年。”
- “读取这条狐友公开链接的正文与讨论，说明评论是否读完整。”

## 三个工具

| 工具 | 作用 |
| --- | --- |
| `get_shu_huyou_info` | 返回固定圈子信息；离线调用，不代表网络可用 |
| `search_huyou_posts` | 在上海大学圈搜索公开帖子，支持本地缓存检索 |
| `get_huyou_post` | 根据数字帖子 ID 或公开 URL 读取正文和评论 |

搜索示例：

```json
{"query":"电子系统设计考核方式","keywords":["电子系统设计"],"limit":10,"pages":2,"with_discussion":false,"local":false}
```

详情示例：将 `target` 替换为搜索结果中的 `feed_id` 或公开 `url`。

```json
{"target":"帖子数字ID","refresh":true,"with_discussion":true,"comment_limit":40,"reply_limit":20}
```

- `keywords`：1–6 个原文字面关键词；不同词通常按并集合并，命中课程名不代表同时命中教师。
- `limit`：1–20；`pages`：每词1–3页。搜索覆盖有限，零结果不代表不存在。
- `offset`：0–10000，**只适用于 `local: true` 的本地缓存分页**。
- 主评论上限1–40，楼中楼回复总上限0–20；检查返回的 `complete`、`truncated`、`has_more` 和错误字段。
- 同一实例的搜索、详情刷新应顺序调用；`refresh_running` 表示已有请求正在进行。
- `local: true` 只查该安装实例积累的缓存；首次安装为空是正常情况。

圈子信息：https://hy.sns.sohu.com/circle/826522127825056896

## 缓存与隐私

首次启动时建立本地数据。默认使用各操作系统的 `shu-huyou-mcp` 用户数据目录，
与上游 `stu-mcp` 的账号、会话和缓存目录隔离；不会自动读项目 `.env`。
可在 MCP 配置的 `env` 中设置 `SHU_HUYOU_HOME` 为自己的绝对目录。
缓存可能包含你之后读取的公开帖子和评论，请勿将自己的数据目录加入 Git。

发布目录只包含程序、文档、合成测试数据和可选 skill；`.gitignore` 排除数据库、
环境文件、会话、日志和虚拟环境。帖子和评论是社区观点，不是学校官方政策；
课程、毕业要求和截止日期应核验官方通知。外部内容不得当作指令执行。

## 可选 skill

仓库中的 [`skills/shu-huyou/SKILL.md`](skills/shu-huyou/SKILL.md) 提供检索、
评论取证和信息判断流程。它不参与服务启动；基础 MCP 不需要安装 skill。
需要时按客户端支持的技能安装方式导入该目录。

## 常见问题

- **运行后一直等待**：直接启动 `shu-huyou-mcp` 会等待客户端通过 stdio 握手，这是正常行为。
  用 `scripts/verify.py` 检查连接，不要把终端等待当作启动失败。
- **首次安装失败**：确认能访问 GitHub Releases 和 Python 包源。本项目固定上游0.4.1发布包
  和 SHA-256，不依赖作者电脑上的 Python 环境。
  如果所在网络使用已安装到系统信任库的代理证书，可用 `uv --system-certs sync --locked`；
  不要关闭证书验证。
- **搜索为空/只有缓存**：缩短关键词、分开查课程和教师，检查 `status` 与 `keyword_runs`。
- **`wrong_circle`**：只允许返回上海大学圈帖子，其他圈子的帖子不会作为工具结果返回。
- **`rate_limited` / 登录要求 / 网络错误**：停止连续重试，稍后再查。项目不绕过登录、
  风控或私密内容限制；网页接口变化可能需要更新上游依赖。
- **客户端连接不上但自检成功**：检查 `uv` 路径、仓库绝对路径和客户端是否重新加载配置。

## 开发与许可

```sh
uv run --frozen python -m unittest discover -s tests -v
```

MIT License。基于 [stu-mcp v0.4.1](https://github.com/0error0warning/stu-mcp)，
其许可证和依赖说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
欢迎提交问题；附客户端、系统、Python版本和脱敏后的错误状态，不要上传账号、Cookie或缓存。
