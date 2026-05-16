# 飞书 Agent 自动化连接包

这是一个可分发给其他人的轻量工具包，用来把官方 `lark-cli` 接入 Codex、Claude Code、Cursor 或其他支持 `SKILL.md` 的 Agent。拿到这个文件夹的人只需要安装、完成飞书页面授权，就能让 Agent 操作飞书云文档、云空间、电子表格、多维表格、Wiki 和 Markdown。

## 直接给 Agent 的提示词

如果对方使用 OpenClaw、Hermes、Codex 或其他能执行 shell 命令的 Agent，最稳的做法不是只发裸仓库地址，而是把下面这段完整发给它：

```text
请打开并使用这个仓库完成飞书自动化连接：
https://github.com/jclll7721-rgb/feishu-agent-kit

请按 README 执行安装，并先判断当前环境是 Codex、OpenClaw、Hermes 还是普通本地 Agent。

通用安装命令：
curl -fsSL https://raw.githubusercontent.com/jclll7721-rgb/feishu-agent-kit/main/install.sh | bash

如果是 Codex 或普通本地 Agent，使用：
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py init-app
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py auth-cloud-docs

如果是 OpenClaw，使用：
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py bind-agent --source openclaw --identity user-default
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py auth-cloud-docs

如果是 Hermes，使用：
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py bind-agent --source hermes --identity user-default
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py auth-cloud-docs

过程中如果出现飞书或 GitHub 授权页面，请把链接或设备码发给我确认；不要输出 app_secret、access token、refresh token。
```

## 组成

- `skills/feishu-agent-connect/SKILL.md`：给 Agent 读的路由 skill，负责低 token 地指挥官方 `lark-cli` 和官方 `lark-*` skills。
- `skills/feishu-agent-connect/scripts/setup_feishu_agent.py`：连接脚本，支持创建/绑定飞书应用、复用 `cc-connect` 配置、发起云文档权限授权。
- `scripts/install.sh`：安装官方 CLI、官方 skills，并把本 skill 复制到常见 Agent skill 目录。

## 最优安装方式：一条命令

发布到 GitHub 后，对方直接复制这一条命令即可安装官方 CLI、官方 skills 和本连接 skill：

```bash
curl -fsSL https://raw.githubusercontent.com/jclll7721-rgb/feishu-agent-kit/main/install.sh | bash
```

安装脚本会把工具包缓存到 `~/.feishu-agent-kit`，后续连接飞书时使用这个路径里的脚本。

普通本地 Agent：

```bash
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py init-app
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py auth-cloud-docs
```

OpenClaw：

```bash
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py bind-agent --source openclaw --identity user-default
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py auth-cloud-docs
```

Hermes：

```bash
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py bind-agent --source hermes --identity user-default
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py auth-cloud-docs
```

## 本地文件夹安装

如果是直接把整个 `feishu-agent-kit` 文件夹发给对方，也可以在文件夹根目录运行：

```bash
./scripts/install.sh --target all
```

安装会做三件事：

1. 安装官方飞书 CLI：`npm install -g @larksuite/cli`
2. 安装官方 Agent skills：`npx skills add larksuite/cli -y -g`
3. 安装本路由 skill 到常见目录：`~/.codex/skills`、`~/.agents/skills`、`~/.claude/skills`

如果只装给 Codex：

```bash
./scripts/install.sh --target codex
```

安装后建议重启 Agent，让新 skill 被加载。

## 连接飞书

### 方案 A：普通 Agent / 本地终端创建一个新的官方飞书应用

```bash
python3 skills/feishu-agent-connect/scripts/setup_feishu_agent.py init-app
```

脚本会调用官方流程并输出飞书页面链接。打开链接，按页面提示创建/授权应用。

### 方案 B：OpenClaw / Hermes 绑定 Agent 已有应用

如果对方是在 OpenClaw 或 Hermes 里使用，且该 Agent 环境已经带飞书应用身份，优先用这个方式：

```bash
python3 skills/feishu-agent-connect/scripts/setup_feishu_agent.py bind-agent --source openclaw --identity user-default
```

或：

```bash
python3 skills/feishu-agent-connect/scripts/setup_feishu_agent.py bind-agent --source hermes --identity user-default
```

说明：

- `user-default` 允许用户身份访问个人可见的云文档、云空间和多维表格，适合本工具包的文档自动化场景。
- 如果只想让 bot 做应用级操作，可改成 `--identity bot-only`，但它通常看不到用户自己的文档。
- OpenClaw 多账号场景可能需要额外传 `--app-id <cli_xxx>`。

### 方案 C：复用已有 `cc-connect` 飞书应用

如果机器上已经通过 `cc-connect` 绑定过飞书：

```bash
python3 skills/feishu-agent-connect/scripts/setup_feishu_agent.py import-cc-connect --profile cc-connect
```

这个命令会从 `~/.cc-connect/config.toml` 读取已有 `app_id/app_secret` 并写入 `lark-cli` profile；脚本不会把 `app_secret` 打印到终端。

先检查不写入配置：

```bash
python3 skills/feishu-agent-connect/scripts/setup_feishu_agent.py import-cc-connect --dry-run
```

## 一次性授权云文档基础权限

```bash
python3 skills/feishu-agent-connect/scripts/setup_feishu_agent.py auth-cloud-docs
```

脚本会输出飞书授权链接，并等待用户在浏览器完成授权。授权域为：

```text
docs,drive,base,sheets,wiki,markdown
```

覆盖范围：

- 云文档：创建、读取、编辑、导入、导出、评论、素材、权限设置
- 云空间：搜索、上传、下载、移动、删除、文件夹、协作者权限、公开分享
- 多维表格：Base、表、字段、记录、视图、表单、仪表盘、workflow、角色
- 电子表格：创建、读写、格式、筛选、行列、图片、导出
- Wiki：空间、节点、复制、移动、成员管理
- Markdown：读取、创建、覆盖 Drive 中的 `.md` 文件

不包含日历、邮箱、IM、审批、会议等无关权限。

## 使用方式

连接完成后，用户可以直接对 Agent 说：

- “读取这个飞书文档并总结”
- “把这份 Markdown 写成飞书云文档”
- “创建一个多维表格来跟进销售线索”
- “把这个飞书表格开放成链接可查看”
- “查询这个 Base 的字段结构并批量写入记录”

Agent 会优先使用官方 shortcut，例如 `lark-cli docs +fetch`、`lark-cli sheets +write`、`lark-cli base +record-upsert`。遇到不确定参数时，会先查官方 `lark-cli schema`。

## 安全边界

- 不输出 `app_secret`、access token、refresh token。
- 默认用用户身份 `--as user` 操作用户可见资源。
- 删除、转移所有权、开放到互联网、停用高级权限等高风险动作仍需用户单独确认。
- 如果具体文档本身没有授权，即使 OAuth 权限齐全，也仍需要文档所有者开放访问或授权。

## 验证

```bash
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py doctor
```

正常时会看到 `lark-cli` 已安装、官方 skills 已存在、当前 token 状态有效或提示下一步授权。

## 最短可复制版本

普通本地 Agent：

```bash
curl -fsSL https://raw.githubusercontent.com/jclll7721-rgb/feishu-agent-kit/main/install.sh | bash
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py init-app
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py auth-cloud-docs
```

OpenClaw：

```bash
curl -fsSL https://raw.githubusercontent.com/jclll7721-rgb/feishu-agent-kit/main/install.sh | bash
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py bind-agent --source openclaw --identity user-default
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py auth-cloud-docs
```

Hermes：

```bash
curl -fsSL https://raw.githubusercontent.com/jclll7721-rgb/feishu-agent-kit/main/install.sh | bash
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py bind-agent --source hermes --identity user-default
python3 ~/.feishu-agent-kit/skills/feishu-agent-connect/scripts/setup_feishu_agent.py auth-cloud-docs
```
