"""macro 엔진 메타데이터 — generateSpec.py 연동."""

from __future__ import annotations

SPEC = {
    "engine": "macro",
    "layer": "L2",
    "description": "시장 레벨 매크로 경제 분석. Company 불필요.",
    "entrypoint": "dartlab.macro()",
    "axes": {
        "cycle": "경제 사이클 4국면 판별 + 전환 시퀀스 감지",
        "rates": "금리 방향 + 고용/물가 해석 + DKW 근사 분해",
        "assets": "5대 자산(금리/환율/금/VIX) 심층 해석",
        "sentiment": "시장 공포탐욕 근사 + VIX 구간 + ISM 자산배분 바로미터",
        "liquidity": "M2 + 연준 B/S + 신용스프레드 + 설비투자 압력",
        "forecast": "LEI 복제 + Cleveland Fed 침체확률 + 성장 모멘텀",
        "crisis": "Credit-to-GDP gap(BIS) + GHS 위기예측 + 침체 대시보드",
        "inventory": "ISM 재고순환 4국면 + 자산배분 바로미터",
        "corporate": "전종목 재무집계 — 이익사이클, Ponzi비율, 레버리지사이클",
        "trade": "교역조건 + 대용치(환율-유가) + 수출이익 선행",
        "summary": "전 10축 종합 매트릭스 + 40개 투자전략 대시보드",
    },
    "markets": ["US", "KR"],
    "dataSources": {
        "FRED": "미국 경제 지표 (금리, 고용, 물가, VIX, 스프레드 등)",
        "ECOS": "한국 경제 지표 (기준금리, CPI, 경기선행지수 등)",
    },
}
