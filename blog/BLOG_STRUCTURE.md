# Blog Structure

이 블로그는 `카테고리 폴더 -> 포스트 폴더 -> index.md + assets/` 구조로 관리한다.

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

## 시리즈 정의

- `dart-foundations`
- `edgar-reading`
- `report-reading-foundations`
- `fixed-cost-and-capex`
- `financial-context`
- `data-automation`
- `working-capital-and-earnings-quality`
- `audit-and-governance-reading`
- `ownership-and-governance-reading`

새 시리즈를 만들 때는 먼저 이 문서에 추가한다.

## 운영 문서

- `BLOG_STRUCTURE.md`: 카테고리, 번호, URL, frontmatter 규칙
- `ASSET_POLICY.md`: 자산 위치, 파일명, SVG 기준
- `TOPIC_ROADMAP.md`: 다음 글 후보, 시리즈 우선순위, 공식 출처, 작성 준비 메모

## 새 글 추가 절차

1. 카테고리를 정한다.
2. 전체 포스트 번호를 하나 예약한다.
3. `카테고리/NNN-slug/index.md`를 만든다.
4. 자산은 해당 포스트의 `assets/`에 둔다.
5. frontmatter에 `category`, `series`, `seriesOrder`를 채운다.
6. 본문에서는 자산을 `./assets/파일명.svg`로 참조한다.
7. `landing` 빌드로 slug, 메타, 자산 복사를 확인한다.
