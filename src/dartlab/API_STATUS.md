# dartlab 공개 API 현황

> `dartlab.__init__.py`의 `__all__`에 노출된 모든 항목.
> 상태: **공개**(검증 완료) / **대기**(미검증, 승격 또는 폐기 판단 필요) / **폐기**(제거 예정)
>
> 승격 기준: 편의성 원칙 — 종목코드 하나면 끝, `import dartlab` 하나로 접근, 첫 호출 5초 이내.

## 공개 (검증 완료)

| API | 형태 | 설명 |
|-----|------|------|
| `Company` | 클래스 | 핵심 facade. 종목코드 하나로 전체 접근 |
| `search` | 함수 | 종목 검색 (KR+US) |
| `listing` | 함수 | 전체 상장법인 목록 |
| `getKindList` | 함수 | KR 상장사 DataFrame |
| `codeToName` | 함수 | 종목코드 → 회사명 |
| `nameToCode` | 함수 | 회사명 → 종목코드 |
| `searchName` | 함수 | 이름 검색 |
| `fuzzySearch` | 함수 | 퍼지 검색 |
| `collect` | 함수 | 지정 종목 DART 데이터 수집 |
| `collectAll` | 함수 | 전체 상장종목 수집 |
| `downloadAll` | 함수 | HF 전체 데이터 다운로드 |
| `scanAccount` | 함수 | 전종목 단일 계정 시계열 |
| `scanRatio` | 함수 | 전종목 재무비율 시계열 |
| ~~`scanRatioList`~~ | 제거 | `scan("ratio")`로 대체 |
| `config` | 모듈 | 전역 설정 |
| `verbose` | 속성 | 출력 레벨 |
| `dataDir` | 속성 | 데이터 디렉토리 |

## 대기 (미검증 — 승격 또는 폐기 판단 필요)

## 공개 — 외부 데이터 (gather)

| API | 형태 | 설명 |
|-----|------|------|
| `price` | 함수 | 주가 시계열/스냅샷. 종목코드 하나로 동작 |
| `news` | 함수 | 기업 뉴스 수집. 종목코드 하나로 동작 |
| `macro` | 함수 | 거시 지표 시계열. ECOS(KR)/FRED(US) |
| `Fred` | 클래스 | FRED API 직접 래퍼 |

### 외부 데이터 (대기)

| API | 형태 | 현황 | 판단 포인트 |
|-----|------|------|-------------|
| `consensus` | 함수 | 종목코드 하나로 동작 | 수집원 안정성 미검증 |
| `flow` | 함수 | 종목코드 하나로 동작, KR 전용 | 수집원 안정성 미검증 |

## 공개 — OpenAPI 진입점

| API | 형태 | 설명 |
|-----|------|------|
| `OpenDart` | 클래스 | DART OpenAPI 래퍼. API 키 필요 |
| `OpenEdgar` | 클래스 | EDGAR OpenAPI 래퍼 |

### Market 전수 분석

| API | 형태 | 현황 | 판단 포인트 |
|-----|------|------|-------------|
| `screen` | 함수 | 프리셋 기반 스크리닝 | scanAccount 기반 재구성 가능성 |
| `benchmark` | 함수 | 섹터별 비율 벤치마크 | screen과 결합 여부 |
| `signal` | 함수 | 공시 키워드 트렌드 | docs 전체 필요. 실험적 |
| `network` | 함수 | 상장사 관계 네트워크 | 시각화 의존. 독립 기능인가 |
| `groupHealth` | 함수 | 그룹사 건전성 | network 의존. 독립 가치 있나 |
| `governance` | 함수 | 6축 scan — 지배구조 | **미인정**. 미검증 |
| `workforce` | 함수 | 6축 scan — 인력 | **미인정**. 미검증 |
| `capital` | 함수 | 6축 scan — 주주환원 | **미인정**. 미검증 |
| `debt` | 함수 | 6축 scan — 부채 | **미인정**. 미검증 |

### Analysis (종목 분석)

| API | 형태 | 현황 | 판단 포인트 |
|-----|------|------|-------------|
| `insights` | 함수 | 종목코드 하나로 동작. 7영역 등급 | 편의성 OK. 결과 품질 검증 필요 |
| `audit` | 함수 | 종목코드 하나로 동작. Red Flag | 편의성 OK. 결과 품질 검증 필요 |
| `forecast` | 함수 | 종목코드 하나로 동작. 매출 예측 | 편의성 OK. 예측 정확도 검증 필요 |
| `valuation` | 함수 | 종목코드 하나로 동작. DCF+DDM+상대 | 편의성 OK. 모델 검증 필요 |
| `simulation` | 함수 | 종목코드 하나로 동작. 시나리오 | 편의성 OK. 모델 검증 필요 |
| `research` | 함수 | 종목코드 하나로 동작. 종합 리포트 | 편의성 OK. 결과 품질 검증 필요 |
| `digest` | 함수 | 인자 없이/섹터로 동작. 변화 다이제스트 | docs 전체 필요. 실험적 |
| `crossBorderPeers` | 함수 | 종목코드 하나로 동작 | WICS→GICS 매핑 품질 확인 |

## 공개 — AI

| API | 형태 | 설명 |
|-----|------|------|
| `ask` | 함수 | LLM 기업 분석 질문. 종목+질문 |
| `chat` | 함수 | 에이전트 모드. tool calling 심화 |
| `setup` | 함수 | AI provider 설정/안내 |
| `llm` | 모듈 | ai 모듈 alias (llm.configure 등) |

## 공개 — Review

| API | 형태 | 설명 |
|-----|------|------|
| `Review` | 클래스 | 기업 리뷰 템플릿 기반 분석 |

### 기타

| API | 형태 | 현황 | 판단 포인트 |
|-----|------|------|-------------|
| `SelectResult` | 클래스 | select 결과 타입 | 내부 타입 노출. 사용자가 쓸 일 있나 |
| `ChartResult` | 클래스 | 차트 결과 타입 | 내부 타입 노출. 사용자가 쓸 일 있나 |
| `checkFreshness` | 함수 | 종목코드 하나로 동작 | API 키 필요. 사용 빈도 낮음 |
| `plugins` | 함수 | 플러그인 목록 | 플러그인 생태계 미형성 |
| `reload_plugins` | 함수 | 플러그인 재스캔 | 위와 동일 |
| `chart` / `table` / `text` | 모듈프록시 | 도구 모듈 lazy 로드 | 사용 빈도, 독립 가치 확인 |
| `core` | 모듈 | 내부 인프라 모듈 | 사용자가 직접 쓸 일 있나 |

## 정리 대상 요약

- **공개 확정**: 17개 (Company, 검색/목록, 수집, scanAccount 계열, config)
- **대기**: 30개 (승격 또는 폐기 판단 필요)
- **즉시 폐기 후보**: `SelectResult`, `ChartResult`, `core` (내부 타입/모듈 노출)
