"""Sprint 2 재무 알파 팩터 — dartlab 고유 강점 (DART 9년 SSOT).

세계 표준 학술 알파를 한국 시장 전종목 횡단면으로 자동 평가.

- Piotroski F-Score (Piotroski 2000): 9점 재무 건강
- Altman Z/Z'' (Altman 1968 이후): 비금융사 부실위험 판별 점수 + 적용성 원장
- Beneish M-Score: canonical 공급자 입력 계약 전까지 structured unavailable
- q-factor (Hou-Xue-Zhang 2015): 투자 + 수익성
- QMJ (Asness-Frazzini-Pedersen 2019): 품질 minus 쓰레기
- BAB (Frazzini-Pedersen 2014): 저베타 프리미엄
- Accruals Quality (Sloan 1996, Dechow-Dichev 2002): 회계 품질
- Earnings Surprise (Bernard-Thomas 1989): PEAD
- Fundamental Momentum (Chordia-Shivakumar 2006): 펀더멘털 개선 × 가격 모멘텀

공통 인터페이스:
    calc{Alpha}Factor(market="KR") → dict
        market, year, universe, scores: {stockCode: float},
        interpretation: str, topN: list[(stockCode, score)]

story 통합은 각 calc 함수 레벨에서. catalog.py BlockMeta 등록.
"""
