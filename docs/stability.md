---
title: API 안정성 정책
description: dartlab API의 안정성 등급과 변경 정책
---

# API 안정성 정책

dartlab은 현재 **Alpha** 단계입니다. 이 문서는 API의 안정성 등급과 변경 시 호환성 정책을 정의합니다.

## Tier 분류

### Tier 1: Stable

변경 시 deprecation 기간을 두고 마이그레이션 가이드를 제공합니다.

| API | 설명 |
|-----|------|
| `Company(code)` | 종목 객체 생성 (팩토리) |
| `Company.finance` | 재무제표 시계열 (annual, timeseries) |
| `Company.sector` | WICS 섹터 분류 |
| `Company.ratios` | 재무비율 |
| `dartlab.search()` | 종목 검색 |
| `dartlab.listing()` | 전체 상장법인 목록 |
| `Company.IS/BS/CF` | 피벗 재무제표 (DataFrame) |

### Tier 2: Beta

경고 후 변경 가능합니다. CHANGELOG에 기록합니다.

| API | 설명 |
|-----|------|
| `Company.insight` | 인사이트 등급 (7영역) |
| `Company.rank` | 시장 규모 순위 |
| `Company.report` | 정기보고서 API 데이터 |
| `Company.ask()` | LLM 기반 분석 |
| Server API `/api/*` | 웹 서버 엔드포인트 |
| `engines.ai.*` | AI/LLM 엔진 |

### Tier 3: Experimental

파괴적 변경이 허용됩니다. 프로덕션 사용을 권장하지 않습니다.

| API | 설명 |
|-----|------|
| `USCompany` | 미국 주식 (EDGAR) |
| `Compare` | 복수 종목 비교 |
| `engines.edgar.*` | EDGAR 데이터 엔진 |
| `export.*` | Excel 내보내기 |
| `engines.ai.tools.*` | LLM tool calling |

## Deprecation 정책

| Tier | 공지 | 제거 |
|------|------|------|
| Tier 1 | 2 minor 버전 전 | deprecated 경고 → 다음 minor에서 제거 |
| Tier 2 | 1 minor 버전 전 | CHANGELOG 기록 후 변경 |
| Tier 3 | 즉시 | CHANGELOG 기록만 |

Deprecation 경고 예시:

```python
import warnings
warnings.warn(
    "Company.oldMethod()는 v0.5.0에서 제거됩니다. "
    "Company.newMethod()를 사용하세요.",
    DeprecationWarning,
    stacklevel=2,
)
```

## Beta 졸업 체크리스트

dartlab이 Beta(0.x → 1.0)로 전환하기 위한 조건:

- [ ] CI 테스트 커버리지 80%+ (핵심 엔진)
- [ ] API Tier 1 테스트 100% 통과
- [ ] 매핑 벤치마크 10종목 × 18계정 통과
- [ ] BS 항등식 95%+ 통과
- [ ] 3개월간 Tier 1 파괴적 변경 없음
- [ ] PyPI 다운로드 안정적 증가 추세
- [ ] 외부 사용자 피드백 수렴 (2+ 건)

## 버전 정책

- **0.x.y**: Alpha — 모든 Tier에서 파괴적 변경 가능
- **1.0.0**: Beta 졸업 — Tier 1 안정성 보장 시작
- **semver 준수**: major=파괴적, minor=기능추가, patch=버그수정
