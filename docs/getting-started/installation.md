---
title: 설치
---

# 설치

## 패키지 설치

### pip

```bash
pip install dartlab
```

### uv (권장)

```bash
uv add dartlab
```

## 요구사항

- Python 3.12 이상
- Polars 1.0.0 이상 (자동 설치)

## 데이터

DartLab은 DART 공시 원문을 파싱한 Parquet 파일을 사용한다. [GitHub Releases](https://github.com/eddmpython/dartlab/releases/tag/data-v1)에 260개 이상의 상장 기업 데이터가 있다.

데이터를 직접 다운로드할 필요는 없다. `Company("005930")` 같은 호출 시 로컬에 파일이 없으면 자동으로 다운로드한다.

### 수동 다운로드

개별 종목:

```bash
mkdir -p data/docsData
curl -L -o data/docsData/005930.parquet \
  "https://github.com/eddmpython/dartlab/releases/download/data-v1/005930.parquet"
```

전체 일괄 다운로드:

```python
from dartlab.core import downloadAll

downloadAll()
```

## 설치 확인

```python
from dartlab import Company

samsung = Company("005930")
print(samsung.corpName)  # "삼성전자"
```
