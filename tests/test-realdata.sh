#!/usr/bin/env bash
# test-realdata.sh — realData 마커 스위트 전용 runner.
#
# 목적:
#   엔진별 실제 데이터 스모크 (tests/realData/) 를 메모리 안전하게 실행.
#   **파일별로 독립 pytest 프로세스**를 돌려 Polars 네이티브 메모리가
#   단일 세션에서 누적되지 않게 한다. 각 파일 사이 프로세스 종료 = 네이티브 힙 완전 해제.
#
# 사용법:
#   bash tests/test-realdata.sh                          # realData 전체 (파일별 독립)
#   bash tests/test-realdata.sh tests/realData/test_companyFacade.py  # 단일 파일
#   bash tests/test-realdata.sh --single -m freshInstall # 단일 세션 모드 (fresh 마커만)
#
# 메모리 규칙:
#   - 기본 = 파일별 프로세스 분리 (realData 의 경우 이게 유일한 안전 실행)
#   - --single = 일반 pytest 처럼 단일 세션 (작은 subset 에만 권장)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REAL_DATA_DIR="$REPO_ROOT/tests/realData"
cd "$REPO_ROOT" || exit 1

SINGLE_MODE=0
if [ "${1:-}" = "--single" ]; then
    SINGLE_MODE=1
    shift
fi

# realData 는 lazy 로딩 속성 + 전종목 scan 프리빌드를 포함하므로 고용량 필요.
# 기본 6000MB. scan 20 axes iterate 시 3~4GB 도달 관측됨.
export PYTEST_MEMORY_LIMIT_MB="${PYTEST_MEMORY_LIMIT_MB:-6000}"

# 단일 파일/단일 세션 모드 — test-lock.sh 직접 위임
if [ "$SINGLE_MODE" = "1" ] || { [ $# -ge 1 ] && [ -f "$1" ]; }; then
    if [ $# -eq 0 ]; then
        set -- "$REAL_DATA_DIR" -m "realData" -v --tb=short
    fi
    echo "[test-realdata] 단일 세션 모드 — $@"
    bash "$SCRIPT_DIR/test-lock.sh" "$@"
    exit $?
fi

# 기본 = 파일별 분리 실행
MARKER_ARGS=("$@")
if [ $# -eq 0 ]; then
    MARKER_ARGS=(-m realData)
fi
shopt -s nullglob
TEST_FILES=("$REAL_DATA_DIR"/test_*.py)
if [ ${#TEST_FILES[@]} -eq 0 ]; then
    echo "[test-realdata] tests/realData/test_*.py 없음" >&2
    exit 1
fi

TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_SKIP=0
FAILED_FILES=()

for f in "${TEST_FILES[@]}"; do
    rel="${f#$REPO_ROOT/}"
    echo ""
    echo "================================================================"
    echo "[test-realdata] $rel"
    echo "================================================================"
    bash "$SCRIPT_DIR/test-lock.sh" "$rel" "${MARKER_ARGS[@]}" -v --tb=short
    rc=$?
    if [ $rc -eq 0 ]; then
        TOTAL_PASS=$((TOTAL_PASS + 1))
    elif [ $rc -eq 5 ]; then
        # no tests collected (marker filter)
        echo "[test-realdata] 수집 0건 (marker filter) — skip"
        TOTAL_SKIP=$((TOTAL_SKIP + 1))
    else
        TOTAL_FAIL=$((TOTAL_FAIL + 1))
        FAILED_FILES+=("$rel (exit=$rc)")
    fi
done

echo ""
echo "================================================================"
echo "[test-realdata] 전체 요약: pass=$TOTAL_PASS  fail=$TOTAL_FAIL  noCollection=$TOTAL_SKIP"
if [ ${#FAILED_FILES[@]} -gt 0 ]; then
    echo "[test-realdata] 실패 파일:"
    for x in "${FAILED_FILES[@]}"; do
        echo "  - $x"
    done
    exit 1
fi
exit 0
