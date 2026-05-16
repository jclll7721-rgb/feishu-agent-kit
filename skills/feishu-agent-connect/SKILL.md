---
name: feishu-agent-connect
description: "Use when setting up or operating Feishu/Lark automation through the official `lark-cli`: install official CLI skills, create or bind a Feishu app, reuse cc-connect credentials, run OAuth device authorization, grant cloud-doc/Base/Sheets/Wiki/Drive permissions, and route future Feishu document, spreadsheet, and Base automation to the official lark-* skills."
metadata:
  requires:
    bins: ["lark-cli"]
---

# Feishu Agent Connect

This skill is a thin router around the official `lark-cli` and the official `/lark-*` Agent skills. Keep context small: read this skill for setup and routing, then read only the official domain skill needed for the task.

## Setup

Check the machine:

```bash
lark-cli --version
lark-cli auth status
python3 <this-skill>/scripts/setup_feishu_agent.py doctor
```

If `lark-cli` or official skills are missing, install from the kit root:

```bash
./scripts/install.sh --target all
```

## Connect A Feishu App

For a normal local Agent or terminal, create/bind an official Feishu app:

```bash
python3 <this-skill>/scripts/setup_feishu_agent.py init-app
```

For OpenClaw/Hermes/Lark Channel, prefer binding the Agent-provided app instead of creating a parallel app:

```bash
python3 <this-skill>/scripts/setup_feishu_agent.py bind-agent --source openclaw --identity user-default
python3 <this-skill>/scripts/setup_feishu_agent.py bind-agent --source hermes --identity user-default
```

Use `user-default` for user-visible docs/drive/base automation. Use `bot-only` only for bot-owned resources.

If the machine already has `cc-connect` configured, reuse it instead of creating a parallel app:

```bash
python3 <this-skill>/scripts/setup_feishu_agent.py import-cc-connect --profile cc-connect
```

Never print `app_secret`, access tokens, or refresh tokens.

## Grant Cloud-Docs Permissions

For broad document/Base automation requested by the user:

```bash
python3 <this-skill>/scripts/setup_feishu_agent.py auth-cloud-docs
```

This requests only these domains:

```text
docs,drive,base,sheets,wiki,markdown
```

It intentionally excludes calendar, mail, IM, approval, meetings, and other unrelated domains. If the user asks for those later, request them separately.

## Route Tasks

Always read the official shared rules before auth, permission repair, identity choice, or risky writes:

```text
~/.agents/skills/lark-shared/SKILL.md
```

Then load only the relevant official skill:

| Task | Official skill |
| --- | --- |
| docs/docx read, create, update, media | `lark-doc` |
| Drive search, import/export, upload/download, permissions, comments | `lark-drive` |
| spreadsheets | `lark-sheets` |
| Base / bitable / multi-dimensional tables | `lark-base` |
| Wiki spaces/nodes | `lark-wiki` |
| Drive-native Markdown files | `lark-markdown` |
| unsupported endpoint | `lark-openapi-explorer`, then `lark-cli schema` |

Prefer official shortcuts (`lark-cli docs +fetch`, `lark-cli sheets +write`, `lark-cli base +record-upsert`). For raw API calls, check schema first.

## Safety

- Default to `--as user` for user-owned documents and personal Drive resources.
- Use `--as bot` only for bot-owned/app-level operations or when the user explicitly asks.
- For high-risk `confirmation_required` / exit 10, explain the exact action and parameters, wait for explicit approval, then retry with `--yes`.
- Opening a document to “anyone with link” is high risk; confirm separately even if OAuth scopes are already granted.
- OAuth scopes do not override document-level permissions. If a specific doc/Base denies access, ask the owner to grant access or open the link.
