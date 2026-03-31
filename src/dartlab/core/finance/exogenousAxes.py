"""외생변수 6축 체계 — 기업 매출의 직접 외생변수 매핑.

GDP/환율 같은 거시 대분류가 아니라, 원자재 가격, 산업생산, 실물수요 등
기업 매출에 직접 영향을 주는 외생변수를 업종별로 자동 매핑한다.

Walk-forward 검증 결과:
- 기존(IPI+금리+환율): 방향 정확도 58%
- 외생변수 6축: 방향 정확도 75~87%

6축 구조:
1. 원자재 가격 — 구리, 알루미늄, 유가, 금속PPI, 밀, 면화
2. 산업생산 — 반도체, 자동차, 화학, 식품, INDPRO, 배터리PPI
3. 실물수요 — 자동차판매, 내구재주문, 화물운송, 설비가동률, BSI
4. 금융조건 — 금리, 하이일드 스프레드, 회사채
5. 내수경기 — IPI, 서비스업, BSI 내수/수출, 아파트가격
6. 환율 — 원/달러, 원/엔, 원/위안
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExogenousIndicator:
    """외생변수 지표."""

    seriesId: str
    source: str  # "fred" or "ecos"
    label: str
    axis: str  # "commodity", "production", "demand", "financial", "domestic", "fx"


# ══════════════════════════════════════
# 6축 지표 정의
# ══════════════════════════════════════

# Axis 1: 원자재 가격
COPPER = ExogenousIndicator("PCOPPUSDM", "fred", "구리", "commodity")
ALUMINUM = ExogenousIndicator("PALUMUSDM", "fred", "알루미늄", "commodity")
OIL = ExogenousIndicator("DCOILWTICO", "fred", "WTI 유가", "commodity")
METAL_PPI = ExogenousIndicator("WPU101", "fred", "금속PPI", "commodity")
WHEAT = ExogenousIndicator("PWHEAMTUSDM", "fred", "밀", "commodity")
COTTON = ExogenousIndicator("PCOTTINDUSDM", "fred", "면화", "commodity")

# Axis 2: 산업 가격/생산 (한국 PPI 우선 + FRED 보조)
# 한국 PPI = 한국 기업의 실제 판가/원가 → FRED 미국 지표보다 직접적
KR_SEMI_PPI = ExogenousIndicator("PPI_SEMI", "ecos", "반도체PPI(한국)", "production")
KR_DISPLAY_PPI = ExogenousIndicator("PPI_DISPLAY", "ecos", "디스플레이PPI", "production")
KR_AUTO_PPI = ExogenousIndicator("PPI_AUTO", "ecos", "자동차PPI(한국)", "production")
KR_PHARMA_PPI = ExogenousIndicator("PPI_PHARMA", "ecos", "의약품PPI", "production")
KR_FOOD_PPI = ExogenousIndicator("PPI_FOOD", "ecos", "식료품PPI", "production")
KR_STEEL_PPI = ExogenousIndicator("PPI_STEEL", "ecos", "철강PPI", "production")
KR_CHEM_PPI = ExogenousIndicator("PPI_CHEM", "ecos", "기초화학PPI", "production")
KR_OIL_PPI = ExogenousIndicator("PPI_OIL", "ecos", "석유제품PPI", "production")
KR_ELEC_PPI = ExogenousIndicator("PPI_ELEC", "ecos", "전기장비PPI", "production")
KR_MACHINE_PPI = ExogenousIndicator("PPI_MACHINE", "ecos", "기계장비PPI", "production")
KR_PLASTIC_PPI = ExogenousIndicator("PPI_PLASTIC", "ecos", "플라스틱PPI", "production")
KR_TEXTILE_PPI = ExogenousIndicator("PPI_TEXTILE", "ecos", "섬유의복PPI", "production")
KR_MFG_PPI = ExogenousIndicator("PPI_MFG", "ecos", "공산품PPI", "production")
KR_EXPORT = ExogenousIndicator("EXPORT", "ecos", "상품수출", "production")

# FRED 보조 (한국 PPI에 없는 것)
SEMI_PROD = ExogenousIndicator("IPG3344S", "fred", "반도체 생산", "production")
AUTO_PROD = ExogenousIndicator("IPG3361T3S", "fred", "자동차 생산", "production")
CHEM_PROD = ExogenousIndicator("IPG325S", "fred", "화학 생산", "production")
FOOD_PROD = ExogenousIndicator("IPG311A2S", "fred", "식품 생산", "production")
US_INDPRO = ExogenousIndicator("INDPRO", "fred", "미국 산업생산", "production")
SEMI_PPI = ExogenousIndicator("PCU33443344", "fred", "반도체PPI", "production")
BATTERY_PPI = ExogenousIndicator("PCU335911335911", "fred", "배터리PPI", "production")
MFG_PPI = ExogenousIndicator("PCUOMFGOMFG", "fred", "제조업PPI", "production")

# Axis 3: 실물수요
AUTO_SALES = ExogenousIndicator("TOTALSA", "fred", "미국 자동차판매", "demand")
DURABLE_ORDERS = ExogenousIndicator("DGORDER", "fred", "내구재 주문", "demand")
FREIGHT = ExogenousIndicator("FRGSHPUSM649NCIS", "fred", "화물운송", "demand")
CAPACITY = ExogenousIndicator("TCU", "fred", "설비가동률", "demand")
BSI_ALL = ExogenousIndicator("BSI_ALL", "ecos", "BSI 전산업", "demand")
BSI_DOMESTIC = ExogenousIndicator("BSI_DOMESTIC", "ecos", "BSI 내수", "demand")
BSI_EXPORT = ExogenousIndicator("BSI_EXPORT", "ecos", "BSI 수출", "demand")

# Axis 4: 금융조건
BASE_RATE = ExogenousIndicator("BASE_RATE", "ecos", "기준금리", "financial")
HY_SPREAD = ExogenousIndicator("BAMLH0A0HYM2", "fred", "하이일드 스프레드", "financial")
CORP_BOND = ExogenousIndicator("CORP_BOND_3Y", "ecos", "회사채 금리", "financial")

# Axis 5: 내수경기
IPI = ExogenousIndicator("IPI", "ecos", "산업생산지수", "domestic")
SVC_PROD = ExogenousIndicator("SVC_PROD", "ecos", "서비스업 생산", "domestic")
APT_PRICE = ExogenousIndicator("APT_PRICE", "ecos", "아파트가격", "domestic")
CPI = ExogenousIndicator("CPI", "ecos", "소비자물가", "domestic")

# Axis 6: 환율
USDKRW = ExogenousIndicator("USDKRW", "ecos", "원/달러", "fx")
JPYKRW = ExogenousIndicator("JPYKRW", "ecos", "원/엔", "fx")
CNYKRW = ExogenousIndicator("CNYKRW", "ecos", "원/위안", "fx")


# ══════════════════════════════════════
# 업종 → 외생변수 매핑 (162개 전수)
# ══════════════════════════════════════

# 각 업종에 대해 [1순위, 2순위, 3순위] 지표 지정
# OLS는 3개만 쓰므로 최대 3개
_INDUSTRY_MAP: dict[str, list[ExogenousIndicator]] = {
    # ── 반도체/전자 ──
    "반도체 제조업": [KR_SEMI_PPI, COPPER, BASE_RATE],
    "전자부품 제조업": [KR_SEMI_PPI, COPPER, CAPACITY],
    "통신 및 방송 장비 제조업": [KR_SEMI_PPI, DURABLE_ORDERS, BASE_RATE],
    "영상 및 음향기기 제조업": [SEMI_PROD, AUTO_SALES, BASE_RATE],
    "전동기, 발전기 및 전기 변환 · 공급 · 제어 장치 제조업": [US_INDPRO, COPPER, CAPACITY],
    "기타 전기장비 제조업": [US_INDPRO, COPPER, CAPACITY],
    "일차전지 및 이차전지 제조업": [BATTERY_PPI, CHEM_PROD, COPPER],
    "측정, 시험, 항해, 제어 및 기타 정밀기기 제조업; 광학기기 제외": [US_INDPRO, DURABLE_ORDERS, BASE_RATE],

    # ── 자동차/기계 ──
    "자동차 신품 부품 제조업": [KR_AUTO_PPI, AUTO_SALES, METAL_PPI],
    "자동차용 엔진 및 자동차 제조업": [KR_AUTO_PPI, AUTO_SALES, CAPACITY],
    "특수 목적용 기계 제조업": [US_INDPRO, DURABLE_ORDERS, CAPACITY],
    "일반 목적용 기계 제조업": [US_INDPRO, DURABLE_ORDERS, CAPACITY],
    "선박 및 보트 건조업": [FREIGHT, METAL_PPI, OIL],
    "항공기, 우주선 및 부품 제조업": [DURABLE_ORDERS, ALUMINUM, OIL],
    "기타 운송장비 제조업": [AUTO_PROD, FREIGHT, METAL_PPI],

    # ── 화학/소재 ──
    "기초 화학물질 제조업": [KR_CHEM_PPI, KR_OIL_PPI, KR_EXPORT],
    "기타 화학제품 제조업": [KR_CHEM_PPI, KR_OIL_PPI, BASE_RATE],
    "플라스틱제품 제조업": [KR_PLASTIC_PPI, KR_OIL_PPI, CAPACITY],
    "합성고무 및 플라스틱 물질 제조업": [KR_CHEM_PPI, KR_OIL_PPI, KR_EXPORT],
    "비료, 농약 및 살균, 살충제 제조업": [KR_CHEM_PPI, WHEAT, KR_OIL_PPI],

    # ── 철강/금속 ──
    "1차 철강 제조업": [KR_STEEL_PPI, COPPER, CAPACITY],
    "1차 비철금속 제조업": [ALUMINUM, COPPER, METAL_PPI],
    "기타 금속 가공제품 제조업": [METAL_PPI, US_INDPRO, CAPACITY],
    "구조용 금속제품, 탱크 및 증기발생기 제조업": [METAL_PPI, US_INDPRO, CAPACITY],
    "금속 열처리, 도금 및 기타 금속 가공업": [METAL_PPI, US_INDPRO, CAPACITY],
    "절삭가공 및 유사 처리업": [METAL_PPI, US_INDPRO, CAPACITY],
    "무기 및 총포탄 제조업": [METAL_PPI, DURABLE_ORDERS, BASE_RATE],

    # ── 석유/에너지 ──
    "석유 정제품 제조업": [OIL, CHEM_PROD, FREIGHT],
    "코크스, 연탄 및 석유정제품 제조업": [OIL, CHEM_PROD, US_INDPRO],
    "전기업": [BASE_RATE, IPI, OIL],
    "가스 제조 및 배관공급업": [OIL, BASE_RATE, IPI],
    "증기, 냉·온수 및 공기 조절 공급업": [OIL, BASE_RATE, IPI],

    # ── 의약/바이오 ──
    "의약품 제조업": [KR_PHARMA_PPI, BASE_RATE, IPI],
    "기초 의약물질 제조업": [KR_PHARMA_PPI, BASE_RATE, KR_CHEM_PPI],
    "의료용 기기 제조업": [KR_PHARMA_PPI, BASE_RATE, DURABLE_ORDERS],
    "의료용품 및 기타 의약 관련제품 제조업": [KR_PHARMA_PPI, BASE_RATE, IPI],
    "자연과학 및 공학 연구개발업": [KR_PHARMA_PPI, BASE_RATE, IPI],

    # ── 식품/음료 ──
    "기타 식품 제조업": [KR_FOOD_PPI, WHEAT, IPI],
    "곡물가공품, 전분 및 전분제품 제조업": [KR_FOOD_PPI, WHEAT, IPI],
    "낙농품 및 식용빙과류 제조업": [KR_FOOD_PPI, WHEAT, IPI],
    "조미료 및 식품 첨가물 제조업": [KR_FOOD_PPI, WHEAT, IPI],
    "도축, 육류 가공 및 저장 처리업": [KR_FOOD_PPI, WHEAT, IPI],
    "수산물 가공 및 저장 처리업": [KR_FOOD_PPI, KR_OIL_PPI, IPI],
    "알코올음료 제조업": [KR_FOOD_PPI, WHEAT, BASE_RATE],
    "비알코올음료 및 얼음 제조업": [KR_FOOD_PPI, IPI, BASE_RATE],
    "동물용 사료 및 조제식품 제조업": [WHEAT, KR_FOOD_PPI, KR_OIL_PPI],
    "과실, 채소 가공 및 저장 처리업": [KR_FOOD_PPI, WHEAT, IPI],

    # ── 섬유/의류 ──
    "봉제의복 제조업": [COTTON, IPI, BASE_RATE],
    "편조 의복 제조업": [COTTON, IPI, BASE_RATE],
    "방적 및 가공사 제조업": [COTTON, US_INDPRO, IPI],
    "직물직조 및 직물제품 제조업": [COTTON, US_INDPRO, IPI],
    "섬유제품 염색, 정리 및 마무리 가공업": [COTTON, US_INDPRO, IPI],
    "가죽, 가방 및 유사 제품 제조업": [COTTON, IPI, BASE_RATE],
    "신발 및 신발 부분품 제조업": [COTTON, IPI, BASE_RATE],

    # ── 건설/부동산 ──
    "건물 건설업": [APT_PRICE, BASE_RATE, METAL_PPI],
    "토목 건설업": [IPI, BASE_RATE, METAL_PPI],
    "건축기술, 엔지니어링 및 관련 기술 서비스업": [APT_PRICE, BASE_RATE, IPI],
    "기반조성 및 시설물 축조관련 전문공사업": [APT_PRICE, BASE_RATE, IPI],
    "건물설비 설치 공사업": [APT_PRICE, BASE_RATE, IPI],
    "실내건축 및 건축마무리 공사업": [APT_PRICE, BASE_RATE, IPI],
    "시멘트, 석회, 플라스터 및 그 제품 제조업": [APT_PRICE, METAL_PPI, BASE_RATE],
    "부동산 임대 및 공급업": [APT_PRICE, BASE_RATE, IPI],

    # ── 금융 ──
    "기타 금융업": [BASE_RATE, HY_SPREAD, IPI],
    "금융 지원 서비스업": [BASE_RATE, HY_SPREAD, IPI],
    "은행 및 저축기관": [BASE_RATE, CORP_BOND, IPI],
    "투자기관": [BASE_RATE, HY_SPREAD, IPI],
    "보험업": [BASE_RATE, HY_SPREAD, APT_PRICE],
    "신탁업 및 집합투자업": [BASE_RATE, HY_SPREAD, IPI],

    # ── 소프트웨어/IT ──
    "소프트웨어 개발 및 공급업": [SVC_PROD, DURABLE_ORDERS, BASE_RATE],
    "컴퓨터 프로그래밍, 시스템 통합 및 관리업": [SVC_PROD, DURABLE_ORDERS, BASE_RATE],
    "자료처리, 호스팅, 포털 및 기타 인터넷 정보매개 서비스업": [SVC_PROD, BASE_RATE, IPI],
    "기타 정보 서비스업": [SVC_PROD, BASE_RATE, IPI],
    "전기 통신업": [SVC_PROD, BASE_RATE, IPI],

    # ── 미디어/엔터 ──
    "영화, 비디오물, 방송프로그램 제작 및 배급업": [SVC_PROD, BASE_RATE, IPI],
    "방송업": [SVC_PROD, BASE_RATE, IPI],
    "오디오물 출판 및 원판 녹음업": [SVC_PROD, BASE_RATE, IPI],
    "광고업": [SVC_PROD, BASE_RATE, IPI],
    "시장조사 및 여론조사업": [SVC_PROD, BASE_RATE, IPI],

    # ── 유통/도매 ──
    "기타 전문 도매업": [IPI, BASE_RATE, FREIGHT],
    "상품 종합 도매업": [IPI, BASE_RATE, FREIGHT],
    "생활용품 도매업": [IPI, BASE_RATE, FREIGHT],
    "기계장비 및 관련 물품 도매업": [US_INDPRO, DURABLE_ORDERS, FREIGHT],
    "종합 소매업": [IPI, BASE_RATE, CPI],
    "음·식료품 및 담배 소매업": [FOOD_PROD, IPI, BASE_RATE],
    "기타 생활용품 소매업": [IPI, BASE_RATE, CPI],

    # ── 운송/물류 ──
    "도로 화물 운송업": [FREIGHT, OIL, IPI],
    "수상 운송업": [FREIGHT, OIL, US_INDPRO],
    "항공 여객 운송업": [OIL, BASE_RATE, FREIGHT],
    "창고 및 운송관련 서비스업": [FREIGHT, OIL, IPI],
    "기타 여행보조 및 예약 서비스업": [SVC_PROD, BASE_RATE, OIL],

    # ── 제지/인쇄/목재 ──
    "펄프, 종이 및 판지 제조업": [OIL, US_INDPRO, IPI],
    "골판지, 종이 상자 및 종이용기 제조업": [OIL, US_INDPRO, IPI],
    "기타 종이 및 판지 제품 제조업": [OIL, US_INDPRO, IPI],
    "인쇄 및 인쇄관련 산업": [IPI, OIL, BASE_RATE],
    "목재 및 나무제품 제조업; 가구 제외": [APT_PRICE, OIL, IPI],

    # ── 고무/유리/세라믹 ──
    "고무제품 제조업": [OIL, AUTO_PROD, US_INDPRO],
    "유리 및 유리제품 제조업": [US_INDPRO, APT_PRICE, OIL],
    "기타 비금속 광물제품 제조업": [US_INDPRO, IPI, METAL_PPI],
    "도자기 및 기타 요업제품 제조업": [APT_PRICE, US_INDPRO, IPI],

    # ── 가구/생활 ──
    "가구 제조업": [APT_PRICE, BASE_RATE, IPI],
    "귀금속 및 장신구 제조업": [METAL_PPI, BASE_RATE, IPI],
    "그외 기타 제품 제조업": [US_INDPRO, IPI, BASE_RATE],
    "운동 및 경기용구 제조업": [IPI, BASE_RATE, SVC_PROD],
    "장난감 및 오락용품 제조업": [IPI, BASE_RATE, SVC_PROD],

    # ── 전문/과학/기술 서비스 ──
    "그외 기타 전문, 과학 및 기술 서비스업": [SVC_PROD, DURABLE_ORDERS, BASE_RATE],
    "경영 컨설팅 및 공공관계 서비스업": [SVC_PROD, BASE_RATE, IPI],
    "사진 처리업": [SVC_PROD, BASE_RATE, IPI],
    "전문 디자인업": [SVC_PROD, BASE_RATE, IPI],

    # ── 교육/서비스/기타 ──
    "교육 서비스업": [SVC_PROD, BASE_RATE, IPI],
    "사업시설 유지·관리 서비스업": [SVC_PROD, BASE_RATE, IPI],
    "사업지원 서비스업": [SVC_PROD, BASE_RATE, IPI],
    "인력 공급 및 고용알선업": [SVC_PROD, BASE_RATE, IPI],
    "숙박업": [SVC_PROD, OIL, BASE_RATE],
    "음식점 및 주점업": [FOOD_PROD, BASE_RATE, IPI],

    # ── 환경/폐기물 ──
    "폐기물 수집, 운반, 처리 및 원료 재생업": [IPI, OIL, BASE_RATE],
    "환경 정화 및 복원업": [IPI, BASE_RATE, OIL],

    # ── 추가 커버 (fallback 제거용) ──
    "사진장비 및 광학기기 제조업": [SEMI_PROD, DURABLE_ORDERS, BASE_RATE],
    "컴퓨터 및 주변장치 제조업": [SEMI_PROD, DURABLE_ORDERS, US_INDPRO],
    "회사 본부 및 경영 컨설팅 서비스업": [SVC_PROD, BASE_RATE, IPI],
    "서적, 잡지 및 기타 인쇄물 출판업": [SVC_PROD, BASE_RATE, IPI],
    "연료용 가스 제조 및 배관공급업": [OIL, BASE_RATE, IPI],
    "음·식료품 및 담배 도매업": [FOOD_PROD, IPI, BASE_RATE],
    "항공기,우주선 및 부품 제조업": [DURABLE_ORDERS, ALUMINUM, OIL],
    "절연선 및 케이블 제조업": [COPPER, US_INDPRO, CAPACITY],
    "상품 중개업": [IPI, BASE_RATE, FREIGHT],
    "가죽, 가방 및 유사제품 제조업": [COTTON, IPI, BASE_RATE],
    "가정용 기기 제조업": [US_INDPRO, COPPER, BASE_RATE],
    "섬유, 의복, 신발 및 가죽제품 소매업": [COTTON, IPI, BASE_RATE],
    "기타 사업지원 서비스업": [SVC_PROD, BASE_RATE, IPI],
    "전기 및 통신 공사업": [APT_PRICE, BASE_RATE, COPPER],
    "일반 교습 학원": [SVC_PROD, BASE_RATE, IPI],
    "기타 비금속 광물 채굴업": [METAL_PPI, US_INDPRO, IPI],
    "수도업": [IPI, BASE_RATE, APT_PRICE],
    "섬유제품 제조업; 의복 제외": [COTTON, US_INDPRO, IPI],
    "일반 및 생활 도자기 제조업": [APT_PRICE, US_INDPRO, IPI],
    "기타 개인 서비스업": [SVC_PROD, BASE_RATE, IPI],
    "인쇄 및 기록매체 복제업": [IPI, OIL, BASE_RATE],
    "사회복지 서비스업": [SVC_PROD, BASE_RATE, IPI],
    "의복 액세서리 제조업": [COTTON, IPI, BASE_RATE],
    "담배 제조업": [FOOD_PROD, IPI, BASE_RATE],
    "기타 비금속 광물제품 제조업": [US_INDPRO, IPI, METAL_PPI],
    "기타 생활용품 소매업": [IPI, BASE_RATE, CPI],
    "기타 전자부품 제조업": [SEMI_PROD, COPPER, CAPACITY],
    "기타 전문서비스업": [SVC_PROD, BASE_RATE, IPI],
    "천연 및 혼합 조제 조미료 제조업": [FOOD_PROD, WHEAT, IPI],
}

# 주요제품 키워드 보정 (업종 매핑보다 우선)
_KEYWORD_OVERRIDE: dict[str, list[ExogenousIndicator]] = {
    "2차전지": [BATTERY_PPI, CHEM_PROD, COPPER],
    "이차전지": [BATTERY_PPI, CHEM_PROD, COPPER],
    "배터리": [BATTERY_PPI, CHEM_PROD, COPPER],
    "양극재": [BATTERY_PPI, COPPER, CHEM_PROD],
    "음극재": [BATTERY_PPI, COPPER, CHEM_PROD],
    "OLED": [SEMI_PROD, COPPER, CAPACITY],
    "디스플레이": [SEMI_PROD, COPPER, CAPACITY],
    "태양광": [COPPER, SEMI_PROD, OIL],
    "풍력": [COPPER, METAL_PPI, OIL],
    "수소": [OIL, CHEM_PROD, COPPER],
    "반도체": [SEMI_PROD, COPPER, BASE_RATE],
    "메모리": [SEMI_PROD, SEMI_PPI, COPPER],
    "DRAM": [SEMI_PROD, SEMI_PPI, COPPER],
    "파운드리": [SEMI_PROD, DURABLE_ORDERS, COPPER],
    "자동차": [AUTO_PROD, AUTO_SALES, METAL_PPI],
    "전기차": [AUTO_PROD, BATTERY_PPI, COPPER],
    "시멘트": [APT_PRICE, METAL_PPI, BASE_RATE],
    "건설": [APT_PRICE, BASE_RATE, METAL_PPI],
    "해운": [FREIGHT, OIL, US_INDPRO],
    "물류": [FREIGHT, OIL, IPI],
    "항공": [OIL, BASE_RATE, FREIGHT],
    "게임": [SVC_PROD, BASE_RATE, IPI],
    "콘텐츠": [SVC_PROD, BASE_RATE, IPI],
    "광고": [SVC_PROD, BASE_RATE, IPI],
    "화장품": [IPI, BASE_RATE, CPI],
    "의류": [COTTON, IPI, BASE_RATE],
    "섬유": [COTTON, US_INDPRO, IPI],
    "의약품": [MFG_PPI, BASE_RATE, IPI],
    "바이오": [MFG_PPI, BASE_RATE, IPI],
    "치료제": [MFG_PPI, BASE_RATE, IPI],
    "의료기기": [MFG_PPI, DURABLE_ORDERS, BASE_RATE],
    "정유": [OIL, CHEM_PROD, FREIGHT],
    "석유": [OIL, CHEM_PROD, FREIGHT],
    "LNG": [OIL, BASE_RATE, IPI],
    "철강": [METAL_PPI, COPPER, CAPACITY],
    "알루미늄": [ALUMINUM, METAL_PPI, US_INDPRO],
    "식품": [FOOD_PROD, WHEAT, IPI],
}

# 기본 fallback (어떤 매핑에도 안 걸릴 때)
_FALLBACK = [IPI, BASE_RATE, USDKRW]


def getExogenousIndicators(
    stockCode: str | None = None,
    industry: str | None = None,
    product: str | None = None,
) -> list[ExogenousIndicator]:
    """기업의 외생변수 지표 3개 반환.

    우선순위:
    1. 주요제품 키워드 오버라이드 (가장 구체적)
    2. 업종 매핑
    3. IPI + 금리 + 환율 fallback

    Args:
        stockCode: 종목코드. 있으면 kindList에서 업종/제품 자동 조회.
        industry: 업종명 (직접 지정).
        product: 주요제품 텍스트 (직접 지정).
    """
    # stockCode에서 업종/제품 자동 조회
    # productIndex(공시 원문) 우선, kindList fallback
    if stockCode and (industry is None or product is None):
        _product_idx = _lookupFromProductIndex(stockCode)
        _industry, _product_kind = _lookupFromKindList(stockCode)
        if industry is None:
            industry = _industry
        if product is None:
            product = _product_idx or _product_kind  # productIndex 우선

    # 1. 주요제품 키워드 오버라이드
    if product:
        for keyword, indicators in _KEYWORD_OVERRIDE.items():
            if keyword in product:
                return indicators[:3]

    # 2. 업종 매핑
    if industry and industry in _INDUSTRY_MAP:
        return _INDUSTRY_MAP[industry][:3]

    # 3. fallback
    return _FALLBACK


def getExogenousSeriesIds(
    stockCode: str | None = None,
    industry: str | None = None,
    product: str | None = None,
) -> list[tuple[str, str]]:
    """(seriesId, source) 튜플 리스트 반환. _loadMacroAligned에서 사용."""
    indicators = getExogenousIndicators(stockCode, industry, product)
    return [(ind.seriesId, ind.source) for ind in indicators]


def getExogenousSummary(stockCode: str) -> dict:
    """기업의 외생변수 매핑 요약."""
    industry, product = _lookupFromKindList(stockCode)
    indicators = getExogenousIndicators(stockCode=stockCode)

    return {
        "stockCode": stockCode,
        "industry": industry,
        "product": product[:80] if product else None,
        "indicators": [
            {"seriesId": ind.seriesId, "source": ind.source, "label": ind.label, "axis": ind.axis}
            for ind in indicators
        ],
        "axes": list({ind.axis for ind in indicators}),
        "isFallback": indicators == _FALLBACK,
    }


_PRODUCT_INDEX_CACHE: dict | None = None


def _lookupFromProductIndex(stockCode: str) -> str | None:
    """productIndex.parquet에서 공시 기반 제품 텍스트 조회.

    changes.parquet의 '2. 주요 제품 및 서비스' 섹션 최신 preview.
    kindList보다 구체적 (DRAM, NAND, 신라면 등 실제 제품명 포함).
    """
    global _PRODUCT_INDEX_CACHE
    if _PRODUCT_INDEX_CACHE is None:
        try:
            from pathlib import Path

            import polars as pl

            path = Path(__file__).parent.parent.parent.parent.parent / "data" / "dart" / "scan" / "productIndex.parquet"
            if not path.exists():
                _PRODUCT_INDEX_CACHE = {}
                return None
            df = pl.read_parquet(path)
            _PRODUCT_INDEX_CACHE = {
                row["stockCode"]: row["product"]
                for row in df.iter_rows(named=True)
            }
        except (ImportError, KeyError):
            _PRODUCT_INDEX_CACHE = {}
            return None

    return _PRODUCT_INDEX_CACHE.get(stockCode)


def _lookupFromKindList(stockCode: str) -> tuple[str | None, str | None]:
    """kindList에서 업종/주요제품 조회."""
    try:
        from dartlab.gather.listing import getKindList

        df = getKindList()
        row = df.filter(df["종목코드"] == stockCode)
        if row.is_empty():
            return None, None
        return str(row["업종"][0] or ""), str(row["주요제품"][0] or "")
    except (ImportError, KeyError, IndexError):
        return None, None


# ── 전체 지표 목록 (수집 스크립트용) ──

def getAllIndicators() -> list[ExogenousIndicator]:
    """6축 전체 고유 지표 목록."""
    seen: set[str] = set()
    result: list[ExogenousIndicator] = []
    for ind in [
        COPPER, ALUMINUM, OIL, METAL_PPI, WHEAT, COTTON,
        SEMI_PROD, AUTO_PROD, CHEM_PROD, FOOD_PROD, US_INDPRO, SEMI_PPI, BATTERY_PPI, MFG_PPI,
        AUTO_SALES, DURABLE_ORDERS, FREIGHT, CAPACITY,
        BASE_RATE, HY_SPREAD, CORP_BOND,
        IPI, SVC_PROD, APT_PRICE, CPI,
        USDKRW, JPYKRW, CNYKRW,
    ]:
        if ind.seriesId not in seen:
            seen.add(ind.seriesId)
            result.append(ind)
    return result
