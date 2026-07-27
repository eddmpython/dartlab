"""GATE — claim ↔ ref 매칭 검증 (programmatic, LLM 없음).

verify_answer 도구의 검증 로직과 통합 SSOT. 답안 본문의 material claim 을 추출하고
`<kindRef:id>` 토큰 또는 같은 줄 인접한 ref 종류를 매칭해 검증한다 (P-revised: 단일 형식).

차단 사유:
- emit_result_missing: WORK 가 executionRef 만 만들고 emit_result 로 valueRef/tableRef/dateRef 를 안 발급
- unsupported_numeric_claim: 숫자 claim 에 valueRef/tableRef/executionRef 매칭 없음
- unsupported_date_claim: 날짜 claim 에 dateRef 매칭 없음
- missing_ranking_table_ref: 후보·랭킹 답변에 tableRef 없음
- missing_required_evidence: 선택 skill 의 requiredEvidence 가 발급 ref kinds 에 충족 안 됨
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from dartlab.ai.contracts import Ref, TraceEvent

from .state import WorkbenchState

_CODE_SPAN_RE = re.compile(r"`[^`]*`")
_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_REF_KIND = r"value|table|execution|date|web|artifact|api|skill|verify|dataset|doc"
# 단일 형식 — `<kindRef:id>` (angle bracket + Ref 접미사). markdown link 문법 충돌 회피
# + LLM 자작 fake token 차단. 이전 `[kind:id]` 사각괄호 형식 폐기 (P-revised).
_REF_TOKEN_RE = re.compile(rf"<({_REF_KIND})Ref:[^>]+>")
_BROAD_REF_TOKEN_RE = re.compile(rf"<({_REF_KIND})Ref:([^>]+)>")
_MATERIAL_NUMBER_RE = re.compile(r"\d[\d,.]*\s?(?:조원|억원|원|%|배|건|개|위|Q[1-4])")
_DATE_RE = re.compile(r"(?:20\d{2}|19\d{2})(?:[-./]\d{1,2})?(?:[-./]\d{1,2})?(?:Q[1-4])?|\d{1,2}분기")
_MATERIAL_DATE_TERMS = ("기준", "최신", "기간", "시점", "as of", "asof", "latest")
_RANKING_TERMS = ("순위", "상위", "후보", "랭킹")

_NUMBER_KINDS = {"valueRef", "tableRef", "executionRef"}
_DATE_KINDS = {"dateRef"}
_TABLE_KINDS = {"tableRef"}


def runGate(state: WorkbenchState) -> Iterator[TraceEvent]:
    """GATE 패스 — answer 의 숫자/날짜/표가 ref 로 뒷받침되는지 검증."""
    state.currentPass = "gate"
    yield TraceEvent(kind="pass_enter", data={"pass": "gate"})

    raw_text = state.answerText or ""
    text = _stripCode(raw_text)
    issues: list[str] = []

    ref_kinds = {r.kind for r in state.refs}
    # ref token 은 backtick code span 안에 들어가도 인식 — raw text 사용
    ref_token_kinds = _refTokenKinds(raw_text)

    # 1) emit_result 강제 — executionRef 가 있는데 value/table/date 가 0 이면 emit_result 누락
    has_execution = "executionRef" in ref_kinds
    has_emitted = bool(ref_kinds & {"valueRef", "tableRef", "dateRef"})
    if has_execution and not has_emitted and _hasMaterialNumber(text):
        issues.append("emit_result_missing")

    # 2) material number claim ↔ value/table/execution ref
    if _hasMaterialNumber(text) and not (ref_kinds & _NUMBER_KINDS) and not (ref_token_kinds & _NUMBER_KINDS):
        issues.append("unsupported_numeric_claim")

    # 3) material date claim ↔ dateRef
    if _hasMaterialDate(text) and not (ref_kinds & _DATE_KINDS) and not (ref_token_kinds & _DATE_KINDS):
        issues.append("unsupported_date_claim")

    # 4) ranking ↔ tableRef
    if _hasRankingClaim(text) and not (ref_kinds & _TABLE_KINDS) and not (ref_token_kinds & _TABLE_KINDS):
        issues.append("missing_ranking_table_ref")

    # 5) skill.requiredEvidence 동적 체크 — kind 이름 형태만 검사 (target/period/metric 같은 입력 항목은 제외)
    required = {ev for ev in state.requiredEvidence if ev.endswith("Ref") or ev in _KNOWN_KIND_ALIASES}
    normalized_required = {_normalizeRequiredKind(ev) for ev in required}
    missing = normalized_required - ref_kinds
    if missing:
        issues.append(f"missing_required_evidence:{sorted(missing)}")

    # 6) fake/truncated ref token 검증 — raw text 사용 (backtick code span 안에서도 검증)
    fake_tokens = _findFakeRefTokens(raw_text, state.refs)
    if fake_tokens:
        issues.append(f"fake_ref_token:{fake_tokens[:3]}")

    # numbers/dates 는 사용자 trace 에 노출용 통계 (material claim — stripped text)
    numbers = _MATERIAL_NUMBER_RE.findall(text)
    dates = _DATE_RE.findall(text)
    # ref token 카운트는 raw text 에서 (backtick 안도 포함)
    ref_tokens = _REF_TOKEN_RE.findall(raw_text)

    # 7) ref token 주변 context 추출 → state.claims 자동 발급 (raw text 사용)
    state.claims = _extractClaimsFromAnswer(raw_text, state.refs)

    state.gateIssues = issues
    state.gateBlocked = bool(issues)
    state.verification = {
        "numbers": len(numbers),
        "dates": len(dates),
        "refTokens": len(ref_tokens),
        "totalRefs": len(state.refs),
        "issues": issues,
        "ok": not issues,
    }

    state.refs.append(
        Ref(
            id="verify:answer",
            kind="verifyRef",
            title="answer verification",
            source="gate",
            payload={
                "ok": not issues,
                "issues": issues,
                "refKinds": sorted(ref_kinds),
            },
        )
    )

    yield TraceEvent(
        kind="gate_result",
        data={
            "pass": "gate",
            "blocked": state.gateBlocked,
            "issues": issues,
            "verification": state.verification,
        },
    )
    yield TraceEvent(kind="pass_exit", data={"pass": "gate"})


_KNOWN_KIND_ALIASES = {
    "skill",
    "api",
    "execution",
    "table",
    "value",
    "date",
    "web",
    "artifact",
    "verify",
    "dataset",
}


def _normalizeRequiredKind(name: str) -> str:
    """requiredEvidence 의 항목 이름을 ref kind 로 정규화."""
    if name.endswith("Ref"):
        return name
    if name in _KNOWN_KIND_ALIASES:
        return f"{name}Ref"
    return name


def _stripCode(text: str) -> str:
    return _CODE_SPAN_RE.sub("", _CODE_BLOCK_RE.sub("", str(text or "")))


def _hasMaterialNumber(text: str) -> bool:
    return bool(_MATERIAL_NUMBER_RE.search(text))


def _hasMaterialDate(text: str) -> bool:
    if not _DATE_RE.search(text):
        return False
    lowered = text.lower()
    return any(term in lowered for term in _MATERIAL_DATE_TERMS)


def _hasRankingClaim(text: str) -> bool:
    if not any(term in text for term in _RANKING_TERMS):
        return False
    return "|" in text or bool(_MATERIAL_NUMBER_RE.search(text))


def _refTokenKinds(text: str) -> set[str]:
    """답안 본문의 `<kindRef:id>` 토큰에서 ref kind 집합 추출."""
    kinds: set[str] = set()
    for match in _REF_TOKEN_RE.finditer(str(text or "")):
        kind_short = match.group(1)
        if kind_short:
            kinds.add(f"{kind_short}Ref")
    return kinds


def _prefixMatchesAtSegmentBoundary(refId: str, candidate: str) -> bool:
    """`candidate` 가 `refId` 의 앞부분이되 세그먼트 경계에서 끝나는지 본다.

    ref id 는 `value:005930:BS:총자산` 처럼 콜론으로 끊긴 구조라, 중간에서 아무렇게나 잘린
    앞부분은 다른 것을 가리킬 수 있다. 경계를 요구하지 않으면 글자 하나짜리 token 이 실재하는
    근거를 가리키는 것으로 통과한다.
    """
    if refId == candidate:
        return True
    return refId.startswith(f"{candidate}:")


def _findFakeRefTokens(text: str, refs: list[Ref]) -> list[str]:
    """답안에 박힌 ref token 중 state.refs id 와 매칭 안 되는 fake/truncated token 목록.

    감지 대상 (단일 `<kindRef:id>` 형식):
    - LLM 자작 fake (예: `<valueRef:value:samsung_latest_bs_total_assets:343>`)
    - LLM 이 잘라 박은 truncated (예: `<valueRef:value:samsung_bs_…>`)
    - kind 가 `valueRef:` 형태로 박혔지만 `value:` prefix 가 빠진 경우
    """
    state_ids = {ref.id for ref in refs}
    fake: list[str] = []
    seen: set[str] = set()
    for match in _BROAD_REF_TOKEN_RE.finditer(str(text or "")):
        kind_short = match.group(1)
        id_raw = match.group(2)
        if not kind_short or id_raw is None:
            continue
        id_part = id_raw.strip()
        # token 안에 truncate 표시 (`…` U+2026 또는 `...`) 가 있으면 무조건 fake
        if "…" in id_part or "..." in id_part:
            full = f"{kind_short}:{id_part}"
            if full not in seen:
                seen.add(full)
                fake.append(full)
            continue
        # state.refs id 형태는 `value:005930:BS:...` 즉 kind_short prefix 포함
        candidate_with_prefix = f"{kind_short}:{id_part}" if not id_part.startswith(f"{kind_short}:") else id_part
        # token 의 id_part 가 state.refs id 와 정확히 또는 prefix 매칭되는지
        if candidate_with_prefix in state_ids:
            continue
        if id_part in state_ids:
            continue
        # prefix 매칭은 세그먼트 경계(`:`)에서 끝나야 한다. 예전에는 아무 데서나 끊어도
        # 받아 줘서, 실재하는 id 의 첫 글자 하나만 적은 `<valueRef:v>` 가 진짜 인용으로
        # 통과했다. 모델이 받지도 않은 근거 표를 지어낼 수 있는 자리다.
        if any(_prefixMatchesAtSegmentBoundary(rid, candidate_with_prefix) for rid in state_ids):
            continue
        full = f"{kind_short}:{id_part}"
        if full not in seen:
            seen.add(full)
            fake.append(full)
    return fake


def _extractClaimsFromAnswer(text: str, refs: list[Ref]) -> list[dict]:
    """답안의 `<kindRef:id>` token 주변 context 를 claim dict 으로 직렬화.

    출력 형식: `[{"text": context, "refIds": [...], "kind": "numeric"|"date"|"ranking"|"narrative"}]`.
    같은 ref 가 여러 번 등장하면 첫 출현만 claim 으로 등록 (중복 제거).
    GATE 가 이미 검증한 ref kind 정보를 활용해 claim kind 분류.
    """
    if not text:
        return []
    state_ids = {ref.id for ref in refs}
    state_kind_by_id = {ref.id: ref.kind for ref in refs}
    # raw text 그대로 — backtick code span 안의 ref token 도 claim 으로 추출
    stripped = str(text)
    claims: list[dict] = []
    seen_ref_ids: set[str] = set()

    for match in _BROAD_REF_TOKEN_RE.finditer(stripped):
        kind_short = match.group(1)
        id_raw = match.group(2)
        if not kind_short or id_raw is None:
            continue
        id_part = id_raw.strip()
        if "…" in id_part or "..." in id_part:
            continue
        candidate = f"{kind_short}:{id_part}" if not id_part.startswith(f"{kind_short}:") else id_part
        refId = candidate if candidate in state_ids else (id_part if id_part in state_ids else None)
        if not refId:
            continue
        if refId in seen_ref_ids:
            continue
        seen_ref_ids.add(refId)

        # 주변 context 추출 (앞 80 char + 토큰 + 뒤 30 char)
        start = max(0, match.start() - 80)
        end = min(len(stripped), match.end() + 30)
        context = stripped[start:end].replace("\n", " ").strip()

        # claim kind 분류
        ref_kind = state_kind_by_id.get(refId, f"{kind_short}Ref")
        if ref_kind in {"valueRef", "tableRef", "executionRef"} and _hasMaterialNumber(context):
            claim_kind = "numeric"
        elif ref_kind == "dateRef":
            claim_kind = "date"
        elif _hasRankingClaim(context):
            claim_kind = "ranking"
        else:
            claim_kind = "narrative"

        claims.append(
            {
                "id": f"claim:{len(claims) + 1}",
                "text": context,
                "refIds": [refId],
                "kind": claim_kind,
            }
        )
    return claims
