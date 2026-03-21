"""scan 엔진 스펙 — AI spec 수집기에 제공."""

from __future__ import annotations


def buildSpec() -> dict:
    """scan 엔진 메타데이터."""
    return {
        "name": "dart.scan",
        "description": "상장사 전수 스캔 엔진 — 6축 분석 (company 4축 + market network/signal)",
        "summary": {
            "governance": "지배구조 (지분율, 사외이사비율, 임원보수비율, 감사의견) → A~E 등급",
            "workforce": "인력/급여 (직원수, 평균급여, 급여성장률, 인건비부담, 고액보수)",
            "capital": "주주환원 (배당, 자사주, 증자/감자) → 환원형/중립/희석형",
            "debt": "부채구조 (사채잔액, 부채비율, ICR) → 안전/관찰/주의/고위험",
            "network": "관계 네트워크 (출자/지분/계열 관계, 순환출자 탐지)",
            "signal": "서술형 공시 키워드 트렌드 (year, keyword, category, companies, totalMentions)",
        },
        "detail": {
            "governance": {
                "metrics": ["최대주주_지분율", "사외이사비율", "임원_직원_보수비율", "감사의견"],
                "scoring": "4축 × 25점 = 100점, A(85+) B(70+) C(55+) D(40+) E(<40)",
            },
            "workforce": {
                "metrics": [
                    "직원수",
                    "평균급여_만원",
                    "남녀격차",
                    "근속_년",
                    "직원당매출_억",
                    "급여성장률",
                    "매출성장률",
                    "인건비부담",
                ],
            },
            "capital": {
                "metrics": ["배당여부", "DPS", "배당수익률", "자사주보유", "자사주취득", "최근증자"],
                "classification": "환원점수: +1(배당) +1(자사주) -1(증자) → 환원형/중립/희석형",
            },
            "debt": {
                "metrics": ["사채잔액", "단기비중", "총부채", "부채비율", "ICR"],
                "risk_levels": "고위험(단기≥50%+ICR<1) / 주의 / 관찰 / 안전",
            },
            "network": {
                "metrics": ["출자엣지", "지분엣지", "그룹분류", "순환출자"],
            },
            "signal": {
                "metrics": ["year", "keyword", "category", "companies", "totalMentions"],
                "scope": "market-level only; current local docs corpus coverage only",
            },
        },
    }
