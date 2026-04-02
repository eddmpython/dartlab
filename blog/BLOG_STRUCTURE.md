# Blog Structure

`카테고리 폴더 → 번호-slug 폴더 → index.md + assets/` 구조.

## 컨셉

**공시 원문을 직접 읽고 판단하는 실전 교재**

- 각 글은 독자가 "아, 이걸 이렇게 봐야 하는구나" 하는 순간이 있어야 함
- dartlab 없이도 가치 있는 글이어야 함
- 템플릿 복사가 아니라 각 주제에 맞는 고유한 구조

## 카테고리

- `01-reading-disclosures`: 공시 읽기 — DART, EDGAR, 사업보고서, 감사, 재무제표, 지배구조, 파이프라인
- `02-dartlab-news`: DartLab 소식 (사용자 직접 관리)
- `03-corporate-analysis`: 실전기업분석 (사용자 직접 관리)

## 번호 체계

- **카테고리별 순번**: 각 카테고리 내에서 01부터 시작
- URL에는 번호가 노출되지 않음 (slug 기반: `/blog/audit-report-and-kam`)
- 번호는 순수하게 파일 정렬용

```text
blog/
  01-reading-disclosures/
    07-audit-report-and-kam/
      index.md
      assets/
```

## Frontmatter

```yaml
title: 글 제목
date: YYYY-MM-DD
description: 1문장 설명
category: reading-disclosures | dartlab-news | corporate-analysis
series: 시리즈 id
seriesOrder: 숫자
thumbnail: /avatar-*.png
```

## 시리즈

| 시리즈 id | 라벨 | 약속 |
| --- | --- | --- |
| `dart-foundations` | DART 첫걸음 | DART에서 길을 잃지 않게 |
| `edgar-reading` | EDGAR 실전 입문 | EDGAR form과 Risk Factors를 빠르게 |
| `report-reading-foundations` | 사업보고서 실전 읽기 | 텍스트를 판단 순서로 |
| `audit-and-governance` | 감사와 경고 신호 | 감사보고서에서 리스크를 |
| `ownership-and-governance` | 대주주·보수·주주환원 | 소유와 통제를 같이 |
| `industry-reading` | 업종별 공시 읽기 | 업종별 체크포인트 |
| `global-comparison` | 한미 공시 비교 | DART vs EDGAR 나란히 |
| `financial-context` | 숫자 뒤 맥락 읽기 | 숫자만 보면 놓치는 해석 |
| `capital-and-earnings` | 자본·이익의 질 | CAPEX, 운전자본, 현금흐름 |
| `data-pipeline` | 공시 데이터 파이프라인 | 수집 구조 설계 |
| `corporate-analysis` | 실전기업분석 | 기업 전체 분석 프레임워크 |
| `dartlab-news` | DartLab 소식 | 설치, 기능, 업데이트 |

## 글 작성 원칙

- 제목은 검색형 질문 또는 실전 판단 문장
- 첫 2문단에 질문에 대한 직접 답
- 각 글은 핵심 질문 1개만 중심축
- 고정 템플릿 금지 — 글마다 주제에 맞는 고유한 H2 구조
- SVG는 장식이 아니라 정보 자산
- 본문 내부 링크 최소 3개

## 검수

- `posts.ts`가 단일 진실의 원천
- 운영 문서와 실제 시리즈가 어긋나면 `posts.ts` 기준으로 맞춤
