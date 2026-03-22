#!/usr/bin/env bash
# test-lock.sh — pytest를 세션 간 직렬화하는 wrapper
# 사용법: bash scripts/test-lock.sh tests/ -v
#
# mkdir은 atomic 연산이므로 flock 없는 Windows bash에서도 동작한다.
# 다른 세션이 테스트 중이면 최대 300초 대기 후 타임아웃.

LOCK_DIR="/tmp/dartlab-test.lock"
MAX_WAIT=300
WAIT=0

cleanup() {
    rm -rf "$LOCK_DIR" 2>/dev/null
}

# 대기 루프: lock 획득까지 3초 간격으로 재시도
while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    if [ $WAIT -ge $MAX_WAIT ]; then
        echo "[test-lock] 다른 세션이 테스트 중 — ${MAX_WAIT}초 대기 초과. 포기합니다."
        echo "[test-lock] 수동 해제: rm -rf $LOCK_DIR"
        exit 1
    fi
    echo "[test-lock] 다른 세션이 테스트 중... 대기 (${WAIT}/${MAX_WAIT}s)"
    sleep 3
    WAIT=$((WAIT + 3))
done

# lock 획득 성공 — 종료 시 반드시 해제
trap cleanup EXIT INT TERM

echo "[test-lock] lock 획득. pytest 시작."
uv run pytest "$@"
EXIT_CODE=$?

echo "[test-lock] pytest 완료 (exit=$EXIT_CODE). lock 해제."
exit $EXIT_CODE
