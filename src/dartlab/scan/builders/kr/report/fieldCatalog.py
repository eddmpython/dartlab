"""KR scan screen field catalog rows."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import polars as pl

_NUMERIC_OPS = ">,>=,<,<=,==,!=,between,exists,not_exists"
_CONTEXT_OPS = "context"
_TEXT_OPS = "contains,==,!=,exists,not_exists"

# 복합축 승격 필드 SSOT. scan 축 스캐너(debt/audit/quality/dividendTrend/liquidity)의 raw 네이티브 컬럼을
# first-class screen 필드로 등재한다. scan() dispatch 의 한글 리네임(_enrichWithKorean)을 우회해 raw 스캐너를
# 직접 호출하므로 컬럼이 안정적이다(드리프트 가드: test_composite_axis 가 컬럼 실재 검증). module/fn/col 이 정본.
_COMPOSITE_AXIS_FIELDS: dict[str, dict[str, str]] = {
    "axis.debt.icr": {
        "module": "dartlab.scan.debt",
        "fn": "scanDebt",
        "col": "ICR",
        "label": "이자보상배율(축)",
        "kind": "number",
        "unit": "배",
    },
    "axis.debt.riskGrade": {
        "module": "dartlab.scan.debt",
        "fn": "scanDebt",
        "col": "위험등급",
        "label": "부채위험등급(축)",
        "kind": "text",
        "unit": "없음",
    },
    "axis.debt.debtRatio": {
        "module": "dartlab.scan.debt",
        "fn": "scanDebt",
        "col": "부채비율",
        "label": "부채비율(축)",
        "kind": "number",
        "unit": "%",
    },
    "axis.debt.shortRatio": {
        "module": "dartlab.scan.debt",
        "fn": "scanDebt",
        "col": "단기비중",
        "label": "단기차입비중(축)",
        "kind": "number",
        "unit": "%",
    },
    "axis.quality.cfToNi": {
        "module": "dartlab.scan.financial.quality",
        "fn": "scanQuality",
        "col": "cfToNi",
        "label": "영업현금흐름/순이익(축)",
        "kind": "number",
        "unit": "배",
    },
    "axis.quality.accrualRatio": {
        "module": "dartlab.scan.financial.quality",
        "fn": "scanQuality",
        "col": "accrualRatio",
        "label": "발생액비율(축)",
        "kind": "number",
        "unit": "배",
    },
    "axis.quality.grade": {
        "module": "dartlab.scan.financial.quality",
        "fn": "scanQuality",
        "col": "grade",
        "label": "이익품질등급(축)",
        "kind": "text",
        "unit": "없음",
    },
    "axis.audit.opinion": {
        "module": "dartlab.scan.audit",
        "fn": "scanAudit",
        "col": "opinion",
        "label": "감사의견(축)",
        "kind": "text",
        "unit": "없음",
    },
    "axis.audit.riskLevel": {
        "module": "dartlab.scan.audit",
        "fn": "scanAudit",
        "col": "riskLevel",
        "label": "감사위험수준(축)",
        "kind": "number",
        "unit": "점",
    },
    "axis.dividendTrend.pattern": {
        "module": "dartlab.scan.dividendTrend",
        "fn": "scanDividendTrend",
        "col": "pattern",
        "label": "배당패턴(축)",
        "kind": "text",
        "unit": "없음",
    },
    "axis.liquidity.grade": {
        "module": "dartlab.scan.financial.liquidity",
        "fn": "scanLiquidity",
        "col": "grade",
        "label": "유동성등급(축)",
        "kind": "text",
        "unit": "없음",
    },
}

_KRX_FIELDS: dict[str, tuple[str, str, str]] = {
    "close": ("종가", "원", "latest"),
    "open": ("시가", "원", "latest"),
    "high": ("고가", "원", "latest"),
    "low": ("저가", "원", "latest"),
    "volume": ("거래량", "주", "latest"),
    "amount": ("거래대금", "원", "latest"),
    "marketCap": ("시가총액", "원", "latest"),
    "listShares": ("상장주식수", "주", "latest"),
    "fluctuationRate": ("등락률", "%", "latest"),
    "priceChange": ("전일대비", "원", "latest"),
}

_KRX_INDEX_FIELDS: dict[str, tuple[str, str]] = {
    "close": ("종가지수", "점"),
    "open": ("시가지수", "점"),
    "high": ("고가지수", "점"),
    "low": ("저가지수", "점"),
    "volume": ("거래량", "주"),
    "amount": ("거래대금", "원"),
    "marketCap": ("시가총액", "원"),
    "fluctuationRate": ("등락률", "%"),
}

_REPORT_META = {
    "stockCode",
    "year",
    "quarter",
    "apiType",
    "rcept_no",
    "corp_code",
    "corp_name",
    "corpCode",
    "collectStatus",
    "apiName",
    "corp_cls",
}


@lru_cache(maxsize=1)
def _catalog() -> pl.DataFrame:
    """screen field catalog DataFrame 생성.

    Parameters:
        없음.

    Returns:
        source/field 기준으로 정렬된 catalog DataFrame.

    Raises:
        없음 — 원천별 schema 읽기 실패는 해당 원천 row 생성을 건너뛴다.

    Examples:
        >>> _catalog().columns

    Guide:
        screen 실행기와 fields 검색기가 공유하는 필드 SSOT.

    Capabilities:
        finance, valuation, report, docs, krx, krxIndex 필드를 단일 표로 결합.

    AIContext:
        AI가 screen spec 을 만들 때 사용할 수 있는 필드와 연산자 경계를 제공한다.

    When:
        ``scanFields`` 또는 ``executeScreenSpec`` 가 필드 메타가 필요할 때.

    How:
        각 source row builder 를 호출하고 polars DataFrame 으로 정렬한다.

    Requires:
        선택적으로 prebuild report parquet schema.

    SeeAlso:
        ``scanFields`` · ``executeScreenSpec``.
    """
    rows: list[dict[str, str]] = []
    rows.extend(_financeCatalogRows())
    rows.extend(_valuationCatalogRows())
    rows.extend(_reportCatalogRows())
    rows.extend(_docsCatalogRows())
    rows.extend(_krxCatalogRows())
    rows.extend(_krxIndexCatalogRows())
    rows.extend(_noteCatalogRows())
    rows.extend(_compositeAxisCatalogRows())
    return pl.DataFrame(rows).sort(["source", "field"])


def _compositeAxisCatalogRows() -> list[dict[str, str]]:
    """복합축 승격 필드를 screen 필드로 등재 (scan 축 산출을 first-class 로).

    :data:`_COMPOSITE_AXIS_FIELDS` 정본에서 도출. debt.riskGrade/audit.opinion 등 등급/텍스트는 텍스트
    연산자, icr/cfToNi 등 수치는 numeric 연산자. raw 스캐너 네이티브 컬럼이라 안정적이다.
    """
    rows: list[dict[str, str]] = []
    for field, r in _COMPOSITE_AXIS_FIELDS.items():
        opset = _NUMERIC_OPS if r["kind"] == "number" else _TEXT_OPS
        rows.append(
            _row(
                field,
                r["label"],
                "axis",
                r["kind"],
                r["unit"],
                opset,
                "composite axis",
                f"scan 축 {r['fn']} 산출 컬럼 {r['col']!r} 승격. 종목별 최신값. raw 스캐너 직독.",
            )
        )
    return rows


def _row(
    field: str,
    label: str,
    source: str,
    kind: str,
    unit: str,
    operatorSet: str,
    coverage: str,
    notes: str,
) -> dict[str, str]:
    if kind == "number":
        example = f'{{"field": "{field}", "op": ">", "value": 0}}'
    elif kind == "boolean":
        example = f'{{"field": "{field}", "op": "exists"}}'
    elif kind == "context":
        example = f'{{"select": ["{field}"]}}'
    else:
        example = f'{{"field": "{field}", "op": "contains", "value": "키워드"}}'
    return {
        "field": field,
        "label": label,
        "source": source,
        "kind": kind,
        "unit": unit,
        "operatorSet": operatorSet,
        "coverage": coverage,
        "example": example,
        "notes": notes,
    }


def _financeCatalogRows() -> list[dict[str, str]]:
    from dartlab.providers.dart.finance.scanAccount import scanAccountList, scanRatioList

    rows: list[dict[str, str]] = []
    for rec in scanAccountList():
        name = rec["name"]
        label = rec.get("label", name)
        stmt = rec.get("statement", "")
        rows.append(
            _row(
                f"finance.account.{name}",
                label,
                "finance",
                "number",
                "원",
                _NUMERIC_OPS,
                stmt,
                "DART 재무제표 계정. 종목별 최신 기간 값을 비교한다.",
            )
        )
    for rec in scanRatioList():
        name = rec["name"]
        label = rec.get("label", name)
        unit = rec.get("unit", "%")
        rows.append(
            _row(
                f"finance.ratio.{name}",
                label,
                "finance",
                "number",
                unit,
                _NUMERIC_OPS,
                "ratio",
                "DART 재무제표 기반 비율. 종목별 최신 기간 값을 비교한다.",
            )
        )
    return rows


def _valuationCatalogRows() -> list[dict[str, str]]:
    fields = {
        "marketCap": ("시가총액", "원"),
        "per": ("PER", "배"),
        "pbr": ("PBR", "배"),
        "psr": ("PSR", "배"),
        "dividendYield": ("배당수익률", "%"),
        "current": ("현재가", "원"),
    }
    return [
        _row(
            f"valuation.{name}",
            label,
            "valuation",
            "number",
            unit,
            _NUMERIC_OPS,
            "daily snapshot",
            "일일 prebuild 밸류에이션 snapshot 기반 최신 값.",
        )
        for name, (label, unit) in fields.items()
    ]


def _reportCatalogRows() -> list[dict[str, str]]:
    from dartlab.core.dataLoader import _dataDir
    from dartlab.providers.dart.report.types import API_TYPE_LABELS, API_TYPES

    rows: list[dict[str, str]] = []
    report_dir = Path(_dataDir("scan")) / "report"
    for apiType in API_TYPES:
        label = API_TYPE_LABELS.get(apiType, apiType)
        rows.append(
            _row(
                f"report.{apiType}.__exists__",
                f"{label} 존재",
                "report",
                "boolean",
                "없음",
                "exists,not_exists,==,!=",
                "apiType",
                "OpenDART 구조화 공시 API type 존재 여부.",
            )
        )
        path = report_dir / f"{apiType}.parquet"
        if not path.exists():
            continue
        try:
            cols = pl.scan_parquet(str(path)).collect_schema().names()
        except (OSError, pl.exceptions.PolarsError):
            continue
        for col in cols:
            if col in _REPORT_META:
                continue
            rows.append(
                _row(
                    f"report.{apiType}.{col}",
                    f"{label}.{col}",
                    "report",
                    "text",
                    "텍스트",
                    "contains,>,>=,<,<=,==,!=,between,exists,not_exists",
                    "prebuild",
                    "구조화 공시 원천 컬럼. schema 기준 노출이며 숫자 비교 시 문자열 숫자를 파싱한다.",
                )
            )
    return rows


def _docsCatalogRows() -> list[dict[str, str]]:
    return [
        _row(
            "docs.content",
            "공시 본문",
            "docs",
            "text",
            "텍스트",
            "contains,==",
            "search index",
            "본문 검색 인덱스 hit 기반 후보 생성.",
        ),
        _row(
            "docs.title",
            "공시 제목/섹션",
            "docs",
            "text",
            "텍스트",
            "contains,==",
            "search index",
            "보고서명·섹션명 검색 인덱스 기반 후보 생성.",
        ),
        _row(
            "docs.report",
            "보고서명",
            "docs",
            "text",
            "텍스트",
            "contains,==",
            "search index",
            "보고서명 검색 후보 생성.",
        ),
    ]


def _krxCatalogRows() -> list[dict[str, str]]:
    from dartlab.gather.transforms.indicatorDispatch import _DEFAULT_INDICATORS_ALL

    rows = [
        _row(
            f"krx.{name}",
            label,
            "krx",
            "number",
            unit,
            _NUMERIC_OPS,
            coverage,
            "KRX 가격/거래 raw 최신값. 기본 window 는 252 거래일이다.",
        )
        for name, (label, unit, coverage) in _KRX_FIELDS.items()
    ]
    for name in _DEFAULT_INDICATORS_ALL:
        rows.append(
            _row(
                f"krx.{name}",
                name,
                "krx",
                "number",
                "점",
                _NUMERIC_OPS,
                "window=252",
                "KRX OHLCV 기반 기술지표. start/end 미지정 시 최근 252 거래일 window 를 사용한다.",
            )
        )
    return rows


def _noteCatalogRows() -> list[dict[str, str]]:
    """추출 카탈로그 registered 단일축 note 개념을 screen 필드로 등재 (개념만, 항목은 on-demand 주소).

    lineitem 수천 행 평탄화 대신 개념당 1행만 등재한다. 실제 항목은 spec 에서 ``note.<concept>@<항목명>``
    주소로 지정하며 ``scan('note', concept)`` 로 항목을 확인한다. 값은 종목별 최신 valueNum.
    """
    from dartlab.scan.builders.kr.notes import SCAN_NOTE_CONCEPTS

    rows: list[dict[str, str]] = []
    for bare, _ntKey, label in SCAN_NOTE_CONCEPTS:
        row = _row(
            f"note.{bare}",
            f"{label}(주석)",
            "note",
            "number",
            "원",
            _NUMERIC_OPS,
            "prebuild",
            f"주석 lineitem 횡단. 항목 지정 필수: note.{bare}@<항목명>. scan('note', '{bare}') 로 항목 확인.",
        )
        row["example"] = f'{{"field": "note.{bare}@<항목명>", "op": ">", "value": 0}}'
        rows.append(row)
    return rows


def _krxIndexCatalogRows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for market in ("KRX", "KOSPI", "KOSDAQ"):
        for name, (label, unit) in _KRX_INDEX_FIELDS.items():
            rows.append(
                _row(
                    f"krxIndex.{market}.{name}",
                    f"{market} {label}",
                    "krxIndex",
                    "context",
                    unit,
                    _CONTEXT_OPS,
                    "latest",
                    "시장 지수 컨텍스트. 종목별 필터가 아니라 결과 컬럼으로만 붙인다.",
                )
            )
    return rows
