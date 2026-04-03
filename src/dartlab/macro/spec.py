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
        "sentiment": "시장 공포탐욕 근사 + VIX 구간 + 분할매수 신호",
        "liquidity": "M2 + 연준 B/S + 신용스프레드 종합 유동성",
        "summary": "전체 매크로 종합 판정",
    },
    "markets": ["US", "KR"],
    "dataSources": {
        "FRED": "미국 경제 지표 (금리, 고용, 물가, VIX, 스프레드 등)",
        "ECOS": "한국 경제 지표 (기준금리, CPI, 경기선행지수 등)",
    },
}
