"""synth. L1.5 분석 후처리/매칭/시나리오.

분석 결과 + scan 결과 + 룰 (reference) 을 결합해 매칭·분류·시나리오를 후처리한다.

구성 (갈래별): 지표·축 (`indicators` · `axisGuide` · `ratioCategories` ·
`overrides`) · 밸류에이션 입력 (`damodaranL15` · `impliedERP` · `bottomUpBeta` ·
`riskPremiums`) · 국면·사건 (`dalio48Match` · `eventRadar` · `eventStudy` ·
`turningPoint` · `quadrant`) · 서술·감성 (`narrativePulse` · `newsSentiment` ·
`newsTopic` · `lmDict`) · 전략 (`strategyRules` · `strategyGroups` ·
`portfolioMapping`) · 부실 (`distress` · `creditGradeTable` ·
`evidenceForensics`) · 접근 헬퍼 (`companyAccess` · `marketDataAccess` ·
`rowAccess` · `scanBridge`).

룰 (operation.architecture SSOT):
- import OK: dartlab.core, dartlab.gather, dartlab.providers
- import 금지: dartlab.{scan, frame, reference} (L1.5 4 형제 cross 금지)
- 진입 조건: 2 개 이상 분석엔진이 같은 형태로 사용해야 함
- scan 결과 후처리가 필요하면 L2 가 scan 에서 synth 로 데이터를 전달한다
  (synth 가 scan 을 직접 import 하지 않음)
- 공개 호출계약 아님. 분석엔진이 소비하는 내부 가공층이라 `__all__` 을 비워 두고
  `dartlab.synth(...)` 같은 호출 표면을 두지 않는다. 소비자는 모듈 경로로 직접 쓴다.
"""

__all__: list[str] = []
