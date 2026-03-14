# EDGAR Engine Development Guide

## 핵심 사상 (EDGAR 적용)

**1. sections 수평화 = 10-K/10-Q 수평화**

EDGAR docs는 sections 수평화가 유일한 기초 경로다. 레거시 파서가 없다.
10-K와 10-Q의 topic을 form-native namespace로 구분한다:
- `10-K::item1Business`, `10-K::item1ARiskFactors`
- `10-Q::partIItem2Mdna`, `10-Q::partIIItem1ARiskFactors`

연간(10-K)과 분기(10-Q)가 같은 시간축에 자연 나열되며,
의미적 대응 6쌍(riskFactors, mdna, financialStatements, controls, legalProceedings, exhibits)으로
form 경계를 넘는 시계열 비교가 가능하다.

**2. 추가 내림 = 향후 확장**

현재는 topic 단위 content만 존재한다.
향후 topic 안의 세부 테이블(예: segment revenue table)이 식별되면
DART와 동일하게 행을 내려서 세분화한다.

**3. 뼈대 위 대체 = finance authoritative**

- finance (SEC XBRL): BS/IS/CF, ratios — 숫자 authoritative
- docs (10-K/10-Q sections): 서술형 전체 — 정성 authoritative
- report (SEC API): 향후 — 정형 structured disclosure
- profile.sections가 이 source들을 merge한 최종 뷰 (향후 구현)

**4. DART와의 차이**

- 레거시 파서 없음 — sections가 처음부터 유일한 경로
- sectionMappings.json 매퍼 100% (109개 매핑)
- report namespace 아직 없음 (SEC API 정형 데이터는 향후)
- profile namespace 아직 없음 (docs + finance merge는 향후)

## 현재 구조

```
c = Company("AAPL")

c.index                      # 39 topics 수평화 보드 DataFrame
c.show("BS")                 # DataFrame (finance)
c.show("ratios")             # DataFrame (ratio series)
c.show("10-K::item1Business")  # str (docs)
c.trace("BS")                # {"primarySource": "finance", ...}
c.trace("10-K::item1Business")  # {"primarySource": "docs", ...}
c.topics                     # ["BS", "IS", "CF", "ratios", "10-K::...", ...]

c.docs.sections              # 35 topics x 66 periods (pure source)
c.docs.filings()             # 69 filings
c.docs.show("10-K::item1Business")  # content 조회

c.finance.BS                 # 57 accounts x 18 years
c.finance.IS / CF / ratios / ratioSeries

c.BS                         # finance.BS 바로가기
c.sections                   # docs.sections 바로가기
c.filings()                  # docs.filings() 바로가기

c.insights                   # 7영역 등급
```

DART와 동일한 index / show / trace 공개 인터페이스를 갖추고 있다.
- `index`: finance(BS/IS/CF/ratios) + docs(sections topics) 통합 보드
- `show(topic)`: finance 제표, ratios, docs content 자동 라우팅
- `trace(topic)`: source provenance 딕셔너리

## 검증

- 335개 ticker, 333 성공, 에러 0 (2개는 CIK 매핑 누락)
- sections 매퍼 100% (106,023/106,023)
- 파이프라인 무에러 (211개 → 335개 검증)
- Company 인터페이스 테스트 13개 통과 (index/show/trace/topics/filings)
