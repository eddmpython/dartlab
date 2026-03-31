# Guide

dartlab의 **안내 데스크(concierge)이자 교육 안내자**. 사용자 편의성 교차 관심사 총괄.
단순히 에러를 안내하는 게 아니라, 사용자가 분석 방법 자체를 배울 수 있게 친절하게 안내한다.

## 4층위 체계

```
L4  맥락 인식    "데이터가 120일 전이다", 키 발급 URL + 입력 방법 3가지
L3  여정 안내    Company repr에 nextSteps, 분석 축 선택 가이드
L2  사전 점검    checkReady() 9개 feature (data/ai/dart_key/finance/valuation/analysis/scan/review/ask)
L1  에러 안내    5개 병목(CLI/Server/MCP/AI Runtime)에서 handleError() 자동 안내
```

## 레이어 위치

교차 관심사 — 모든 레이어가 guide를 import, guide는 lazy import로 모든 레이어 조회.
import 방향 제약에서 제외.

## 핵심 API

```python
dartlab.guide.checkReady("finance", stockCode="005930")
dartlab.guide.whatCanIDo("재무 분석")
dartlab.guide.handleError(error, feature="ai")

from dartlab.guide.hints import onKeyRequired, promptKeyIfMissing
onKeyRequired("gemini")         # 키 발급 URL + 설정 방법
promptKeyIfMissing("dart")      # 대화형 입력 → .env 저장
```

## 핵심 원칙

- **Facade, not Rewrite**: 기존 모듈 래핑
- **병목 전략**: 815개 에러를 5개 접점에서 자동 커버
- **lazy import**: 순환 의존 방지
- **키 안내 통합**: DART/FRED/ECOS + 9개 AI provider

## 교육 원칙

- **How, not just What**: "이 축을 사용하세요"가 아니라 "이 축은 이런 질문에 답하고, 이렇게 호출합니다"
- **코드 예시 우선**: 텍스트 설명보다 실행 가능한 코드 1줄이 낫다
- **발견 경로 제공**: whatCanIDo()는 "뭘 할 수 있는지" 뿐 아니라 "왜 그걸 해야 하는지"까지 맥락을 준다
- **점진적 깊이**: 초보자는 ask()로 시작 → guide가 show/select/analysis 경로를 제안 → 사용자가 직접 코드를 쓰게 된다

## 관련 코드

- `src/dartlab/guide/` — desk, readiness, credentials, hints, integration (17파일)
