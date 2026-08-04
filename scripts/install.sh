#!/usr/bin/env bash
# macOS / Linux — delegates to cross-platform install.py
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 scripts/install.py "$@"
