# 058 EDGAR docs sections 수평화

## 목적

EDGAR docs를 DART sections와 동일한 구조로 수평화한다.
sections가 EDGAR docs의 유일한 기초 경로이며, 레거시 파서 없이 처음부터 sections 기반으로 간다.

## 목표 구조

```
c = Company("AAPL")
c.docs.sections       # pure source: topic × period DataFrame
c.docs.filings        # 문서 목록
c.profile.sections    # merged view (향후)
```

## 의존성

- 057 실험: 매퍼 100%, 파이프라인 무에러 (211개 검증)
- `engines/edgar/docs/sections/pipeline.py` — 이미 동작하는 sections()
- 수집 배치 진행 중 (211/7,537)

## 진행 순서

1. sections 수평화 품질 검증 (content 길이, 공백률, form 분포)
2. Company.docs namespace에 sections 연결
3. show() 메서드 — topic별 content 조회

## 실험 파일

| 파일 | 상태 | 내용 |
|------|------|------|
| `001_sectionsQuality.py` | ✅ | content 길이/fill rate/form 분포 검증 |
| `002_docsNamespaceProto.py` | ✅ | EdgarDocsProto: sections/filings/show 동작 검증 |
| `003_topicAlignment.py` | ✅ | 10-K/10-Q topic 정렬 + 의미적 대응 쌍 분석 |
| `004_crossFormContent.py` | ✅ | 대응 쌍 content 길이 비교 |

## 실행 결과

### 001 완료 (2026-03-13, 10개 대형주)

- fill rate: 30~40% (10-K 연1회 + 10-Q 분기별이므로 정상)
- content avg: 14K~66K chars, median 1~2K
- 10-K topics: 22~24개, 10-Q topics: 7~11개
- 실질 content가 충분히 들어감 — 수평화 품질 양호

### 002 완료 (2026-03-13)

- EdgarDocsProto 클래스: sections/filings/show 3개 메서드
- AAPL: 35 topics × 66 periods, filings 69건, item1Business 15,998 chars
- MSFT: 34 topics × 67 periods, filings 69건, item1Business 69,341 chars
- TSLA: 34 topics × 61 periods, filings 63건, item1Business 45,451 chars
- 프로토타입 동작 검증 완료 — 패키지 반영 가능

### 003 완료 (2026-03-13)

- 10-K topic은 annual에만, 10-Q topic은 quarter에만 값 — 깔끔 분리
- 의미적 대응 6쌍 전부 존재 (AAPL/MSFT): riskFactors, mdna, financialStatements, controls, legalProceedings, exhibits
- JPM은 10-Q Part I 없음 (금융회사 특이 구조 — Full Document 포함 가능성)
- form 경계를 넘는 시계열 비교 가능 — 같은 시간축에 연간+분기 자연 나열

### 004 완료 (2026-03-13)

content 길이 비교 (10-K vs 10-Q 대응 쌍):
- **MD&A**: 10-Q ≈ 10-K (ratio 0.75~1.11) — 분기별 MD&A도 실질적 content 풍부
- **Financial Statements**: 10-Q = 10-K × 0.47~0.76 — 분기는 condensed지만 여전히 대량
- **Risk Factors**: 패턴이 회사마다 다름
  - AAPL/TSLA/GOOGL: 10-Q에서는 짧은 업데이트만 (ratio 0.01)
  - AMZN: 10-Q에서도 전문 복사 (ratio 0.98)
- **Controls**: 10-Q = 10-K × 0.19~0.68 — 분기는 간략
- **Legal Proceedings**: 대체로 유사 길이
- MSFT 이상치: item8FinancialStatements가 10-K에서 2,430 chars뿐 — 별도 exhibit 참조 구조
