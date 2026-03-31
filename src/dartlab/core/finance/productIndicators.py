"""제품-산업 지표 매핑 — kindList 주요제품 → FRED/ECOS 시리즈.

kindList의 `주요제품` 텍스트에서 키워드를 매칭하여
해당 기업에 관련된 산업 지표(생산지수, PPI 등)를 자동 결정한다.
calcMacroRegression에서 회귀 변수로 사용.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


# ── 제품 키워드 → 산업 지표 매핑 ──

PRODUCT_INDICATOR_MAP: dict[str, dict] = {
    # 반도체/전자
    "반도체": {"fred": ["IPG3344S", "PCU33443344"], "label": "반도체 생산/가격"},
    "메모리": {"fred": ["IPG3344S", "PCU33443344"], "label": "반도체 생산/가격"},
    "DRAM": {"fred": ["IPG3344S"], "label": "반도체 생산"},
    "NAND": {"fred": ["IPG3344S"], "label": "반도체 생산"},
    "웨이퍼": {"fred": ["IPG3344S"], "label": "반도체 생산"},
    "파운드리": {"fred": ["IPG3344S"], "label": "반도체 생산"},
    "디스플레이": {"fred": ["IPG3344S"], "label": "전자부품 생산"},
    "OLED": {"fred": ["IPG3344S"], "label": "전자부품 생산"},
    "LCD": {"fred": ["IPG3344S"], "label": "전자부품 생산"},
    "LED": {"fred": ["IPG3344S"], "label": "전자부품 생산"},
    # 자동차
    "자동차": {"fred": ["IPG3361T3S"], "label": "자동차 생산"},
    "자동차부품": {"fred": ["IPG3361T3S"], "label": "자동차 생산"},
    "자동차용": {"fred": ["IPG3361T3S"], "label": "자동차 생산"},
    "차량": {"fred": ["IPG3361T3S"], "label": "자동차 생산"},
    "타이어": {"fred": ["IPG3361T3S"], "label": "자동차 생산"},
    # 2차전지/배터리
    "2차전지": {"fred": ["PCU335911335911"], "label": "배터리 가격"},
    "이차전지": {"fred": ["PCU335911335911"], "label": "배터리 가격"},
    "배터리": {"fred": ["PCU335911335911"], "label": "배터리 가격"},
    "양극재": {"fred": ["PCU335911335911"], "label": "배터리 가격"},
    "음극재": {"fred": ["PCU335911335911"], "label": "배터리 가격"},
    "전해질": {"fred": ["PCU335911335911"], "label": "배터리 가격"},
    # 화학
    "화학": {"fred": ["IPG325S"], "label": "화학 생산"},
    "석유화학": {"fred": ["IPG325S", "DCOILWTICO"], "label": "화학 생산/유가"},
    "합성수지": {"fred": ["IPG325S"], "label": "화학 생산"},
    "플라스틱": {"fred": ["IPG325S"], "label": "화학 생산"},
    # 철강/금속
    "철강": {"fred": ["WPU101"], "label": "금속 가격"},
    "강판": {"fred": ["WPU101"], "label": "금속 가격"},
    "주물": {"fred": ["WPU101"], "label": "금속 가격"},
    "알루미늄": {"fred": ["WPU101"], "label": "금속 가격"},
    "동박": {"fred": ["WPU101"], "label": "금속 가격"},
    # 에너지
    "석유": {"fred": ["DCOILWTICO"], "label": "WTI 유가"},
    "정유": {"fred": ["DCOILWTICO"], "label": "WTI 유가"},
    "가스": {"fred": ["DCOILWTICO"], "label": "유가"},
    "에너지": {"fred": ["DCOILWTICO"], "label": "유가"},
    "태양광": {"fred": ["IPG3344S"], "label": "전자부품 생산"},
    # 식품
    "식품": {"fred": ["IPG311A2S"], "label": "식품 생산"},
    "음료": {"fred": ["IPG311A2S"], "label": "식품 생산"},
    "식료품": {"fred": ["IPG311A2S"], "label": "식품 생산"},
    # 의약/바이오
    "의약품": {"fred": ["PCUOMFGOMFG"], "label": "제조업 PPI"},
    "바이오": {"fred": ["PCUOMFGOMFG"], "label": "제조업 PPI"},
    "치료제": {"fred": ["PCUOMFGOMFG"], "label": "제조업 PPI"},
    "의료기기": {"fred": ["PCUOMFGOMFG"], "label": "제조업 PPI"},
    # 건설
    "건설": {"ecos": ["IPI"], "label": "산업생산"},
    "건축": {"ecos": ["IPI"], "label": "산업생산"},
    "시멘트": {"ecos": ["IPI"], "label": "산업생산"},
    # 물류/운송
    "물류": {"fred": ["TSIFRGHT"], "label": "화물운송"},
    "운송": {"fred": ["TSIFRGHT"], "label": "화물운송"},
    "해운": {"fred": ["TSIFRGHT"], "label": "화물운송"},
    "항공": {"fred": ["TSIFRGHT"], "label": "화물운송"},
    # 소프트웨어/IT (거시 지표 약함 — 범용)
    "소프트웨어": {"fred": ["PCUOMFGOMFG"], "label": "제조업 PPI"},
    "플랫폼": {"fred": ["PCUOMFGOMFG"], "label": "제조업 PPI"},
    # 섬유/의류
    "섬유": {"fred": ["IPG313T6S"], "label": "섬유 생산"},
    "의류": {"fred": ["IPG313T6S"], "label": "섬유 생산"},
}


def getProductIndicators(stockCode: str) -> list[dict]:
    """kindList 주요제품 → 관련 산업 지표 목록.

    Args:
        stockCode: 종목코드 (예: "005930").

    Returns:
        [{"seriesId": "IPG3344S", "source": "fred", "label": "반도체 생산"}, ...]
        빈 리스트이면 매핑 실패.
    """
    product = _getProductText(stockCode)
    if not product:
        return []

    matched: list[dict] = []
    seen: set[str] = set()

    for keyword, mapping in PRODUCT_INDICATOR_MAP.items():
        if keyword in product:
            for source_key in ["fred", "ecos"]:
                for seriesId in mapping.get(source_key, []):
                    if seriesId not in seen:
                        seen.add(seriesId)
                        matched.append(
                            {
                                "seriesId": seriesId,
                                "source": source_key,
                                "label": mapping["label"],
                                "matchedKeyword": keyword,
                            }
                        )

    return matched


def _getProductText(stockCode: str) -> str:
    """kindList에서 주요제품 텍스트 조회."""
    try:
        from dartlab.gather.listing import getKindList

        df = getKindList()
        row = df.filter(df["종목코드"] == stockCode)
        if row.is_empty():
            return ""
        return str(row["주요제품"][0] or "")
    except (ImportError, KeyError, IndexError):
        return ""


def getProductSummary(stockCode: str) -> dict | None:
    """기업의 제품-지표 매핑 요약.

    Returns:
        {"product": "반도체...", "indicators": [...], "keywords": ["반도체", "메모리"]}
    """
    product = _getProductText(stockCode)
    if not product:
        return None

    indicators = getProductIndicators(stockCode)
    keywords = [ind["matchedKeyword"] for ind in indicators]

    return {
        "product": product,
        "indicators": indicators,
        "keywords": list(set(keywords)),
    }
