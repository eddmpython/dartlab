"""마크다운 테이블 범용 파서 — docs section_content에서 표 추출.

DART 공시의 section_content는 마크다운 형식의 텍스트다.
`| cell | cell |` 패턴으로 테이블을 파싱한다.

특징:
- 여러 테이블이 한 섹션에 나올 수 있음
- 헤더가 여러 줄에 걸칠 수 있음 (multi-row header)
- 빈 셀 많음, 소계/총계 행 포함
- 셀 병합 시 공백이 이어짐
"""

from __future__ import annotations

import re


def _splitTableRow(line: str) -> list[str] | None:
    """'| a | b | c |' 한 줄을 셀 리스트로 분리. 테이블 행이 아니면 None."""
    line = line.strip()
    if not line.startswith("|") or not line.endswith("|"):
        return None
    # 맨 앞/뒤 | 제거 후 split
    cells = [c.strip() for c in line[1:-1].split("|")]
    return cells


def _isSeparatorRow(cells: list[str]) -> bool:
    """`| --- | --- |` 같은 구분선 행인지."""
    return all(re.fullmatch(r"-+", c) or c == "" for c in cells) and any("-" in c for c in cells)


def extractTables(content: str) -> list[list[list[str]]]:
    """마크다운 텍스트에서 모든 테이블을 추출.

    Capabilities:
        파이프 (`|`) 기반 마크다운 테이블을 줄 단위 파싱해 row × cell 2D 리스트로 추출. 구분선
        (`---`) 행은 자동 제거, 1 행짜리 노이즈 테이블은 폐기.

    Returns
    -------
    list[list[list[str]]]
        테이블 리스트. 각 테이블은 행(list) × 셀(str).
        구분선 행(---)은 제거됨.

    Raises:
        없음.

    Example:
        >>> from dartlab.providers.dart.tableRows import extractTables
        >>> tables = extractTables("|a|b|\\n|---|---|\\n|1|2|")
        >>> tables
        [[['a', 'b'], ['1', '2']]]

    Guide:
        ``findTableByHeaders`` 가 본 함수 결과에서 키워드 매칭 테이블을 골라낸다. 1 행 헤더만
        있는 비정형 표는 자동 제거 (len(t) >= 2 필터).

    When:
        ``extractRawMaterialEdges`` 가 docs 본문 → 테이블 추출 1 단계로 사용.

    How:
        줄 단위 split → ``_splitTableRow`` 로 셀 분리 → 구분선 검출 → 빈 줄 도달 시 한 테이블
        종료 → 1 행 이상 테이블만 수집.

    Requires:
        - 외부 의존 없음 — 순수 텍스트 파싱.

    See Also:
        - ``dartlab.providers.dart.tableRows.findTableByHeaders`` : 본 결과 검색
        - ``dartlab.providers.dart.tableRows.tableToRowDicts`` : 헤더 기반 dict 변환

    AIContext:
        AI 가 docs 본문 표를 직접 다루지 않는다 (table_parser 가 처리한 후 IndustryEdge 형태로
        받음). 본 함수는 내부 헬퍼.
    """
    if not content:
        return []

    tables: list[list[list[str]]] = []
    current: list[list[str]] = []

    for line in content.split("\n"):
        cells = _splitTableRow(line)
        if cells is None:
            # 테이블 종료
            if current:
                tables.append(current)
                current = []
            continue

        if _isSeparatorRow(cells):
            continue  # 구분선은 skip

        current.append(cells)

    if current:
        tables.append(current)

    # 1행짜리 노이즈 제거
    return [t for t in tables if len(t) >= 2]


def tableToRowDicts(table: list[list[str]]) -> list[dict[str, str]]:
    """테이블을 헤더 기반 dict 리스트로 변환.

    Capabilities:
        2D 테이블의 첫 행을 헤더로 삼아 각 데이터 행을 {header: value} dict 로 변환. 빈 셀은
        이전 행 값 상속 (마크다운 병합 효과).

    첫 번째 행을 헤더로 간주. 이전 행 값이 빈 셀은 상속(병합 효과).

    Returns
    -------
    list[dict[str, str]]
        각 row = {header: value}

    Raises:
        없음 — 빈/단일 행 테이블은 빈 리스트.

    Example:
        >>> tableToRowDicts([["A","B"],["1","2"]])
        [{'A': '1', 'B': '2'}]

    Guide:
        헤더가 메타 행 ("(단위: 억원)") 등으로 시작하면 ``findTableByHeaders`` 로 헤더 행을 찾아 슬라이스.

    When:
        단순 테이블 → dict 변환 (헤더 0 행이 명확할 때).

    How:
        첫 행 헤더 → 데이터 행 루프 → 열 수 padding → 빈 셀 → prev 상속 → dict.

    Requires:
        - 외부 의존 없음.

    See Also:
        - ``dartlab.providers.dart.tableRows.findTableByHeaders`` : 헤더 행 검색
        - ``dartlab.providers.dart.panel.text.gridToRowDicts`` : panel XML 격자(rowspan 전개) dict 변환

    AIContext:
        AI 직접 호출 없음 (내부 헬퍼).
    """
    if not table or len(table) < 2:
        return []

    header = table[0]
    rows: list[dict[str, str]] = []
    prev: list[str] = ["" for _ in header]

    for raw in table[1:]:
        # 열 수 맞추기
        padded = raw[: len(header)] + [""] * (len(header) - len(raw))
        # 빈 셀은 이전 값 상속 (병합 셀 처리)
        row = []
        for i, v in enumerate(padded):
            if v:
                row.append(v)
                prev[i] = v
            else:
                row.append(prev[i])
        rows.append(dict(zip(header, row)))

    return rows


def findTableByHeaders(
    tables: list[list[list[str]]],
    requiredHeaders: list[str],
    maxHeaderRows: int = 3,
) -> tuple[list[list[str]], int] | None:
    """헤더에 특정 키워드가 모두 포함된 테이블을 찾는다.

    "(단위: 억원)" 같은 메타 행이 첫 줄에 올 수 있으므로 상위 maxHeaderRows까지 탐색.

    Parameters
    ----------
    tables : list of tables
        extractTables 결과.
    requiredHeaders : list[str]
        헤더에 포함되어야 하는 키워드. 부분 매칭.
    maxHeaderRows : int
        어느 행까지 헤더로 시도할지.

    Returns
    -------
    tuple[list[list[str]], int] | None
        (매칭된 테이블, 실제 헤더 행 인덱스).

    Raises:
        없음 — 매칭 실패 시 None.

    Example:
        >>> from dartlab.providers.dart.tableRows import extractTables, findTableByHeaders
        >>> tables = extractTables(docContent)
        >>> findTableByHeaders(tables, ["매입처", "비중"])[1]
        0

    Requires:
        - 외부 의존 없음.
    """
    for table in tables:
        if not table:
            continue
        limit = min(maxHeaderRows, len(table))
        for hi in range(limit):
            headerText = " ".join(table[hi]).lower()
            if all(kw.lower() in headerText for kw in requiredHeaders):
                return table, hi
    return None


def parseAmount(text: str) -> float | None:
    """'138,272' 같은 숫자 문자열을 float로 변환.

    Capabilities:
        쉼표/공백 포함 숫자 문자열을 float 로 변환. 빈 문자열 / "-" / 변환 불가 시 None.
        DART 표의 천 단위 쉼표 처리에 특화.

    Args:
        text: 입력 문자열 (예: "138,272").

    Returns:
        float 변환 결과 또는 None.

    Raises:
        없음.

    Example:
        >>> parseAmount("138,272"), parseAmount("-")
        (138272.0, None)

    Guide:
        통화 단위 (억원/백만원) 는 호출자가 별도 정규화. 본 함수는 순수 숫자 파싱.

    When:
        ``extractRawMaterialEdges`` 가 매입액 셀 값 변환 시.

    How:
        쉼표/공백 strip → "-" 체크 → float() try/except → None 폴백.

    Requires:
        - 외부 의존 없음.

    See Also:
        - ``dartlab.providers.dart.tableRows.parsePercent`` : 비율 셀 변환

    AIContext:
        AI 직접 호출 없음.
    """
    if not text:
        return None
    cleaned = text.replace(",", "").replace(" ", "").strip()
    if not cleaned or cleaned == "-":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parsePercent(text: str) -> float | None:
    """'18.5%' 같은 비율을 float(0~100)로 변환.

    Capabilities:
        '%' 접미사 포함 비율 문자열을 0~100 float 로 변환. 빈 문자열 / "-" / 변환 불가 시 None.

    Args:
        text: 입력 문자열 (예: "18.5%").

    Returns:
        float (0~100) 또는 None.

    Raises:
        없음.

    Example:
        >>> parsePercent("18.5%"), parsePercent("-")
        (18.5, None)

    Guide:
        결과는 0~100 스케일 (0.185 가 아닌 18.5). 0~1 스케일 필요 시 호출자가 /100.

    When:
        ``extractRawMaterialEdges`` 가 매입 비중 셀 값 변환 시.

    How:
        '%' / 쉼표 strip → "-" 체크 → float() try/except.

    Requires:
        - 외부 의존 없음.

    See Also:
        - ``dartlab.providers.dart.tableRows.parseAmount`` : 숫자 셀 변환

    AIContext:
        AI 직접 호출 없음.
    """
    if not text:
        return None
    cleaned = text.replace("%", "").replace(",", "").strip()
    if not cleaned or cleaned == "-":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


# ── 회사명 추출 ──

# 매입처 셀에서 회사명 분리 (쉼표, 및, 등)
_SPLIT_RE = re.compile(r"[,、]|\s+(?:및|and)\s+")
# 뒤에 붙는 " 등", "등", "(...)" 제거
_CLEAN_RE = re.compile(r"(\s*등\s*$|\s*\([^)]*\)\s*$)")


def extractCorpNames(cell: str) -> list[str]:
    """'Qualcomm, MediaTek' 또는 '솔브레인㈜, 동우화인켐㈜ 등' 같은 셀에서 회사명을 분리.

    Capabilities:
        쉼표 / 점 / "및"·"and" 구분자로 셀을 분리하고 끝의 " 등" / "( ... )" 접미사를 제거.
        2 글자 이상 회사명만 남김. ㈜/(주) 등 원본 정규형 보존 (정규화는 ``normalizeCorpName``).

    Returns
    -------
    list[str]
        정제된 회사명 리스트 (㈜/(주) 포함 원본 유지).

    Raises:
        없음.

    Example:
        >>> extractCorpNames("솔브레인㈜, 동우화인켐㈜ 등")
        ['솔브레인㈜', '동우화인켐㈜']

    Guide:
        반환 회사명은 정규형 (㈜ 포함) 그대로. KindList 매칭 전 ``normalizeCorpName`` 으로 ㈜ 제거.

    When:
        ``extractRawMaterialEdges`` 가 "매입처" 셀에서 공급사 다중 추출 시.

    How:
        끝 "등" / "(...)" 제거 → 쉼표/점/"및"/"and" split → 각 토큰 trim → 2 글자 이상 필터.

    Requires:
        - 외부 의존 없음.

    See Also:
        - ``dartlab.providers.dart.tableRows.normalizeCorpName`` : 매칭용 정규화

    AIContext:
        AI 직접 호출 없음.
    """
    if not cell:
        return []

    # 맨 끝 "등" 제거
    cleaned = _CLEAN_RE.sub("", cell).strip()

    # 쉼표/및로 분리
    parts = [p.strip() for p in _SPLIT_RE.split(cleaned) if p.strip()]

    # 각 이름에서 끝 "등" 제거
    result: list[str] = []
    for p in parts:
        p = _CLEAN_RE.sub("", p).strip()
        if p and len(p) >= 2:
            result.append(p)

    return result


def normalizeCorpName(name: str) -> str:
    """㈜/(주)/주식회사 제거하여 정규화 (매칭용).

    Capabilities:
        ㈜ / (주) / 주식회사 접미·접두사를 제거해 KindList 회사명과 매칭 가능한 정규형 반환.
        결과는 공백 strip.

    Args:
        name: 원본 회사명 (예: "솔브레인㈜").

    Returns:
        정규화된 이름 (예: "솔브레인").

    Raises:
        없음.

    Example:
        >>> normalizeCorpName("솔브레인㈜")
        '솔브레인'

    Guide:
        본 함수는 매칭용 — UI 표시는 원본 ㈜ 포함 형태 유지 권장.

    When:
        ``extractRawMaterialEdges`` 가 매입처 셀 → KindList 룩업 매칭 직전에.

    How:
        ㈜ / (주) / 주식회사 substring 모두 제거 → strip.

    Requires:
        - 외부 의존 없음.

    See Also:
        - ``dartlab.providers.dart.tableRows.extractCorpNames`` : 회사명 분리

    AIContext:
        AI 직접 호출 없음.
    """
    if not name:
        return ""
    n = name.strip()
    for suffix in ["㈜", "(주)", "주식회사"]:
        n = n.replace(suffix, "")
    return n.strip()
