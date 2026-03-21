# startMarimo

`startMarimo` 는 `dartlab.Company`의 현재 공개 흐름을 바로 확인하는 marimo 예제 폴더다.

현재 예제:

- **dartCompany.py** — DART (한국 상장기업)
- **edgarCompany.py** — EDGAR (미국 상장기업)
- **aiAnalysis.py** — AI 기업 분석 (LLM 기반 대화형)

### dartCompany.py

- `dartlab.Company("005930")` 로 삼성전자 생성
- `c.sections` 로 전체 topic × period 맵 확인
- `c.topics` 로 topic 목록 확인
- `c.show("companyOverview")` 로 topic 블록 목차 확인
- `c.show("IS")` 로 재무 시계열 확인
- `c.trace("stockTotal")` 로 데이터 소스 추적
- `c.diff()` 로 텍스트 변화 감지

### edgarCompany.py

- `dartlab.Company("AAPL")` 로 Apple 생성
- `c.sections` 로 전체 topic × period 맵 확인
- `c.show("riskFactors")` 로 docs topic 확인
- `c.show("IS")` 로 재무 시계열 확인
- `c.ratios` 로 재무비율 확인
- `c.filings()` 로 보고서 목록 확인
- `c.trace("riskFactors")` 로 데이터 소스 추적

### aiAnalysis.py

- `ask(company, question)` — AI에게 기업 분석 질문
- Provider 선택: `provider="ollama"`, `provider="openai"`
- 스트리밍: `stream=True` — 실시간 출력
- 데이터 필터: `include=["BS", "IS"]`, `exclude=["dividend"]`
- **사전 조건**: `dartlab setup` 으로 provider 설정 필요

## 실행

marimo가 아직 없으면:

```bash
uv add marimo
```

예제 열기:

```bash
uv run marimo edit startMarimo/dartCompany.py
uv run marimo edit startMarimo/edgarCompany.py
uv run marimo edit startMarimo/aiAnalysis.py
```

원하면 새 예제 파일을 같은 폴더에 추가해서 같은 방식으로 열면 된다.
