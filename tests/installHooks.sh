#!/usr/bin/env bash
# 추적되는 .githooks를 단일 Git hook 진입점으로 설치한다.
set -eu
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/commit-msg .githooks/pre-push
echo "[installHooks] .githooks: 버전 정책, 공개 산출물, preflight 필수 검증"
