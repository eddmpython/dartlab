"""Audit 데이터 분석기 — audit JSONL에서 에러 패턴을 자동 추출.

auditAi 디렉토리의 세션 JSONL을 파싱하여:
1. 에러가 발생한 코드 라운드를 식별
2. 이전 라운드의 (에러 코드, 에러 메시지)를 추출
3. 다음 라운드의 (수정 코드)를 올바른 코드로 매칭
4. error_patterns.db에 자동 기록
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

_AUDIT_DIR = Path(__file__).resolve().parents[4] / "data" / "dart" / "auditAi"

# 코드블록 추출 패턴
_CODE_BLOCK_RE = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)


def _extractCodeFromChunks(chunks: list[str]) -> str | None:
    """스트리밍 chunk 텍스트에서 마지막 python 코드블록 추출."""
    full = "".join(chunks)
    matches = _CODE_BLOCK_RE.findall(full)
    return matches[-1].strip() if matches else None


def _detectToolFromCode(code: str) -> str:
    """코드에서 사용된 주요 도구를 감지."""
    if ".analysis(" in code:
        return "analysis"
    if "dartlab.macro(" in code:
        return "macro"
    if "dartlab.scan(" in code:
        return "scan"
    if ".credit(" in code:
        return "credit"
    if ".review(" in code:
        return "review"
    if ".gather(" in code:
        return "gather"
    if ".quant(" in code:
        return "quant"
    if "dartlab.search(" in code:
        return "search"
    if ".show(" in code or ".select(" in code:
        return "show"
    if "newsSearch(" in code or "webSearch(" in code:
        return "search"
    return ""


def analyzeSession(jsonl_path: Path) -> list[dict]:
    """단일 세션 JSONL에서 (에러코드, 에러메시지, 수정코드) 트리플을 추출.

    Args:
        jsonl_path: 세션 JSONL 파일 경로

    Returns:
        [{"wrong_code": str, "error_text": str, "correct_code": str, "tool_name": str}]
    """
    try:
        lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # code_round 이벤트 추출
    code_rounds: list[dict] = []
    for ev in events:
        kind = ev.get("kind", ev.get("type", ""))
        data = ev.get("data", ev)
        if kind == "code_round" and data.get("status") == "done":
            code_rounds.append(data)

    # 연속 라운드에서 (에러 → 수정) 쌍 추출
    results = []
    for i, cr in enumerate(code_rounds):
        result_text = cr.get("result", "")
        code = cr.get("code", "")

        is_error = any(kw in result_text for kw in ("Error", "Traceback", "실행 오류"))
        if not is_error or not code:
            continue

        # 다음 라운드에서 수정 코드가 있으면 매칭
        correct_code = ""
        if i + 1 < len(code_rounds):
            next_cr = code_rounds[i + 1]
            next_result = next_cr.get("result", "")
            # 다음 라운드가 성공이면 correct_code로 사용
            if not any(kw in next_result for kw in ("Error", "Traceback", "실행 오류")):
                correct_code = next_cr.get("code", "")

        results.append(
            {
                "wrong_code": code,
                "error_text": result_text,
                "correct_code": correct_code,
                "tool_name": _detectToolFromCode(code),
            }
        )

    return results


def harvestAllSessions() -> int:
    """auditAi 디렉토리의 모든 세션을 분석하여 error_patterns.db에 기록.

    Returns:
        기록된 패턴 수
    """
    from dartlab.ai.selfai.error_patterns import record

    if not _AUDIT_DIR.exists():
        log.info("auditAi 디렉토리 없음: %s", _AUDIT_DIR)
        return 0

    count = 0
    # 날짜별 디렉토리 순회
    for date_dir in sorted(_AUDIT_DIR.iterdir()):
        if not date_dir.is_dir():
            continue
        for jsonl_file in sorted(date_dir.glob("*.jsonl")):
            triples = analyzeSession(jsonl_file)
            for t in triples:
                record(
                    error_text=t["error_text"],
                    wrong_code=t["wrong_code"],
                    correct_code=t["correct_code"],
                    tool_name=t["tool_name"],
                )
                count += 1

    return count


def buildInitialDb() -> dict[str, int]:
    """초기 DB 구축: 알려진 패턴 seed + audit 데이터 수확.

    Returns:
        {"seeded": N, "harvested": M}
    """
    from dartlab.ai.selfai.error_patterns import seed_from_known_patterns

    seeded = seed_from_known_patterns()
    harvested = harvestAllSessions()

    log.info("error_patterns DB 초기화: seed=%d, harvest=%d", seeded, harvested)
    return {"seeded": seeded, "harvested": harvested}
