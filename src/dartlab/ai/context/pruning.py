"""도구 결과 필드 pruning — LLM에 불필요한 컬럼/필드 재귀 제거.

dexter의 stripFieldsDeep 패턴을 Python에 적용.
토큰 절약 + 분석 관련성 향상.

응답 상태 태그:
- [OK] 정상 조회
- [PARTIAL] 데이터 일부만 반환 (truncation/pruning 발생)
- [FAIL] 또는 [데이터 없음] — 도구 자체에서 반환하는 실패 메시지
"""

from __future__ import annotations

import json
from typing import Any

# LLM 분석에 불필요한 필드 — 재귀적으로 제거
_STRIP_FIELDS: frozenset[str] = frozenset(
    {
        # XBRL 메타데이터
        "concept_id",
        "xbrl_context_id",
        "instant",
        "member",
        "dimension",
        "label_ko_raw",
        # 공시 메타데이터
        "acceptance_number",
        "rcept_no",
        "filing_date",
        "report_code",
        "reprt_code",
        "corp_cls",
        "corp_code",
        # 기술적 식별자
        "sj_div",
        "ord",
        "data_rank",
        "source_file",
        "source_path",
        "sourceBlockOrder",
        # 중복/내부용
        "account_id_raw",
        "account_nm_raw",
        "currency",
    }
)

# 모듈별 추가 제거 필드
_MODULE_STRIP: dict[str, frozenset[str]] = {
    "finance": frozenset({"bsns_year", "sj_nm", "stock_code", "fs_div", "fs_nm"}),
    "explore": frozenset({"blockHash", "rawHtml", "charCount"}),
    "report": frozenset({"rcept_no", "corp_code", "corp_cls"}),
}

# 실패/빈 결과 접두사 — 이미 태그가 있으면 재태그 방지
_FAIL_PREFIXES = ("[데이터 없음]", "[오류]", "[FAIL]", "[차단]", "[캐시]")


def pruneToolResult(toolName: str, result: str, *, maxChars: int = 8000) -> str:
    """도구 결과 문자열에서 불필요 필드를 제거하고 상태 태그를 추가."""
    if not result or len(result) < 100:
        return result

    # 이미 상태 태그가 있으면 그대로
    if result.startswith(("[OK]", "[PARTIAL]")) or result.startswith(_FAIL_PREFIXES):
        return result[:maxChars] if len(result) > maxChars else result

    # JSON 파싱 시도
    try:
        data = json.loads(result)
    except (json.JSONDecodeError, ValueError):
        # JSON이 아니면 마크다운 테이블 등 — 길이만 제어
        truncated = len(result) > maxChars
        text = result[:maxChars] if truncated else result
        if truncated:
            return f"[PARTIAL] 결과가 잘렸습니다 ({len(result)}자 중 {maxChars}자).\n{text}"
        return text

    # 모듈별 추가 필드 결정
    category = _resolveCategory(toolName)
    extra = _MODULE_STRIP.get(category, frozenset())
    stripFields = _STRIP_FIELDS | extra

    pruned = _pruneValue(data, stripFields, depth=0)

    # 배열 축소 (JSON 내 리스트가 20개 초과 시)
    pruned = _shrinkArrays(pruned, maxItems=20)

    text = json.dumps(pruned, ensure_ascii=False, indent=2, default=str)
    if len(text) > maxChars:
        return f"[PARTIAL] 결과가 잘렸습니다.\n{text[:maxChars]}"
    return text


def _pruneValue(value: Any, stripFields: frozenset[str], depth: int) -> Any:
    """재귀적 필드 제거."""
    if depth > 8:
        return value
    if isinstance(value, dict):
        return {k: _pruneValue(v, stripFields, depth + 1) for k, v in value.items() if k not in stripFields}
    if isinstance(value, list):
        return [_pruneValue(item, stripFields, depth + 1) for item in value]
    return value


def _shrinkArrays(value: Any, maxItems: int = 20) -> Any:
    """재귀적으로 배열 길이를 maxItems까지 축소."""
    if isinstance(value, dict):
        return {k: _shrinkArrays(v, maxItems) for k, v in value.items()}
    if isinstance(value, list):
        if len(value) > maxItems:
            kept = [_shrinkArrays(item, maxItems) for item in value[:maxItems]]
            kept.append({"_note": f"{len(value) - maxItems}개 항목 생략"})
            return kept
        return [_shrinkArrays(item, maxItems) for item in value]
    return value


def _resolveCategory(toolName: str) -> str:
    """도구 이름에서 카테고리 추출."""
    if toolName in ("finance", "get_data", "compute_ratios"):
        return "finance"
    if toolName in ("explore", "show", "search_data"):
        return "explore"
    if toolName in ("report", "get_report"):
        return "report"
    return ""
