"""전종목 단일 계정/비율 연간 시계열 배치 추출.

finance parquet 2,744개를 병렬 읽기하여
특정 snakeId 하나의 전종목 × 연도 시계열 DataFrame을 생성한다.

Q4 사업보고서 thstrm_amount = 연간 누적값이므로 standalone 변환 불필요.

설계: ThreadPool I/O + 파일별 즉시 필터(CFS+account 매칭)
      → concat 대상 ~25K행 → 메모리 +135MB, 속도 ~3초
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

import polars as pl

from dartlab.core.accounts.data import loadAccounts
from dartlab.core.memory import withMemoryBudget
from dartlab.providers.dart.finance.mapper import (
    ACCOUNT_NAME_SYNONYMS,
    ID_SYNONYMS,
)

_log = logging.getLogger(__name__)


_REPRT_TO_Q = {"1분기": "Q1", "2분기": "Q2", "3분기": "Q3", "4분기": "Q4"}
_SCAN_ACCOUNT_MEMORY_BUDGET_MB = 800
_SCAN_ACCOUNT_BASE_COLS = (
    "bsns_year",
    "reprt_nm",
    "sj_div",
    "fs_nm",
    "account_id",
    "account_nm",
    "thstrm_amount",
    "thstrm_add_amount",
)


def _emptyStockCodeFrame() -> pl.DataFrame:
    """scan 계열 빈 결과의 join key 타입을 고정한다."""
    return pl.DataFrame(schema={"stockCode": pl.Utf8})


def _scanAccountColumns(columnNames: list[str], scCol: str) -> list[str]:
    """scanAccount 경로에서 필요한 컬럼만 반환한다."""
    available = set(columnNames)
    cols = [scCol, *_SCAN_ACCOUNT_BASE_COLS]
    return [col for col in cols if col in available]


def _resolveSjDiv(snakeId: str) -> str:
    """sortOrder.json에서 snakeId → sjDiv 자동 결정."""
    from dartlab.core.utils.ordering import _ensureLoaded

    data = _ensureLoaded()
    for sjDiv in ("IS", "BS", "CF"):
        if snakeId in data.get(sjDiv, {}):
            return sjDiv
    msg = f"snakeId '{snakeId}'를 sortOrder.json에서 찾을 수 없습니다"
    raise ValueError(msg)


def _parseAmount(val: str | None) -> float | None:
    """문자열 금액 → float. 쉼표 제거, 빈값 → None."""
    from dartlab.providers.dart.parse.amount import parseAmount

    return parseAmount(val)


def _buildFastKeys(snakeId: str) -> set[str]:
    """snakeId에 매핑되는 모든 원본 키를 사전 수집 (O(1) set lookup)."""
    mappings = loadAccounts().get("mappings", {})

    directKeys: set[str] = set()
    for key, sid in mappings.items():
        if sid == snakeId:
            directKeys.add(key)

    allKeys = set(directKeys)
    for synonym, canonical in ACCOUNT_NAME_SYNONYMS.items():
        if canonical in directKeys:
            allKeys.add(synonym)

    for synonym, canonical in ID_SYNONYMS.items():
        if canonical in directKeys:
            allKeys.add(synonym)
            for prefix in ("ifrs-full_", "ifrs_", "dart_", "ifrs-smes_"):
                allKeys.add(prefix + synonym)

    for key in list(directKeys):
        for prefix in ("ifrs-full_", "ifrs_", "dart_", "ifrs-smes_"):
            allKeys.add(prefix + key)

    return allKeys


def _parseAmountCol(col: str) -> pl.Expr:
    """금액 문자열 컬럼 → Float64."""
    from dartlab.providers.dart.parse.amount import parseAmountExpr

    return parseAmountExpr(col)


def _resolveSnakeId(nameOrId: str) -> str:
    """한글 항목/영문 snakeId → 정규 snakeId 변환."""
    # 이미 snakeId면 그대로
    if nameOrId.isascii() and "_" in nameOrId:
        return nameOrId

    # SSOT mappings 로 한글 → snakeId 변환
    mappings = loadAccounts().get("mappings", {})
    # 한글명 우선
    normalizedNm = ACCOUNT_NAME_SYNONYMS.get(nameOrId, nameOrId)
    if normalizedNm in mappings:
        return mappings[normalizedNm]
    # 공백 제거 후 재시도
    noSpace = normalizedNm.replace(" ", "")
    if noSpace in mappings:
        return mappings[noSpace]
    # 영문 ID로도 시도
    stripped = nameOrId.lower().replace("-", "").replace(" ", "")
    normalizedId = ID_SYNONYMS.get(stripped, stripped)
    if normalizedId in mappings:
        return mappings[normalizedId]

    # 변환 실패 시 원본 반환 (이후 _resolveSjDiv에서 에러)
    return nameOrId


def _scanAccountFromMerged(
    scanPath: Path | None,
    snakeId: str,
    sjDiv: str,
    filterDivs: list[str],
    fsPref: str,
    fastKeys: set[str],
    *,
    freq: str = "Q",
    lazyFrame: pl.LazyFrame | None = None,
) -> pl.DataFrame | None:
    """단일 계정 시계열 추출 — 합본 또는 raw glob LazyFrame 모두 처리.

    scanPath 경로 (프리빌드 ``finance.parquet`` 또는 ``finance-lite.parquet``) 가
    있으면 그것을, 없으면 ``lazyFrame`` 주입 인자 (raw glob DuckDB 결과) 를 받아
    동일 후처리 (CFS/OFS · 분기 standalone · 종목 wide pivot) 적용.

    Pyodide(브라우저 WASM) 에서는 polars `scan_parquet` 이 미지원이라 pyarrow 로
    전체 로드 → `pl.from_arrow` 로 DataFrame 전환 후 동일 필터 연산. 원본 파일은
    `finance-lite.parquet`(18MB) 이므로 메모리 부담 없음.
    """
    from dartlab.core.dataLoader import _IS_PYODIDE

    try:
        if lazyFrame is not None:
            # raw glob fallback path (DuckDB 가 sj_div 필터까지만 push-down)
            # account 매칭은 polars 단에서 (fastKeys 에 `'` 등 SQL 특수문자 포함 안전)
            scCol = "stockCode"
            fastKeysList = list(fastKeys)
            lz = lazyFrame.select(_scanAccountColumns(lazyFrame.collect_schema().names(), scCol)).filter(
                pl.col("account_nm").is_in(fastKeysList) | pl.col("account_id").is_in(fastKeysList)
            )
            if freq == "Y":
                lz = lz.filter(pl.col("reprt_nm") == "4분기")
            df = lz.collect(engine="streaming")
        elif _IS_PYODIDE:
            import pyarrow.parquet as pq

            fastKeysList = list(fastKeys)
            # finance-lite 스키마 고정: stockCode, bsns_year, reprt_nm, sj_div, fs_nm,
            # account_id, account_nm, thstrm_amount, thstrm_add_amount
            schemaNames = pq.read_schema(str(scanPath)).names
            scCol = "stockCode" if "stockCode" in schemaNames else "stock_code"
            tbl = pq.read_table(str(scanPath), columns=_scanAccountColumns(schemaNames, scCol))
            pyodideFrame = cast(pl.DataFrame, pl.from_arrow(tbl))
            df = pyodideFrame.filter(
                pl.col("sj_div").is_in(filterDivs)
                & (pl.col("account_nm").is_in(fastKeysList) | pl.col("account_id").is_in(fastKeysList))
            )
            if freq == "Y":
                df = df.filter(pl.col("reprt_nm") == "4분기")
        else:
            schema = pl.scan_parquet(str(scanPath)).collect_schema()
            scCol = "stockCode" if "stockCode" in schema.names() else "stock_code"

            lz = (
                pl.scan_parquet(str(scanPath))
                .select(_scanAccountColumns(schema.names(), scCol))
                .filter(
                    pl.col("sj_div").is_in(filterDivs)
                    & (pl.col("account_nm").is_in(list(fastKeys)) | pl.col("account_id").is_in(list(fastKeys)))
                )
            )

            if freq == "Y":
                lz = lz.filter(pl.col("reprt_nm") == "4분기")

            df = lz.collect(engine="streaming")
    except (pl.exceptions.PolarsError, OSError, FileNotFoundError):
        return None

    if df.is_empty():
        return None

    # CFS/OFS 우선: 종목별로 연결재무제표가 있으면 연결만
    cfsLabel = "연결" if fsPref == "CFS" else "재무제표"
    hasCfs = df.filter(pl.col("fs_nm").str.contains(cfsLabel)).select(scCol).unique().to_series().to_list()
    hasCfsSet = set(hasCfs)

    # 연결 있는 종목은 연결만, 없는 종목은 전체
    if hasCfsSet:
        cfsPart = df.filter(pl.col(scCol).is_in(list(hasCfsSet)) & pl.col("fs_nm").str.contains(cfsLabel))
        ofsPart = df.filter(~pl.col(scCol).is_in(list(hasCfsSet)))
        df = pl.concat([cfsPart, ofsPart]) if not ofsPart.is_empty() else cfsPart

    if df.is_empty():
        return None

    # 금액 파싱
    df = df.with_columns(_parseAmountCol("thstrm_amount").alias("amount"))

    if freq == "Y":
        # 연간: thstrm_amount (4분기 사업보고서) 그대로
        parsed = df.filter(pl.col("amount").is_not_null())
        if parsed.is_empty():
            return None
        result = (
            parsed.select(
                pl.col(scCol).alias("stockCode"),
                pl.col("bsns_year").cast(pl.Utf8).alias("period"),
                pl.col("amount"),
            )
            .group_by(["stockCode", "period"])
            .agg(pl.col("amount").first())
        )
    else:
        # 분기별 standalone 계산 — Polars 벡터 연산
        df = df.with_columns(_parseAmountCol("thstrm_add_amount").alias("_addAmount"))
        df = df.filter(pl.col("amount").is_not_null())
        if df.is_empty():
            return None

        isBs = sjDiv == "BS"

        # period 컬럼 생성
        qMap = pl.DataFrame({"reprt_nm": list(_REPRT_TO_Q.keys()), "_qLabel": list(_REPRT_TO_Q.values())})
        df = df.join(qMap, on="reprt_nm", how="inner")
        df = df.with_columns((pl.col("bsns_year").cast(pl.Utf8) + pl.col("_qLabel")).alias("period"))

        if isBs:
            # BS: 잔액 그대로
            result = df.select(
                pl.col(scCol).alias("stockCode"),
                pl.col("period"),
                pl.col("amount"),
            )
        else:
            # IS/CF: 1~3분기 thstrm = standalone, 4분기 = thstrm - Q3 addAmount
            notQ4 = df.filter(pl.col("reprt_nm") != "4분기").select(
                pl.col(scCol).alias("stockCode"),
                pl.col("period"),
                pl.col("amount"),
            )

            q4 = df.filter(pl.col("reprt_nm") == "4분기")
            q3Add = df.filter(pl.col("reprt_nm") == "3분기").select(
                pl.col(scCol).alias("_sc"),
                pl.col("bsns_year").alias("_by"),
                pl.col("_addAmount").alias("_q3add"),
            )
            q4j = q4.join(q3Add, left_on=[scCol, "bsns_year"], right_on=["_sc", "_by"], how="left")
            q4j = q4j.with_columns(
                pl.when(pl.col("_q3add").is_not_null())
                .then(pl.col("amount") - pl.col("_q3add"))
                .otherwise(pl.col("amount"))
                .alias("amount")
            ).select(
                pl.col(scCol).alias("stockCode"),
                pl.col("period"),
                pl.col("amount"),
            )
            result = pl.concat([notQ4, q4j])

    return result


@withMemoryBudget(limitMb=_SCAN_ACCOUNT_MEMORY_BUDGET_MB)
def scanAccount(
    snakeId: str,
    *,
    sjDiv: str | None = None,
    fsPref: str = "CFS",
    freq: str = "Q",
) -> pl.DataFrame:
    """전종목 단일 계정 시계열 — dartlab scan 의 **원자 primitive**.

    scan 의 모든 복합 축 (profitability · growth · quality · liquidity 등) 은 이 함수의
    반환값을 **polars join + with_columns** 로 조합해 만들 수 있다. prebuild 된
    ``finance.parquet`` 한 파일을 lazy scan + push-down filter 로 한 번에 추출하므로
    2664 종목 전체가 수 초에 나온다. Python for 문 없음, iter_rows 없음.

    **사상**: 개별 계정 (원자) + ``scanRatio`` (비율) 조합이 **무궁무진**. AI 는 질문에
    맞춰 이 두 축을 자유롭게 엮어라. 복합 축 (scan("profitability") 등) 은 그저
    **자주 쓰는 프리셋** 일 뿐이다.

    Parameters
    ----------
    snakeId : str
        계정 식별자. 영문 snake_case (``"sales"``, ``"operating_profit"``,
        ``"net_income"``) 또는 한글 (``"매출액"``, ``"영업이익"``, ``"당기순이익"``)
        모두 가능. 지원 목록은 ``scanAccountList()``.
    sjDiv : str | None, optional
        재무제표 구분 (``"IS"`` · ``"CIS"`` · ``"BS"`` · ``"CF"``). None 이면 snakeId
        로부터 자동 판정 (sortOrder.json).
    fsPref : {"CFS", "OFS"}, default "CFS"
        연결(CFS) 우선 · 별도(OFS) 우선. 연결 없으면 별도 fallback.
    freq : {"Q", "Y"}, default "Q"
        ``"Q"`` = 분기 데이터 (``2025Q4`` · ``2025Q3`` 컬럼 — 가장 최신 마일스톤 포함).
        ``"Y"`` = 연간 (``2025`` · ``2024`` 컬럼). Company 엔진의 `freq` 와 일치.

    Returns
    -------
    df : pl.DataFrame
        2664 종목 행. 컬럼:

        - ``stockCode`` : str — 종목코드
        - 기간 컬럼들 : float — 금액 (원)
          * freq="Q": ``"2025Q4"`` · ``"2025Q3"`` · ``"2025Q2"`` · ``"2024Q4"`` · ...
          * freq="Y": ``"2025"`` · ``"2024"`` · ``"2023"`` · ...

        종목별 자기 최신 기간이 있는 컬럼에만 값, 없으면 null. sort / head /
        with_columns 로 바로 조작 가능한 wide 테이블.

    Examples
    --------
    **단순 랭킹** — "영업이익 큰 회사 10":

    >>> scanAccount("operating_profit", freq="Y").sort("2025", descending=True).head(10)

    **YoY 성장률 상위**:

    >>> df = scanAccount("sales", freq="Y")
    >>> df.with_columns(((pl.col("2025") - pl.col("2024")) / pl.col("2024") * 100).alias("yoy")).sort("yoy", descending=True).head(20)

    **다계정 조합** — "매출 > 1조인데 영업이익 역성장":

    >>> rev = scanAccount("sales", freq="Y").select(["stockCode", "2025"]).rename({"2025": "rev25"})
    >>> op  = scanAccount("operating_profit", freq="Y").select(["stockCode", "2024", "2025"]).rename({"2024": "op24", "2025": "op25"})
    >>> rev.join(op, on="stockCode").filter((pl.col("rev25") > 1e12) & (pl.col("op25") < pl.col("op24")))

    **분기 모멘텀** — "최근 분기 대비 전분기 증가":

    >>> df = scanAccount("operating_profit", freq="Q")  # 분기
    >>> df.with_columns(((pl.col("2025Q4") - pl.col("2025Q3")) / pl.col("2025Q3")).alias("qoq"))

    Notes
    -----
    - ``finance.parquet`` prebuild 사용 (첫 호출 자동 다운로드). Python loop 없음.
    - 종목별 최신 기간 자동 정렬 — **latestYear 글로벌 필터 버그 없음**.
    - pyodide 환경은 경량본 ``finance-lite.parquet`` (~18MB) 자동 사용.

    Guide
    -----
    **⛔ 광역 발굴 질문 ("투자할만한 회사" / "좋은 회사" / "요즘 투자하기 좋은") 에
    scanAccount 하나만 쓰고 끝내지 말 것.** 계정 하나는 원자이고, 발굴은 최소 3~4
    축 조합이다. 자세한 레시피 · 7 관점 스크리닝 · 5 단계 워크플로는
    :func:`scanRatio` 의 Guide 섹션이 SSOT — 그쪽을 먼저 읽고 본 함수를 원자로 끼워
    넣는 구조로 조합한다.

    **이 함수의 4 가지 사용 패턴**:

    1. **단일 축 랭킹** — ``scanAccount("X", freq="Y").sort("YYYY", desc).head(N)``
    2. **시계열 변화** — 두 기간 컬럼으로 YoY/QoQ/CAGR 계산 (``with_columns``)
    3. **크로스 계정** — 매출 · 영업이익 · 순이익 · 자산 · 부채를 join 해 독자 비율 산출
       예) "매출 1조+ 인데 영업이익 역성장" = sales 상위 ∩ operating_profit YoY 음수
    4. **프리셋 대체** — ``scanRatio`` 와 join 해 primitive 조합으로 복합 스크린 구성

    **계정 1 개로 무엇을 판단하는가** — primitive 단독 호출 패턴 ::

        ┌──────────────────────────────────────┬───────────────────────────────────────────────────────┐
        │ 단독 호출                            │ 판단 (AI 가 이걸로 알 수 있는 것)                     │
        ├──────────────────────────────────────┼───────────────────────────────────────────────────────┤
        │ scanAccount("매출액", freq="Y")      │ 매출 규모 랭킹 — 1 조 클럽 · 1000 억 클럽 분류         │
        │ scanAccount("매출액", freq="Q")      │ 분기 매출 모멘텀 — 최근 QoQ 가속/감속 · 계절성        │
        │ scanAccount("영업이익", freq="Y")    │ 본업 수익 절대값 + 적자 종목 (음수) 분류              │
        │ scanAccount("연구개발비", freq="Y")  │ R&D 절대 규모 — 산업 강도 + 미래 투자 비교            │
        │ scanAccount("재고자산", freq="Q")    │ 재고 절대 규모 — 사이클 산업 (반도체·화학) 재고 사이클 │
        │ scanAccount("총자산", freq="Y")      │ 자산 거인 — 자본 집약도 + 산업 평균 대비 위치          │
        │ scanAccount("현금성자산", freq="Y")  │ 현금 보유 거인 — 자본환원 여력 (배당·자사주) 후보      │
        │ scanAccount("영업현금흐름", freq="Y")│ OCF 절대 규모 — 본업 현금 창출력 직접 비교             │
        │ scanAccount("이익잉여금", freq="Y")  │ 누적 이익 — 장기 흑자 누적 종목 분류                  │
        └──────────────────────────────────────┴───────────────────────────────────────────────────────┘

    **계정 2 개 join = 무한 조합** — ratio 가 미구현인 지표를 primitive 로 직접 만든다 ::

        ┌──────────────────────────────────────────┬──────────────────────────────────────────────────┐
        │ 두 계정 조합                             │ 새로 판단 가능한 것 (= 미구현 ratio 대체)          │
        ├──────────────────────────────────────────┼──────────────────────────────────────────────────┤
        │ 매출액 YoY + 영업이익 YoY                │ 마진 변화 — 매출 늘어도 이익 줄면 비용 압박       │
        │ 연구개발비 ÷ 매출액                      │ R&D 집약도 (R&D / Sales) — 경쟁력·미래 투자 강도  │
        │ 재고자산 YoY + 매출액 YoY                │ 재고 누적 vs 매출 정체 → 사이클 하강·불황 신호    │
        │ 현금성자산 + 단기차입금                  │ 단기 유동성 cushion — 부채비율보다 직접 측정       │
        │ 영업현금흐름 + 유형자산취득(CAPEX)       │ Free Cash Flow 추정 (FCF = OCF − CAPEX)            │
        │ 매출원가 ÷ 매출액                        │ 매출원가율 (= 1 − 매출총이익률) 추이              │
        │ 영업이익 ÷ 이자비용                      │ 이자보상배율 (interest coverage)                  │
        │ 매출액 ÷ 무형자산                        │ 무형자산 활용 효율 — 브랜드·IP 회사 영업 레버리지  │
        │ 자기자본 + 시가총액 (gather)             │ PBR 직접 계산 — 시가총액 ÷ 자기자본               │
        └──────────────────────────────────────────┴──────────────────────────────────────────────────┘

    **조합 예시 (scanRatio 와 엮는다)**:

    ========================================  ======================================================
    질문                                      scanAccount ⨝ scanRatio
    ========================================  ======================================================
    "자산 많은데 수익 못 내는"                total_assets 상위 ∩ scanRatio("roa") 하위
    "매출 큰데 영업이익 역성장"                sales 상위 ∩ operating_profit YoY 음수
    "현금 많이 쌓고 있는 회사"                 cash_and_cash_equivalents 상위 + YoY 양수 + debtRatio 낮음
    "R&D 비중 높은데 성장 느림"                 research_expenses / sales 상위 ∩ scanRatio("revenueGrowth") 하위
    ========================================  ======================================================

    Verified
    --------
    아래는 2026-04-27 시점 실데이터로 검증한 account ⨝ ratio 조합 한 예 ::

        # "자산 많은데 수익 못 내는" — total_assets 상위 200 ∩ ROA < 1% (2024)
        #    → 후보 77 종목. 상위 (roa asc):
        #      034220 LG디스플레이   (총자산 32.9 조 / ROA -7.3 %)
        #      011790 SKC            (총자산  6.7 조 / ROA -6.7 %)
        #      035760 CJ ENM         (총자산  9.3 조 / ROA -6.2 %)
        #      361610 SK아이이테크놀로지 (총자산 4.2 조 / ROA -5.9 %)
        #      011170 롯데케미칼    (총자산 34.5 조 / ROA -5.3 %)
        #    → 화학·디스플레이 시클리컬 적자 사이클 (단순 음수 ROA 가 아닌 자산 거인의
        #       구조적 비효율 vs 사이클 일시 적자 구분은 macro · scan("debt") 와 엮어 판단)

    See Also
    --------
    scanRatio : 비율 시계열 (primitive 2/2) — 발굴 레시피·7 관점 SSOT
    scanAccountList : 지원 계정 목록
    scan("profitability") · scan("growth") 등 : 자주 쓰는 프리셋 (이 함수 + scanRatio 조합 결과)

    Raises
    ------
    없음 (지원되지 않는 snakeId 또는 데이터 부재 시 빈 DataFrame).

    Args:
        snakeId: 계정 식별자 (영문 snake_case 또는 한글). ``scanAccountList()`` 목록.
        sjDiv: 재무제표 구분 ("IS"/"CIS"/"BS"/"CF"). None 이면 sortOrder.json 자동 판정.
        fsPref: 연결 우선 ("CFS") 또는 별도 ("OFS"). 연결 부재 시 별도 fallback.
        freq: "Q" (분기 wide) 또는 "Y" (연간 wide). Company.panel 의 freq 와 동치.

    Returns:
        pl.DataFrame — ``stockCode`` (str 6) + 가변 기간 컬럼 (float 원).
              (계정 + 비율 + macro + sector) 조합 강제 — Guide 의 "광역 발굴" 경고 준수.
            - ``snakeId`` 오타 → 빈 DataFrame (예외 X). ``scanAccountList()`` 사전 확인.
            - 다회 호출 시 ``finance.parquet`` 매번 lazy scan — 같은 snakeId 재사용 시 caller cache.
            - ``freq="M"`` 등 비표준 X — Q / Y strict.
        OutputSchema:
            - pl.DataFrame — ``stockCode`` (str 6) + 가변 기간 컬럼 (float 원).
            - freq="Q": ``"2025Q4"`` / ``"2025Q3"`` / ... / ``"2019Q1"`` (분기 wide).
            - freq="Y": ``"2025"`` / ``"2024"`` / ... / ``"2019"`` (연간 wide).
            - 종목별 최신 기간만 채워짐, 결측 null. row ~2,664 (전종목).
        Prerequisites:
            - prebuilt ``scan/finance.parquet`` (~307MB) 또는 pyodide ``finance-lite.parquet`` (~18MB).
            - parquet 부재 시 ``finance/*.parquet`` raw glob → DuckDB streaming SQL fallback.
            - 둘 다 없으면 ``emit("hint:market_data_needed")`` + 빈 DataFrame.
        Freshness:
            - DART 분기 마감 후 ~45 일 (반기 60 일) 공시 cadence.
            - scan 가속 parquet 은 nightly rebuild — HuggingFace origin.
        Dataflow:
            - snakeId → ``_resolveSnakeId`` (한글/영문 → snake_case 정규화)
            - → ``_resolveSjDiv`` (sjDiv None 시 sortOrder.json 로 IS/BS/CF/CIS 자동 판정)
            - → ``_buildFastKeys`` (가속 룩업 set)
            - → (tier 1) ``scan/finance.parquet`` lazy scan + push-down filter
            - → (tier 2) ``finance/*.parquet`` raw glob → DuckDB streaming SQL
            - → freq 별 pivot wide (Q: YYYYQn / Y: YYYY) → pl.DataFrame.
            - withMemoryBudget(800MB) decorator — RSS 초과 시 mid-stream abort.
        TargetMarkets:
            - KR (DART) 전종목 — KOSPI/KOSDAQ/KONEX 연결재무제표 우선 (별도 fallback).
    """
    from dartlab.core.dataLoader import _dataDir

    snakeId = _resolveSnakeId(snakeId)

    if sjDiv is None:
        sjDiv = _resolveSjDiv(snakeId)

    filterDivs = ["IS", "CIS"] if sjDiv in ("IS", "CIS") else [sjDiv]
    fastKeys = _buildFastKeys(snakeId)

    # ── scan/finance(-lite).parquet 가속 경로 ──
    # Pyodide(브라우저) 에서는 경량본 `finance-lite.parquet`(~18MB) 을 우선 사용한다.
    # 일반 환경은 전량 `finance.parquet`(~307MB) 사용.
    import importlib

    from dartlab.core.dataLoader import _IS_PYODIDE

    _ensureScanData = importlib.import_module("dartlab.scan.io.parquet")._ensureScanData

    scanDir = _ensureScanData()
    scanFileName = "finance-lite.parquet" if _IS_PYODIDE else "finance.parquet"
    scanPath = scanDir / scanFileName
    allDf = None

    if scanPath.exists():
        allDf = _scanAccountFromMerged(
            scanPath,
            snakeId,
            sjDiv,
            filterDivs,
            fsPref,
            fastKeys,
            freq=freq,
        )
        if allDf is not None:
            _log.info("scanAccount('%s'): %s 가속 경로 사용", snakeId, scanFileName)

    # ── fallback: raw glob → DuckDB streaming SQL ──
    if allDf is None:
        financeDir = Path(_dataDir("finance"))
        parquetFiles = sorted(financeDir.glob("*.parquet"))

        if not parquetFiles:
            from dartlab.core.messaging import emit

            emit("hint:market_data_needed", category="finance", fn="scanAccount")
            return _emptyStockCodeFrame()

        _log.info(
            "scanAccount('%s', freq=%s): DuckDB raw glob fallback (%d 종목)",
            snakeId,
            freq,
            len(parquetFiles),
        )

        _loadRawFinanceViaDuckDb = importlib.import_module("dartlab.scan.io.parquet")._loadRawFinanceViaDuckDb

        # sinceYear=2021 — prebuild 합본과 동일 cutoff (buildFinance default)
        # account 매칭은 SQL push-down (raw 3M row → 매칭 row 만 polars 통과)
        lz = _loadRawFinanceViaDuckDb(
            financeDir,
            sjDivs=filterDivs,
            sinceYear=2021,
            accountIds=set(fastKeys),
            accountNms=set(fastKeys),
        )
        if lz is None:
            return _emptyStockCodeFrame()

        allDf = _scanAccountFromMerged(
            None,
            snakeId,
            sjDiv,
            filterDivs,
            fsPref,
            fastKeys,
            freq=freq,
            lazyFrame=lz,
        )

        if allDf is None or allDf.is_empty():
            return _emptyStockCodeFrame()

    # 기간당 첫 값 + pivot
    allDf = allDf.group_by(["stockCode", "period"]).agg(pl.col("amount").first())

    result = allDf.pivot(on="period", index="stockCode", values="amount")  # polars-streaming-unsupported: pivot
    periodCols = sorted(c for c in result.columns if c != "stockCode")

    # 분기: 첫 연도에 Q4만 존재하면 제거 (불완전 분기)
    if freq != "Y" and periodCols:
        firstYear = periodCols[0][:4]
        firstYearQs = [c for c in periodCols if c.startswith(firstYear)]
        if len(firstYearQs) == 1 and firstYearQs[0].endswith("Q4"):
            periodCols = periodCols[1:]

    # 최신 먼저 역순 정렬
    periodCols = list(reversed(periodCols))
    # 행도 종목코드로 정렬한다. 위 group_by 와 pivot 은 polars 가 병렬로 처리해서 행 순서를
    # 보장하지 않는다. 그래서 같은 질의를 두 번 돌리면 전종목 표가 매번 다른 순서로 나왔다.
    # 사용자가 보는 표가 흔들리는 것도 문제지만, 그 위에 얹힌 content seal 이 같은 내용에
    # 매번 다른 식별자를 붙이는 것이 더 크다. 여기가 전종목 축 대부분의 공통 원천이라
    # 한 줄로 그 계열 전체가 결정적이 된다.
    result = result.select(["stockCode"] + periodCols).sort("stockCode")

    _log.info(
        "scanAccount('%s'): %d종목 × %d기간",
        snakeId,
        result.height,
        len(periodCols),
    )

    return result


def scanAccountList() -> list[dict[str, str]]:
    """사용 가능한 scanAccount 계정 목록을 반환한다.

    Summary
    -------
    `sortOrder.json` 기준 재무제표 계정 카탈로그.

    Description
    -----------
    재무제표 계정의 단일 원천은 `sortOrder.json` 과 `AccountMapper` 이다.
    이 함수는 IS/BS/CF 계정 키와 한글 라벨을 반환하며, `scan("account")` 와
    `scan("fields")` 가 같은 목록을 소비한다.

    Parameters
    ----------
    없음.

    Returns
    -------
    list[dict[str, str]]
        name : str — `scanAccount(snakeId=...)` 에 넣는 정규 계정 키 (단위 없음).
        label : str — 한글 계정명 또는 snakeId fallback (단위 없음).
        statement : str — 재무제표 구분. `IS`, `BS`, `CF` 중 하나.

    Raises
    ------
    없음.

    Examples
    --------
    >>> dartlab.scan("account")
    >>> dartlab.scan("fields", "매출")

    Notes
    -----
    금액 단위는 원이다. 기간별 값은 `scanAccount` 가 wide DataFrame 으로 반환하고,
    조건형 screen 은 종목별 최신 기간 값을 비교한다.

    Guide
    -----
    When: 매출액·영업이익·자산·현금흐름 같은 원자 계정으로 후보를 찾을 때.
    How: `name` 을 `scan("account", name)` 또는 `finance.account.{name}` 필드로 사용한다.
    Verified: `scan("fields")` 의 finance account 행이 이 목록에서 생성된다.

    See Also
    --------
    scanAccount : 전종목 계정 시계열.
    scanFields : 조건형 스크리닝 필드 카탈로그.

    Returns:
        list[dict[str, str]] — 카탈로그 dict 리스트.
    """
    from dartlab.core.utils.ordering import _ensureLoaded

    data = _ensureLoaded()

    # 한글명 역매핑: snakeId → 한글 항목
    mappings = loadAccounts().get("mappings", {})
    idToKr: dict[str, str] = {}
    if mappings:
        for krName, snakeId in mappings.items():
            if not krName.isascii() and snakeId not in idToKr:
                idToKr[snakeId] = krName

    result = []
    for sjDiv in ("IS", "BS", "CF"):
        for snakeId in data.get(sjDiv, {}):
            label = idToKr.get(snakeId, snakeId)
            result.append({"name": snakeId, "label": label, "statement": sjDiv})
    return result


# ── scanRatio 재내보내기 (분리: scanRatio.py) ────────────────────
# 호출자 호환 — _RATIO_DEFS / scanRatio / scanRatioList 는 scanRatio.py 로 이전.
from dartlab.providers.dart.finance.scanRatio import (  # noqa: E402  re-export
    _RATIO_DEFS,
    scanRatio,
    scanRatioList,
)
