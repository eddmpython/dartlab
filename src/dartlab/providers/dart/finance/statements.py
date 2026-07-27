"""재무제표 추출 파이프라인. 연결 우선, 별도 fallback.

P2 통합: 기존 statements/{parser,pipeline,types}.py 단일 모듈로 흡수.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    import polars as pl


# types
@dataclass
class StatementsResult:
    """재무제표 추출 결과 — BS/IS/CF DataFrame + 메타데이터."""

    corpName: str | None
    period: str  # "y" | "q" | "h"
    scope: str = "consolidated"  # "consolidated" | "separate"
    nYears: int = 0
    BS: pl.DataFrame | None = None  # 재무상태표
    IS: pl.DataFrame | None = None  # 손익계산서
    CF: pl.DataFrame | None = None  # 현금흐름표


# parser
_STATEMENT_PATTERNS = {
    "BS": r"재무상태표",
    "CI": r"포괄손익",
    # PNL 은 '포괄' 이 앞에 없는 '손익계산서' 만 매칭. 순서도 CI 뒤에 두어 이중 방어.
    "PNL": r"(?<!포괄)손익계산서",
    "SCE": r"자본변동표",
    "CF": r"현금흐름표",
}

_TEXT_STATEMENT_COLS = {"year", "report_type", "section_title", "section_content"}


def extractContent(
    report: pl.DataFrame,
    scope: str | None = None,
) -> tuple[str | None, str]:
    """보고서에서 재무제표 섹션 추출 (연결 우선, 별도 fallback).

    Capabilities:
        - ``section_title`` 의 ``연결재무제표`` substring 매칭으로 1 차 추출.
        - ``연결대상이 없어... 작성하지 않습니다`` 키워드 검출 시 연결 skip 후 별도로 진행.
        - 별도/개별 = ``재무제표`` ∧ ¬``연결`` ∧ ¬``주석`` 필터.
        - scope 명시 시 (consolidated / separate) 해당 쪽만 시도, fallback 없음.
        - 매칭 행이 여러 개면 첫 번째 ``section_content`` 채택.

    Args:
        report: 정기보고서 DataFrame. ``section_title``/``section_content`` 컬럼 필수.
            ``selectReport`` 결과를 그대로 전달.
        scope: ``None`` (연결 우선 + 별도 fallback, 기본) / ``"consolidated"`` (연결만, 없으면
            (None, "none")) / ``"separate"`` (별도만).

    Returns:
        tuple[str | None, str] — ``(content, scope)``. content = 재무제표 섹션 raw text.
        scope = ``"consolidated"``/``"separate"``/``"none"``. 추출 불가 → ``(None, "none")``.

    Example:
        >>> # report = selectReport(df, 2023, reportKind="annual")
        >>> # content, scope = extractContent(report)  # 연결 우선
        >>> # content, scope = extractContent(report, scope="separate")  # 별도만

    Guide:
        - "연결재무제표가 있으면 연결, 없으면 별도" → ``extractContent(report)`` (기본).
        - "은행계열 별도 재무제표 강제" → ``extractContent(report, scope="separate")``.
        - "연결만 있는지 검사" → ``(_, scope) = extractContent(report, scope="consolidated")``
          후 ``scope == "consolidated"`` 검사.

    SeeAlso:
        - ``extractConsolidatedContent`` — 하위 호환 wrapper (scope 무시).
        - ``splitStatements`` — 본 함수 결과 content 를 BS/IS/CF 로 분리.
        - ``statements`` — 본 함수의 일반적 호출자 (시계열 빌드).
        - ``dartlab.providers._common.reportSelector.selectReport`` — report 의 source.

    Requires:
        - polars — DataFrame 필터.
        - 외부 의존 없음 — 순수 텍스트 매칭.

    AIContext:
        Ask Workbench 가 "이 회사 작년 재무제표" 류 질문 처리 시 statements 파이프 내부에서
        호출. ``(None, "none")`` 반환 = "회사가 정기보고서를 제출 안 했거나 재무제표 섹션
        파싱 실패" — caller 가 사용자에게 "데이터 미수집" fallback. scope 메타로 "이 회사
        연결 vs 별도 재무제표" 답변 분기 가능.

    LLM Specifications:
        AntiPatterns:
            - ``연결대상이 없어`` 키워드가 다른 맥락 (예 "연결대상이 없어서 별도로 작성") 에서
              false positive 가능 — 사용자 검증 필요.
            - report 에 ``section_title``/``section_content`` 부재 → polars KeyError. caller
              는 ``selectReport`` 결과만 직접 전달해야 안전.
            - 매칭 행 여러 개일 때 첫 번째만 → 동일 회사의 다중 정기보고서 우선순위 모호.
        OutputSchema:
            - tuple[str | None, str] — content 본문 + scope 라벨 3 종.
        Prerequisites:
            - report DataFrame 이 정기보고서 row + section 컬럼 보유 (selectReport 정상 결과).
        Freshness:
            - report 데이터 시점 의존. 본 함수 자체는 무상태.
        Dataflow:
            - selectReport → 본 함수 → splitStatements → extractAccounts → DataFrame.
        TargetMarkets:
            - KR (DART) 정기보고서. EDGAR 10-K 의 financial statements 와 별개.

    Raises:
        없음.
    """
    if scope != "separate":
        cons = report.filter(
            pl.col("section_title").str.contains("연결재무제표") & ~pl.col("section_title").str.contains("주석")
        )
        if cons.height > 0:
            content = cons["section_content"][0]
            # "연결대상이 없어 연결재무제표를 작성하지 않습니다" 처리
            hasNoSub = "연결대상" in content and ("없어" in content or "없으므로" in content)
            if not hasNoSub:
                if scope == "consolidated":
                    return content, "consolidated"
                return content, "consolidated"

        if scope == "consolidated":
            return None, "none"

    # 별도/개별 재무제표
    sep = report.filter(
        pl.col("section_title").str.contains("재무제표")
        & ~pl.col("section_title").str.contains("연결")
        & ~pl.col("section_title").str.contains("주석")
    )
    if sep.height > 0:
        return sep["section_content"][0], "separate"

    return None, "none"


def extractConsolidatedContent(report: pl.DataFrame) -> str | None:
    """보고서에서 연결재무제표 섹션 내용 (content only) 추출 — ``extractContent`` 의 단순 wrapper.

    Capabilities:
        - ``extractContent(report)`` (scope=None) 호출 후 content 만 반환.
        - scope 메타데이터 버림 (하위 호환 API).
        - 추출 실패 → None.

    Args:
        report: 정기보고서 DataFrame (``selectReport`` 결과).

    Returns:
        str | None — 재무제표 content 본문. 추출 불가 → None.

    Example:
        >>> # content = extractConsolidatedContent(report)
        >>> # if content is None: skip

    Guide:
        - "scope 구분 불필요, content 만 필요" → 본 함수.
        - "scope 도 같이 필요" → ``extractContent(report)`` 직접 사용.

    SeeAlso:
        - ``extractContent`` — 본 함수의 본체 (scope 반환 포함).
        - ``splitStatements`` — 본 함수 결과를 받아 BS/IS/CF 로 분리.

    Requires:
        - polars — DataFrame 필터 (extractContent 경유).
        - 외부 의존 없음.

    AIContext:
        Workbench 가 scope 정보 무시하고 content 만 처리하는 단순 경로에서 호출. 새 코드는
        ``extractContent`` 사용 권장 — scope 정보가 답변 품질 향상 (예 "이 회사 연결 vs 별도").
        본 함수는 기존 코드 하위 호환 유지용.

    LLM Specifications:
        AntiPatterns:
            - scope 정보가 필요한데 본 함수 사용 → 정보 누락. caller 가 ``extractContent``
              로 migrate.
        OutputSchema:
            - 1 스칼라. str | None.
        Prerequisites:
            - ``extractContent`` 의 사전조건 동일.
        Freshness:
            - report 데이터 시점 의존. 본 함수 무상태.
        Dataflow:
            - report → ``extractContent`` → 본 함수 → caller (content only).
        TargetMarkets:
            - KR (DART) 정기보고서.

    Raises:
        없음.
    """
    content, scope = extractContent(report)
    return content


def splitStatements(content: str) -> dict[str, str]:
    """재무제표 content 본문을 5 종 제표 (BS/CI/PNL/SCE/CF) 별 텍스트로 분리.

    Capabilities:
        - 라인 단위로 ``_STATEMENT_PATTERNS`` 5 정규식 매칭 (재무상태표/포괄손익/손익계산서/
          자본변동표/현금흐름표).
        - 매칭 라인 종류 3 가지 — 독립 행 (2024+), 테이블 단일 셀 (~2023), 공백 삽입 변형 (``재 무 상 태 표``).
        - 공백 모두 제거 후 패턴 매칭 (``re.sub(r"\\s+", "", line)``).
        - 같은 키 중복 등장 시 뒤에 나온 게 우선 (이중 방어).
        - 분리 = 각 헤더 위치를 start/end 로 사용해 그 사이 lines slice.

    Args:
        content: ``extractContent`` 결과 content 본문 (다중 라인 raw text).

    Returns:
        dict[str, str] — 키 = ``{"BS", "PNL", "CI", "SCE", "CF"}`` 중 매칭된 것만. 값 = 해당
        제표 영역의 raw 텍스트 (다음 헤더 직전까지).

    Example:
        >>> from dartlab.providers.dart.finance.statements import splitStatements
        >>> content = "재무상태표\\n자산 100\\n손익계산서\\n매출 50"
        >>> parts = splitStatements(content)
        >>> "BS" in parts and "PNL" in parts
        True

    Guide:
        - "재무제표 텍스트를 BS/IS/CF 로 분리" → 본 함수.
        - "포괄손익 (CI) vs 당기순이익 (PNL) 구분" → ``parts.get("PNL")`` vs ``parts.get("CI")``.
        - "삼성전자 자본변동표만 보고싶다" → ``parts.get("SCE")``.

    SeeAlso:
        - ``_STATEMENT_PATTERNS`` (모듈 상수) — 5 종 정규식 SSOT.
        - ``extractContent`` — 본 함수 입력의 source.
        - ``dartlab.providers._common.tableParser.extractAccounts`` — 본 함수 결과 각 제표의 다음 단계 파서.

    Requires:
        - re (stdlib) — 정규식 매칭.
        - 외부 의존 없음 — 순수 텍스트 처리.

    AIContext:
        Workbench statements 파이프 내부 헬퍼. 사람이 직접 호출 X, ``statements`` 함수가 5 종
        제표 중 BS/IS (PNL) /CF 만 추출해 시계열 빌드. CI/SCE 는 본 함수 결과에 포함되지만
        파이프 다음 단계가 사용 X — 향후 cash 흐름 vs 포괄손익 비교 시 활용 가능.

    LLM Specifications:
        AntiPatterns:
            - 같은 키 (예 "재무상태표") 가 본문 안 여러 번 등장 → 뒤에 나온 것만 채택, 앞 부분
              데이터 누락 가능성.
            - 헤더 라인이 80 자 이상 → skip (긴 라인은 헤더 아닌 본문으로 간주).
            - 테이블 행 (``|``로 시작) 인데 셀이 여러 개 → skip (단일 셀만 헤더).
        OutputSchema:
            - dict[str, str] — 최대 5 키.
            - 키 = "BS" / "PNL" / "CI" / "SCE" / "CF" 중 매칭된 것만 (없는 키는 dict 에 미존재).
        Prerequisites:
            - content 가 ``\\n`` 라인 분리 가능, UTF-8 정상.
            - 재무제표 본문이 한국어 헤더 + 표 형식 (DART 표준).
        Freshness:
            - 정적 정규식. DART 양식 변경 시 ``_STATEMENT_PATTERNS`` 갱신 필요.
        Dataflow:
            - extractContent → 본 함수 → extractAccounts → DataFrame.
        TargetMarkets:
            - KR (DART) 한정.

    Raises:
        없음.
    """
    lines = content.split("\n")

    # 헤더 위치 찾기
    # 2024+: "2-1. 연결 재무상태표" (독립 행)
    # ~2023: "| 연결 재무상태표 |" (테이블 행, 셀 1개)
    # 일부 기업: "연 결 재 무 상 태 표" (공백 삽입)
    headers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or len(s) >= 80:
            continue

        # 테이블 행인 경우: 셀이 1개이고 키워드 포함 시에만 헤더로 인식
        if s.startswith("|"):
            cells = [c.strip() for c in s.split("|") if c.strip()]
            if len(cells) != 1:
                continue
            s = cells[0]

        # 공백 제거 후 패턴 매칭 ("재 무 상 태 표" → "재무상태표")
        sNoSpace = re.sub(r"\s+", "", s)
        for key, pattern in _STATEMENT_PATTERNS.items():
            if re.search(pattern, sNoSpace):
                headers.append((i, key))
                break

    # 중복 키 처리: 뒤에 나온 게 우선 (포괄손익 vs 손익계산서 구분)
    seen: dict[str, int] = {}
    uniqueHeaders: list[tuple[int, str]] = []
    for idx, key in headers:
        if key in seen:
            uniqueHeaders[seen[key]] = (idx, key)
        else:
            seen[key] = len(uniqueHeaders)
            uniqueHeaders.append((idx, key))

    result: dict[str, str] = {}
    for j, (startIdx, key) in enumerate(uniqueHeaders):
        if j + 1 < len(uniqueHeaders):
            endIdx = uniqueHeaders[j + 1][0]
        else:
            endIdx = len(lines)
        result[key] = "\n".join(lines[startIdx:endIdx])

    return result


# pipeline
def statements(
    stockCode: str,
    ifrsOnly: bool = True,
    period: str = "y",
    scope: str | None = None,
) -> StatementsResult | None:
    """재무제표 (BS / IS / CF) 다년 시계열 ``StatementsResult`` 빌드 — finance 엔진 본체.

    Capabilities:
        - ``loadData(stockCode)`` 로 정기보고서 parquet 로드 후 연도별 ``selectReport`` 반복.
        - 각 보고서 → ``extractContent`` → ``splitStatements`` → ``extractAccounts`` 파이프.
        - period = ``"y"`` (사업보고서) / ``"q"`` (분기) / ``"h"`` (반기) 별 reportKind 매핑.
        - ``ifrsOnly=True`` 시 2011 년 이전 (K-GAAP) skip.
        - scope = consolidated (연결) / separate (별도) / None (자동) — ``extractContent`` 위임.
        - 동일 key (year 또는 reportType) 중복 시 첫 결과 보존 (선반영 원칙).
        - 항목 직접 매칭 — 동일 항목명 → 동일 row, 연도 컬럼 wide 변환.
        - BS/IS/CF 어느 것도 데이터 없음 → None.

    Args:
        stockCode: KR 종목코드 6 자리.
        ifrsOnly: ``True`` → K-IFRS 도입 (2011~) 이후만. ``False`` → 전체 연도 (K-GAAP 포함).
        period: ``"y"`` (사업보고서 annual) / ``"q"`` (분기) / ``"h"`` (반기). 미정의 키 → ``"y"`` fallback.
        scope: ``None`` (기본, 연결 우선) / ``"consolidated"`` / ``"separate"``.

    Returns:
        ``StatementsResult`` — corpName / period / scope / nYears / BS / IS / CF (각 pl.DataFrame
        또는 None). 데이터 부족 시 None.

    Example:
        >>> from dartlab.providers.dart.finance.statements import statements
        >>> r = statements("005930", period="y")  # 삼성전자 연도별 BS/IS/CF
        >>> r is None or r.nYears >= 0
        True

    Guide:
        - "삼성전자 5 년 재무제표" → ``statements("005930", period="y")``.
        - "분기 단위 손익" → ``statements("005930", period="q").IS``.
        - "별도 재무제표 강제" → ``statements("005930", scope="separate")``.
        - "K-GAAP 포함 장기 시계열" → ``ifrsOnly=False``.
        - "삼성전자 vs LG전자 매출 추이 비교" → 두 회사 ``statements`` 호출 후 IS 의 "매출액" 행 join.

    SeeAlso:
        - ``StatementsResult`` (dataclass) — 본 함수 반환 타입.
        - ``extractContent`` / ``splitStatements`` — 파이프 단계.
        - ``dartlab.providers._common.tableParser.extractAccounts`` — 항목/금액 파싱.
        - ``dartlab.providers._common.reportSelector.selectReport`` — 정기보고서 선택.

    Requires:
        - polars — DataFrame.
        - dartlab.core.dataLoader — ``loadData`` + ``PERIOD_KINDS``.
        - dartlab.providers._common.reportSelector — ``selectReport`` + ``parsePeriodKey``.
        - dartlab.providers._common.tableParser — ``extractAccounts``.

    AIContext:
        Workbench 재무 토픽의 entry point. "이 회사 매출/순이익 추이" / "EPS / ROE" / "자산총계
        변화" 질문 처리 시 본 함수가 반환한 IS/BS 에서 항목 row 를 lookup → 시계열 답변.
        None 반환 시 caller 는 "재무제표 미수집" fallback. 항목명 한국어 (예 "매출액") → AI 가
        영문 라벨로 변환해 답변 가능.

    LLM Specifications:
        AntiPatterns:
            - 정기보고서 parquet 결락 (gather 미수집) → None. caller 는 미수집 가능성 의심.
            - ifrsOnly=True 인데 2011 년 이전만 데이터 → None. caller 는 ifrsOnly=False 재시도.
            - period="q" 인데 분기보고서 미제출 (소규모 회사) → 매우 적은 데이터 또는 None.
            - 항목명 변화 (예 "매출액" → "수익(매출액)") → row 가 둘로 분리 (회계기준 변경 영향).
              caller 는 항목 fuzzy matching 필요.
        OutputSchema:
            - 1 StatementsResult instance.
            - BS/IS/CF: pl.DataFrame — "항목" 컬럼 + 연도/분기 wide columns (Float64).
            - corpName: str | None / nYears: int / scope: "consolidated" | "separate".
        Prerequisites:
            - gather (정기보고서) 가 stockCode 에 대해 1 회 이상 수집됨.
            - K-IFRS 2011~ + DART standard 표 형식.
        Freshness:
            - gather 수집 시점. 본 함수 자체는 무상태.
        Dataflow:
            - loadData → selectReport → extractContent → splitStatements → extractAccounts →
              본 함수 (시계열 빌드) → caller (AI 답변).
        TargetMarkets:
            - KR (DART) 한정. EDGAR 의 ``finance.scanAccount`` (XBRL 기반) 가 동등 함수
              (다른 파이프).

    Raises:
        없음.
    """
    return _statementsFromFinancePivot(stockCode, period=period, scope=scope, ifrsOnly=ifrsOnly)


# 공개 scope 이름과 pivot 의 재무제표 구분 코드 사이 대응. 연결이 기본이고, 없으면 pivot 이
# 알아서 별도로 내려간다.
_SCOPE_TO_FS_DIV = {None: "CFS", "consolidated": "CFS", "separate": "OFS"}

# K-IFRS 의무 적용 첫 해. 그 이전은 K-GAAP 이라 계정 구조가 달라 한 시계열에 섞으면 안 된다.
_IFRS_FIRST_YEAR = 2011


def _statementsFromFinancePivot(
    stockCode: str, *, period: str, scope: str | None = None, ifrsOnly: bool = True
) -> StatementsResult | None:
    """finance pivot 으로 StatementsResult 를 구성한다.

    예전에는 `stockCode` 와 `period` 만 넘기고 `scope` 와 `ifrsOnly` 를 통째로 버렸다. 그래서
    `statements(code, scope="separate")` 가 연결 재무제표를 돌려주면서 결과에는 "consolidated"
    라고 적었다. 문서의 "별도 재무제표 강제" 예제가 정확히 반대로 동작한 셈이다. 배선은
    pivot 의 `fsDivPref` 로 이미 있었고 연결만 안 돼 있었다.
    """
    from dartlab.providers.dart.finance.pivot import buildAnnual, buildTimeseries

    fsDivPref = _SCOPE_TO_FS_DIV.get(scope, "CFS")
    result = (
        buildAnnual(stockCode, fsDivPref=fsDivPref)
        if period == "y"
        else buildTimeseries(stockCode, fsDivPref=fsDivPref)
    )
    if result is None:
        return None
    series, keys = result
    if ifrsOnly:
        keep = [i for i, key in enumerate(keys) if _isIfrsEraKey(key)]
        if len(keep) != len(keys):
            keys = [keys[i] for i in keep]
            series = {
                stmt: {name: [values[i] for i in keep if i < len(values)] for name, values in rows.items()}
                for stmt, rows in series.items()
            }
    bs = _buildSeriesDf(keys, series.get("BS", {}))
    is_ = _buildSeriesDf(keys, series.get("IS", {}))
    cf = _buildSeriesDf(keys, series.get("CF", {}))
    if bs.is_empty() and is_.is_empty() and cf.is_empty():
        return None
    return StatementsResult(
        corpName=None,
        period=period,
        scope="separate" if fsDivPref == "OFS" else "consolidated",
        nYears=len(keys),
        BS=bs,
        IS=is_,
        CF=cf,
    )


def _isIfrsEraKey(key: str) -> bool:
    """기간 key 가 K-IFRS 시대(2011~)인지 본다. 연도를 못 읽으면 버리지 않는다."""
    head = str(key)[:4]
    if not head.isdigit():
        return True
    return int(head) >= _IFRS_FIRST_YEAR


def _buildSeriesDf(sortedKeys: list[str], data: dict[str, list[float | None]]) -> pl.DataFrame:
    rows = []
    for name, values in data.items():
        row: dict[str, object] = {"항목": name}
        for i, key in enumerate(sortedKeys):
            row[key] = values[i] if i < len(values) else None
        rows.append(row)
    if not rows:
        return pl.DataFrame()
    schema = {"항목": pl.Utf8}
    for key in sortedKeys:
        schema[key] = pl.Float64
    return pl.DataFrame(rows, schema=schema)


def _buildDf(
    sortedKeys: list[str],
    data: dict[str, tuple[dict, list]],
) -> pl.DataFrame:
    """항목 직접 매칭 방식으로 DataFrame 생성."""
    nameData: dict[str, dict[str, float | None]] = {}
    accountOrder: list[str] = []

    for key in sortedKeys:
        if key not in data:
            continue
        accounts, order = data[key]
        for name in order:
            if name not in nameData:
                nameData[name] = {}
                accountOrder.append(name)
            amts = accounts[name]
            nameData[name][key] = amts[0] if amts else None

    rows = []
    for name in accountOrder:
        row: dict[str, object] = {"항목": name}
        for key in sortedKeys:
            row[key] = nameData[name].get(key)
        rows.append(row)

    if not rows:
        return pl.DataFrame()

    schema = {"항목": pl.Utf8}
    for key in sortedKeys:
        schema[key] = pl.Float64
    return pl.DataFrame(rows, schema=schema)
