"""ECOS 지표 카탈로그 — 한국은행 경제통계 주요 지표."""

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
    "TREASURY_3Y": {
        "table": "721Y001",
        "item": "010200000",
        "label": "국고채(3년)",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "국고채 3년물 수익률",
    },
    "TREASURY_5Y": {
        "table": "721Y001",
        "item": "010200001",
        "label": "국고채(5년)",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "국고채 5년물 수익률",
    },
    "TREASURY_10Y": {
        "table": "721Y001",
        "item": "010200002",
        "label": "국고채(10년)",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "국고채 10년물 수익률",
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
    "CORP_BOND_BBB_5Y": {
        "table": "721Y001",
        "item": "010400000",
        "label": "회사채(5년,BBB-)",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "회사채 BBB- 등급 5년물 수익률",
    },
    "CD_91D": {
        "table": "721Y001",
        "item": "010100000",
        "label": "CD(91일)",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "CD 91일물 수익률",
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
    # 서비스업 생산 (외생변수 Axis 5)
    "SVC_PROD": {
        "table": "901Y033",
        "item": "AC00",
        "label": "서비스업생산지수",
        "group": "산업/생산",
        "freq": "M",
        "unit": "2020=100",
        "desc": "서비스업 생산지수",
    },
    # BSI 기업경기실사 (외생변수 Axis 3)
    "BSI_ALL": {
        "table": "512Y014",
        "item": "99988",
        "label": "BSI 전산업",
        "group": "경기/심리",
        "freq": "M",
        "unit": "지수",
        "desc": "전산업 업황 BSI (기업체감경기)",
    },
    "BSI_DOMESTIC": {
        "table": "512Y014",
        "item": "X9000",
        "label": "BSI 내수기업",
        "group": "경기/심리",
        "freq": "M",
        "unit": "지수",
        "desc": "내수기업 업황 BSI",
    },
    "BSI_EXPORT": {
        "table": "512Y014",
        "item": "X8000",
        "label": "BSI 수출기업",
        "group": "경기/심리",
        "freq": "M",
        "unit": "지수",
        "desc": "수출기업 업황 BSI",
    },
    # 한국 PPI 세부 (업종별 판가/원가 직접 지표)
    "PPI_SEMI": {
        "table": "403Y003",
        "item": "3091AA",
        "label": "반도체PPI(한국)",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 반도체",
    },
    "PPI_DISPLAY": {
        "table": "403Y003",
        "item": "3092AA",
        "label": "디스플레이PPI",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 전자표시장치",
    },
    "PPI_AUTO": {
        "table": "403Y003",
        "item": "3121AA",
        "label": "자동차PPI(한국)",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 자동차및부품",
    },
    "PPI_PHARMA": {
        "table": "403Y003",
        "item": "3054AA",
        "label": "의약품PPI",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 의약품",
    },
    "PPI_FOOD": {
        "table": "403Y003",
        "item": "3011AA",
        "label": "식료품PPI",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 식료품",
    },
    "PPI_STEEL": {
        "table": "403Y003",
        "item": "3071AA",
        "label": "철강PPI",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 철강1차제품",
    },
    "PPI_CHEM": {
        "table": "403Y003",
        "item": "3051AA",
        "label": "기초화학PPI",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 기초화학물질",
    },
    "PPI_OIL": {
        "table": "403Y003",
        "item": "3041AA",
        "label": "석유제품PPI",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 석탄및석유제품",
    },
    "PPI_ELEC": {
        "table": "403Y003",
        "item": "3101AA",
        "label": "전기장비PPI",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 전기장비",
    },
    "PPI_MACHINE": {
        "table": "403Y003",
        "item": "311AA",
        "label": "기계장비PPI",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 기계및장비",
    },
    "PPI_PLASTIC": {
        "table": "403Y003",
        "item": "3057AA",
        "label": "플라스틱PPI",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 플라스틱제품",
    },
    "PPI_TEXTILE": {
        "table": "403Y003",
        "item": "3021AA",
        "label": "섬유의복PPI",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 섬유및의복",
    },
    "PPI_MFG": {
        "table": "403Y003",
        "item": "3AA",
        "label": "공산품PPI",
        "group": "생산자물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "생산자물가 공산품 전체",
    },
    # 교역조건 (수출/수입 물가)
    "EXPORT_PRICE": {
        "table": "403Y001",
        "item": "*AA",
        "label": "수출물가지수",
        "group": "무역",
        "freq": "M",
        "unit": "2020=100",
        "desc": "수출물가지수 총지수",
    },
    "IMPORT_PRICE": {
        "table": "403Y002",
        "item": "*AA",
        "label": "수입물가지수",
        "group": "무역",
        "freq": "M",
        "unit": "2020=100",
        "desc": "수입물가지수 총지수",
    },
    # 재고순환 프록시 (ECOS에서 출하/재고지수 직접 미제공 — 통계청 KOSIS 전용)
    # 광공업생산 모멘텀 + BSI로 재고순환 대용
    # MANUFACTURING(AB00)은 이미 등록 → 출하 프록시
    # BSI_ALL(99988)은 이미 등록 → 재고판단 프록시
    # 설비투자
    "FACILITY_INV": {
        "table": "901Y066",
        "item": "A00",
        "label": "설비투자지수",
        "group": "산업/생산",
        "freq": "M",
        "unit": "2020=100",
        "desc": "설비투자지수 (원지수)",
    },
    # 신용 (Credit-to-GDP)
    "CREDIT_TOTAL": {
        "table": "104Y016",
        "item": "BBGA11",
        "label": "총국내신용",
        "group": "통화/금융",
        "freq": "M",
        "unit": "십억원",
        "desc": "예금은행 + 비은행 총국내신용",
    },
    # 소비자기대지수 (선행 심리)
    "CSI_FUTURE": {
        "table": "513Y001",
        "item": "FME",
        "label": "소비자기대지수",
        "group": "경기/심리",
        "freq": "M",
        "unit": "지수",
        "desc": "소비자기대지수(향후 경기전망)",
    },
    # 경기후행지수
    "CLI_LAG": {
        "table": "901Y067",
        "item": "I16G",
        "label": "경기후행지수",
        "group": "경기/심리",
        "freq": "M",
        "unit": "2020=100",
        "desc": "경기후행지수 순환변동치",
    },
    # 경상수지 (수출 기업 매출과 직접 연결)
    "EXPORT": {
        "table": "301Y013",
        "item": "110000",
        "label": "상품수출",
        "group": "무역",
        "freq": "M",
        "unit": "백만달러",
        "desc": "상품수출(국제수지)",
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
