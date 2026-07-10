"""횡단(cross-industry) 투자 테마 — themes.json 로드·태깅·매출노출 등급 (내부 백엔드).

공개 호출계약은 *엔진 verb 만*: ``Industry().theme(themeId)`` (테마 스코프) ·
``Company(code).themes()`` (회사 스코프). 본 모듈 함수(``_``)는 그 백엔드 — 직접 호출 대상 아님.
태깅=주요제품 substring, 등급=panel ``segmentRevenueExposure`` × 테마별 segmentKeywords.
사전(themes.json)=사람 큐레이션 SSOT. ``노출%``=None 은 100% 등치 금지(정직 계약).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import polars as pl

_DATA_DIR = Path(__file__).parent
_DOSSIER_SCHEMA = {
    "themeId": pl.Utf8,
    "테마": pl.Utf8,
    "근거": pl.Utf8,
    "노출%": pl.Float64,
    "등급근거": pl.Utf8,
}


@dataclass(frozen=True)
class ThemeDef:
    """단일 테마 정의 (themes.json 한 항목, 내부 타입)."""

    themeId: str
    name: str
    desc: str
    keywords: list[str]
    negative: list[str] = field(default_factory=list)
    segmentKeywords: list[str] = field(default_factory=list)


@lru_cache(maxsize=1)
def _loadThemes() -> dict[str, ThemeDef]:
    """themes.json → 테마ID→ThemeDef (lru_cache). Industry.theme/Company.themes 백엔드."""
    raw = json.loads((_DATA_DIR / "themes.json").read_text(encoding="utf-8"))
    return {
        tid: ThemeDef(
            themeId=tid,
            name=t.get("name", tid),
            desc=t.get("desc", ""),
            keywords=t.get("keywords", []),
            negative=t.get("negative", []),
            segmentKeywords=t.get("segmentKeywords", []),
        )
        for tid, t in raw.get("themes", {}).items()
    }


def _matchTheme(theme: ThemeDef, text: str) -> list[str]:
    """주요제품 텍스트 × 테마 키워드 substring 매칭 (negative 제거 후). 매칭 키워드 리스트."""
    if not text:
        return []
    low = text.lower()
    for neg in theme.negative:
        low = low.replace(neg.lower(), " ")
    return [kw for kw in theme.keywords if kw.lower() in low]


def _themeExposure(themeId: str, code: str) -> dict | None:
    """한 종목의 해당 테마 매출 노출% (테마-인지, 테마별 segmentKeywords 로만).

    basis: graded / pure_play_candidate / no_segment_data / theme_no_segment_keywords.
    ``exposurePct``=None(graded 외 전부)은 미산출 — 100% 등치 금지(정직 계약).
    """
    theme = _loadThemes().get(themeId)
    if theme is None:
        return None
    if not theme.segmentKeywords:
        return {"exposurePct": None, "basis": "theme_no_segment_keywords"}

    from dartlab.providers.dart.panel.cell import segmentRevenueExposure

    exp = segmentRevenueExposure(code)
    if exp is None:
        return {"exposurePct": None, "basis": "no_segment_data"}
    if not exp:
        return {"exposurePct": None, "basis": "pure_play_candidate"}
    segKws = [k.lower() for k in theme.segmentKeywords]
    pct = sum(p for seg, p in exp.items() if any(k in seg.lower() for k in segKws))
    return {"exposurePct": round(pct, 1), "basis": "graded"}


def _stockThemes(code: str) -> pl.DataFrame:
    """한 종목의 소속 테마 도시에 (``Industry().theme(stockCode=...)`` 백엔드).

    공개 listing 파사드로 주요제품 획득(gather 내부 직접 호출 아님) → 소속 테마·근거·노출%.
    컬럼 ``themeId·테마·근거·노출%·등급근거``. 매칭 테마 없으면 빈 DataFrame.
    """
    import gc

    if not code:
        return pl.DataFrame([], schema=_DOSSIER_SCHEMA)

    from dartlab._listingDispatch import listing as _listing

    df = _listing()
    # 컬럼이 있어도 목록이 비면 dtype 이 Null 이라 str 비교가 그 자리에서 TypeError 를 낸다(브라우저).
    hasCode = df.height > 0 and "종목코드" in df.columns
    row = df.filter(df["종목코드"] == code) if hasCode else df.head(0)
    product = row["주요제품"][0] if row.height and "주요제품" in row.columns else ""

    rows: list[dict] = []
    for tid, theme in _loadThemes().items():
        hits = _matchTheme(theme, product or "")
        if not hits:
            continue
        g = _themeExposure(tid, code) or {}
        rows.append(
            {
                "themeId": tid,
                "테마": theme.name,
                "근거": ", ".join(hits),
                "노출%": g.get("exposurePct"),
                "등급근거": g.get("basis"),
            }
        )
        gc.collect()
    return pl.DataFrame(rows, schema=_DOSSIER_SCHEMA)
