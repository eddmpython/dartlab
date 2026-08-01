"""심리 lens — 컨센서스·뉴스·공시 톤·외인 수급 중심."""

from .types import Lens

SENTIMENT_LENS = Lens(
    name="sentiment",
    promptPatch="""관점: 시장 심리 분석가.
- 애널리스트 컨센서스 (목표가·등급) 의 분포와 변화를 본다.
- 뉴스 톤·공시 빈도·실적 발표 직전후 가격 반응을 단서로 활용.
- 외국인·기관·개인 수급의 누적 흐름과 단기 충격을 구분.
- 공포·탐욕 같은 경향성은 정량 지표 없이 단정하지 않는다.
""",
    capabilityHints=[
        "gather.news",
        "gather.flow",
        "gather.revenueConsensus",
        "Company.filings",
    ],
)
