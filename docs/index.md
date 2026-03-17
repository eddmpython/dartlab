---
title: DartLab
---

# DartLab

DartLab은 공시를 하나의 회사 맵으로 바꾸는 Python 라이브러리다.

지금 DartLab의 중심은 `sections`다. 사업보고서와 분기보고서의 섹션 구조를 먼저 기간축으로 수평화하고, 그 위에 `finance`와 `report` 같은 더 강한 source를 얹는다.

```python
import dartlab

c = dartlab.Company("005930")

c.sections
c.show("companyOverview")
c.trace("BS")
```

## 지금 공개 서사

- `Company` 하나로 시작한다
- `sections`가 회사의 canonical board다
- `show(topic)`으로 필요한 topic을 연다
- `trace(topic)`으로 선택된 source와 provenance를 확인한다

즉 예전처럼 parser 목록을 먼저 외우는 흐름이 아니다. 회사 전체를 하나의 맵으로 보고, 필요한 topic으로 내려가는 흐름이다.

## 왜 `sections`가 중요한가

공시는 원래 세로 문서다. 회사의 개요, 사업의 내용, 재무에 관한 사항, 리스크, 지배구조가 시간에 따라 이어진다.

DartLab은 이 세로 문서를 그대로 소비하지 않고 다음처럼 바꾼다.

1. 섹션 경계를 먼저 잡는다
2. 같은 구조 단위를 연도/분기별로 옆으로 맞춘다
3. 그 위에서 `finance`, `report`, `docs`를 source-aware하게 소비한다

이 구조 덕분에:

- 회사 전체 구조를 한 번에 볼 수 있고
- 같은 topic을 여러 기간에 걸쳐 비교할 수 있고
- AI GUI도 같은 맵을 그대로 소비할 수 있다

## Company 구조

- `c.sections`: 공개 company board
- `c.docs.sections`: pure docs horizontalization source
- `c.finance`: authoritative numeric layer
- `c.report`: authoritative structured disclosure layer
- `c.profile`: docs spine 위에 merge된 최종 company layer

현재 공개 사용 흐름은 `sections -> show -> trace`다.

## 바로 시작

- [빠른 시작](getting-started/quickstart)
- [API 개요](api/overview)
- [안정성 안내](stability)
- [변경 이력](changelog)
