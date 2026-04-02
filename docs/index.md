---
title: DartLab
---

# DartLab

종목코드 하나로 기업의 전체 이야기를 본다.

```python
import dartlab

c = dartlab.Company("005930")           # 삼성전자

c.show("BS")                            # 재무상태표
c.analysis("financial", "수익성")         # 14축 재무분석
c.credit()                              # dCR 신용평가
dartlab.scan("governance")               # 전종목 지배구조
dartlab.ask("삼성전자 분석해줘")           # AI 분석가
```

## 엔진 체계

| 엔진 | 진입점 | 역할 |
|------|--------|------|
| [Company](api/company) | `Company("005930")` | 데이터 조회 (show/select/sections) |
| [Financial Data](api/finance) | `c.BS`, `c.ratios` | 재무제표 + 비율 |
| [Analysis](api/analysis) | `c.analysis()` | 14축 재무분석 + 6막 서사 |
| [Credit](api/credit) | `c.credit()` | 독립 신용평가 (dCR 20단계) |
| [Scan](api/scan) | `dartlab.scan()` | 전종목 횡단분석 |
| [Gather](api/gather) | `c.gather()` | 외부 시장 데이터 |
| [Review](api/review) | `c.review()` | 보고서 렌더링 |
| [AI](api/ai) | `dartlab.ask()` | 적극적 분석가 |

## 시작하기

- [설치](getting-started/installation)
- [빠른 시작](getting-started/quickstart)
- [API 개요](api/overview)

## 신용평가 보고서

dartlab 독립 신용평가(dCR) 보고서가 정기 발간된다.

- [Samsung Electronics — dCR-AA](credit/reports/005930)
- [SK hynix — dCR-AA+](credit/reports/000660)
- [NAVER — dCR-AA](credit/reports/035420)
- [LG — dCR-AA](credit/reports/003550)

## 참고

- [안정성 정책](stability)
- [변경 이력](changelog)
- [CAPABILITIES.md](https://github.com/eddmpython/dartlab/blob/master/CAPABILITIES.md) — 전체 API 레퍼런스
