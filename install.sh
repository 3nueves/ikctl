#!/usr/bin/env bash
set -euo pipefail

PACKAGE="ikctl"
LOCAL_BIN="$HOME/.local/bin"
SHELL_NAME="$(basename "${SHELL:-bash}")"

case "$SHELL_NAME" in
  zsh)  RC_FILE="$HOME/.zshrc" ;;
  bash) RC_FILE="${BASH_ENV:-$HOME/.bashrc}" ;;
  *)    RC_FILE="$HOME/.profile" ;;
esac

pip install --user "$PACKAGE"

if ! echo "$PATH" | tr ':' '\n' | grep -qx "$LOCAL_BIN"; then
  printf '\nexport PATH="%s:$PATH"\n' "$LOCAL_BIN" >> "$RC_FILE"
  echo ""
  echo "Added $LOCAL_BIN to PATH in $RC_FILE"
  echo "Run: source $RC_FILE"
else
  echo "$LOCAL_BIN is already in PATH"
fi

echo ""
echo "ikctl installed. Try: ikctl --version"
