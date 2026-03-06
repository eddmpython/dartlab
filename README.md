<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="120">

<h1>DartLab</h1>
<p><em>Read Beyond the Numbers</em></p>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=f59e0b&labelColor=0c0a09&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&labelColor=0c0a09&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-a8a29e?style=for-the-badge&labelColor=0c0a09" alt="License"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/">문서</a> ·
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-v1">샘플 데이터</a> ·
<a href="https://buymeacoffee.com/eddmpython">Buy Me a Coffee</a>
</p>

</div>

---

## 이건 뭔가

DART 공시에는 재무제표 숫자만 있는 게 아니다.
사업의 내용, 위험 요인, 감사의견, 소송 현황, 지배구조 변동 — 이런 텍스트 정보가 대부분이다.

기존 도구들은 숫자만 뽑아간다. **DartLab은 숫자와 텍스트 모두 다룬다.**

## 설치

```bash
pip install dartlab
```

```bash
uv add dartlab
```

의존성: Polars 하나.

## 빠른 시작

### 데이터 다운로드

[GitHub Releases](https://github.com/eddmpython/dartlab/releases/tag/data-v1)에서 종목별 Parquet 파일을 받는다.

```bash
mkdir -p data/docsData
curl -L -o data/docsData/005930.parquet \
  "https://github.com/eddmpython/dartlab/releases/download/data-v1/005930.parquet"
```

### 요약 재무정보 시계열

```python
from dartlab.finance.summary import analyze

result = analyze("data/docsData/005930.parquet")

result.FS    # 전체 재무제표 (Polars DataFrame)
result.BS    # 재무상태표
result.IS    # 손익계산서
```

누적 재무제표에서 개별 분기 실적을 역산하고, 계정명이 바뀌어도 시계열을 연결한다 (Bridge Matching).

## 공시 수평 정렬

DART 공시는 보고서 유형별로 잘려 있다:

```
         Q1        Q2        Q3        Q4
1분기    ████░░░░░░░░░░░░░░░░░░░░░░░░░░
반기     ████████████░░░░░░░░░░░░░░░░░░
3분기    ██████████████████████░░░░░░░░░
사업     ████████████████████████████████
```

이 조각들을 시계열로 정렬해서 하나의 연속된 흐름으로 만든다.
숫자도, 텍스트도 — 같은 시간축 위에 놓는다.

## 로드맵

- [x] 요약재무정보 시계열 추출 (Bridge Matching)
- [ ] 재무제표 본문 상세 파싱
- [ ] 텍스트 섹션 시계열 정렬 및 diff
- [ ] 정량 + 정성 교차 검증
- [ ] 시각화

## 지원

<a href="https://buymeacoffee.com/eddmpython">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180"/>
</a>

## 라이선스

MIT License
