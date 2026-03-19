---
title: API 안정성 정책
description: dartlab API의 안정성 등급과 변경 정책
---

# API 안정성 정책

dartlab은 현재 **DART core 기준 안정적** 상태입니다. 이 문서는 API의 안정성 등급과 변경 시 호환성 정책을 정의합니다.

## Tier 분류

### Tier 1: Stable

변경 시 deprecation 기간을 두고 마이그레이션 가이드를 제공합니다.

| API | 설명 |
|-----|------|
| `dartlab.Company(code)` | 종목 객체 생성 facade |
| `Company.sections` | canonical company map (topic × period Polars DataFrame) |
| `Company.show()` | topic payload 조회 (source-aware) |
| `Company.trace()` | source provenance 조회 |
| `Company.diff()` | 기간 간 텍스트 변화 감지 |
| `Company.topics` | 사용 가능한 topic 목록 |
| `Company.docs` | docs source namespace |
| `Company.finance` | 재무제표 시계열 및 statement namespace |
| `Company.report` | 정형 공시 namespace (28개 API 체계) |
| `dartlab.search()` | 종목 검색 |
| `dartlab.listing()` | 전체 상장법인 목록 |
| `Company.IS/BS/CF` | authoritative statement shortcut |
| `dartlab` CLI entrypoint | 설치 후 실행되는 공개 명령 진입점 |

### Tier 2: Beta

경고 후 변경 가능합니다. CHANGELOG에 기록합니다.

| API | 설명 |
|-----|------|
| `dartlab.Company("AAPL")` | EDGAR Company facade (미국 주식) |
| `engines.edgar.docs` | EDGAR 10-K/10-Q sections |
| `engines.edgar.finance` | SEC XBRL 재무제표 |
| `Company.insights` | 인사이트 등급 (7영역) |
| `Company.rank` | 시장 규모 순위 |
| `Company.docs.retrievalBlocks` | 원문 block retrieval |
| `Company.docs.contextSlices` | LLM/context slice view |
| `Company.ask()` | LLM 기반 분석 |
| `dartlab` subcommands/options | `ask`, `status`, `setup`, `ai`, `excel`, `profile` 명령 UX |
| Server API `/api/*` | 웹 서버 엔드포인트 |
| `engines.ai.*` | AI/LLM 엔진 |

### Tier 3: Experimental

파괴적 변경이 허용됩니다. 프로덕션 사용을 권장하지 않습니다.

| API | 설명 |
|-----|------|
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

## 안정성 운영 기준

DART core stable 판단 기준:

- [ ] CI 테스트 커버리지 80%+ (핵심 엔진)
- [ ] API Tier 1 테스트 100% 통과
- [ ] sections raw residual 0 유지 (대표 종목군)
- [ ] BS 항등식 95%+ 통과
- [ ] 3개월간 Tier 1 파괴적 변경 없음
- [ ] PyPI 다운로드 안정적 증가 추세
- [ ] 외부 사용자 피드백 수렴 (2+ 건)

## 버전 정책

- **semver 준수**: major=파괴적, minor=기능추가, patch=버그수정
- DART core stable 범위는 minor 내에서 호환성을 우선한다
- EDGAR과 일부 AI 기능은 Tier 정책에 따라 더 빠르게 바뀔 수 있다
- `Company.profile` 보고서형 뷰는 아직 로드맵 단계이며, 향후 terminal/notebook 문서형 렌더로 추가될 예정이다

## CLI 호환성 규칙

- 최상위 엔트리포인트 `dartlab` 는 Tier 1로 취급한다.
- 공개 서브커맨드와 주요 옵션 변경은 최소 1개 minor 버전 전에 deprecated 경고를 둔다.
- 종료 코드는 계약으로 본다: `0` 성공, `1` 런타임 오류, `2` 사용법 오류, `130` 사용자 인터럽트.
- deprecated alias는 help에서 숨길 수 있지만, 제거 전까지 실행 가능해야 한다.

