#!/usr/bin/env bash
set -euo pipefail

TARGET="all"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./scripts/install.sh [--target all|codex|agents|claude|none]

Installs:
  - @larksuite/cli
  - official larksuite/cli Agent skills
  - this feishu-agent-connect routing skill into selected skill directories
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SRC="$ROOT_DIR/skills/feishu-agent-connect"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required. Install Node.js first, then rerun this script." >&2
  exit 1
fi

echo "Installing official lark-cli..."
npm install -g @larksuite/cli

echo "Installing official larksuite/cli Agent skills..."
npx skills add larksuite/cli -y -g

install_skill() {
  local dest_root="$1"
  local dest="$dest_root/feishu-agent-connect"
  mkdir -p "$dest_root"
  rm -rf "$dest"
  cp -R "$SKILL_SRC" "$dest"
  echo "Installed routing skill: $dest"
}

case "$TARGET" in
  all)
    install_skill "$HOME/.codex/skills"
    install_skill "$HOME/.agents/skills"
    install_skill "$HOME/.claude/skills"
    ;;
  codex)
    install_skill "$HOME/.codex/skills"
    ;;
  agents)
    install_skill "$HOME/.agents/skills"
    ;;
  claude)
    install_skill "$HOME/.claude/skills"
    ;;
  none)
    ;;
  *)
    echo "Invalid target: $TARGET" >&2
    exit 2
    ;;
esac

echo
echo "Done. Restart your Agent app if it was already running."
echo "Next: python3 skills/feishu-agent-connect/scripts/setup_feishu_agent.py init-app"
