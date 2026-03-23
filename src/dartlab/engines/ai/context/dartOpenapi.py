"""OpenDART 공시목록 retrieval helper.

회사 미선택 질문에서도 최근 공시목록/수주공시/계약공시를
deterministic prefetch로 회수해 AI 컨텍스트로 주입한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from html import unescape
from typing import Any

import polars as pl

from dartlab.core.capabilities import UiAction
from dartlab.engines.ai.context.formatting import df_to_markdown
from dartlab.engines.company.dart.openapi.dartKey import hasDartApiKey

_FILING_TERMS = (
    "공시",
    "전자공시",
    "공시목록",
    "공시 리스트",
    "수주공시",
    "계약공시",
    "단일판매공급계약",
    "공급계약",
    "판매공급계약",
    "수주",
)
_REQUEST_TERMS = (
    "알려",
    "보여",
    "찾아",
    "정리",
    "요약",
    "분석",
    "골라",
    "추천",
    "무슨",
    "뭐 있었",
    "리스트",
    "목록",
)
_DETAIL_TERMS = (
    "요약",
    "분석",
    "핵심",
    "중요",
    "읽을",
    "리스크",
    "내용",
    "무슨 내용",
    "꼭",
)
_ORDER_KEYWORDS = (
    "단일판매공급계약",
    "판매공급계약",
    "공급계약",
    "수주",
)
_DISCLOSURE_TYPE_HINTS = {
    "정기공시": "A",
    "주요사항": "B",
    "주요사항보고": "B",
    "발행공시": "C",
    "지분공시": "D",
    "기타공시": "E",
    "외부감사": "F",
    "펀드공시": "G",
    "자산유동화": "H",
    "거래소공시": "I",
    "공정위공시": "J",
}
_MARKET_HINTS = {
    "코스피": "Y",
    "유가증권": "Y",
    "코스닥": "K",
    "코넥스": "N",
}
_DEFAULT_LIMIT = 20
_DEFAULT_DAYS = 7


@dataclass(frozen=True)
class DartFilingIntent:
    matched: bool = False
    corp: str | None = None
    start: str = ""
    end: str = ""
    disclosureType: str | None = None
    market: str | None = None
    finalOnly: bool = False
    limit: int = _DEFAULT_LIMIT
    titleKeywords: tuple[str, ...] = ()
    includeText: bool = False
    textLimit: int = 0


@dataclass(frozen=True)
class DartFilingPrefetch:
    matched: bool
    needsKey: bool = False
    message: str = ""
    contextText: str = ""
    uiAction: dict[str, Any] | None = None
    filings: pl.DataFrame | None = None
    intent: DartFilingIntent | None = None


def buildMissingDartKeyMessage() -> str:
    return (
        "OpenDART API 키가 필요합니다.\n"
        "- 이 질문은 실시간 공시목록 조회가 필요합니다.\n"
        "- 설정에서 `OpenDART API 키`를 저장하면 최근 공시, 수주공시, 계약공시를 바로 검색할 수 있습니다.\n"
        "- 키는 프로젝트 루트 `.env`의 `DART_API_KEY`로 저장됩니다."
    )


def buildMissingDartKeyUiAction() -> dict[str, Any]:
    return UiAction.update(
        "settings",
        {
            "open": True,
            "section": "openDart",
            "message": "OpenDART API 키를 설정하면 최근 공시목록을 바로 검색할 수 있습니다.",
        },
    ).to_payload()


def isDartFilingQuestion(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    normalized = q.replace(" ", "")
    if any(term in normalized for term in ("openapi", "opendart", "dartapi")) and not any(
        term in q for term in _FILING_TERMS
    ):
        return False
    has_filing_term = any(term in q for term in _FILING_TERMS)
    has_request_term = any(term in q for term in _REQUEST_TERMS)
    has_time_term = any(term in q for term in ("최근", "오늘", "어제", "이번 주", "지난 주", "이번 달", "며칠", "몇일"))
    return has_filing_term and (has_request_term or has_time_term or "?" not in q)


def detectDartFilingIntent(question: str, company: Any | None = None) -> DartFilingIntent:
    if not isDartFilingQuestion(question):
        return DartFilingIntent()

    today = date.today()
    start_date, end_date = _resolve_date_window(question, today)
    title_keywords = _resolve_title_keywords(question)
    include_text = any(term in question for term in _DETAIL_TERMS)
    limit = _resolve_limit(question)
    corp = None
    if company is not None:
        corp = getattr(company, "stockCode", None) or getattr(company, "corpName", None)

    disclosure_type = None
    for hint, code in _DISCLOSURE_TYPE_HINTS.items():
        if hint in question:
            disclosure_type = code
            break

    market = None
    for hint, code in _MARKET_HINTS.items():
        if hint in question:
            market = code
            break

    final_only = any(term in question for term in ("최종", "정정 제외", "정정없는", "정정 없는"))
    text_limit = 3 if include_text and limit <= 5 else (2 if include_text else 0)

    return DartFilingIntent(
        matched=True,
        corp=corp,
        start=start_date.strftime("%Y%m%d"),
        end=end_date.strftime("%Y%m%d"),
        disclosureType=disclosure_type,
        market=market,
        finalOnly=final_only,
        limit=limit,
        titleKeywords=title_keywords,
        includeText=include_text,
        textLimit=text_limit,
    )


def searchDartFilings(
    *,
    corp: str | None = None,
    start: str | None = None,
    end: str | None = None,
    days: int | None = None,
    weeks: int | None = None,
    disclosureType: str | None = None,
    market: str | None = None,
    finalOnly: bool = False,
    titleKeywords: list[str] | tuple[str, ...] | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> pl.DataFrame:
    from dartlab import OpenDart

    if not hasDartApiKey():
        raise ValueError(buildMissingDartKeyMessage())

    resolved_start, resolved_end = _coerce_search_window(start, end, days=days, weeks=weeks)
    dart = OpenDart()
    filings = dart.filings(
        corp=corp,
        start=resolved_start,
        end=resolved_end,
        type=disclosureType,
        final=finalOnly,
        market=market,
    )
    if filings is None or filings.height == 0:
        return pl.DataFrame()

    df = filings
    if titleKeywords and "report_nm" in df.columns:
        mask = pl.lit(False)
        for keyword in titleKeywords:
            mask = mask | pl.col("report_nm").str.contains(keyword, literal=True)
        df = df.filter(mask)

    if df.height == 0:
        return pl.DataFrame()

    sort_cols = [col for col in ("rcept_dt", "rcept_no") if col in df.columns]
    if sort_cols:
        descending = [True] * len(sort_cols)
        df = df.sort(sort_cols, descending=descending)

    return df.head(max(1, min(limit, 100)))


def getDartFilingText(rceptNo: str, maxChars: int = 4000) -> str:
    from dartlab import OpenDart

    if not rceptNo:
        raise ValueError("rcept_no가 필요합니다.")
    if not hasDartApiKey():
        raise ValueError(buildMissingDartKeyMessage())

    raw_text = OpenDart().documentText(rceptNo)
    return cleanDartFilingText(raw_text, maxChars=maxChars)


def buildDartFilingPrefetch(question: str, company: Any | None = None) -> DartFilingPrefetch:
    intent = detectDartFilingIntent(question, company=company)
    if not intent.matched:
        return DartFilingPrefetch(matched=False)
    if not hasDartApiKey():
        return DartFilingPrefetch(
            matched=True,
            needsKey=True,
            message=buildMissingDartKeyMessage(),
            uiAction=buildMissingDartKeyUiAction(),
            intent=intent,
        )

    filings = searchDartFilings(
        corp=intent.corp,
        start=intent.start,
        end=intent.end,
        disclosureType=intent.disclosureType,
        market=intent.market,
        finalOnly=intent.finalOnly,
        titleKeywords=intent.titleKeywords,
        limit=intent.limit,
    )
    context_text = formatDartFilingContext(filings, intent, question=question)
    if intent.includeText and filings.height > 0 and "rcept_no" in filings.columns:
        detail_blocks = []
        for rcept_no in filings["rcept_no"].head(intent.textLimit).to_list():
            try:
                excerpt = getDartFilingText(str(rcept_no), maxChars=1800)
            except (OSError, RuntimeError, ValueError):
                continue
            detail_blocks.append(f"### 접수번호 {rcept_no} 원문 발췌\n{excerpt}")
        if detail_blocks:
            context_text = "\n\n".join([context_text, *detail_blocks]) if context_text else "\n\n".join(detail_blocks)

    return DartFilingPrefetch(
        matched=True,
        needsKey=False,
        contextText=context_text,
        filings=filings,
        intent=intent,
    )


def formatDartFilingContext(
    filings: pl.DataFrame,
    intent: DartFilingIntent,
    *,
    question: str = "",
) -> str:
    if intent.start or intent.end:
        window_label = f"{_format_date(intent.start or intent.end)} ~ {_format_date(intent.end or intent.start)}"
    else:
        window_label = "자동 기본 범위"
    lines = ["## OpenDART 공시목록 검색 결과", f"- 기간: {window_label}"]
    if intent.corp:
        lines.append(f"- 회사 필터: {intent.corp}")
    else:
        lines.append("- 회사 필터: 전체 시장")
    if intent.market:
        lines.append(f"- 시장 필터: {intent.market}")
    if intent.disclosureType:
        lines.append(f"- 공시유형: {intent.disclosureType}")
    if intent.finalOnly:
        lines.append("- 최종보고서만 포함")
    if intent.titleKeywords:
        lines.append(f"- 제목 키워드: {', '.join(intent.titleKeywords)}")
    if question:
        lines.append(f"- 사용자 질문: {question}")

    if filings is None or filings.height == 0:
        lines.append("")
        lines.append("해당 조건에 맞는 공시가 없습니다.")
        return "\n".join(lines)

    display_df = _build_display_df(filings)
    lines.extend(["", df_to_markdown(display_df, max_rows=min(intent.limit, 20), compact=False)])
    return "\n".join(lines)


def cleanDartFilingText(text: str, *, maxChars: int = 4000) -> str:
    normalized = unescape(text or "")
    normalized = re.sub(r"<[^>]+>", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if len(normalized) <= maxChars:
        return normalized
    return normalized[:maxChars].rstrip() + " ... (truncated)"


def _build_display_df(df: pl.DataFrame) -> pl.DataFrame:
    display = df
    if "rcept_dt" in display.columns:
        display = display.with_columns(
            pl.col("rcept_dt").cast(pl.Utf8).map_elements(_format_date, return_dtype=pl.Utf8).alias("rcept_dt")
        )

    preferred_cols = [
        col
        for col in ("rcept_dt", "corp_name", "stock_code", "corp_cls", "report_nm", "rcept_no")
        if col in display.columns
    ]
    if preferred_cols:
        display = display.select(preferred_cols)

    rename_map = {
        "rcept_dt": "접수일",
        "corp_name": "회사",
        "stock_code": "종목코드",
        "corp_cls": "시장",
        "report_nm": "공시명",
        "rcept_no": "접수번호",
    }
    actual_map = {src: dst for src, dst in rename_map.items() if src in display.columns}
    return display.rename(actual_map)


def _resolve_title_keywords(question: str) -> tuple[str, ...]:
    if any(term in question for term in _ORDER_KEYWORDS) or "계약공시" in question:
        return _ORDER_KEYWORDS
    explicit = []
    for phrase in ("감사보고서", "합병", "유상증자", "무상증자", "배당", "자기주식", "최대주주"):
        if phrase in question:
            explicit.append(phrase)
    return tuple(explicit)


def _resolve_limit(question: str) -> int:
    match = re.search(r"(\d+)\s*건", question)
    if match:
        return max(1, min(int(match.group(1)), 50))
    if "쫙" in question or "전부" in question or "전체" in question:
        return 30
    return _DEFAULT_LIMIT


def _resolve_date_window(question: str, today: date) -> tuple[date, date]:
    q = question.replace(" ", "")
    if "오늘" in question:
        return today, today
    if "어제" in question:
        target = today - timedelta(days=1)
        return target, target
    if "이번주" in q:
        start = today - timedelta(days=today.weekday())
        return start, today
    if "지난주" in q:
        end = today - timedelta(days=today.weekday() + 1)
        start = end - timedelta(days=6)
        return start, end
    if "이번달" in q:
        start = today.replace(day=1)
        return start, today

    recent_match = re.search(r"최근\s*(\d+)\s*(일|주|개월|달)", question)
    if recent_match:
        amount = int(recent_match.group(1))
        unit = recent_match.group(2)
        if unit == "일":
            return today - timedelta(days=max(amount - 1, 0)), today
        if unit == "주":
            return today - timedelta(days=max(amount * 7 - 1, 0)), today
        if unit in {"개월", "달"}:
            return today - timedelta(days=max(amount * 30 - 1, 0)), today

    if "최근 몇일" in q or "최근몇일" in q or "최근 며칠" in question or "최근며칠" in q:
        return today - timedelta(days=_DEFAULT_DAYS - 1), today
    if "최근 몇주" in q or "최근몇주" in q:
        return today - timedelta(days=13), today

    return today - timedelta(days=_DEFAULT_DAYS - 1), today


def _coerce_search_window(
    start: str | None,
    end: str | None,
    *,
    days: int | None,
    weeks: int | None,
) -> tuple[str, str]:
    today = date.today()
    if start or end:
        resolved_start = _strip_date_sep(start or (end or today.strftime("%Y%m%d")))
        resolved_end = _strip_date_sep(end or today.strftime("%Y%m%d"))
        return resolved_start, resolved_end
    if days:
        begin = today - timedelta(days=max(days - 1, 0))
        return begin.strftime("%Y%m%d"), today.strftime("%Y%m%d")
    if weeks:
        begin = today - timedelta(days=max(weeks * 7 - 1, 0))
        return begin.strftime("%Y%m%d"), today.strftime("%Y%m%d")
    begin = today - timedelta(days=_DEFAULT_DAYS - 1)
    return begin.strftime("%Y%m%d"), today.strftime("%Y%m%d")


def _strip_date_sep(value: str) -> str:
    return (value or "").replace("-", "").replace(".", "").replace("/", "")


def _format_date(value: str) -> str:
    digits = _strip_date_sep(str(value))
    if len(digits) == 8 and digits.isdigit():
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:]}"
    return str(value)
