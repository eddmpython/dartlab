#!/bin/sh
set -eu

git config core.hooksPath .githooks
chmod +x .githooks/commit-msg .githooks/pre-commit .githooks/pre-push scripts/check_no_ai_markers.py
echo "Git hooks installed: $(git config --get core.hooksPath)"
