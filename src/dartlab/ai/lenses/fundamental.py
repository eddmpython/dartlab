"""펀더멘털 lens — 재무제표·이익·자본구조·valuation 중심."""

from .types import Lens

FUNDAMENTAL_LENS = Lens(
    name="fundamental",
    promptPatch="""관점: 펀더멘털 분석가.
- 매출·마진·이익의 변화와 그 원인 (가격·물량·믹스·비용) 을 본다.
- 자본구조 (자산·부채·자본) 와 현금흐름 (영업·투자·재무) 의 정합성을 점검한다.
- valuation (PER·PBR·EV/EBITDA·DCF) 은 경쟁사·역사 평균 대비 위치로 해석한다.
- 회계 정책 변경·일회성·세제 영향은 별도 표기.
""",
    capabilityHints=[
        "Company.panel",
        "Company.analysis",
        "Company.trace",
        "Company.select",
    ],
)
