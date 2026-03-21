"""업종별 벤치마크 구조화 데이터.

하드코딩 문자열 → 구조화 dict 분리.
수치만 바꾸면 프롬프트가 자동 갱신되고,
_meta.updated로 갱신 시점을 추적한다.
"""

from __future__ import annotations

BENCHMARK_DATA: dict[str, dict] = {
    "반도체": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "영업이익률": {"good": 20, "normal_low": 10, "normal_high": 20, "unit": "%"},
            "ROE": {"good": 15, "normal_low": 8, "normal_high": 15, "unit": "%"},
            "R&D/매출": {"good": 15, "normal_low": 8, "normal_high": 15, "unit": "%"},
        },
        "분석포인트": [
            "**사이클 위치**: 재고일수 추세로 판단 (재고일수↑ = 다운사이클 진입). 3-5년 평균으로 수익성 판단",
            "**CAPEX 강도**: CAPEX/매출 30%+ = 공격적 투자기, 다운사이클 시 감가상각 부담 급증",
            "**메모리 vs 비메모리**: segments에서 분리 확인. 가격 변동성 크게 다름",
        ],
        "회계함정": [
            "감가상각비 비중 높아 EBITDA와 영업이익 괴리 큼. EBITDA 기준 분석 병행 필수",
        ],
        "topic확인": ["show_topic('segments')", "show_topic('tangibleAsset')", "show_topic('rnd')"],
    },
    "제약/바이오": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "영업이익률": {"good": 15, "normal_low": 5, "normal_high": 15, "unit": "%", "note": "적자 가능"},
            "R&D/매출": {"good": 20, "normal_low": 10, "normal_high": 20, "unit": "%"},
        },
        "분석포인트": [
            "**파이프라인 단계**: 바이오텍은 매출 전 단계일 수 있음 (적자 정상). 임상 단계가 핵심 가치",
            "**기술이전(L/O)**: 마일스톤/로열티 수익은 일회성 판단. recurring 매출과 분리 분석",
            "**R&D 자본화**: 개발비 자본화 비율 상승 시 실질 비용 과소 표시 ⚠️",
        ],
        "회계함정": [
            "임상실패 시 자본화된 개발비 일시 상각 → 대규모 손실. 무형자산 중 개발비 비중 확인",
        ],
        "topic확인": ["show_topic('rnd')", "show_topic('productService')", "get_notes('개발비')"],
    },
    "금융/은행": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "ROE": {"good": 10, "normal_low": 6, "normal_high": 10, "unit": "%"},
            "NIM(순이자마진)": {"good": 1.8, "normal_low": 1.4, "normal_high": 1.8, "unit": "%"},
            "NPL비율": {"good": 0.5, "normal_low": 0.5, "normal_high": 1.5, "unit": "%", "invert": True},
            "BIS자기자본비율": {"good": 14, "normal_low": 10, "normal_high": 14, "unit": "%"},
        },
        "분석포인트": [
            "**건전성 지표**: 일반 부채비율 대신 BIS비율 사용. 대손충당금전입률 추이 = 자산건전성 선행지표",
            "**수익 구조**: 순이자이익 vs 비이자이익 비중. NIM 추이가 핵심 수익성 지표",
            "**NPL 이동**: 정상→요주의→고정→회수의문→추정손실 이동률. 요주의 급증은 미래 부실 선행",
        ],
        "회계함정": [
            "대손충당금 적립률 조정으로 이익 관리 가능. 충당금/부실채권 비율 확인",
        ],
        "topic확인": ["show_topic('riskFactor')", "get_notes('대출')", "get_notes('충당금')"],
    },
    "금융/보험": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "ROE": {"good": 10, "normal_low": 5, "normal_high": 10, "unit": "%"},
            "손해율(손보)": {"good": 80, "normal_low": 80, "normal_high": 85, "unit": "%", "invert": True},
            "합산비율(CR)": {"good": 100, "normal_low": 100, "normal_high": 105, "unit": "%", "invert": True},
        },
        "분석포인트": [
            "**K-ICS(2023~)**: 새 자본 적정성 기준. 보험부채 시가평가 영향으로 자본 급변동 가능",
            "**손해율/합산비율**: CR > 100% = 보험 영업만으로 이익 불가, 투자수익 의존",
        ],
        "회계함정": [
            "IFRS 17 도입(2023~)으로 보험수익 인식 기준 변경. 전년 비교 시 주의",
        ],
        "topic확인": [],
    },
    "금융/증권": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "ROE": {"good": 12, "normal_low": 6, "normal_high": 12, "unit": "%"},
            "순자본비율(NCR)": {"good": 300, "normal_low": 150, "normal_high": 300, "unit": "%"},
            "판관비/순영업수익": {"good": 50, "normal_low": 50, "normal_high": 65, "unit": "%", "invert": True},
        },
        "분석포인트": [
            "**수익 변동성**: 시장 변동성에 따른 트레이딩 수익 급변. 수수료 vs 자기매매 비중 분석",
            "**IB 수익**: PF 관련 우발부채 규모 반드시 확인. 부동산 PF 노출 = 건설업과 동일 리스크",
        ],
        "회계함정": [
            "파생상품 평가손익이 영업이익에 큰 영향. 실현 vs 미실현 구분 필요",
        ],
        "topic확인": [],
    },
    "자동차": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "영업이익률": {"good": 8, "normal_low": 4, "normal_high": 8, "unit": "%"},
            "판매대수 성장률": {"good": 5, "normal_low": 0, "normal_high": 5, "unit": "%"},
            "R&D/매출": {"good": 5, "normal_low": 3, "normal_high": 5, "unit": "%"},
        },
        "분석포인트": [
            "**환율 민감도**: 수출 비중 높은 기업은 원/달러 환율 10원 변동 시 영업이익 영향 추정",
            "**전기차 전환**: 전기차 관련 투자(CAPEX/R&D) 비중 확인. 전환 투자 부담 vs 미래 성장",
            "**인센티브**: 판매 보조금 증가는 수요 약화 신호. 믹스(고급차 비중) 변화 추적",
        ],
        "회계함정": [],
        "topic확인": ["show_topic('segments')", "show_topic('productService')", "show_topic('rawMaterial')"],
    },
    "화학": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "영업이익률": {"good": 10, "normal_low": 5, "normal_high": 10, "unit": "%"},
            "EBITDA마진": {"good": 15, "normal_low": 8, "normal_high": 15, "unit": "%"},
        },
        "분석포인트": [
            "**스프레드**: 제품가 - 원료가(나프타) 추이가 핵심 수익성 지표. rawMaterial에서 원료비 확인",
            "**업스트림/다운스트림**: 다운스트림일수록 수익 안정. segments에서 부문별 마진 차이 확인",
            "**설비 투자 사이클**: 대규모 증설 완료 시 감가상각 부담 급증. CAPEX/감가상각 추이",
        ],
        "회계함정": [
            "유가 급변 시 재고평가 손익이 영업이익에 큰 영향 (선입선출 vs 가중평균)",
        ],
        "topic확인": [],
    },
    "철강": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "영업이익률": {"good": 8, "normal_low": 3, "normal_high": 8, "unit": "%"},
            "부채비율": {"good": 80, "normal_low": 80, "normal_high": 150, "unit": "%", "invert": True},
        },
        "분석포인트": [
            "**원재료 의존**: 철광석·유연탄 가격 변동이 직접 원가율 결정. rawMaterial 확인",
            "**중국 공급과잉**: 업황 핵심 변수. 중국 수출 증가 시 가격 하락 압력",
            "**설비 감가상각**: 대규모 설비 → 감가상각 부담 큼. EBITDA 기준 분석 병행",
        ],
        "회계함정": [],
        "topic확인": [],
    },
    "건설": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "영업이익률": {"good": 5, "normal_low": 2, "normal_high": 5, "unit": "%"},
            "수주잔고/매출": {"good": 3, "normal_low": 2, "normal_high": 3, "unit": "배"},
            "부채비율": {"good": 150, "normal_low": 150, "normal_high": 250, "unit": "%", "invert": True},
        },
        "분석포인트": [
            "**PF 우발부채**: contingentLiability에서 PF 보증 규모 확인. 자기자본 대비 20% 초과 시 ⚠️",
            "**공사미수금/선수금**: 공사미수금 급증 = 대금 회수 지연, 선수금 감소 = 수주 둔화 신호",
            "**진행률 수익인식**: K-IFRS 15 기준. 원가율 변동에 따라 매출·이익 급변동 가능",
        ],
        "회계함정": [
            "공사손실충당부채 미인식 → 향후 손실 폭탄. 진행률 산정 기준 변경 주의",
        ],
        "topic확인": ["show_topic('contingentLiability')", "show_topic('salesOrder')", "get_notes('공사')"],
    },
    "유통": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "영업이익률": {"good": 5, "normal_low": 2, "normal_high": 5, "unit": "%"},
            "재고회전율": {"good": 12, "normal_low": 6, "normal_high": 12, "unit": "회"},
            "매출성장률": {"good": 5, "normal_low": 0, "normal_high": 5, "unit": "%"},
        },
        "분석포인트": [
            "**채널 전환**: 온라인 매출 비중 추이. 오프라인 점포 효율성(점포당 매출) 확인",
            "**리스부채**: IFRS 16 적용으로 임차 관련 부채 대폭 증가. 실질 부채비율 vs 회계 부채비율 구분",
            "**재고 관리**: 재고회전율 악화 = 체화 재고 리스크. 재고일수 추이 확인",
        ],
        "회계함정": [],
        "topic확인": [],
    },
    "IT/소프트웨어": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "영업이익률": {"good": 15, "normal_low": 8, "normal_high": 15, "unit": "%"},
            "매출성장률(YoY)": {"good": 20, "normal_low": 10, "normal_high": 20, "unit": "%"},
            "인건비/매출": {"good": 40, "normal_low": 40, "normal_high": 55, "unit": "%", "invert": True},
        },
        "분석포인트": [
            "**SaaS 기업**: ARR(연간반복수익) 성장률과 고객이탈률이 핵심. 구독매출 비중 추적",
            "**고객 집중도**: 상위 고객 매출 비중 30%+ → 의존 리스크. salesOrder 확인",
            "**인력 의존**: 인건비/매출 비율이 핵심 원가. 인력 증감과 1인당 매출 추이",
        ],
        "회계함정": [
            "R&D 자본화 비율 높으면 실질 비용 과소 표시. 무형자산 중 개발비 비중 확인",
        ],
        "topic확인": [],
    },
    "통신": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "EBITDA마진": {"good": 35, "normal_low": 25, "normal_high": 35, "unit": "%"},
            "배당수익률": {"good": 5, "normal_low": 3, "normal_high": 5, "unit": "%"},
            "부채비율": {"good": 100, "normal_low": 100, "normal_high": 150, "unit": "%", "invert": True},
        },
        "분석포인트": [
            "**ARPU**: 가입자당 매출 추이가 핵심 KPI. 5G 가입자 비중 = ARPU 상승 동력",
            "**설비 투자**: 5G/인프라 투자 감가상각 부담. CAPEX/매출 비율 추이 확인",
            "**배당 안정성**: 안정적 현금흐름 기반 고배당. FCF 대비 배당금 비율로 지속가능성 판단",
        ],
        "회계함정": [],
        "topic확인": [],
    },
    "전력/에너지": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "영업이익률": {"good": 8, "normal_low": 3, "normal_high": 8, "unit": "%"},
            "부채비율": {"good": 200, "normal_low": 200, "normal_high": 300, "unit": "%", "invert": True},
        },
        "분석포인트": [
            "**규제 산업**: 전기요금 인상/인하가 수익성 직결. 정부 정책 변수 확인",
            "**연료비 변동**: 연료비 증감 → 미수금/미지급금 변동으로 BS에 영향",
            "**신재생 전환**: 신재생에너지 투자 비중 추이. 탄소 규제 대응 비용 증가",
        ],
        "회계함정": [],
        "topic확인": [],
    },
    "식품": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "영업이익률": {"good": 8, "normal_low": 4, "normal_high": 8, "unit": "%"},
            "ROE": {"good": 12, "normal_low": 6, "normal_high": 12, "unit": "%"},
            "매출성장률": {"good": 5, "normal_low": 0, "normal_high": 5, "unit": "%"},
        },
        "분석포인트": [
            "**원재료 가격**: 곡물·유지 가격 변동이 직접 원가율 결정. rawMaterial 확인",
            "**가격 전가력**: 브랜드 파워에 따라 원가 상승분 판가 전가 가능 여부 차이",
            "**해외 비중**: 해외 매출 비중 증가 추이. 환율 영향과 성장 기회 동시 평가",
        ],
        "회계함정": [],
        "topic확인": [],
    },
    "섬유/의류": {
        "_meta": {"updated": "2026-03", "source": "업종 평균 기반"},
        "지표": {
            "영업이익률": {"good": 10, "normal_low": 5, "normal_high": 10, "unit": "%"},
            "재고회전율": {"good": 6, "normal_low": 3, "normal_high": 6, "unit": "회"},
        },
        "분석포인트": [
            "**재고 관리**: 시즌성 상품이므로 재고 소진율이 핵심. 재고일수 급증 = 체화 리스크",
            "**브랜드 vs OEM**: 자체 브랜드(고마진) vs OEM(저마진) 매출 비중 변화 추적",
            "**환율**: 수출 비중 높은 기업은 원화 약세 시 수출 경쟁력↑, 원재료 수입비용↑ 동시 영향",
        ],
        "회계함정": [],
        "topic확인": [],
    },
    "일반": {
        "_meta": {"updated": "2026-03", "source": "일반 제조업 기준"},
        "지표": {
            "영업이익률": {"good": 10, "normal_low": 5, "normal_high": 10, "unit": "%"},
            "ROE": {"good": 12, "normal_low": 6, "normal_high": 12, "unit": "%"},
            "부채비율": {"good": 100, "normal_low": 100, "normal_high": 200, "unit": "%", "invert": True},
            "유동비율": {"good": 150, "normal_low": 100, "normal_high": 150, "unit": "%"},
        },
        "분석포인트": [
            "업종 특화 벤치마크가 없으므로 일반 제조업 기준 적용",
            "원가구조(costByNature)와 부문별 수익성(segments)을 직접 조회하여 업종 특성 파악 권장",
        ],
        "회계함정": [],
        "topic확인": [],
    },
}
