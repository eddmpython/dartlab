---
title: API 개요
---

# API 개요

dartlab은 **종목코드 하나**로 기업의 전체 데이터에 접근하고, 분석하고, 보고서를 만든다.

## 아키텍처

```
L0 (인프라)     Company        종목코드 → 재무/공시/주석 통합
L1 (데이터)     scan/gather    시장 횡단 + 외부 데이터
L2 (분석)       analysis       14축 재무분석 + 전망 + 가치평가
                credit         독립 신용평가 (dCR 20단계)
                review         블록식 보고서 조합
L3 (AI)         ask/chat       적극적 분석가
```

## 핵심 호출 패턴

```python
import dartlab

c = dartlab.Company("005930")       # 삼성전자

# 데이터 조회
c.show("BS")                        # 재무상태표
c.select("IS", ["매출액", "영업이익"])  # 특정 계정 추출

# 재무분석
c.analysis("financial", "수익성")     # 14축 중 수익성 분석

# 신용평가
c.credit()                          # dCR 등급 종합
c.credit("채무상환")                  # 축별 접근

# 보고서
c.review("수익성")                   # 보고서 렌더링

# 시장 횡단
dartlab.scan("governance")           # 전종목 지배구조

# AI 분석
dartlab.ask("삼성전자 재무 분석해줘")   # AI 분석가
```

## 엔진별 가이드

| 엔진 | 진입점 | 용도 | 상세 |
|------|--------|------|------|
| [Company](company) | `Company("005930")` | 데이터 조회 | show/select/sections/notes |
| [Financial Data](finance) | `c.BS`, `c.ratios` | 재무제표 + 비율 | BS/IS/CF/ratios/timeseries |
| [Analysis](analysis) | `c.analysis()` | 14축 재무분석 | 수익성/성장성/안정성 등 |
| [Credit](credit) | `c.credit()` | 독립 신용평가 | dCR 20단계 + 7축 |
| [Scan](scan) | `dartlab.scan()` | 시장 횡단분석 | 전종목 비교 15축 |
| [Gather](gather) | `c.gather()` | 외부 시장 데이터 | 주가/수급/매크로/뉴스 |
| [Review](review) | `c.review()` | 보고서 렌더링 | 마크다운/HTML/JSON |
| [AI](ai) | `dartlab.ask()` | AI 분석가 | 6개 provider |
| [Advanced](advanced) | `c.insights` 등 | 등급/순위/섹터 | insight/rank/sector |
| [MCP](mcp) | `dartlab mcp` | AI 연동 | Claude/Cursor 등 |

## Python API 목록

```python
# 핵심 함수
dartlab.Company("005930")           # 기업 객체 생성
dartlab.ask("질문")                  # AI 분석
dartlab.chat("005930", "질문")       # 종목 바인딩 AI
dartlab.scan("축")                   # 시장 횡단분석
dartlab.analysis("그룹", "축")       # 재무분석
dartlab.gather("축", "005930")       # 외부 데이터
dartlab.credit("005930")            # 신용평가
dartlab.quant("005930")             # 기술적 분석
dartlab.search("유상증자")           # 공시 검색
dartlab.listing()                   # 상장사 목록

# 유틸리티
dartlab.codeToName("005930")        # → "삼성전자"
dartlab.nameToCode("삼성전자")       # → "005930"
dartlab.searchName("삼성")           # 종목 검색
dartlab.capabilities()              # 기능 카탈로그
```

## DART + EDGAR 동일 인터페이스

```python
kr = dartlab.Company("005930")      # 한국 DART
us = dartlab.Company("AAPL")        # 미국 EDGAR

# 동일한 메서드
kr.BS                               # K-IFRS 재무상태표
us.BS                               # US-GAAP Balance Sheet

kr.analysis("financial", "수익성")    # 한국어 계정
us.analysis("financial", "수익성")    # 자동 번역
```
