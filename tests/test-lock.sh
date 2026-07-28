#!/usr/bin/env bash
# test-lock.sh — pytest를 세션 간 직렬화하는 wrapper
# 사용법: bash scripts/test-lock.sh tests/ -v
#
# mkdir은 atomic 연산이므로 flock 없는 Windows bash에서도 동작한다.
# 다른 세션이 테스트 중이면 최대 300초 대기 후 타임아웃.
# PID 파일로 stale lock 자동 감지.

LOCK_DIR="/tmp/dartlab-test.lock"
PID_FILE="$LOCK_DIR/pid"
REPO_LOCK_MARKER=".pytest_cache/dartlab-test.locked"
MAX_WAIT=300
WAIT=0

cleanup() {
    rm -rf "$LOCK_DIR" 2>/dev/null
    rm -f "$REPO_LOCK_MARKER" 2>/dev/null
}

# stale lock 감지: lock 폴더 있고 PID 파일의 프로세스가 죽었으면 제거
check_stale() {
    if [ -d "$LOCK_DIR" ] && [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$OLD_PID" ] && ! kill -0 "$OLD_PID" 2>/dev/null; then
            echo "[test-lock] stale lock 감지 (PID $OLD_PID 종료됨). 자동 해제."
            rm -rf "$LOCK_DIR" 2>/dev/null
        fi
    fi
}

# 첫 시도 전 stale lock 확인
check_stale

# 대기 루프: lock 획득까지 3초 간격으로 재시도
while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    if [ $WAIT -ge $MAX_WAIT ]; then
        echo "[test-lock] 다른 세션이 테스트 중 — ${MAX_WAIT}초 대기 초과. 포기합니다."
        echo "[test-lock] 수동 해제: rm -rf $LOCK_DIR"
        exit 1
    fi
    # 매 시도마다 stale lock 재확인
    check_stale
    if mkdir "$LOCK_DIR" 2>/dev/null; then
        break
    fi
    echo "[test-lock] 다른 세션이 테스트 중... 대기 (${WAIT}/${MAX_WAIT}s)"
    sleep 3
    WAIT=$((WAIT + 3))
done

# lock 획득 성공 — PID 기록 + 종료 시 반드시 해제
echo $$ > "$PID_FILE"
mkdir -p "$(dirname "$REPO_LOCK_MARKER")"
echo $$ > "$REPO_LOCK_MARKER"
trap cleanup EXIT INT TERM

echo "[test-lock] lock 획득 (PID $$). pytest 시작."
export DARTLAB_TEST_LOCKED=1
# Polars 의 Rust 힙은 할당자가 해제한 페이지를 붙들고 있어 RSS 가 안 줄어든다. 회사를 여러 개
# 순차로 돌리면 파이썬 객체가 모두 해제된 뒤에도(실측: 살아있는 Company 0 개) RSS 가 계속
# 오른다. 그 상태로 단일 프로세스 전수 검사를 돌리면 1.5GB 천장에 걸려 백여 건에서 끊겼고,
# 그래서 뒤쪽 테스트가 한 번도 안 돌았다. 할당자에 즉시 반환을 지시하면 같은 8 개 회사 부하의
# 최대 RSS 가 1192·1243·1420MB 에서 867·722·819MB 로 내려간다(각 3 회 측정, 범위 안 겹침).
# 이 설정은 프로세스 시작 전에 읽히므로 파이썬 안에서 켤 수 없다. 여기가 유일한 자리다.
export MIMALLOC_PURGE_DELAY=${MIMALLOC_PURGE_DELAY:-0}
export MIMALLOC_PURGE_DECOMMITS=${MIMALLOC_PURGE_DECOMMITS:-1}
export MALLOC_CONF=${MALLOC_CONF:-dirty_decay_ms:0,muzzy_decay_ms:0}
# repo venv가 있으면 우선 사용한다. Windows bash에서 `uv run`을 먼저 타면
# pytest 쪽 환경변수 감지가 깨지는 경우가 있어 lock 경고가 잘못 출력된다.
if [ -x ".venv/Scripts/python.exe" ]; then
    DARTLAB_TEST_LOCKED=1 .venv/Scripts/python.exe -X utf8 -m pytest "$@"
elif [ -x ".venv/bin/python" ]; then
    DARTLAB_TEST_LOCKED=1 .venv/bin/python -X utf8 -m pytest "$@"
elif command -v uv >/dev/null 2>&1; then
    DARTLAB_TEST_LOCKED=1 uv run pytest "$@"
else
    DARTLAB_TEST_LOCKED=1 python -X utf8 -m pytest "$@"
fi
EXIT_CODE=$?

echo "[test-lock] pytest 완료 (exit=$EXIT_CODE). lock 해제."
exit $EXIT_CODE
