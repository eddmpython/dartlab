# Data Prism Attempt

목표: 기존 `data("catalog")`, `data("query")` 두 축을 유지하면서 한 번의 query로 서로 다른 asset을 팩터, 내러티브, 그래프, native 형태로 동시에 요청할 수 있는지 검증한다.

## 가설

1. asset마다 projection을 지정하는 `DataRequest`를 query envelope에 넣으면 공개 axis를 늘리지 않고도 혼합 데이터 작업대가 된다.
2. query 공통값과 request별 override를 결정적으로 합성할 수 있다.
3. 내러티브를 단순 문자열 배열이 아니라 document, chunk, content hash, 시간, source, evidence가 있는 행으로 만들 수 있다.
4. 최신 전용 데이터의 `knownAt`은 현재 시각으로 꾸미지 않고 `None`으로 남겨야 한다.

## 승격 기준

- 동일 asset을 서로 다른 requestId와 projection으로 요청할 수 있다.
- request별 subjects, measures, params가 query 공통값을 오염시키지 않는다.
- 내러티브 chunk ID와 content hash가 같은 입력에서 결정적이다.
- factor와 narrative가 공통 `assetId`, `eventAt`, `availableAt`, `knownAt`, `revisionId`, `sourceRef`, `evidenceRef`, `temporalStatus` 의미를 공유한다.
- 기존 단일 asset query와 결과 계약은 그대로 동작한다.

## 정리 판정

attempt는 공개 런타임과 독립된 순수 모델이다. 통과한 계약만 `src/dartlab/data`로 옮기고, 실행 로직이나 owner 계산을 이 디렉터리에 남기지 않는다.
