---
id: start.installUv
title: uv로 DartLab 설치와 첫 실행
kind: curated
scope: builtin
status: observed
category: start
purpose: DartLab을 처음 설치하거나 새 환경에서 실행할 때 uv로 Python부터 dartlab까지 한 번에 준비하는 최소 절차다.
whenToUse:
  - DartLab 처음 설치
  - uv로 새 가상환경에서 시작
  - 첫 실행 전 환경 점검
  - Python이 깔려있지 않은 상태에서 시작
  - dartlab[ai] 같은 옵션 의존성 추가
inputs:
  - 운영체제 (Windows · macOS · Linux)
  - 인터넷 연결
  - 설치 권한 있는 사용자 계정
outputs:
  - 작동하는 가상환경
  - import 가능한 dartlab 패키지
  - 자동 다운로드된 첫 회사 데이터
toolRefs:
  - uv
  - dartlab CLI
sourceRefs:
  - dartlab://skills/start.installUv
  - https://github.com/eddmpython/dartlab
requiredEvidence:
  - execution
  - executionRef
  - sourceRef
expectedOutputs:
  - 설치 명령
  - smoke check 결과
  - 다음 분석 skill 후보
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
    notes:
      - 웹에서는 설치 대신 Pyodide 또는 hosted runtime skill을 연결한다.
  pyodide:
    status: unsupported
    limitations:
      - uv 설치는 로컬 Python 환경 절차다.
procedure:
  - uv를 설치한다 (Windows PowerShell 또는 macOS/Linux 터미널).
  - uv init 으로 프로젝트와 가상환경을 만든다.
  - uv add dartlab 으로 패키지를 추가한다.
  - uv run python 으로 import 와 첫 회사 호출을 검증한다.
  - 분석 목적이면 다음 skill (start.dartlabSkillOs · start.quickStart) 로 넘어간다.
failureModes:
  - cmd 에서 PowerShell 전용 명령을 실행
  - 시스템 Python 으로 dartlab 을 호출 (uv run python 미사용)
  - HuggingFace 다운로드 속도 문제를 설치 실패로 오해
forbidden:
  - 검증 없이 설치 성공 단정
  - dartlab 패키지를 시스템 Python 에 직접 설치 권장
examples:
  - DartLab 처음 깔아본다
  - Windows 에 dartlab 설치
  - Mac 에서 dartlab 시작
  - dartlab[ai] 추가
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-05-06"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 무엇을 설치하나

DartLab 은 **uv** 와 **Python** 위에서 돌아간다. Python 이 없어도 괜찮다 — uv 가 자동으로 받아준다.

> **uv 가 뭔가**: Rust 로 만든 Python 패키지 관리자. pip 보다 10~100 배 빠르고 Python 버전까지 관리한다. uv 만 설치하면 별도 Python 설치는 필요 없다.

---

## 0 단계 — 터미널 열기

### Windows

`Win + R` → `powershell` 입력 → Enter. 또는 작업 표시줄 검색에 `PowerShell` 입력 → Windows PowerShell 클릭.

> Command Prompt (cmd) 가 아니라 **PowerShell** 이어야 한다. 아래 설치 명령 일부가 cmd 에서 작동하지 않는다.

### macOS

`Cmd + Space` → Spotlight 에 `Terminal` 입력 → Enter.

### Linux

대부분의 배포판에서 `Ctrl + Alt + T`.

---

## 1 단계 — uv 설치

### Windows (PowerShell)

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치 후 터미널을 **닫고 다시 열어야** `uv` 명령이 인식된다.

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치 후 터미널을 다시 열거나 `source ~/.bashrc` (또는 `~/.zshrc`) 를 실행한다.

### 설치 확인

```bash
uv --version
```

버전 번호가 찍히면 성공. `uv: command not found` 가 보이면 터미널을 다시 연다.

---

## 2 단계 — 프로젝트 만들기

```bash
uv init my-dart-analysis
cd my-dart-analysis
```

이 명령이 자동으로 처리한다:
- Python 3.12+ 감지 또는 **자동 다운로드**.
- `pyproject.toml` (프로젝트 설정) 생성.
- `.venv/` 가상환경 생성.

Python 을 따로 설치할 필요는 없다.

---

## 3 단계 — DartLab 설치

```bash
uv add dartlab
```

의존성 (Polars, rich, alive-progress) 도 같이 설치된다.

---

## 4 단계 — 설치 검증

```bash
uv run python -X utf8 -c "import dartlab; c = dartlab.Company('005930'); print(c.corpName)"
```

`삼성전자` 가 출력되면 끝.

> `uv run` 은 가상환경 안에서 실행한다. `uv run python` 을 쓰면 방금 설치한 dartlab 패키지가 보장된다. `-X utf8` 은 Windows 의 cp949 출력 깨짐을 막는다.

---

## AI 옵션 (dartlab ai)

LLM 기반 회사 분석 웹 인터페이스를 쓰려면 AI 의존성을 추가한다.

```bash
uv add "dartlab[ai]"
uv run dartlab ai
```

브라우저가 `http://localhost:8400` 에서 열린다. Ollama 설치 ([ollama.com/download](https://ollama.com/download)) 후 `ollama pull gemma3` 으로 모델을 받아두면 바로 동작한다.

---

## 데이터 흐름

DartLab 은 DART 공시 원문을 파싱한 Parquet 파일을 사용한다. 직접 다운로드할 필요 없다 — `dartlab.Company("005930")` 호출 시 없으면 **자동으로 받는다**.

### DART — 3 단계 파이프라인

```python
import dartlab

c = dartlab.Company("005930")   # 로컬 없으면 자동 다운로드
```

1. **로컬 캐시** — 이미 받았으면 즉시.
2. **HuggingFace** — [HuggingFace Datasets](https://huggingface.co/datasets/eddmpython/dartlab-data) 미리 빌드된 Parquet (빠르고 전 종목 커버).
3. **DART API** — OpenDART 직접 수집 (느리고 API 키 필요).

### 신선도 자동 감지

3 계층 모델로 로컬 데이터의 최신 여부를 확인한다:

| 계층 | 방식 | 속도 | 감지 대상 |
|---|---|---|---|
| L1 | HuggingFace ETag (HTTP HEAD) | ~0.5s | 미리 빌드 데이터 갱신 |
| L2 | 파일 나이 TTL (90 일) | 즉시 | 오래된 로컬 파일 |
| L3 | DART API `rcept_no` diff | ~1s | DART 신규 공시 |

L1 + L2 는 API 키 없이 동작. L3 는 DART API 키 필요 (`dartlab setup dart-key`).

새 공시가 감지되면 안내 메시지만 띄우고 자동 수집은 하지 않는다 (`Company` 생성 시점에는).

```python
c = dartlab.Company("005930")   # 신선도는 panel 결과의 dataAsOf 로 확인
print(result.isFresh, result.missingCount)

c = dartlab.Company("005930")
c.panel("IS")  # 첫 접근 시 필요한 데이터를 자동으로 내려받는다
```

```bash
dartlab collect --check 005930          # 단일 종목 신선도
dartlab collect --check                 # 로컬 종목 전수 (7 일)
dartlab collect --incremental 005930    # 단일 종목 증분
dartlab collect --incremental           # 신규 공시 있는 모든 종목 증분
```

### EDGAR — 실시간 가져오기

미국 종목은 SEC API 에서 처음 호출 시 가져온다.

```python
c = dartlab.Company("AAPL")   # SEC API 호출
```

SEC 의 rate limit 때문에 첫 로드가 잠깐 걸릴 수 있다. 이후는 로컬 캐시.

---

## Google Colab 으로 시도

로컬 설치 없이 바로 돌려보고 싶으면 Colab.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb)

Colab 셀에서:

```python
!pip install dartlab

import dartlab
c = dartlab.Company("005930")
c.panel("BS")
```

---

## 트러블슈팅

### `uv: command not found`

터미널을 닫고 다시 연다. 그래도 안 되면 설치 스크립트를 다시 실행.

### Windows: `irm` 명령 인식 안 됨

PowerShell 이 아니라 cmd 에 있을 가능성. `Win + R` → `powershell` → Enter.

### `ModuleNotFoundError: No module named 'dartlab'`

`python` 이 아니라 `uv run python` 을 써야 한다. 가상환경 밖의 시스템 Python 으로는 dartlab 을 못 찾는다.

### 데이터 다운로드가 느림

HuggingFace 에서 받기 때문에 네트워크 속도에 의존한다.

---

## 다음 단계

- [start.dartlabSkillOs](/skills/start.dartlabSkillOs) — Skill OS 첫 진입과 검색 절차.
- [start.quickStart](/skills/start.quickStart) — 8 분 walkthrough (Company / topics/panel / scan / ask).
- [start.useSkillsCatalog](/skills/start.useSkillsCatalog) — skills 카탈로그 사용법.
- [Skills 카탈로그 (`/skills`)](/skills) — 178 개 절차 검색.

## 요구 사양

| 패키지 | 최소 버전 | 비고 |
|---|---|---|
| Python | 3.12 | uv 가 자동 설치 |
| Polars | 1.0.0 | 자동 설치 |
| alive-progress | 3.0.0 | 진행률 바 |
| rich | 13.0.0 | 터미널 출력 |
