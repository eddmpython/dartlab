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


# 직렬화 길목. 외부 ref 가 모델이나 MCP 클라이언트에 닿기 직전에 반드시 지나는 자리다.
# 발급 모듈마다 wrap 을 요구하는 것보다 여기 한 곳이 성립하는지 보는 편이 정확하다.
# 발급은 여러 도구에 흩어지지만 나가는 문은 셋뿐이기 때문이다.
_SERIALIZATION_CHOKEPOINTS: tuple[str, ...] = (
    "src/dartlab/ai/agent.py",
    "src/dartlab/mcp/protocol.py",
    "src/dartlab/ai/workbench/runner.py",
)


def collectChokepointFailures() -> list[str]:
    """길목이 wrap 을 호출하지 않으면 그 자체가 위반이다. baseline 으로 눌러 두지 않는다."""
    failures: list[str] = []
    for rel in _SERIALIZATION_CHOKEPOINTS:
        path = REPO_ROOT / rel
        if not path.exists():
            failures.append(f"{rel} (파일 없음)")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "wrapExternalInResult" not in text:
            failures.append(rel)
    return failures


def collectViolations() -> list[str]:
    """src/dartlab/ 전체 스캔. external 발급 + wrap 미동행 파일 목록.

    길목이 전부 성립하면 발급 모듈은 이미 덮인 것이라 위반으로 세지 않는다. 예전에는
    발급 파일마다 wrap 을 요구해서, 정상적으로 덮인 webSearch 같은 파일이 부채 원장에
    올라 있었다. 길목이 하나라도 무너지면 그때는 발급 목록 전체가 다시 위반이 된다.
    """
    if not collectChokepointFailures():
        return []
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

    chokepointFailures = collectChokepointFailures()
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

    if chokepointFailures:
        print(f"[untrustedWrap] 직렬화 길목 {len(chokepointFailures)} 곳이 wrap 을 호출하지 않는다:")
        for f in chokepointFailures:
            print(f"  - {f}")
        print("  외부 본문이 마커 없이 모델과 MCP 클라이언트에 그대로 나간다.")
    else:
        print(f"[untrustedWrap] 직렬화 길목 {len(_SERIALIZATION_CHOKEPOINTS)} 곳 전부 wrap 호출 확인.")

    print(f"[untrustedWrap] 현재 {len(current)} 파일, baseline {len(baseline)} 파일")
    if newViolations:
        print(f"[untrustedWrap] 신규 위반 {len(newViolations)} 파일:")
        for v in newViolations[:20]:
            print(f"  - {v}")
    else:
        print("[untrustedWrap] OK. baseline 변동 없음")

    if args.strict and (newViolations or chokepointFailures):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
