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

## 데이터 준비

DartLab은 DART 공시 원문을 파싱한 Parquet 파일을 사용한다.
샘플 데이터는 [GitHub Releases](https://github.com/eddmpython/dartlab/releases/tag/data-v1)에서 다운로드할 수 있다.

```bash
mkdir -p data/docsData

# 삼성전자 공시 데이터
curl -L -o data/docsData/005930.parquet \
  "https://github.com/eddmpython/dartlab/releases/download/data-v1/005930.parquet"
```

## 설치 확인

```python
import dartlab
print("DartLab 설치 완료")
```
