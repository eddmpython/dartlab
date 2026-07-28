"""ECOS 지표 카탈로그 — 한국은행 경제통계 주요 지표."""

from __future__ import annotations

import polars as pl

from .types import CatalogEntry

# ── 지표 정의 (eddmpython config.py 포팅) ──

_INDICATORS: dict[str, dict] = {
    # 국민계정
    "GDP": {
        "table": "200Y108",
        "item": "10601",
        "label": "실질GDP",
        "group": "국민계정",
        "freq": "Q",
        "unit": "십억원",
        "desc": "계절조정 실질 국내총생산",
    },
    "GNI": {
        "table": "200Y104",
        "item": "1800",
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
        "table": "901Y010",
        "item": "QB",
        "label": "근원물가지수",
        "group": "물가",
        "freq": "M",
        "unit": "2020=100",
        "desc": "농산물 및 석유류 제외",
    },
    "PPI": {
        "table": "404Y014",
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
        "table": "817Y002",
        "item": "010200000",
        "label": "국고채(3년)",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "국고채 3년물 수익률",
    },
    "TREASURY_5Y": {
        "table": "817Y002",
        "item": "010200001",
        "label": "국고채(5년)",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "국고채 5년물 수익률",
    },
    "TREASURY_10Y": {
        "table": "817Y002",
        "item": "010210000",
        "label": "국고채(10년)",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "국고채 10년물 수익률",
    },
    "CORP_BOND_3Y": {
        "table": "817Y002",
        "item": "010300000",
        "label": "회사채(3년,AA-)",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "회사채 AA- 등급 3년물 수익률",
    },
    "CORP_BOND_BBB_5Y": {
        "table": "817Y002",
        "item": "010320000",
        "label": "회사채(3년,BBB-)",
        "group": "금리",
        "freq": "D",
        "unit": "%",
        "desc": "회사채 BBB- 등급 5년물 수익률",
    },
    "CD_91D": {
        "table": "817Y002",
        "item": "010502000",
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
        "table": "731Y003",
        "item": "0000007",
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
        "item": "I61BA",
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
        "item": "I15A",
        "label": "설비투자지수",
        "group": "산업/생산",
        "freq": "M",
        "unit": "2020=100",
        "desc": "설비투자지수 (원지수)",
    },
    # 신용 (Credit-to-GDP)
    "CREDIT_TOTAL": {
        "table": "104Y016",
        "item": "BDCA1",
        "label": "총국내신용",
        "group": "통화/금융",
        "freq": "M",
        "unit": "십억원",
        "desc": "예금은행 + 비은행 총국내신용",
    },
    # 소비자기대지수 (선행 심리)
    "CSI_FUTURE": {
        "table": "513Y001",
        "item": "E1000",
        "label": "소비자기대지수",
        "group": "경기/심리",
        "freq": "M",
        "unit": "지수",
        "desc": "소비자기대지수(향후 경기전망)",
    },
    # 경기후행지수
    "CLI_LAG": {
        "table": "901Y067",
        "item": "I16C",
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
_INDICATOR_ALIASES: dict[str, str] = {
    "DEXKOUS": "USDKRW",
    "KRWUSD": "USDKRW",
    "USD/KRW": "USDKRW",
    "KRW/USD": "USDKRW",
    "DOLLARKRW": "USDKRW",
    "원달러": "USDKRW",
    "원/달러": "USDKRW",
}


def _build() -> None:
    """카탈로그 인덱스 빌드 (최초 1회).

    Returns
    -------
    None
        ``_entries``/``_groups`` 모듈 변수에 인덱스를 채운다.
    """
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
    """지표 ID 또는 한글 레이블로 카탈로그 항목 조회.

    Parameters
    ----------
    indicatorId : str
        ECOS 카탈로그 지표 ID (예: "GDP", "CPI") 또는 한글 레이블 (예: "기준금리", "국고채(3년)").

    Returns
    -------
    CatalogEntry | None
        매칭된 카탈로그 엔트리. 없으면 None.

    Raises
    ------
    없음
        미존재 시 None 반환.

    Example
    -------
    >>> e = getEntry("GDP")

    Capabilities
    ------------
    indicator ID 또는 한글 label 양쪽 매칭 → CatalogEntry.
    AIContext: AI 가 "기준금리" 같은 자연어 입력해도 정확 매칭.
    Guide: resolveId alias 우선 → 정확 ID lookup → label scan.
    When: 사용자/AI 입력의 indicator 정규화 진입 시.
    How: resolveId → _entries[canonical] → label 매칭 fallback.
    Requires: _build() 가 카탈로그 인덱스 사전 빌드.
    See Also: resolveId · getAllIds · search.
    """
    _build()
    canonical = resolveId(indicatorId)
    hit = _entries.get(canonical)
    if hit is not None:
        return hit
    # 한글 레이블로도 매칭 (AI 가 "기준금리" 같은 레이블을 전달할 때)
    for entry in _entries.values():
        if entry.label == indicatorId:
            return entry
    return None


def resolveId(indicatorId: str | None) -> str | None:
    """사용자/AI 표기 지표명을 ECOS 정식 ID 로 정규화한다.

    Parameters
    ----------
    indicatorId : str | None
        사용자/AI 가 입력한 지표명 또는 alias.

    Returns
    -------
    str | None
        정규화된 ECOS 카탈로그 ID. None/빈 문자열 입력은 그대로 반환.

    Raises
    ------
    없음
        매칭 실패 시 원본 그대로 반환 (대문자/공백 제거 후).

    Example
    -------
    >>> resolveId("기준금리")

    Capabilities
    ------------
    _INDICATOR_ALIASES dict 매칭 → canonical ID. uppercase + space 제거.
    AIContext: USDKRW 별칭 (DEXKOUS, KRWUSD, 원/달러 등) 정규화 진입.
    Guide: 매칭 안 되면 strip + upper 원본 반환.
    When: getEntry / facade 진입 직전.
    How: ``key.upper().replace(' ', '')`` → ``_INDICATOR_ALIASES.get(aliasKey, key)``.
    Requires: _INDICATOR_ALIASES dict.
    See Also: getEntry · _INDICATOR_ALIASES.
    """
    if indicatorId is None:
        return None
    key = str(indicatorId).strip()
    if not key:
        return key
    aliasKey = key.upper().replace(" ", "")
    return _INDICATOR_ALIASES.get(aliasKey, key)


def getGroups() -> list[str]:
    """그룹 이름 목록.

    Returns
    -------
    list[str]
        등록된 그룹명 리스트 (예: ["국민계정", "물가", "금리", ...]).

    Raises
    ------
    없음.

    Example
    -------
    >>> getGroups()

    Capabilities
    ------------
    _groups dict keys → list.
    AIContext: ECOS 카테고리 universe 노출 — UI dropdown / catalog 진입.
    Guide: dict 순서 보장.
    When: 카탈로그 그룹 list 필요 시.
    How: ``list(_groups.keys())``.
    Requires: _build() 사전 호출.
    See Also: getGroup · getGroupIds.
    """
    _build()
    return list(_groups.keys())


def getGroup(name: str) -> list[CatalogEntry]:
    """특정 그룹의 지표 목록.

    Parameters
    ----------
    name : str
        그룹명 (예: "금리", "환율").

    Returns
    -------
    list[CatalogEntry]
        해당 그룹의 카탈로그 엔트리 리스트. 그룹이 없으면 빈 리스트.

    Raises
    ------
    없음
        미존재 그룹은 빈 리스트.

    Example
    -------
    >>> entries = getGroup("물가")

    Capabilities
    ------------
    _groups[name] → CatalogEntry list.
    AIContext: 그룹 단위 fetch 직전 entry detail 확인 진입.
    Guide: 미존재 그룹 빈 list — silent.
    When: facade.group 의 사용자/AI 입력 dispatch 시.
    How: ``_groups.get(name, [])``.
    Requires: _build() 사전 호출.
    See Also: getGroupIds · facade.group.
    """
    _build()
    return _groups.get(name, [])


def getGroupIds(name: str) -> list[str]:
    """특정 그룹의 지표 ID 목록.

    Parameters
    ----------
    name : str
        그룹명.

    Returns
    -------
    list[str]
        해당 그룹의 지표 ID 리스트 (예: ["BASE_RATE", "TREASURY_3Y", ...]).

    Raises
    ------
    없음
        미존재 그룹은 빈 리스트.

    Example
    -------
    >>> ids = getGroupIds("금리")

    Capabilities
    ------------
    getGroup → [e.id for e in entries].
    AIContext: 그룹 단위 fetchMulti 직전 ID list 추출.
    Guide: 미존재 그룹 빈 list.
    When: facade.group 의 bulk fetch 직전.
    How: ``[e.id for e in getGroup(name)]``.
    Requires: getGroup 동작.
    See Also: series.fetchMulti.
    """
    return [e.id for e in getGroup(name)]


def getAllIds() -> list[str]:
    """전체 지표 ID 목록.

    Returns
    -------
    list[str]
        카탈로그에 등록된 모든 지표 ID 리스트.

    Raises
    ------
    없음.

    Example
    -------
    >>> ids = getAllIds()

    Capabilities
    ------------
    _entries dict keys → list.
    AIContext: 운영자 cron 의 ECOS publish universe / 사용자 catalog.
    Guide: 중복 ID 없음 — dict key unique.
    When: bulk publish / 카탈로그 동기화 시.
    How: ``list(_entries.keys())``.
    Requires: _build() 사전 호출.
    See Also: getGroupIds · scripts/build/macroBuild.
    """
    _build()
    return list(_entries.keys())


def search(keyword: str, *, limit: int | None = None) -> list[CatalogEntry]:
    """키워드로 카탈로그 검색 (ID, 라벨, 설명에서 매칭).

    Parameters
    ----------
    keyword : str
        검색 키워드 (대소문자 무시).
    limit : int | None
        반환 행수 상한. None이면 전체.

    Returns
    -------
    list[CatalogEntry]
        매칭된 카탈로그 엔트리 리스트.

    Raises
    ------
    없음
        매칭 0건은 빈 리스트.

    Example
    -------
    >>> hits = search("물가", limit=5)

    Capabilities
    ------------
    id/label/description substring 매칭 (lowercase) → entry list.
    AIContext: 카탈로그 fuzzy 탐색 — 한글/영문 키워드.
    Guide: case-insensitive substring 만. fuzzy (자모) 미지원.
    When: 사용자가 카탈로그에서 특정 키워드 탐색 시.
    How: ``[e for e in _entries.values() if kw in e.id|label|description]``.
    Requires: _build() 사전 호출.
    See Also: getEntry : 정확 매칭.
    """
    _build()
    kw = keyword.lower()
    result = [
        e for e in _entries.values() if kw in e.id.lower() or kw in e.label.lower() or kw in e.description.lower()
    ]
    if limit is not None and limit > 0:
        return result[:limit]
    return result


def toDataframe(group: str | None = None) -> pl.DataFrame:
    """카탈로그 → Polars DataFrame.

    Parameters
    ----------
    group : str | None
        특정 그룹만 필터. None이면 전체.

    Returns
    -------
    pl.DataFrame
        컬럼: ``id`` (Utf8) — 지표 ID, ``label`` (Utf8) — 한글 라벨,
        ``group`` (Utf8) — 그룹명, ``frequency`` (Utf8) — 주기 코드,
        ``unit`` (Utf8) — 단위, ``description`` (Utf8) — 설명.

    Raises
    ------
    없음
        미존재 그룹은 빈 DataFrame.

    Example
    -------
    >>> df = toDataframe(group="물가")

    Capabilities
    ------------
    entries → DataFrame (id/label/group/frequency/unit/description).
    AIContext: facade.catalog 의 본체 — 사용자 catalog UI 표시.
    Guide: group 미명시 시 전체.
    When: catalog UI / dashboard / 외부 export 시.
    How: getGroup or _entries.values() → list[dict] → pl.DataFrame.
    Requires: polars + _build().
    See Also: facade.Ecos.catalog.
    """
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
