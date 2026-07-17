---
title: "DART EDGAR, 한 줄로 열기"
date: "2026-07-11"
description: "삼성전자와 Apple을 같은 Company 한 줄로 열지만, 원화와 달러와 결산월이 달라 매출을 그대로 비교하면 틀린다. DART와 EDGAR를 같은 panel 호출로 열되 기준은 따로 적는 법을 익힌다."
category: dartlab-stories
series: dartlab-stories
seriesOrder: 6
topicSlug: "dart-edgar-company"
ogImage: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/d0/d0f326e2c72fe630cf5f3ab323debb6560db00f97389fd278056af3eb42873bf.webp
cardPreview: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/89/89312fef9780cd42d35fd32bf7b841be638eb0f3d91093a7b5d16208174bfe9d.webp
thumbnail: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/d0/d0f326e2c72fe630cf5f3ab323debb6560db00f97389fd278056af3eb42873bf.webp
thumbnailBg: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/0c/0c0220855a4a26e6cbdc99378c8e5376ef97b4aa2bf1dd9d7bfe8a4501a5a1be.webp
tags:
  - dartlab
  - DART
  - EDGAR
  - 재무제표
  - 공시
  - 파이썬
  - 브라우저
---

## 삼성전자와 애플을 같은 한 줄로 여는데, 매출부터 틀린다

삼성전자와 애플을 dartlab에서는 똑같이 한 줄로 연다. `dartlab.Company("005930")`과 `dartlab.Company("AAPL")`. 여는 문법도 같고, 그다음 부르는 함수도 같다. 그런데 두 회사의 매출을 나란히 놓는 순간 문장이 틀린다. 한쪽은 원화로 적힌 수십조이고, 다른 쪽은 달러로 적힌 수천억이다. 결산월(fiscal period)까지 어긋난다. 자릿수만 보고 큰 쪽이 이겼다고 말하면, 코드는 통과했는데 결론이 틀린 것이다.

그래서 이번 편의 규칙은 한 문장으로 압축된다. 같은 질문으로 열되, 같은 기준이라고 말하지 않는다. 6편은 비교를 가르치지 않는다. 두 나라 회사가 같은 입구로 열린다는 것을 먼저 확인하고, 화면에 뜬 계정명과 기간 열과 돈 단위를 따로 적어 두는 습관을 만든다. 비교는 그다음 편의 일이다.

지금까지는 [DART 공시분석, 설치 없이](/blog/what-is-dartlab)에서 본 전체 그림과 [DART 종목코드, 회사 열기](/blog/pick-company-by-code)에서 배운 여섯 자리 종목코드로 국내 회사만 다뤘다. 삼성전자는 `005930`이다. 그런데 공시는 한국에만 있지 않다. 미국 회사는 [SEC EDGAR](https://www.sec.gov/edgar)에서 10-K와 10-Q를 내고, 애플은 `AAPL`이라는 ticker로 부른다. 초보자는 여기서 DART와 EDGAR를 완전히 다른 도구로 배워야 한다고 겁을 먹는다. dartlab의 답은 다르다. 둘 다 `Company`로 시작한다. 입력값만 다를 뿐 첫 문은 같다.

```python
import dartlab

kr = dartlab.Company("005930")
us = dartlab.Company("AAPL")

kr.market, us.market
```

결과는 `KR`과 `US`로 갈라진다. 같은 `Company`로 시작했지만 dartlab은 안쪽에서 한국 회사와 미국 회사를 구분한다. 여섯 자리 숫자는 국내 종목코드로, 알파벳 ticker는 미국 종목으로 알아서 갈래를 탄다. 국내 회사는 DART 공시 데이터로 가고, 미국 회사는 EDGAR 데이터로 간다. 여는 코드는 하나인데 원천은 둘이다. 이 한 줄이 나머지 편 전체의 밑바탕이다.

![DART와 EDGAR를 같은 Company로 여는 흐름](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/c2/c2ca478b4d64353e9f3147c254ac4188a5100729893bf37fc8efd71c63809fe3.webp)

## 같은 표를 열어 본다

[재무제표, 파이썬 한 줄](/blog/call-financial-statements)에서 `panel("IS")`를 배웠다. `IS`는 손익계산서다. 이번에는 삼성전자와 애플 손익계산서를 같은 코드 모양으로 열어 보자.

```python
kr_is = kr.panel("IS")
us_is = us.panel("IS")

kr_is.head(5)
```

삼성전자 표는 `snakeId`, `항목`, 그리고 `2026Q1`, `2025Q4` 같은 기간 열로 열린다. 앞줄에는 매출액, 매출원가, 매출총이익처럼 손익계산서의 맨 위 계정이 순서대로 뜬다. `snakeId`는 여러 회사의 이름 흔들림을 줄이려는 표준 이름이고, `항목`은 사람이 읽는 계정명이다. 표가 열렸다는 사실만 중요한 게 아니라, 실제 계정명과 실제 기간 숫자가 함께 보인다는 점이 중요하다.

애플도 같은 방식으로 보자.

```python
us_is.head(5)
```

애플 표도 왼쪽에 `snakeId`와 `항목`이 있고, 오른쪽으로 기간 열이 펼쳐진다. 한국 회사에서 쓰던 "앞줄을 먼저 본다"는 습관이 미국 회사에서도 그대로 통한다. 계정명은 영어 원문 기반이라 삼성전자 표의 한글 계정명과 글자는 다르지만, 표의 뼈대는 똑같다. 왼쪽에 이름, 오른쪽에 기간. 여기까지 확인한 것은 딱 하나다. 두 표가 같은 모양으로 열렸다. 그 이상은 아직 없다.

## 표가 비슷해도 돈 단위는 다르다

표가 비슷하게 생기면 사람은 바로 비교하고 싶어진다. 하지만 삼성전자 숫자는 원화이고 애플 숫자는 달러다. 표 모양이 같다고 돈 단위까지 같지는 않다. 통화 환산도 하지 않았고, 회계연도 기준도 다를 수 있다.

삼성전자는 DART의 사업보고서와 분기보고서 리듬을 따르고, 애플은 EDGAR의 10-K와 10-Q 리듬을 따른다. 둘 다 연간과 분기 공시가 있지만, 결산월과 fiscal period가 다르면 달력 기준으로 바로 나란히 놓기 어렵다. 삼성전자는 12월 결산이라 회계연도가 달력 해와 거의 겹친다. 반면 애플의 회계연도는 9월 마지막 토요일 근처에서 끝난다. 그래서 애플의 `2025Q4`는 여름 분기이지, 겨울 분기가 아니다. 라벨만 보고 같은 석 달로 읽으면 계절부터 어긋난다.

[재무제표 기간, Y와 Q 조회](/blog/the-grid)에서 배운 기간 감각이 여기서 다시 필요하다. 국내 회사의 `2025Q4`와 미국 회사의 `2025Q4`가 항상 같은 달력 기간을 뜻하지는 않는다. 통화도 마찬가지다. 삼성전자 매출액은 조 단위 원화로 찍히고, 애플 매출액은 십억 단위 달러로 찍힌다. 환율을 곱하기 전에는 두 숫자의 자릿수 자체가 다른 언어다.

![같은 panel 호출과 다른 기준을 나누는 비교 순서](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/7a/7a52630dd3c431a749836783b968a0c560cc735bf1f12e73c0b8a36403ffef0d.webp)

그래서 화면을 볼 때 세 가지를 따로 적는다. 계정명, 기간 열, 돈 단위. 표 옆에 "원화", "DART", "국내 분기"라고 적고, 다른 표 옆에 "달러", "EDGAR", "미국 fiscal period"라고 적는다. 이 메모가 나중에 자동 분석 문장을 그대로 믿지 않고 원 표로 돌아오게 하는 안전선이다.

## 세 장을 모두 같은 질문으로 연다

손익계산서 하나만 되는지 보면 부족하다. 재무제표의 기본 세 장은 손익계산서, 재무상태표, 현금흐름표다. 같은 질문을 세 장에 던져 보자.

```python
kr_bs = kr.panel("BS")
us_bs = us.panel("BS")

kr_bs.head(4)
```

```python
us_bs.head(4)
```

재무상태표도 같은 방식으로 열린다. 왼쪽은 계정이고 오른쪽은 기간이다. 다만 항목 이름, 기간 열, 돈 단위는 회사와 시장에 따라 다르다. 현금흐름표도 확인한다.

```python
kr_cf = kr.panel("CF")
us_cf = us.panel("CF")

kr_cf.head(4)
```

```python
us_cf.head(4)
```

손익계산서, 재무상태표, 현금흐름표가 모두 실제 표로 열린다. 회사가 다르고, 시장이 다르고, 공시 축적 기간도 다르기 때문에 보이는 기간 열과 계정 줄은 서로 다르다. 예컨대 오래된 미국 회사는 미국 공시 축적 기간이 길어 더 먼 과거 열까지 보이고, 국내 회사는 DART 전자공시 도입 이후 구간이 촘촘하다. 그래도 코드는 같다. 회사를 만들고, `panel("IS")`, `panel("BS")`, `panel("CF")`를 열고, 앞줄을 확인하면 끝이다. 인자로 넣는 세 글자, `IS`와 `BS`와 `CF`만 바꾸면 세 장이 차례로 열린다. 새 도구를 처음부터 다시 배우지 않아도 국내 회사와 미국 회사에 똑같이 쓸 수 있다. 아직 분석 결론은 아니다. 표를 제대로 연 것이다.

## 순서를 지키면 코드가 맞아도 문장이 안 틀린다

초보자가 가장 많이 하는 실수는 같은 표 모양을 보고 바로 비교하는 것이다. 두 숫자를 그대로 나란히 놓으면 큰 숫자처럼 보이는 쪽이 이기는 착시가 생긴다. "손익계산서를 열었다"와 "두 회사의 매출을 비교했다"는 전혀 다른 말이다. 비교하려면 통화 환산, 기간 정렬, 회계연도 확인이 더 필요하다.

그래서 좋은 노트북은 순서를 지킨다. 먼저 표를 열고, 다음에 기간을 맞추고, 그다음 돈 단위를 맞추고, 마지막에 비교한다. 예를 들어 애플의 여름 분기와 삼성전자의 겨울 분기를 나란히 놓았다면 이미 기간 정렬 단계에서 멈춰야 한다. 여기서 환율까지 곱하지 않은 채 매출 숫자를 빼면, 계산기는 답을 내지만 그 답은 아무 뜻이 없다. 이 순서를 건너뛰면 코드가 맞아도 문장이 틀린다. 이 원칙은 [DART와 EDGAR, 한 구조로 읽기](/blog/dart-edgar-unified-structure)에서 다룬 큰 구조와도 이어진다. 공시 시스템이 다르다고 질문을 포기할 필요는 없다. 같은 질문으로 연 뒤, 다른 기준을 정직하게 표시하면 된다.

## 원천 페이지도 따로 본다

dartlab은 실행 도구다. 하지만 원천 감각은 따로 가져야 한다. 한국 공시는 [DART 전자공시시스템](https://dart.fss.or.kr/)과 [OpenDART](https://opendart.fss.or.kr/)에서 확인하고, 미국 공시는 [SEC Search Filings](https://www.sec.gov/search-filings), [EDGAR Full Text Search](https://www.sec.gov/edgar/search/), [About EDGAR](https://www.sec.gov/submit-filings/about-edgar)를 참고한다.

이 링크를 외우라는 뜻은 아니다. 코드가 표를 잘 열어도 원천이 어디인지 감각이 있어야 한다는 뜻이다. 표 한 줄이 이상하게 보일 때, 결국 돌아가서 확인할 곳은 이 원천 페이지들이다. DART와 EDGAR를 같은 `Company`로 열 수 있다는 말은 출발 방법이 같다는 말이지, 공시 제도까지 하나가 됐다는 말이 아니다. 한쪽은 금융감독원이 운영하고, 다른 쪽은 미국 증권거래위원회가 운영한다. 제출 양식도, 마감 규정도, 쓰는 언어도 다르다. 이번 편의 코드는 브라우저에서 그대로 도는 범위, 즉 `Company`, `market`, `panel`, 표의 `head`만 쓴다. 실시간 시세나 뉴스, 수급 수집은 외부 요청 조건이 걸려 브라우저에서는 안 된다. 로컬 설치본에서만 되는 영역이라 여기서는 다루지 않는다.

## 자주 걸리는 함정 셋

- 같은 `Company`로 열렸다고 같은 시장이 아니다. `kr.market`은 `KR`, `us.market`은 `US`, 입구 뒤 원천이 다르다.
- 같은 `panel("IS")`로 열렸다고 같은 통화가 아니다. 원화와 달러를 그대로 빼거나 나누면 틀린다.
- 같은 기간 라벨처럼 보여도 같은 달력 기간이 아니다. 미국 회사의 fiscal period는 회사마다 끝나는 달이 다르고, 애플은 9월에 회계연도가 끝난다.

## 다음 편에서 할 것

이번 편은 DART와 EDGAR가 같은 `Company` 입구로 시작한다는 감각을 만들었다. 다음 편에서는 애플의 재무제표 panel을 더 깊게 본다. 손익계산서, 재무상태표, 현금흐름표가 어떤 행과 기간 열로 열리는지 확인하고, 미국 공시의 10-K와 10-Q 리듬이 표 위에서 어떻게 보이는지 배운다. 재무제표 panel이 열린다고 EDGAR 원문 본문 섹션까지 모두 DART 본문처럼 읽힌다는 뜻은 아니다. 확인한 만큼만 쓴다.

오늘 기억할 한 줄은 이것이다. **같은 질문으로 열되, 같은 기준이라고 말하지 않는다.** 이 한 줄이 DART와 EDGAR를 함께 읽는 첫 안전장치다.
