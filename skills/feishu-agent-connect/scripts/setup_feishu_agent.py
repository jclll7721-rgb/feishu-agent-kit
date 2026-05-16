#!/usr/bin/env python3
"""Setup helper for official lark-cli based Feishu automation."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


CLOUD_DOC_DOMAINS = "docs,drive,base,sheets,wiki,markdown"
DEFAULT_CC_CONNECT_CONFIG = Path.home() / ".cc-connect" / "config.toml"


def run(args: list[str], *, input_text: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, input=input_text, text=True, check=check)


def capture(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def load_cc_connect_apps(config_path: Path) -> list[dict[str, str]]:
    if not config_path.exists():
        raise SystemExit(f"cc-connect config not found: {config_path}")

    apps: list[dict[str, str]] = []
    project_name = ""
    in_platform = False
    platform: dict[str, str] = {}

    def flush() -> None:
        if platform.get("type") == "feishu" and platform.get("app_id") and platform.get("app_secret"):
            apps.append({"project": project_name, **platform})

    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[[projects]]":
            flush()
            project_name = ""
            in_platform = False
            platform = {}
            continue
        if line == "[[projects.platforms]]":
            flush()
            in_platform = True
            platform = {}
            continue
        if line.startswith("["):
            in_platform = line == "[projects.platforms.options]"
            continue
        if "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        value = value.strip().strip('"')
        if key == "name" and not in_platform:
            project_name = value
        elif in_platform and key in {"type", "app_id", "app_secret"}:
            platform[key] = value

    flush()
    return apps


def choose_app(apps: list[dict[str, str]], project: str | None) -> dict[str, str]:
    if project:
        matches = [app for app in apps if app["project"] == project]
        if not matches:
            names = ", ".join(app["project"] for app in apps) or "(none)"
            raise SystemExit(f"No Feishu app for project {project!r}. Available: {names}")
        return matches[0]
    if len(apps) == 1:
        return apps[0]
    if not apps:
        raise SystemExit("No Feishu app found in cc-connect config")
    names = ", ".join(app["project"] for app in apps)
    raise SystemExit(f"Multiple Feishu apps found; pass --project. Available: {names}")


def import_cc_connect(args: argparse.Namespace) -> int:
    app = choose_app(load_cc_connect_apps(args.config), args.project)
    print(f"Selected cc-connect project: {app['project']}")
    print(f"Selected App ID: {app['app_id']}")
    print(f"Target lark-cli profile: {args.profile}")
    if args.dry_run:
        print("Dry run only; lark-cli config was not changed.")
        return 0
    init_cmd = [
        "lark-cli",
        "config",
        "init",
        "--app-id",
        app["app_id"],
        "--app-secret-stdin",
        "--brand",
        args.brand,
        "--name",
        args.profile,
    ]
    run(init_cmd, input_text=f"{app['app_secret']}\n")
    run(["lark-cli", "profile", "use", args.profile])
    print("lark-cli profile configured from cc-connect. Next: auth-cloud-docs")
    return 0


def init_app(args: argparse.Namespace) -> int:
    cmd = ["lark-cli", "config", "init", "--new", "--lang", args.lang]
    if args.profile:
        cmd += ["--name", args.profile]
    print("Starting official lark-cli app setup. Open the URL printed by lark-cli and finish setup in Feishu.")
    return run(cmd, check=False).returncode


def bind_agent(args: argparse.Namespace) -> int:
    cmd = [
        "lark-cli",
        "config",
        "bind",
        "--identity",
        args.identity,
        "--lang",
        args.lang,
    ]
    if args.source:
        cmd += ["--source", args.source]
    if args.app_id:
        cmd += ["--app-id", args.app_id]
    if args.force:
        cmd += ["--force"]

    print("Binding lark-cli to the Agent-provided Feishu app.")
    print(f"Identity policy: {args.identity}")
    if args.source:
        print(f"Agent source: {args.source}")
    if args.identity == "user-default":
        print("This allows user identity for user-visible docs, Drive, Sheets, Base, and Wiki automation.")
    else:
        print("Bot-only is safer, but it usually cannot access the user's personal documents.")
    return run(cmd, check=False).returncode


def auth_cloud_docs(_: argparse.Namespace) -> int:
    if not command_exists("lark-cli"):
        raise SystemExit("lark-cli is not installed. Run ./scripts/install.sh first.")

    start = capture(
        ["lark-cli", "auth", "login", "--domain", CLOUD_DOC_DOMAINS, "--no-wait", "--json"],
        check=True,
    )
    try:
        payload = json.loads(start.stdout)
    except json.JSONDecodeError as exc:
        sys.stdout.write(start.stdout)
        sys.stderr.write(start.stderr)
        raise SystemExit(f"Could not parse lark-cli auth output: {exc}") from exc

    url = payload.get("verification_url")
    device_code = payload.get("device_code")
    if not url or not device_code:
        sys.stdout.write(start.stdout)
        raise SystemExit("lark-cli did not return verification_url and device_code")

    print("Open this Feishu authorization URL exactly as shown:")
    print()
    print("```text")
    print(url)
    print("```")
    print()
    print("Waiting for authorization...")
    rc = run(["lark-cli", "auth", "login", "--device-code", device_code], check=False).returncode
    if rc == 0:
        print()
        print("Authorization finished. Current status:")
        run(["lark-cli", "auth", "status"], check=False)
    return rc


def doctor(_: argparse.Namespace) -> int:
    ok = True
    for name in ("node", "npm", "npx", "lark-cli"):
        path = shutil.which(name)
        print(f"{name}: {path or 'missing'}")
        ok = ok and bool(path)

    if command_exists("lark-cli"):
        run(["lark-cli", "--version"], check=False)
        diag = capture(["lark-cli", "doctor", "--offline"], check=False)
        if diag.returncode == 0:
            try:
                payload = json.loads(diag.stdout)
            except json.JSONDecodeError:
                print("lark-cli doctor: ran, but output was not JSON")
            else:
                for check in payload.get("checks", []):
                    name = check.get("name", "unknown")
                    status = check.get("status", "unknown")
                    print(f"lark-cli doctor {name}: {status}")
        else:
            print("lark-cli doctor: failed; run `lark-cli doctor --offline` for details")

    official_shared = Path.home() / ".agents" / "skills" / "lark-shared" / "SKILL.md"
    print(f"official lark-shared skill: {'found' if official_shared.exists() else 'missing'}")
    if not official_shared.exists():
        print("Install official skills with: npx skills add larksuite/cli -y -g")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup Feishu/Lark CLI automation for Agents")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="check local lark-cli and skill installation")
    p.set_defaults(func=doctor)

    p = sub.add_parser("init-app", help="start official app setup flow")
    p.add_argument("--profile", help="optional lark-cli profile name")
    p.add_argument("--lang", default="zh", choices=["zh", "en"])
    p.set_defaults(func=init_app)

    p = sub.add_parser("bind-agent", help="bind OpenClaw/Hermes/Lark Channel app credentials to lark-cli")
    p.add_argument("--source", choices=["openclaw", "hermes", "lark-channel"], help="agent source; auto-detected if omitted")
    p.add_argument("--identity", default="user-default", choices=["bot-only", "user-default"])
    p.add_argument("--app-id", help="required by some OpenClaw multi-account setups")
    p.add_argument("--lang", default="zh", choices=["zh", "en"])
    p.add_argument("--force", action="store_true", help="confirm risky identity transition when lark-cli requires it")
    p.set_defaults(func=bind_agent)

    p = sub.add_parser("import-cc-connect", help="configure lark-cli from existing cc-connect Feishu app")
    p.add_argument("--config", type=Path, default=DEFAULT_CC_CONNECT_CONFIG)
    p.add_argument("--project", help="cc-connect project name when multiple Feishu apps exist")
    p.add_argument("--profile", default="cc-connect")
    p.add_argument("--brand", default="feishu", choices=["feishu", "lark"])
    p.add_argument("--dry-run", action="store_true", help="only show selected app; do not write lark-cli config")
    p.set_defaults(func=import_cc_connect)

    p = sub.add_parser("auth-cloud-docs", help="authorize docs, drive, base, sheets, wiki, markdown")
    p.set_defaults(func=auth_cloud_docs)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
