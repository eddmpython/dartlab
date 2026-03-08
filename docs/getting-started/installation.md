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

---

## 요구사항

- Python 3.12 이상
- Polars 1.0.0 이상 (자동 설치)
- alive-progress 3.0.0 이상 (자동 설치, 진행 표시용)
- rich 13.0.0 이상 (자동 설치, 터미널 출력용)

---

## 데이터

DartLab은 DART 공시 원문을 파싱한 Parquet 파일을 사용한다. [GitHub Releases](https://github.com/eddmpython/dartlab/releases/tag/data-docs)에 260개 이상의 상장 기업 데이터가 있다.

데이터를 직접 다운로드할 필요는 없다. `Company("005930")` 처럼 호출하면 로컬에 파일이 없을 때 **자동으로 다운로드**한다.

### 자동 다운로드 동작

```python
from dartlab import Company

c = Company("005930")   # 로컬에 없으면 자동 다운로드
```

1. 로컬 `data/docsData/` 디렉토리에서 파일 확인
2. 없으면 GitHub Releases에서 해당 종목 Parquet 다운로드
3. 다운로드 후 자동으로 로드

### 수동 다운로드

개별 종목 하나만 받을 때:

```bash
mkdir -p data/docsData
curl -L -o data/docsData/005930.parquet \
  "https://github.com/eddmpython/dartlab/releases/download/data-docs/005930.parquet"
```

전체 일괄 다운로드 (260+ 종목):

```python
from dartlab.core import downloadAll

downloadAll()
```

---

## 설치 확인

```python
from dartlab import Company

c = Company("005930")
print(c.corpName)   # "삼성전자"
print(c.BS)         # 재무상태표 DataFrame
```

Company를 생성하면 아바타와 함께 기업 정보가 터미널에 표시된다. `dartlab.verbose = False`로 끌 수 있다.

```python
import dartlab

dartlab.verbose = False
c = Company("005930")   # 조용히 생성
```

---

## 다음 단계

- [빠른 시작](./quickstart) — 전체 기능 둘러보기
- [API Overview](../api/overview) — property 전체 목록
