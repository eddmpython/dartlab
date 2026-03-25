"""ECOS 지표 카탈로그 — 한국은행 경제통계 21개 주요 지표."""

from __future__ import annotations

import polars as pl

from .types import CatalogEntry

# ── 지표 정의 (eddmpython config.py 포팅) ──

_INDICATORS: dict[str, dict] = {
    # 국민계정
    "GDP": {
        "table": "111Y055",
        "item": "10101",
        "label": "실질GDP",
        "group": "국민계정",
        "freq": "Q",
        "unit": "십억원",
        "desc": "계절조정 실질 국내총생산",
    },
    "GNI": {
        "table": "111Y055",
        "item": "10601",
        "label": "실질GNI",
        "group": "국민계정",
        "freq": "Q",
        "unit": "십억원",
        "desc": "계절조정 실질 국민총소득",
    },
    "GROWTH": {
        "table": "111Y055",
        "item": "10101",
        "label": "경제성장률",
        "group": "국민계정",
        "freq": "Q",
        "unit": "%",
        "desc": "전년동기대비 실질GDP 성장률",
    },
    # 물가
    "CPI": {
        "table": "901Y009",
        "item": "0",
        "label": "소비자물가지수",
        "group": "물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "총지수 (모든 품목)",
    },
    "CORE_CPI": {
        "table": "901Y009",
        "item": "AD",
        "label": "근원물가지수",
        "group": "물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "농산물 및 석유류 제외",
    },
    "PPI": {
        "table": "901Y010",
        "item": "*AA",
        "label": "생산자물가지수",
        "group": "물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "총지수",
    },
    # 금리
    "BASE_RATE": {
        "table": "722Y001",
        "item": "0101000",
        "label": "기준금리",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "한국은행 기준금리",
    },
    "CORP_BOND_3Y": {
        "table": "721Y001",
        "item": "010300000",
        "label": "회사채(3년,AA-)",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "회사채 AA- 등급 3년물 수익률",
    },
    # 환율
    "USDKRW": {
        "table": "731Y003",
        "item": "0000003",
        "label": "원/달러 환율",
        "group": "환율",
        "freq": "D",
        "unit": "원",
        "desc": "미국 달러 매매기준율 (15:30)",
    },
    "JPYKRW": {
        "table": "731Y003",
        "item": "0000006",
        "label": "원/100엔 환율",
        "group": "환율",
        "freq": "D",
        "unit": "원",
        "desc": "일본 엔화 100엔당 매매기준율",
    },
    "EURKRW": {
        "table": "731Y003",
        "item": "0000010",
        "label": "원/유로 환율",
        "group": "환율",
        "freq": "D",
        "unit": "원",
        "desc": "유로화 매매기준율",
    },
    "CNYKRW": {
        "table": "731Y004",
        "item": "0000159",
        "label": "원/위안 환율",
        "group": "환율",
        "freq": "D",
        "unit": "원",
        "desc": "중국 위안화 매매기준율",
    },
    # 통화/금융
    "M2": {
        "table": "161Y005",
        "item": "BBHS00",
        "label": "M2(광의통화)",
        "group": "통화/금융",
        "freq": "M",
        "unit": "십억원",
        "desc": "광의통화(M2) 평잔",
    },
    # 산업/생산
    "IPI": {
        "table": "901Y033",
        "item": "A00",
        "label": "산업생산지수",
        "group": "산업/생산",
        "freq": "M",
        "unit": "2020=100",
        "desc": "전산업생산지수 (농림어업 제외)",
    },
    "MANUFACTURING": {
        "table": "901Y033",
        "item": "AB00",
        "label": "광공업생산",
        "group": "산업/생산",
        "freq": "M",
        "unit": "2020=100",
        "desc": "광공업 생산지수",
    },
    "RETAIL": {
        "table": "901Y049",
        "item": "I16Y",
        "label": "소매판매지수",
        "group": "산업/생산",
        "freq": "M",
        "unit": "2020=100",
        "desc": "소매판매액지수",
    },
    # 무역
    "TRADE": {
        "table": "901Y015",
        "item": "1",
        "label": "무역통계",
        "group": "무역",
        "freq": "M",
        "unit": "억달러",
        "desc": "수출입 합계",
    },
    # 경기/심리
    "CLI": {
        "table": "901Y067",
        "item": "I16A",
        "label": "경기선행지수",
        "group": "경기/심리",
        "freq": "M",
        "unit": "2020=100",
        "desc": "경기선행지수",
    },
    "CCI": {
        "table": "901Y067",
        "item": "I16D",
        "label": "경기동행지수",
        "group": "경기/심리",
        "freq": "M",
        "unit": "2020=100",
        "desc": "경기동행지수 순환변동치",
    },
    "BSI": {
        "table": "512Y014",
        "item": "99988",
        "label": "기업경기실사지수",
        "group": "경기/심리",
        "freq": "M",
        "unit": "지수",
        "desc": "전산업 업황 BSI",
    },
    "CSI": {
        "table": "512Y014",
        "item": "99988",
        "label": "소비자심리지수",
        "group": "경기/심리",
        "freq": "M",
        "unit": "지수",
        "desc": "소비자심리지수(CCSI)",
    },
    # 부동산
    "HOUSE_PRICE": {
        "table": "901Y062",
        "item": "P63A",
        "label": "주택매매가격지수",
        "group": "부동산",
        "freq": "M",
        "unit": "2021.6=100",
        "desc": "전국 주택매매가격지수",
    },
    "APT_PRICE": {
        "table": "901Y062",
        "item": "P63AC",
        "label": "아파트매매가격지수",
        "group": "부동산",
        "freq": "M",
        "unit": "2021.6=100",
        "desc": "전국 아파트매매가격지수",
    },
    # 고용
    "EMPLOYED": {
        "table": "901Y027",
        "item": "I35Y",
        "label": "취업자수",
        "group": "고용",
        "freq": "M",
        "unit": "천명",
        "desc": "15세이상 취업자수",
    },
}

# 빌드 캐시
_entries: dict[str, CatalogEntry] = {}
_groups: dict[str, list[CatalogEntry]] = {}


def _build() -> None:
    """카탈로그 인덱스 빌드 (최초 1회)."""
    if _entries:
        return
    for code, info in _INDICATORS.items():
        entry = CatalogEntry(
            id=code,
            label=info["label"],
            group=info["group"],
            frequency=info["freq"],
            unit=info["unit"],
            description=info["desc"],
            tableCode=info["table"],
            itemCode=info["item"],
        )
        _entries[code] = entry
        _groups.setdefault(info["group"], []).append(entry)


def getEntry(indicatorId: str) -> CatalogEntry | None:
    """지표 ID로 카탈로그 항목 조회."""
    _build()
    return _entries.get(indicatorId)


def getGroups() -> list[str]:
    """그룹 이름 목록."""
    _build()
    return list(_groups.keys())


def getGroup(name: str) -> list[CatalogEntry]:
    """특정 그룹의 지표 목록."""
    _build()
    return _groups.get(name, [])


def getGroupIds(name: str) -> list[str]:
    """특정 그룹의 지표 ID 목록."""
    return [e.id for e in getGroup(name)]


def getAllIds() -> list[str]:
    """전체 지표 ID 목록."""
    _build()
    return list(_entries.keys())


def search(keyword: str) -> list[CatalogEntry]:
    """키워드로 카탈로그 검색 (ID, 라벨, 설명에서 매칭)."""
    _build()
    kw = keyword.lower()
    return [e for e in _entries.values() if kw in e.id.lower() or kw in e.label.lower() or kw in e.description.lower()]


def toDataframe(group: str | None = None) -> pl.DataFrame:
    """카탈로그 → Polars DataFrame."""
    _build()
    entries = getGroup(group) if group else list(_entries.values())
    return pl.DataFrame(
        [
            {
                "id": e.id,
                "label": e.label,
                "group": e.group,
                "frequency": e.frequency,
                "unit": e.unit,
                "description": e.description,
            }
            for e in entries
        ]
    )
