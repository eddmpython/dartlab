# 061 Profile Pipeline 기획

## 요약

Company profile 파이프라인 전면 재설계.
5개 Phase로 아래부터 위로: report 와이드 → index 순서 → 수평화 → diff → viewer.

## 실험 결과

### 001: report toWide 변환 검증

5개 pivot Result → metric(행)×year(열) 와이드 DataFrame 변환 **성공**.

| Result | metric 행 수 | year 열 수 | 값 타입 |
|--------|-------------|-----------|---------|
| DividendResult | 2 | 10 | 숫자 |
| EmployeeResult | 3 | 10 | 숫자 |
| MajorHolderResult | 1 | 10 | 숫자 |
| AuditResult | 2 | 10 | 문자열 |
| ExecutiveResult | 3 | 1 (snapshot) | 정수 |

나머지 23개 apiType 분류:
- **단순 와이드 5개**: executivePayAllTotal, majorHolderChange, minorityHolder, outsideDirector, unregisteredExecutivePay
- **그룹 와이드 7개**: auditContract, corporateBond, executivePayIndividual, investedCompany, stockTotal, topPay, treasuryStock
- **텍스트/부적합 6개**: auditOpinion, capitalChange, nonAuditContract, privateOfferingUsage, publicOfferingUsage, shortTermBond
- **데이터 없음 6개**: commercialPaper, contingentCapital, debtSecurities, executivePayByType, executivePayTotal, hybridSecurities

### 002: index 문서 순서 정렬 검증

95행 index를 I~XII장 순서로 정렬 **성공**. topic 집합 동일.

finance(★)가 III장에, report(◆)가 해당 chapter에 올바르게 삽입됨.

발견된 문제:
- XII장에 미매핑 topic 대량 (sectionMappings 056 과제)
- `_chapterMap()`에 auditOpinion, outsideDirector 누락 → XII로 빠짐
- IV장(이사의 경영진단) topic이 XII로 밀림 — mdna 등

## Phase 확정

### Phase 1: report toWide

- 5개 Result dataclass에 `toWide() -> pl.DataFrame` 메서드 추가
- 범용 `reportToWide(df, valueCols, yearCol)` 함수 (단순 와이드 5개용)
- 축: metric(행) × year(열) — finance와 동일

### Phase 2: index 순서 정렬

- Phase 2a: sections DataFrame에 `chapter` 컬럼 추가 (pipeline.py)
- Phase 2b: index 정렬키 `(chapterOrder, subOrder)` 부여 후 sort
- `_chapterMap()` 누락 보강 (auditOpinion→V, outsideDirector→VI)

### Phase 3: period 형식

- **통일 불필요** 확정. 각 소스 고유 포맷 유지.
- viewer 단에서만 정렬.

### Phase 4: diff 레이어

- 4a: 텍스트 diff — sections 셀 hash 비교 (060-003 검증 완료)
- 4b: 숫자 변곡점 — finance 시계열 ±20% major, ±10% minor, 부호전환

### Phase 5: viewer

- `ViewerSection` / `ViewerDocument` dataclass
- 문서 순서로 정렬된 section 목록
- 각 section은 show() on-demand — 데이터 구조만 정의, 렌더링은 UI/export

## 구현 순서 (의존성)

```
Phase 2a (sections chapter) ─┐
                              ├→ Phase 2b (index 정렬)
Phase 1 (report toWide) ─────┤
Phase 4a (텍스트 diff) ───────┤
Phase 4b (숫자 변곡점) ───────┼→ Phase 5 (viewer)
```
