# Blog Structure

이 블로그는 `카테고리 폴더 -> 포스트 폴더 -> index.md + assets/` 구조로 관리한다.

운영 목표는 두 가지다.

- 검색을 타고 들어온 사람이 `바로 답을 얻고 다음 글로 이동`하게 만든다.
- AI 검색/요약 환경에서도 `문장 자체로 의미가 서는 본문`을 만든다.

즉 글은 단순히 많이 쓰는 것보다, `질문 하나에 정확히 답하는 허브`처럼 운영한다.

## 카테고리

- `01-disclosure-systems`: DART, EDGAR, form 체계, 원문 접근
- `02-report-reading`: 사업보고서 읽기, 서술 섹션 해석, 통합 읽기
- `03-financial-interpretation`: 생산능력, 건설중인자산, 감가상각, 주석 해석
- `04-data-automation`: 파이썬, 데이터 수집, 자동화 파이프라인

카테고리 번호는 고정한다. 중간에 새 카테고리가 필요하면 기존 번호를 바꾸지 말고 새 번호를 추가한다.

## 번호 체계

- 카테고리 번호는 분류용이다.
- 포스트 번호는 블로그 전체 전역 순번을 유지한다.
- 시리즈 순서는 `seriesOrder`로 따로 관리한다.

예시:

```text
blog/
  03-financial-interpretation/
    012-depreciation-after-capex/
      index.md
      assets/
```

## URL 규칙

- 공개 URL에는 카테고리 폴더가 들어가지 않는다.
- `blog/03-financial-interpretation/012-depreciation-after-capex/index.md`
- URL은 `/blog/depreciation-after-capex`

## Frontmatter 규칙

모든 포스트는 아래 메타를 가진다.

```yaml
title: 글 제목
date: YYYY-MM-DD
description: 1문장 설명
category: disclosure-systems | report-reading | financial-interpretation | data-automation
series: 시리즈 id
seriesOrder: 숫자
thumbnail: /avatar-*.png
cardPreview: /blog/assets/*.png | /blog/assets/*.jpg | /blog/assets/*.webp
```

- `thumbnail`: 카드 좌측 메타 영역에 쓰는 아바타형 대표 이미지
- `cardPreview`: 우측 정사각형 썸네일 슬롯에 쓰는 카드 전용 프리뷰 이미지
- `cardPreview`를 생략하면 본문에서 첫 번째로 등장하는 SVG를 우측 썸네일로 자동 사용한다
- 본문 SVG가 없을 때만 `thumbnail`을 fallback으로 사용한다

## 사람 도움 중심 원칙

- 제목은 검색형 질문 또는 실전 판단 문장으로 쓴다.
- 첫 2문단 안에 `질문에 대한 직접 답`을 넣는다.
- 각 글은 `핵심 질문 1개`만 중심축으로 잡는다.
- 입문 글은 `무엇부터 할지`, 판단 글은 `좋은 경우 vs 위험한 경우`, 파이프라인 글은 `어떤 레이어를 어떤 순서로 붙이는지`가 바로 보여야 한다.
- 본문 안의 문맥형 내부 링크를 최소 3개 둔다.
- 기존 글과 이어질 때는 `선행 글`, `같이 보면 좋은 글`, `다음 단계 글` 역할이 겹치지 않게 둔다.

## AI 검색 노출 원칙

- AI 전용 문장을 쓰지 않는다. 사람이 읽어도 바로 이해되는 문장을 우선한다.
- 똑같은 템플릿을 모든 글에 복제하지 않는다. 같은 시리즈라도 각 글이 다른 질문에 답해야 한다.
- FAQ와 체크리스트는 `있는 게 기본`이 아니라 `필요할 때만 강하게` 쓴다.
- 한 문단 안에서 정의, 판단 기준, 다음 행동이 같이 드러나게 쓴다.
- SVG는 장식이 아니라 텍스트를 보강하는 `정보 자산`이어야 한다.

## 포스트 설계 규칙

- `고정 템플릿 금지`: 모든 글을 `자주 틀리는 해석 4가지 -> 10분 체크리스트 -> FAQ -> 정리`로 끝내지 않는다.
- 글마다 아래 4개 구조 중 하나를 분명히 선택한다.

### 1. 입문형

- 예: `DART에서 어디부터 눌러야 하나`
- 필요한 것:
  - 첫 클릭 순서
  - 용어 정의
  - 가장 쉬운 실전 흐름

### 2. 판단형

- 예: `좋은 재고 vs 위험한 재고`
- 필요한 것:
  - 좋은 경우 / 위험한 경우 비교
  - 판단 기준 표
  - 놓치기 쉬운 반례

### 3. 파이프라인형

- 예: `corp_code -> rcept_no -> 원문 파일`
- 필요한 것:
  - 레이어 정의
  - 실패 패턴
  - 최소 구현 예제

### 4. 비교형

- 예: `DART vs EDGAR`, `10-K vs 20-F`
- 필요한 것:
  - 같은 점 / 다른 점
  - 언제 무엇을 먼저 볼지
  - 후속 문서 연결

## 시리즈 정의

시리즈는 `주제 묶음`이 아니라 `독자 약속`이다. 이름만 보고도 무엇을 배우는지 보여야 한다.

| 시리즈 id | 사용자에게 보이는 이름 | 약속 |
| --- | --- | --- |
| `dart-foundations` | DART 첫걸음 | 초보자가 DART에서 길을 잃지 않게 만든다 |
| `edgar-reading` | EDGAR 실전 입문 | 한국 투자자도 EDGAR form 구조를 빠르게 익히게 만든다 |
| `report-reading-foundations` | 사업보고서 실전 읽기 | 사업보고서 텍스트를 실제 판단 순서로 읽게 만든다 |
| `audit-and-governance-reading` | 감사와 경고 신호 | 감사보고서, KAM, 우발부채, 소송에서 리스크를 읽게 만든다 |
| `ownership-and-governance-reading` | 대주주·보수·주주환원 | 소유와 통제, 보상 구조를 같이 읽게 만든다 |
| `fixed-cost-and-capex` | 설비투자와 고정비 | CAPEX 이후 비용 구조까지 읽게 만든다 |
| `financial-context` | 숫자 뒤 맥락 읽기 | 숫자만 보면 놓치는 해석을 잡아준다 |
| `working-capital-and-earnings-quality` | 재고·채권·이익의 질 | 성장의 질과 회수 구조를 읽게 만든다 |
| `data-automation` | 공시 데이터 파이프라인 | 공시를 실제 수집 구조로 연결하게 만든다 |
| `corporate-actions-and-financing` | 이벤트·자금조달 공시 | 희석, 자금조달, 지배력 변화를 읽게 만든다 |

새 시리즈를 만들 때는 먼저 이 문서와 `landing/src/lib/blog/posts.ts`를 같이 갱신한다.

## 운영 문서

- `BLOG_STRUCTURE.md`: 카테고리, 번호, URL, frontmatter 규칙
- `ASSET_POLICY.md`: 자산 위치, 파일명, SVG 기준
- `TOPIC_ROADMAP.md`: 다음 글 후보, 시리즈 우선순위, 리라이트 우선순위, 공식 출처
- `blog/_reference/WRITING_QUEUE.md`: 다음 작성/리라이트 배치

## 검수 규칙

- 새 글 또는 대규모 리라이트 전에는 `uv run python -X utf8 scripts/auditBlog.py`로 블로그 감사를 돌린다.
- 짧은 글, SVG 부족, XML 깨진 SVG, 내부 링크 부족, 헤딩 템플릿 반복을 같이 본다.
- 운영 문서와 실제 시리즈 라벨이 어긋나면 `posts.ts`를 기준으로 맞춘다.

## 새 글 추가 절차

1. 카테고리를 정한다.
2. 전체 포스트 번호를 하나 예약한다.
3. `카테고리/NNN-slug/index.md`를 만든다.
4. 자산은 해당 포스트 폴더의 `assets/`에 둔다.
5. frontmatter에 `category`, `series`, `seriesOrder`를 채운다.
6. 본문에서는 자산을 `./assets/파일명.svg`로 참조한다.
7. `landing` 빌드로 slug, 메타, 자산 복사를 확인한다.
