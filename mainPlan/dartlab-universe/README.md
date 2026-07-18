# DartLab Universe

상태: 제품급 구현 PRD v1.0, 구현 미착수, 2026-07-18 현재 저장소와 HF 실측 기반. 데이터 엔진 우선 원칙과 기존 시스템 무변경 경계를 확정했다. 3D, 공개 경로, RAG 구현은 선행 게이트 통과와 운영자 승인 전까지 금지한다.

## 한 문장 정의

**DartLab Universe는 HF의 모든 DartLab 데이터, 실존 DartLab 엔진이 호출할 수 있는 모든 데이터와 계산 능력, 모든 블로그 글·이미지·영상을 하나의 주소 가능하고 근거 추적 가능한 지식 공간으로 만드는 전용 데이터 엔진이다.**

DART 우주, EDGAR 우주, 기업별 우주가 따로 있는 것이 아니다. DART와 EDGAR, 회사와 산업, 공시와 재무, 블로그와 미디어, 관측과 계산은 하나의 전체 우주 안에서 서로 다른 객체 종류와 근거 상태를 가진다.

## 최상위 결정

1. 렌더러보다 데이터 엔진이 먼저다.
2. `2,664개`나 현재 파일 수는 경계가 아니라 특정 시점의 관측값이다.
3. 모든 발견 항목은 최소한 다시 열 수 있는 주소와 상태를 가져야 한다.
4. 기존 HF, 엔진, 프론트 데이터 작업대, 로컬 시뮬레이터는 Universe를 import하지 않는다.
5. Universe만 기존 시스템을 읽기 전용으로 소비한다.
6. HF와 기존 런타임이 계속 SSOT다. Universe는 두 번째 원본 저장소가 아니다.
7. 관측, 결정론적 파생, 시뮬레이션, 사람의 주장, 모델 추론을 같은 사실로 합치지 않는다.
8. 3D는 지식 SSOT가 아니라 지식 엔진의 공간 투영이다.
9. RAG는 새 독립 AI 루프가 아니라 기존 `dartlab.ask` 작업대가 Universe 검색·관계·엔진 도구를 쓰는 후속 질의 계층이다.
10. 운영자가 직접 검수해 승인하기 전 공개 버튼, 메뉴, 라우트, 내비게이션은 0개다.

## 현재 실측 기준선

| 영역 | 2026-07-18 관측값 | 제품에서의 의미 |
|---|---:|---|
| 접근 가능한 HF 저장소 | 4개 | 선언 레지스트리와 라이브 트리를 함께 조사 |
| HF 파일 | 77,757개 | 고정 경계가 아닌 census 기준선 |
| HF 총 바이트 | 304,535,378,430 | 전체 브라우저 적재가 불가능함을 증명 |
| 로컬 블로그 글 | 275개 | frontmatter부터 문장·표·코드·미디어 ref까지 대상 |
| 블로그 이미지 ref | 1,821개, 고유 1,808개 | HF media 객체와 양방향 정합 검사 |
| 비어 있지 않은 YouTube ID | 14개 | 영상 locator와 시간 구간의 대상 |
| `dartlab.capabilities()` 항목 | 226개 | callable surface 전체 census 시작점 |
| 실존 7개 axis 레지스트리 | 147개, hidden 2개 포함 | 임의 axis 발명 금지 기준선 |
| `simulate/` Python 파일 | 68개 | 공개 안정 엔진이 아닌 로컬 preview 입력 |

이 숫자들은 Universe 정의가 아니다. 각 snapshot의 `observedCount`일 뿐이며 다음 census에서 자동으로 변해야 한다.

## 문서 지도

1. [00-product-charter.md](00-product-charter.md): 하나의 전체 우주, 포함·비포함, 불변식, 사용자 가치, 제품 게이트
2. [01-verified-current-state-and-census.md](01-verified-current-state-and-census.md): HF·엔진·블로그·미디어·시뮬레이터·UI 작업대 실측과 전수성 계산
3. [02-data-engine-architecture.md](02-data-engine-architecture.md): 전용 엔진, 읽기 전용 어댑터, 런타임 SSOT, 의존 방향, UI·로컬 경계
4. [03-knowledge-identity-provenance-contract.md](03-knowledge-identity-provenance-contract.md): 객체·관계·근거·ID·동일성·시간·revision·재현 계약
5. [04-capability-simulator-execution.md](04-capability-simulator-execution.md): 실존 capability, 엔진 실행, 비용·취소·오류, 시뮬레이션 격리
6. [05-query-rag-and-multimodal.md](05-query-rag-and-multimodal.md): 구조화·graph·lexical·vector·tool 질의, RetrievalEvidencePack, 블로그·이미지·영상
7. [06-spatial-projection-and-3d.md](06-spatial-projection-and-3d.md): 진짜 3D 계약, 안정 좌표, semantic LOD, tile, renderer benchmark
8. [07-product-grade-slo-security-accessibility.md](07-product-grade-slo-security-accessibility.md): 성능, 복구, 관측성, 보안, 라이선스, 접근성 SLO
9. [08-implementation-roadmap.md](08-implementation-roadmap.md): 단계별 신규 파일·함수·테스트·인수 기준·롤백·공개 통제
10. [09-evaluation-decision-ledger.md](09-evaluation-decision-ledger.md): ADR, 위험, 기각안, 전문가 평가, 개선 이력, 100점 루브릭

## 착수 순서

```text
전수 census
  -> 지식·ID·근거 계약
  -> Universe 전용 read-only attempts 엔진
  -> 전체 카탈로그와 구조화 질의
  -> 엔진 실행 영수증
  -> hybrid retrieval와 근거 검증
  -> 공간 projection과 semantic tile
  -> 내부 전용 3D
  -> RAG 평가
  -> 운영자 직접 검수
  -> 별도 공개 승인
```

앞 단계가 실패하면 다음 단계는 시작하지 않는다. 특히 G0부터 G3와 모델 없는 근거 검증 G4E까지 통과하기 전 renderer 코드는 0줄이다. 생성 RAG 품질 gate G4R은 내부 3D 뒤에 수행한다.

## 현재 평가

문서 품질만 평가하며 미구현 제품의 성능을 점수로 포장하지 않는다. 최신 HF drift까지 반영한 최종 독립 평가 R8은 100/100, 핵심 영역별 최저점 전부 충족, K01부터 K20까지 PASS, blocker 0으로 합격했고 데이터와 공간 교차 감사도 CLOSED다. 근거, 감점, 개선 이력은 [09-evaluation-decision-ledger.md](09-evaluation-decision-ledger.md)에 기록한다.

## 다음 한 단계

운영자 구현 승인 후 첫 작업은 `tests/_attempts/dartlabUniverse/`에 읽기 전용 census를 만드는 것이다. `src/dartlab`, `ui`, `landing`, `blog`, 기존 시뮬레이터 파일은 이 단계에서 수정하지 않는다.
