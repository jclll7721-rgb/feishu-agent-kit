#!/usr/bin/env bash
set -euo pipefail

DEFAULT_REPO="https://github.com/jclll7721-rgb/feishu-agent-kit"
REPO_URL="${FEISHU_AGENT_KIT_REPO:-$DEFAULT_REPO}"
REF="${FEISHU_AGENT_KIT_REF:-main}"
INSTALL_DIR="${FEISHU_AGENT_KIT_HOME:-$HOME/.feishu-agent-kit}"
TARGET="${FEISHU_AGENT_KIT_TARGET:-all}"
FORCE=0

usage() {
  cat <<'EOF'
Usage:
  curl -fsSL https://raw.githubusercontent.com/jclll7721-rgb/feishu-agent-kit/main/install.sh | bash
  bash install.sh [--target all|codex|agents|claude|none] [--install-dir DIR] [--repo URL] [--ref REF] [--force]

Installs the Feishu Agent Kit and then runs the local installer.

Options:
  --target       Skill install target. Default: all
  --install-dir  Where to cache the kit. Default: ~/.feishu-agent-kit
  --repo         GitHub repo URL. Default: https://github.com/jclll7721-rgb/feishu-agent-kit
  --ref          Git branch/tag to install. Default: main
  --force        Replace an existing install dir even if it does not look like this kit
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --install-dir)
      INSTALL_DIR="${2:-}"
      shift 2
      ;;
    --repo)
      REPO_URL="${2:-}"
      shift 2
      ;;
    --ref)
      REF="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

is_kit_root() {
  local dir="$1"
  [[ -n "$dir" && -f "$dir/scripts/install.sh" && -d "$dir/skills/feishu-agent-connect" ]]
}

SCRIPT_SOURCE="${BASH_SOURCE[0]:-}"
SCRIPT_DIR=""
if [[ -n "$SCRIPT_SOURCE" && -f "$SCRIPT_SOURCE" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd)"
fi

KIT_DIR=""
if is_kit_root "$SCRIPT_DIR"; then
  KIT_DIR="$SCRIPT_DIR"
else
  TMP_DIR="$(mktemp -d)"
  cleanup() {
    rm -rf "$TMP_DIR"
  }
  trap cleanup EXIT

  echo "Downloading Feishu Agent Kit from $REPO_URL ($REF)..."
  if command -v git >/dev/null 2>&1; then
    if git clone --depth 1 --branch "$REF" "$REPO_URL" "$TMP_DIR/kit" >/dev/null 2>&1; then
      :
    else
      rm -rf "$TMP_DIR/kit"
    fi
  fi

  if [[ ! -d "$TMP_DIR/kit" ]]; then
    if ! command -v curl >/dev/null 2>&1; then
      echo "git clone failed and curl is not installed." >&2
      exit 1
    fi
    if ! command -v tar >/dev/null 2>&1; then
      echo "tar is required to extract the downloaded kit." >&2
      exit 1
    fi
    REPO_BASE="${REPO_URL%.git}"
    ARCHIVE_URL="$REPO_BASE/archive/refs/heads/$REF.tar.gz"
    curl -fsSL "$ARCHIVE_URL" -o "$TMP_DIR/kit.tar.gz"
    mkdir -p "$TMP_DIR/extract"
    tar -xzf "$TMP_DIR/kit.tar.gz" -C "$TMP_DIR/extract"
    for extracted in "$TMP_DIR"/extract/*; do
      if [[ -d "$extracted" ]]; then
        mv "$extracted" "$TMP_DIR/kit"
        break
      fi
    done
  fi

  if ! is_kit_root "$TMP_DIR/kit"; then
    echo "Downloaded content does not look like feishu-agent-kit." >&2
    exit 1
  fi

  if [[ -e "$INSTALL_DIR" && "$FORCE" -ne 1 ]]; then
    if [[ ! -f "$INSTALL_DIR/.feishu-agent-kit" && ! -d "$INSTALL_DIR/skills/feishu-agent-connect" ]]; then
      echo "Install dir exists and does not look like this kit: $INSTALL_DIR" >&2
      echo "Rerun with --force or choose --install-dir." >&2
      exit 1
    fi
  fi

  mkdir -p "$(dirname "$INSTALL_DIR")"
  rm -rf "$INSTALL_DIR"
  mv "$TMP_DIR/kit" "$INSTALL_DIR"
  touch "$INSTALL_DIR/.feishu-agent-kit"
  KIT_DIR="$INSTALL_DIR"
fi

bash "$KIT_DIR/scripts/install.sh" --target "$TARGET"

SETUP_SCRIPT="$KIT_DIR/skills/feishu-agent-connect/scripts/setup_feishu_agent.py"
echo
echo "Feishu Agent Kit is ready at: $KIT_DIR"
echo
echo "Next commands for a normal local Agent:"
echo "  python3 \"$SETUP_SCRIPT\" init-app"
echo "  python3 \"$SETUP_SCRIPT\" auth-cloud-docs"
echo
echo "For OpenClaw:"
echo "  python3 \"$SETUP_SCRIPT\" bind-agent --source openclaw --identity user-default"
echo "  python3 \"$SETUP_SCRIPT\" auth-cloud-docs"
echo
echo "For Hermes:"
echo "  python3 \"$SETUP_SCRIPT\" bind-agent --source hermes --identity user-default"
echo "  python3 \"$SETUP_SCRIPT\" auth-cloud-docs"
