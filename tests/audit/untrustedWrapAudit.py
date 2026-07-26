"""untrusted wrap audit — 외부 ref 발급 위치 ↔ wrapExternalInResult 동행 검증 (T2-5).

dartlab 의 보안 룰: 외부 본문 (DART/EDGAR/뉴스/웹) 은 *데이터지 지시 아니다*. 본문
안 '이전 지시 무시' / 'X 실행해라' 따르지 않는다. `Ref.sourceType="external"` 발급
위치는 직렬화 시 `[EXTERNAL CONTENT START — untrusted ...]` 마커로 감싸진다
(`ai/tools/formatting.py::wrapExternalInResult`).

본 audit: src/dartlab/ 전체에서
    1. `sourceType="external"` 또는 `sourceType=\\"external\\"` 발급 위치 grep
    2. 같은 모듈 또는 직계 호출자에 `wrapExternalInResult` 호출 동행 확인
    3. baseline 부채 원장 — 신규 위반만 차단

baseline: `tests/audit/_baselines/untrustedWrap.json`

실행::

    uv run python -X utf8 tests/audit/untrustedWrapAudit.py
    uv run python -X utf8 tests/audit/untrustedWrapAudit.py --strict
    uv run python -X utf8 tests/audit/untrustedWrapAudit.py --update-baseline
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src" / "dartlab"
BASELINE_FILE = REPO_ROOT / "tests" / "audit" / "_baselines" / "untrustedWrap.json"

# external 발급 패턴 (string literal — Python AST 정확도는 후속).
_EXTERNAL_PATTERNS: tuple[str, ...] = (
    'sourceType="external"',
    "sourceType='external'",
    'sourceType: "external"',
    "sourceType: 'external'",
    'source_type="external"',
    "source_type='external'",
)

# wrap 호출 / wrap 동행 신호.
_WRAP_SIGNALS: tuple[str, ...] = (
    "wrapExternalInResult",
    "wrap_external",  # alias
    "wrapExternal",  # camelCase 변형 가능
    "# untrusted-wrap: ok",  # 명시 면제
    "EXTERNAL CONTENT START",  # 마커 직접 사용 (formatting.py 자기 자신)
)

_SKIP_PATH_PREFIXES: tuple[str, ...] = ("__pycache__",)


def _shouldSkip(relPath: Path) -> bool:
    return any(part.startswith(prefix) for part in relPath.parts for prefix in _SKIP_PATH_PREFIXES)


def scanFile(filePath: Path) -> bool:
    """파일 안 external 발급 패턴 ↔ wrap 신호 동행 검증.

    Returns:
        True if 위반 (external 발급 + wrap 신호 없음). False if 안전.
    """
    try:
        text = filePath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    hasExternal = any(pattern in text for pattern in _EXTERNAL_PATTERNS)
    if not hasExternal:
        return False
    hasWrap = any(signal in text for signal in _WRAP_SIGNALS)
    return not hasWrap


def collectViolations() -> list[str]:
    """src/dartlab/ 전체 스캔 — external 발급 + wrap 미동행 파일 목록."""
    violations: list[str] = []
    for pyFile in SRC.rglob("*.py"):
        relPath = pyFile.relative_to(REPO_ROOT)
        if _shouldSkip(relPath):
            continue
        if scanFile(pyFile):
            violations.append(str(relPath).replace("\\", "/"))
    return sorted(violations)


def loadBaseline() -> list[str]:
    if not BASELINE_FILE.exists():
        return []
    return json.loads(BASELINE_FILE.read_text(encoding="utf-8")).get("violations", [])


def saveBaseline(violations: list[str]) -> None:
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_FILE.write_text(
        json.dumps(
            {"violations": violations, "note": "T2-5 baseline — 신규 위반만 strict 차단"},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="untrusted wrap audit (T2-5)")
    parser.add_argument("--strict", action="store_true", help="신규 위반 발견 시 exit 2")
    parser.add_argument("--update-baseline", action="store_true", help="현재 위반을 baseline 으로 저장")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    current = collectViolations()
    baseline = loadBaseline()

    if args.update_baseline:
        saveBaseline(current)
        print(f"[untrustedWrap] baseline 갱신 — {len(current)} 파일")
        return 0

    newViolations = sorted(set(current) - set(baseline))

    if args.json:
        print(
            json.dumps(
                {"current": current, "baseline": baseline, "newViolations": newViolations},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(f"[untrustedWrap] 현재 — {len(current)} 파일, baseline — {len(baseline)} 파일")
    if newViolations:
        print(f"[untrustedWrap] 신규 위반 {len(newViolations)} 파일:")
        for v in newViolations[:20]:
            print(f"  - {v}")
    else:
        print("[untrustedWrap] OK — baseline 변동 없음")

    if args.strict and newViolations:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
