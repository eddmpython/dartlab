"""HuggingFace 데이터셋 README 업로드."""

from huggingface_hub import HfApi

token = None
for line in open(".env", encoding="utf-8"):
    line = line.strip()
    if line.startswith("HF_TOKEN="):
        token = line.split("=", 1)[1].strip()
        break

README = r"""---
license: cc-by-4.0
task_categories:
  - table-question-answering
  - text-classification
language:
  - ko
  - en
tags:
  - finance
  - disclosure
  - dart
  - edgar
  - sec
  - xbrl
  - korea
  - financial-statements
  - corporate-filings
  - stock-prices
  - macroeconomics
  - 전자공시
  - 재무제표
  - 사업보고서
  - 한국
pretty_name: DartLab 전자공시 데이터
size_categories:
  - 1M<n<10M
---

<div align="center">

<br>

<img alt="DartLab" src="https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/assets/logo.png" width="160">

<h3>DartLab 데이터</h3>

<p><b>종목코드 하나로 읽는 한국 DART + 미국 SEC EDGAR 공시 데이터</b></p>
<p><sub>Structured Korean (DART) and US (SEC EDGAR) disclosure data, ready as Parquet.</sub></p>

<p>
<a href="https://eddmpython.github.io/dartlab/terminal"><img src="https://img.shields.io/badge/터미널-바로_써보기-ea4647?style=for-the-badge&labelColor=050811" alt="터미널"></a>
<a href="https://eddmpython.github.io/dartlab/data"><img src="https://img.shields.io/badge/데이터_센터-CSV·엑셀_받기-38bdf8?style=for-the-badge&labelColor=050811" alt="데이터 센터"></a>
<a href="https://github.com/eddmpython/dartlab"><img src="https://img.shields.io/badge/GitHub-dartlab-ea4647?style=for-the-badge&labelColor=050811&logo=github&logoColor=white" alt="GitHub"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://buymeacoffee.com/eddmpython"><img src="https://img.shields.io/badge/후원-Buy_Me_A_Coffee-ffdd00?style=for-the-badge&labelColor=050811&logo=buy-me-a-coffee&logoColor=white" alt="후원"></a>
</p>

</div>

## 무엇인가요?

<img align="right" src="https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/assets/avatar-study.png" width="120">

[DartLab](https://github.com/eddmpython/dartlab)이 한국 DART 전자공시와 미국 SEC EDGAR 공시를 **종목코드 하나로 비교 가능한 표**로 가공해 [Parquet](https://parquet.apache.org/)으로 올려둔 데이터셋입니다.

한국 전 상장사(약 2,700사)와 미국 주요 상장사(약 1,000사)의 재무제표, 사업보고서 본문, 정형 공시, 주가, 거시지표가 들어 있습니다.

이 데이터셋은 DartLab의 **데이터 층**입니다. `dartlab.Company("005930")`을 호출하면 라이브러리가 필요한 parquet을 여기서 자동으로 내려받습니다. 숫자는 원문 그대로 보존합니다(반올림·추정·보간 없음).

## 코드 없이도 바로 씁니다

<img align="right" src="https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/assets/avatar-analyze.png" width="120">

Python을 몰라도 됩니다. 웹에서 데이터를 고르고 미리본 다음, **CSV·엑셀(.xlsx)로 바로 받거나** 구글시트·Python·curl이 읽는 **라이브 API**로 가져갈 수 있습니다.

| 입구 | 무엇을 하나 | 링크 |
|---|---|---|
| **데이터 센터** | DART·EDGAR·시세·거시 데이터를 골라 미리보기 → CSV·엑셀 다운로드 → 구글시트·Python·curl 라이브 API | [열기](https://eddmpython.github.io/dartlab/data) |
| **터미널** | 종목 하나로 재무·주가·공시·신용·산업·매크로를 한 화면에서. 헤더 「데이터」에서 회사 데이터 일괄 CSV·엑셀 묶음 다운로드 | [열기](https://eddmpython.github.io/dartlab/terminal) |
| **공시 뷰어** | 사업보고서 본문을 항목 × 기간 격자로 | [열기](https://eddmpython.github.io/dartlab/viewer) |

> 데이터 센터에서는 종목·항목을 고른 뒤 컬럼 선택, 최근/처음 N행, 일·주·월·분기·연 주기 다운샘플까지 골라 받을 수 있습니다. 구글시트 한 칸에 `=IMPORTDATA(...)` 한 줄이면 약 1시간마다 자동으로 갱신됩니다.

## 데이터 구조

각 파일은 회사 1곳입니다: `{종목코드}.parquet` (시세·거시 등 일부는 날짜·시리즈 단위).

```
dart/        한국 DART 공시
├── panel/       공시 수평화 (회사당 17-col, 본문 + XBRL 한 표)
├── finance/     재무제표 (K-IFRS XBRL: BS·IS·CF)
├── report/      정형 공시 (28종 API: 배당·임원·지분 등)
└── scan/        전 상장사 횡단 프리빌드 (비율·이익의 질·공시 변경 등)

edgar/       미국 SEC EDGAR
├── panel/       공시 수평화 (회사당 16-col, cross-market)
├── financeStmt/ 재무제표 (DART finance 와 동형 표준화)
├── prices/      회사별 일별 OHLCV
└── tickers/     ticker↔CIK 맵

gov/ · krx/  시세·지수 (공공데이터·KRX)
├── prices/company/   회사별 일별 OHLCV + 시가총액
├── prices/date/      일별 전종목 (날짜 샤딩)
└── indices/          KOSPI·KOSDAQ 등 지수 일별

macro/       거시경제 시계열
├── fred/        미국 FRED (금리·물가 등)
├── ecos/        한국은행 ECOS
└── customs/     관세청 월별 수출입

research/
└── brokerage/   증권사 리서치 메타 인덱스 (제목·링크·발간일, 본문 없음)
```

### dart/panel · 공시 수평화

DART 정기보고서를 회사 단위 패널로 수평화합니다. 서술 본문과 XBRL 연결 표가 한 artifact 에 함께 들어가, 뷰어·검색·비교가 같은 출처를 씁니다.

| 컬럼 | 설명 |
|--------|------------|
| `corp` | 종목코드 |
| `period` | 기간 키 (`YYYYQn`) |
| `rceptNo` | DART 접수번호 |
| `chapter` | 보고서 최상위 장 |
| `sectionLeaf` | 원본 섹션 제목 |
| `sectionPath` | 전체 섹션 경로 |
| `leafType` | `text` / `table` |
| `blockLeaf` | 블록·표 제목 |
| `xbrlClass` | DART XBRL 클래스 |
| `disclosureKey` | 수평화 표준 키 |
| `contentRaw` | 원본 보존 XML/텍스트 |

### dart/finance · 재무제표

DART OpenAPI(`fnlttSinglAcntAll`) 기반 XBRL 재무 데이터.

| 컬럼 | 설명 |
|--------|------------|
| `bsns_year` | 사업연도 |
| `reprt_code` | 보고서 분기 코드 |
| `stock_code` | 종목코드 |
| `corp_name` | 회사명 |
| `fs_div` | `CFS`(연결) / `OFS`(별도) |
| `sj_div` | 재무제표 구분 (BS/IS/CF/SCE) |
| `account_id` | XBRL 계정 ID |
| `account_nm` | 계정명(한글) |
| `thstrm_amount` | 당기 금액 |
| `frmtrm_amount` | 전기 금액 |
| `bfefrmtrm_amount` | 전전기 금액 |

### dart/report · 정형 공시

지배구조, 보수, 지분, 배당 등을 다루는 DART API 28종.

| 컬럼 | 설명 |
|--------|------------|
| `apiType` | API 분류 (예: `dividend`, `employee`, `executive`) |
| `year` | 연도 |
| `quarter` | 분기 |
| `stockCode` | 종목코드 |
| `corpCode` | DART 고유번호 |
| *(가변)* | 분류별 컬럼 |

**28종 API:** dividend, employee, executive, majorHolder, treasuryStock, capitalChange, auditOpinion, stockTotal, outsideDirector, corporateBond 등.

### 그 외 데이터

| 경로 | 내용 |
|---|---|
| `edgar/panel` | 미국 공시 본문 수평화 (회사당, cross-market 16-col) |
| `edgar/financeStmt` | 미국 재무제표 (DART finance 와 동형 표준화) |
| `edgar/prices/company` | 미국 회사별 일별 OHLCV |
| `gov/prices/company` | 한국 회사별 일별 OHLCV + 시가총액 |
| `gov/indices/index` | KOSPI·KOSDAQ 등 지수별 일별 시계열 |
| `macro/fred` · `macro/ecos` · `macro/customs` | 미국·한국·무역 거시 시계열 |
| `research/brokerage` | 증권사 리서치 링크 인덱스 (월별, 본문 없음) |

## Python 으로 쓰기

라이브러리가 필요한 parquet 을 자동으로 내려받고 로컬에 캐시합니다. API 키가 필요 없습니다.

```python
import dartlab

c = dartlab.Company("005930")   # 삼성전자, HF 에서 자동 다운로드
c.panel()                       # 공시 항목 × 기간 전체 격자
c.panel("IS")                   # 손익계산서 (finance 정규화 숫자)
c.panel("사업")                  # 사업 개요 등 공시 본문 행 검색
```

## parquet 을 직접 읽기

종목코드별 parquet URL 을 어떤 도구로든 바로 읽을 수 있습니다.

```python
import polars as pl
url = "https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/dart/finance/005930.parquet"
df = pl.read_parquet(url)
```

```python
import duckdb
duckdb.sql(f"SELECT * FROM read_parquet('{url}')")
```

> **엑셀 365**: 데이터 → 데이터 가져오기 → 파일에서 → Parquet 에서 → 위 URL. 또는 [데이터 센터](https://eddmpython.github.io/dartlab/data)에서 CSV·엑셀로 바로 받기.

## 데이터 출처

<img align="right" src="https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/assets/avatar-discover.png" width="120">

- **DART** (한국): [dart.fss.or.kr](https://dart.fss.or.kr) · 금융감독원 전자공시시스템
- **EDGAR** (미국): [sec.gov/edgar](https://www.sec.gov/edgar) · SEC 전자공시 시스템
- **시세·지수**: 공공데이터포털·KRX
- **거시**: 미국 FRED, 한국은행 ECOS, 관세청

모두 공개된 정부·공공 공시 시스템에서 가져온 데이터입니다. 재무 수치는 원문 그대로 보존합니다(반올림·추정·보간 없음). 뉴스 본문은 언론사 저작권 때문에 데이터셋에 포함하지 않습니다.

## 갱신 주기

GitHub Actions 로 매일 자동 갱신됩니다. 최근 공시를 증분으로 확인·수집합니다.

## 라이선스

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). 자유롭게 쓰고 재배포하되, 출처(dartlab)만 남겨주세요. 데이터는 공개 정부·공공 공시를 구조화한 편집물이라 데이터 계열 라이선스인 CC BY 4.0 을 씁니다. 라이브러리 코드는 [Apache 2.0](https://github.com/eddmpython/dartlab) 입니다.

## 더 보기

<div align="center">

<a href="https://www.youtube.com/shorts/97lYLWMWzvA"><img src="https://img.youtube.com/vi/97lYLWMWzvA/maxresdefault.jpg" alt="DartLab 30초 데모" width="320"></a>

<sub>▶ <a href="https://www.youtube.com/shorts/97lYLWMWzvA">DartLab 30초 데모</a></sub>

</div>

- **GitHub** · [github.com/eddmpython/dartlab](https://github.com/eddmpython/dartlab)
- **시작하기** · [DartLab 쉽게 시작하기](https://eddmpython.github.io/dartlab/blog/dartlab-easy-start)
- **문서** · [eddmpython.github.io/dartlab](https://eddmpython.github.io/dartlab/)
- **블로그** · [한국 공시 분석 글 120+편](https://eddmpython.github.io/dartlab/blog/)
- **YouTube** · [@eddmpython](https://www.youtube.com/@eddmpython)

## 후원

DartLab 이 도움이 되셨다면 프로젝트를 후원해주세요.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-후원-ffdd00?style=for-the-badge&labelColor=050811&logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/eddmpython)

- [GitHub Issues](https://github.com/eddmpython/dartlab/issues) · 버그 신고, 기능 제안
"""

api = HfApi(token=token)
api.upload_file(
    repo_id="eddmpython/dartlab-data",
    repo_type="dataset",
    path_or_fileobj=README.encode("utf-8"),
    path_in_repo="README.md",
    commit_message="데이터셋 라이선스 CC BY 4.0 로 전환 (공시 편집물은 CC 계열이 정본, 라이브러리 코드는 Apache 2.0 유지) + 출처 표기 안내",
)
print("README.md 업로드 완료")
