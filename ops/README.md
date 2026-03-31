# dartlab 운영문서

프로젝트 전체의 설계 규칙, 엔진별 운영 체계, 품질 관리 절차를 한곳에 모은다.

## 진입점

| 문서 | 엔진 | 핵심 |
|------|------|------|
| [company.md](company.md) | Company facade | sections 사상, 4 namespace, canHandle 라우팅, 편의성 3원칙 |
| [analysis.md](analysis.md) | analysis/ | 14축 재무분석 + forecast + valuation, 예측신호 6축, audit 체계 |
| [scan.md](scan.md) | scan/ | 13축 시장 횡단분석, 전 종목 품질 검증 |
| [review.md](review.md) | review/ | 블록-템플릿 보고서 렌더링, 4 출력 형식 |
| [search.md](search.md) | core/search/ | 전체 공시 시맨틱 검색, 2단계 수집, GPU 벡터 임베딩 |
| [ai.md](ai.md) | ai/ | LLM 분석 엔진, 5 provider, CAPABILITIES-Driven |
| [guide.md](guide.md) | guide/ | 안내 데스크, 교차 관심사, 4층위 체계 |
| [data.md](data.md) | core/dataConfig, dataLoader | HF 데이터셋, 수집 파이프라인, 카테고리 관리 |
| [gather.md](gather.md) | gather/ | 외부 시장 데이터 (주가/수급/매크로/뉴스) |
| [experiments.md](experiments.md) | experiments/ | 실험 규칙, 진행 현황, 흡수 판단 |
| [code.md](code.md) | 전체 | camelCase, 독스트링 9섹션, CAPABILITIES, 테스트, 릴리즈, Git |

## 레이어 아키텍처

```
L0 (인프라)     core/          protocols, finance, docs, registry, search
L1 (데이터)     providers/     DART, EDGAR, EDINET
                gather/        주가, 수급, 매크로, 뉴스
                scan/          13축 횡단분석
L2 (분석)       analysis/      14축 + forecast + valuation
L3 (AI)         ai/            LLM 대화형 분석

교차 관심사     guide/         안내 데스크 (모든 레이어에서 import 가능)
```

## 공통 규칙

- **코드 스타일**: camelCase (함수/변수), 이동된 snake_case는 하위호환 유지
- **진입점**: 종목코드 하나면 끝. `import dartlab` 하나로 모든 기능 접근
- **README 동기화**: 기능 변경 시 영문+한국어 동시 반영
- **노트북 감사**: 노트북 코드는 실행 확인 후에만 커밋
- **DART 먼저**: 모든 개선은 DART 우선, EDGAR는 안정화 후 따라감
- **import 방향**: L0 ← L1 ← L2 ← L3 (CI 검증)
