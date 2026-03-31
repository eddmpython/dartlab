# Guide

dartlab의 **안내 데스크(concierge)**. 사용자 편의성 교차 관심사 총괄.

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

## 관련 코드

- `src/dartlab/guide/` — desk, readiness, credentials, hints, integration (17파일)
