---
title: "EDGAR 재무제표, 코드 실행"
date: "2026-07-11"
description: "애플 EDGAR 재무제표를 열면 값이 너무 커 보이는데 달러라 자릿수가 다를 뿐이다. dartlab에서 panel 코드로 IS, BS, CF 세 장을 같은 표면으로 열고 왼쪽 계정, 오른쪽 기간 구조를 잡는다."
category: dartlab-stories
series: dartlab-stories
seriesOrder: 7
topicSlug: "edgar-financial-panel"
ogImage: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/68/685fd731eef9dea7054fe147f4c1a87dccf77e518d0c59176e1eb49fedb461f0.webp
cardPreview: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/e0/e0989b009d4ac81a60a3f8b5eeb90554158e847dbab4f5a3db7e6374836f26c3.webp
thumbnail: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/68/685fd731eef9dea7054fe147f4c1a87dccf77e518d0c59176e1eb49fedb461f0.webp
thumbnailBg: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/59/591eabf2c50da1eca8236d979b79d08005c2aa42a5ed797baecdcbdfe14607d8.webp
tags:
  - dartlab
  - EDGAR
  - 재무제표
  - Apple
  - panel
  - 파이썬
  - 브라우저
---

## 애플 재무제표는 값이 너무 커 보인다

애플 손익계산서를 열면 첫 느낌은 "숫자가 너무 크다"다. 착시다. 애플 값은 달러라 자릿수가 원화와 다를 뿐이다. 이 숫자를 한국 회사 원화 매출 옆에 그대로 붙이면 크기 착시가 따라온다. 그래서 이번 편은 애플 하나만 놓고, 매출부터 현금흐름까지 EDGAR 재무제표 세 장이 `panel` 위에서 어떻게 열리는지 감각부터 잡는다.

그리고 하나 더 정직하게 짚는다. 브라우저 공개본과 로컬 설치본은 계정 후보와 기간 범위가 서로 다를 수 있다. 그래서 이 편의 정답은 실행 결과 숫자를 외우는 게 아니다. 왼쪽에 계정, 오른쪽에 기간 값이 오는 표 구조를 잡는 것이다. 이 구조만 잡으면 나중에 DART 회사와 EDGAR 회사를 같은 질문으로 읽을 수 있다.

[DART EDGAR, 한 줄로 열기](/blog/dart-edgar-company)에서 삼성전자와 Apple을 같은 `Company` 입구로 열었다. 이번 편은 그다음 한 걸음이고, 비교는 아직 하지 않는다. 아직 `Company`가 낯설다면 [DART 종목코드, 회사 열기](/blog/pick-company-by-code)를 먼저 보면 된다. 국내 회사는 여섯 자리 종목코드로, 미국 회사는 ticker로 연다. 더 큰 그림은 [DART 공시분석, 설치 없이](/blog/what-is-dartlab)에서 본 `panel`과 `scan`의 역할로 이어진다.

미국 회사도 첫 문은 똑같다. `Company("AAPL")`을 만들고 미국 회사로 잡히는지 확인한다.

```python
import dartlab

aapl = dartlab.Company("AAPL")
aapl.market
```

결과가 `US`면 출발은 맞다. 미국 회사로 열렸다는 표시다. 다만 여기까지가 "미국 회사가 열렸다"이지 "한국 회사와 비교할 준비가 끝났다"는 아니다. 비교하려면 통화, 기간, 회계연도 기준을 더 맞춰야 한다. 지금은 세 표를 같은 표면으로 여는 데까지만 간다.

![EDGAR 재무제표 세 장을 같은 panel로 여는 흐름](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/6b/6b9b2dd2b691a5a3a34d6d6e11623676f4249f2b00acd3587b22d1684c197a26.webp)

## 손익계산서는 매출에서 시작한다

손익계산서는 회사가 얼마나 팔고, 얼마를 비용으로 쓰고, 얼마를 남겼는지 보는 표다. EDGAR에서도 먼저 `panel("IS")`를 연다.

```python
is_panel = aapl.panel("IS")
is_panel.head(5)
```

브라우저에서 이 셀을 실행하면 앞쪽에 `snakeId`와 `항목`이 보인다. 오른쪽에는 `2026Q2`, `2026Q1` 같은 기간 열이 이어진다. 첫 줄 근처에는 `sales`나 `revenue`처럼 매출을 뜻하는 줄이 보이고, 그 아래에는 `cost_of_sales` 같은 매출원가 줄이 보인다.

초보자는 여기서 "값이 너무 크다"라고 먼저 느낀다. 하지만 Apple의 값은 달러 기준이다. 한국 회사 표에서 보던 원화 숫자와 자릿수가 다르다. 이 숫자를 그대로 삼성전자 매출과 붙이면 안 된다.

또 하나 봐야 할 것이 있다. `snakeId`는 사람이 읽는 계정명이 아니다. 여러 회사의 계정 이름 흔들림을 줄이기 위한 표준 이름이다. 사람에게 익숙한 이름은 `항목` 열에 있다. 그래서 표를 볼 때는 왼쪽 두 열을 함께 본다. `snakeId`는 코드가 찾기 좋은 이름이고, `항목`은 사람이 읽기 좋은 이름이다.

[재무제표, 파이썬 한 줄](/blog/call-financial-statements)에서 배운 원칙이 여기서 그대로 이어진다. 먼저 전체 표를 열고, 앞줄을 본다. 바로 좁히지 않는다. 표가 어떤 계정과 기간을 들고 오는지 먼저 확인해야 한다.

## 재무상태표는 남아 있는 것을 본다

손익계산서가 "한 기간 동안 벌고 쓴 것"이라면, 재무상태표는 "그 시점에 남아 있는 것"을 본다. Apple의 자산, 현금, 부채, 자본 같은 줄은 `panel("BS")`에서 확인한다.

```python
bs_panel = aapl.panel("BS")
bs_panel.head(5)
```

앞줄에는 `assets`, `total_assets`, `current_assets`, `cash_and_cash_equivalents` 같은 줄이 나온다. `assets`는 자산총계, `current_assets`는 유동자산, `cash_and_cash_equivalents`는 현금및현금성자산이다.

여기서도 같은 습관을 쓴다. 첫째, 왼쪽 계정명을 본다. 둘째, 최근 기간 값을 본다. 셋째, 값이 비어 있거나 중복처럼 보이는 줄이 있으면 바로 판단하지 않는다. EDGAR 원천의 태그가 여러 방식으로 들어와 같은 의미가 여러 줄로 보일 수 있다.

이런 중복은 실패가 아니다. 오히려 공시 데이터를 기계가 읽을 때 생기는 흔한 장면이다. 처음부터 "한 줄만 정답"이라고 생각하면 표를 오해한다. 먼저 전체 표를 열고, 계정 후보가 어떤 이름으로 들어왔는지 본다. 나중에 분석할 때만 필요한 줄을 좁힌다.

## 현금흐름표는 돈의 이동을 본다

현금흐름표는 이익과 다르다. 회사가 실제로 현금을 얼마나 벌었고, 투자에 얼마나 썼고, 재무활동으로 얼마를 조달하거나 갚았는지 본다.

```python
cf_panel = aapl.panel("CF")
cf_panel.head(5)
```

앞줄에는 `cash_flows_from_operating_activities`, `operating_cashflow`, `operating_cash_flow` 같은 영업활동 현금흐름 줄이 보인다. 이름은 조금 다르지만 질문은 같다. "Apple이 영업으로 현금을 벌고 있는가"를 보기 위한 입구다.

여기서 이익과 현금을 섞으면 안 된다. 손익계산서의 매출과 이익은 발생주의 숫자다. 현금흐름표의 영업활동 현금흐름은 실제 현금 이동에 가까운 숫자다. 둘은 같이 읽어야 하지만 같은 말은 아니다.

초보자에게 좋은 순서는 이것이다.

1. `panel("IS")`로 매출과 비용을 본다.
2. `panel("BS")`로 자산과 현금을 본다.
3. `panel("CF")`로 영업현금흐름을 본다.
4. 세 표를 바로 합치지 말고 각 표가 대답하는 질문을 말로 분리한다.

이 순서를 지키면 표를 열자마자 결론을 쓰는 실수를 줄일 수 있다.

## 10-K와 10-Q 리듬을 따로 본다

Apple 표의 기간 열은 그냥 달력 열이 아니다. 미국 회사는 EDGAR에 10-K와 10-Q를 낸다. 10-K는 연간 보고서이고, 10-Q는 분기 보고서다.

10-K와 10-Q의 기간 기준은 회사의 회계연도와 연결된다. Apple의 최근 분기 열을 볼 때도 "몇 년 몇 분기"라는 이름만 보지 말고, 그 회사가 어떤 fiscal period로 공시했는지 의식해야 한다.

![EDGAR 재무제표의 공시 리듬과 브라우저 경계](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/b9/b9463a3da04faf88c0f9f65400f53b4988e32c8161bd9e66f5dc6e54342ab811.webp)

[재무제표 기간, Y와 Q 조회](/blog/the-grid)에서 배운 기간 감각이 여기서 다시 필요하다. DART 회사의 분기와 EDGAR 회사의 분기를 같은 달력 기간이라고 단정하면 안 된다. `panel`은 표를 열어 주지만, 표의 기간 의미까지 자동으로 투자 문장으로 바꿔 주지는 않는다.

## 원천 페이지를 같이 둔다

코드가 잘 돌아도 원천 페이지 감각은 따로 가져야 한다. dartlab은 표를 빨리 열어 주지만, EDGAR가 무엇을 보관하고 어떤 검색 화면을 주는지는 SEC 원천에서 확인하는 습관이 필요하다.

공시를 찾는 공식 입구는 [SEC Search Filings](https://www.sec.gov/search-filings)다. 회사명, ticker, CIK, filing type로 찾는다. 본문 단어까지 넓게 찾고 싶으면 [EDGAR Full Text Search](https://www.sec.gov/edgar/search/)로 문구를 검색하고 기간, 회사, filing category로 좁힌다. 데이터로 직접 받고 싶으면 [SEC EDGAR Application Programming Interfaces](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)가 companyfacts 같은 경로를 설명하고, 실제 입구는 [data.sec.gov](https://data.sec.gov/)다. 로컬 companyfacts 경로와 브라우저 공개 artifact가 다를 수 있는 이유도 이 원천 경로를 떠올리면 자연스럽다. 10-K와 10-Q가 헷갈리면 [Investor.gov의 10-K와 10-Q 읽기 안내](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/how-read)를, EDGAR 자체의 역할은 [About EDGAR](https://www.sec.gov/submit-filings/about-edgar)에서 본다.

외울 필요는 없다. 방향만 기억하면 된다. 표는 `panel`로 열고, 원천이 궁금하면 SEC 검색 화면이나 API 설명으로 돌아간다. 표를 여는 도구와 공시를 보관하는 원천을 구분해야 문장이 단단해진다.

## 자주 걸리는 함정 셋

이번 글의 코드는 브라우저에서 그대로 실행되는 범위 안에 있다. `dartlab.Company`, `market`, `panel`, `head`만 쓴다. 표를 연 것은 확인했지만 애플을 분석한 것은 아니다. 숫자의 의미 비교와 기간 정렬은 아직 시작도 안 했다. 그 사이에 자주 걸리는 함정이 셋 있다.

- 애플 숫자는 달러다. 한국 회사 원화 숫자 옆에 그대로 붙이면 크기 착시가 그대로 따라온다.
- 계정이 여러 줄로 보여도 바로 틀린 게 아니다. 원천 태그와 표준 이름이 겹치면 같은 의미가 여러 줄로 나온다. 먼저 표를 열고, 필요한 줄은 나중에 좁힌다.
- `panel("IS")`, `panel("BS")`, `panel("CF")`가 다 된다고 EDGAR 본문(`risk`, `mdna`, `item1Business`)까지 같은 방식으로 열리는 건 아니다. 이번 편이 확인한 것은 재무 panel까지고, 확인하지 않은 것은 다음 편의 결론으로 끌고 오지 않는다.

## 다음 편에서 할 것

이번 편에서는 EDGAR 재무제표 세 장을 같은 `panel` 표면으로 열었다. 손익계산서는 벌고 쓴 것, 재무상태표는 남아 있는 것, 현금흐름표는 돈의 이동을 보여 준다. 세 표는 같은 코드 흐름으로 열리지만 같은 질문을 대답하지 않는다.

다음 편에서는 다시 DART 사업보고서로 돌아간다. 숫자 표만 보는 것이 아니라 `chapter`, `sectionLeaf`, `blockLeaf` 같은 위치 정보를 통해 사업보고서 본문이 `panel` 위에서 어떻게 펼쳐지는지 본다. 오늘 기억할 한 줄은 이것이다. **미국 재무제표도 panel로 열되, 통화와 기간 기준은 따로 확인한다.**
