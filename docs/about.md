---
title: About DartLab
description: DartLab이 무엇을 만드는 프로젝트인지, 어떤 데이터를 다루는지, 누가 운영하는지 정리한 소개 페이지.
---

# About DartLab

DartLab은 한국 금융감독원 DART 전자공시와 미국 SEC EDGAR 데이터를 구조적으로 읽기 위해 만든 오픈소스 프로젝트다. 목표는 단순 조회가 아니라, 재무 숫자와 공시 문서를 같은 데이터 흐름으로 묶어 반복 가능한 분석 기반을 만드는 것이다.

## 무엇을 만드는가

DartLab은 아래 세 층을 함께 다룬다.

- 재무제표와 비율 같은 정량 데이터
- 사업보고서, 감사보고서, MD&A, 주석 같은 정성 데이터
- 위 데이터를 코드에서 바로 재사용할 수 있게 하는 표준화 레이어

즉 "공시를 읽는 법"과 "공시를 데이터로 쓰는 법"을 한 프로젝트 안에서 연결하는 것이 핵심이다.

## 왜 만들었나

DART와 EDGAR에는 좋은 정보가 많지만, 대부분은 사람이 직접 사이트를 열어 문서별로 따라가야 한다. 투자자, 연구자, 개발자는 같은 작업을 반복하게 된다.

DartLab은 이 비효율을 줄이기 위해 시작됐다.

- 문서형 공시를 topic 단위로 구조화한다.
- XBRL 재무 데이터를 시계열로 정리한다.
- 공시 텍스트와 숫자를 같은 회사 객체 안에서 다룬다.
- 블로그와 문서로 해석 방법까지 공개한다.

## 어떤 데이터를 다루나

주요 데이터 축은 다음과 같다.

- DART 공시 문서 원문
- OpenDART API와 XBRL 재무제표
- DART 정기보고서 정형 데이터
- SEC EDGAR filing 원문과 XBRL 데이터

여기서 중요한 원칙은 source-aware structure다. 숫자는 더 강한 source를 우선하고, 서술형 정보는 원문 문맥을 유지하는 쪽을 우선한다.

## 누가 운영하나

프로젝트 작성자와 운영자는 `eddmpython`이다. GitHub, PyPI, YouTube, Threads, 블로그를 통해 관련 도구와 글을 계속 공개하고 있다.

- GitHub: https://github.com/eddmpython
- PyPI: https://pypi.org/user/eddmpython/
- YouTube: https://www.youtube.com/@eddmpython
- Threads: https://www.threads.net/@eddmpython
- Blog: https://eddm.tistory.com

## 이 사이트를 어떻게 읽는 것이 좋은가

처음 들어왔다면 아래 순서가 가장 효율적이다.

1. 설치 문서
2. Quickstart
3. API Overview
4. 블로그의 기초 글

문서는 사용법과 구조를 설명하고, 블로그는 공시를 실제로 읽는 해석 프레임을 다룬다. 둘을 같이 보는 편이 더 빠르다.

## 인용과 출처

DartLab 사이트의 문서와 블로그는 가능한 한 공식 출처를 함께 남긴다. DART, OpenDART, SEC, IFRS 같은 1차 출처를 우선하고, 해석과 구현은 별도로 구분한다.

프로젝트를 인용할 때는 다음 페이지가 출발점으로 적절하다.

- 문서: `/docs/api/overview`
- 설치: `/docs/getting-started/installation`
- 블로그 허브: `/blog/`
- GitHub 저장소: `https://github.com/eddmpython/dartlab`

## FAQ

### DartLab은 어떤 문제를 해결하나

전자공시 데이터를 사람이 읽기만 하는 상태에서, 코드와 파이프라인에서 재사용할 수 있는 구조로 바꾸는 문제를 해결한다.

### DartLab은 누구를 위한 프로젝트인가

투자자, 퀀트 연구자, 데이터 엔지니어, 회계/공시 자동화 작업을 하는 개발자에게 가장 직접적으로 유용하다.

### 이 사이트에서 가장 먼저 읽을 페이지는 어디인가

대부분의 사용자는 설치 문서와 Quickstart부터 시작하는 것이 가장 효율적이다. 해석 관점이 필요하면 블로그 기초 글을 같이 보면 된다.

### 데이터 출처는 무엇인가

핵심 출처는 금융감독원 DART, OpenDART, SEC EDGAR, XBRL 원문, 정기보고서 API 데이터다.

### DartLab을 인용할 때 무엇을 참고하면 되나

문서의 canonical URL, 블로그 글의 canonical URL, GitHub 저장소 URL을 우선 참고하면 된다. 구현 논점은 GitHub, 해석 논점은 블로그/문서가 더 적절하다.
