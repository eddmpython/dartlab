"""시장 파라미터화 : KR 배선 + US/EDGAR 스캐폴드 (로드맵 phase) (L2.5 simulate).

원장 규약 = 시장 파라미터화(KR+US)·시장 내 완결 (10 §1b). 채점·중립화·비용 바닥이 전부 시장별로
분리된다. 본 모듈은 시장 설정을 data 로 선언한다: KR 은 배선 완료(gov/prices·dart/finance·
allFilings), US 는 EDGAR 소스 매핑을 갖춘 스캐폴드다. **US 는 스펙(00 §10)이 명시한 로드맵
phase 라 데이터 배선 전까지 status="roadmap"** 이며, roadmap 시장 판독 요청은 명시 오류를 낸다
(US 데이터 날조 금지 = 스펙 자신의 게이트로 보고). US 비용 바닥은 스프레드 추정 동일 + 세율표만
교체(SEC fee), 버킷 중립도 시장 내에서만. do-not-build(US PEAD·US 지수효과)는 levers 원장 박제.

- ``MARKET_CONFIG`` : 시장별 설정 (원천·비용 파라미터·status).
- ``leverSourceMap`` : KR 레버 → US EDGAR 폼 매핑 (10 §1b, 같은 레버 다른 폼).
- ``requireWired`` : roadmap 시장 판독 요청 차단 (스펙 게이트로 보고).

Layer: L2.5 simulate. 순수 선언 (부작용 0).
"""

from __future__ import annotations

# 시장 설정 (10 §1b 시장 파라미터화). KR 배선 완료, US 스캐폴드(로드맵).
MARKET_CONFIG: dict[str, dict] = {
    "KR": {
        "status": "wired",
        "priceSource": "gov/prices",
        "financeSource": "dart/finance",
        "filingsSource": "dart/allFilings",
        "sellTaxNote": "거래일자 세율표 (costs.sellTaxRate: 2026 0.20%)",
        "instFee": 0.000036,
    },
    "US": {
        "status": "roadmap",  # 00 §10: US 프리셋·US elasticity 부재로 구조적 KR-only. 07 로드맵 phase.
        "priceSource": "edgar/prices(미배선)",
        "financeSource": "edgar/panel",
        "filingsSource": "edgar/filings",
        "sellTaxNote": "SEC fee 스왑 (매도 $27.80/백만 등, 세율표만 교체)",
        "secFeeNote": "SEC Section 31 fee (매도측). costs 스프레드 추정은 동일.",
    },
}

# KR 레버 → US EDGAR 폼 매핑 (10 §1b, 같은 레버 다른 폼·다른 판정).
_LEVER_EDGAR_MAP: dict[str, dict] = {
    "insiderBuy": {"form": "Form 4", "code": "P=매수/S=매도(XML)", "verdict": "정제 문헌 원산지=US, KR보다 직행"},
    "treasuryAcquire": {"form": "8-K + 10-Q Rule 10b-18", "code": "buyback", "verdict": "발표 +3% + 장기 드리프트 [K]"},
    "lockupExpiry": {"form": "S-1/424B lockup 조항", "code": "표준 180일", "verdict": "-1.5~2% 만료주 [K]"},
    "cbChain": {
        "form": "8-K + 424B (PIPE/convertible reset)",
        "code": "ratchet",
        "verdict": "death-spiral, KR보다 저빈도",
    },
    "maxLottery": {"form": "가격만 (G9 선결)", "code": "-", "verdict": "원문헌 US >1%/월"},
    "earSueCombo": {
        "form": "10-Q/10-K/8-K 타임스탬프",
        "code": "-",
        "verdict": "EAR 만 생존(대형주 0.9~1.4%), PEAD do-not-build",
    },
    "indexInclusion": {"form": "Russell/S&P 재구성", "code": "-", "verdict": "붕괴 실증 = do-not-build"},
    "auditDelay": {"form": "NT 10-K / NT 10-Q", "code": "기한 미준수 통지", "verdict": "KR보다 구조화. 사내 실측"},
    "bonusIssueFade": {"form": "주식분할/주식배당", "code": "weak", "verdict": "후순위"},
    "majorHolderChange": {"form": "SC 13D/13G", "code": "5%+ 보유", "verdict": "지배구조 [K]"},
}


def leverSourceMap() -> dict[str, dict]:
    """KR 레버 → US EDGAR 폼·판정 매핑 (10 §1b). US 통합 시 같은 레버 다른 폼."""
    return dict(_LEVER_EDGAR_MAP)


def marketStatus(market: str) -> str:
    """시장 배선 상태: "wired"(판독 가능) | "roadmap"(데이터 미배선) | "unknown"."""
    return MARKET_CONFIG.get(market, {}).get("status", "unknown")


def requireWired(market: str) -> None:
    """roadmap/unknown 시장 판독 요청 차단 (스펙 00 §10 게이트로 보고, US 데이터 날조 금지).

    Raises:
        ValueError: 시장이 wired 가 아니면 (US 는 로드맵 phase 라 데이터 배선 전까지 차단).
    """
    st = marketStatus(market)
    if st != "wired":
        raise ValueError(
            f"시장 '{market}' status={st}: 데이터 미배선 (스펙 00 §10 로드맵 phase). "
            f"US 해제는 07 로드맵 명시 phase 후. 현재 판독 가능 시장 = "
            f"{[m for m, c in MARKET_CONFIG.items() if c['status'] == 'wired']}."
        )
