---
title: 설치
---

# 설치

DartLab을 사용하려면 **uv**와 **Python**이 필요하다. Python을 설치한 적 없어도 괜찮다 — uv가 알아서 설치한다.

> **uv란?** Rust로 만든 Python 패키지 매니저다. pip보다 10~100배 빠르고, Python 버전 관리까지 한 번에 해결한다. Python이 없어도 uv만 설치하면 된다.

---

## 0단계: 터미널 열기

터미널은 컴퓨터에 텍스트로 명령어를 입력하는 프로그램이다. 마우스로 클릭하는 대신, 글자를 타이핑해서 프로그램을 설치하거나 실행한다.

### Windows

**방법 1** — 키보드에서 `Win + R` 키를 동시에 누른다. 작은 창이 뜨면 `powershell` 이라고 입력하고 Enter를 누른다.

**방법 2** — 화면 아래 작업표시줄의 검색창에 `PowerShell`을 검색한다. **Windows PowerShell**을 클릭한다.

파란색(또는 검은색) 창이 뜨면 성공이다. 여기에 명령어를 입력한다.

> **주의**: `명령 프롬프트(cmd)`가 아니라 반드시 **PowerShell**을 열어야 한다. cmd에서는 설치 명령어가 작동하지 않는다.

### macOS

**방법 1** — `Cmd + Space`를 눌러 Spotlight 검색을 연다. `터미널` 또는 `Terminal`을 입력하고 Enter.

**방법 2** — Finder → 응용 프로그램 → 유틸리티 → 터미널.

### Linux

`Ctrl + Alt + T`를 누르면 대부분의 배포판에서 터미널이 열린다.

---

## 1단계: uv 설치

터미널이 열렸으면 아래 명령어를 **복사해서 붙여넣고** Enter를 누른다.

### Windows (PowerShell)

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치가 끝나면 터미널을 **닫았다가 다시 열어야** `uv` 명령어가 인식된다.

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치 후 터미널을 다시 열거나 `source ~/.bashrc` (또는 `~/.zshrc`)를 실행한다.

### 설치 확인

```bash
uv --version
```

버전 번호가 출력되면 성공이다. `uv: command not found` 가 나오면 터미널을 다시 열어본다.

---

## 2단계: 프로젝트 만들기

DartLab을 사용할 폴더를 만들고, uv로 Python 프로젝트를 초기화한다.

```bash
uv init my-dart-analysis
cd my-dart-analysis
```

이 명령어를 실행하면 uv가 자동으로:
- Python 3.12 이상을 감지하거나 **자동 다운로드**
- `pyproject.toml` 생성 (프로젝트 설정 파일)
- `.venv/` 가상환경 생성

**Python을 직접 설치할 필요 없다.** uv가 알아서 적절한 버전을 다운로드한다.

---

## 3단계: DartLab 설치

```bash
uv add dartlab
```

끝이다. 의존 패키지(Polars, rich, alive-progress)도 자동으로 같이 설치된다.

---

## 4단계: 설치 확인

```bash
uv run python -c "from dartlab import Company; c = Company('005930'); print(c.corpName)"
```

`삼성전자`가 출력되면 설치 완료다.

> `uv run`은 가상환경 안에서 실행한다는 뜻이다. `uv run python`으로 Python을 실행하면 방금 설치한 dartlab이 자동으로 잡힌다.

---

## AI 기업분석 (dartlab ai)

LLM과 대화하며 기업을 분석하는 웹 인터페이스를 사용하려면 AI 의존성을 함께 설치한다.

```bash
uv add dartlab[ai]
uv run dartlab ai
```

브라우저에서 `http://localhost:8400` 이 열린다. Ollama가 필요하다 — [ollama.com](https://ollama.com/download)에서 설치 후 `ollama pull gemma3`으로 모델을 받으면 된다.

---

## 요구사항

| 패키지 | 최소 버전 | 비고 |
|--------|----------|------|
| Python | 3.12 | uv가 자동 설치 |
| Polars | 1.0.0 | 자동 설치 |
| alive-progress | 3.0.0 | 진행 표시 |
| rich | 13.0.0 | 터미널 출력 |

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

## Google Colab에서 사용하기

설치 없이 바로 사용하고 싶다면 Colab에서 실행할 수 있다.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb)

Colab 셀에서:

```python
!pip install dartlab

from dartlab import Company
c = Company("005930")
c.BS
```

---

## 문제 해결

### `uv: command not found`

터미널을 닫았다가 다시 열어본다. 그래도 안 되면 설치 스크립트를 다시 실행한다.

### Windows에서 `irm` 명령어가 안 되는 경우

CMD(명령 프롬프트)가 아니라 **PowerShell**에서 실행해야 한다. `Win + R` → `powershell` 입력 → Enter.

### `ModuleNotFoundError: No module named 'dartlab'`

`uv run python`으로 실행하고 있는지 확인한다. `python` 대신 `uv run python`을 사용해야 가상환경 안의 dartlab이 잡힌다.

### 회사 데이터 다운로드가 느린 경우

GitHub Releases에서 다운로드하므로 네트워크 상태에 따라 시간이 걸릴 수 있다. `downloadAll()`로 전체를 미리 받아두면 이후 빠르게 사용할 수 있다.

---

## 다음 단계

- [빠른 시작](./quickstart) — 전체 기능 둘러보기
- [API Overview](../api/overview) — property 전체 목록
