---
title: 엑셀·브라우저·노트북에서 설치 없이 dartlab 쓰기 — Pyodide
date: 2026-04-21
description: Pyodide가 CPython을 WebAssembly로 포팅한 덕에 xlwings Lite·Anaconda Code·JupyterLite·Google Colab 같은 브라우저 Python 환경에서도 dartlab이 그대로 돈다. 엑셀 셀에서 `=GETFINANCE("005930")`으로 재무제표를 불러오는 사용자 정의 함수까지 만들 수 있다.
category: dartlab-news
series: dartlab-news
seriesOrder: 8
thumbnail: /avatar-code.png
ogImage: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/e6/e64b9a491cc758b2087785fa7dd619eba23809c9463eff0e0594bd92e991529a.webp
cardPreview: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/35/35a3fb5c6fcd4ede966f81e37227ef6a7df7557c64cde84f96f700b25f454946.webp
youtubeId: "epzGLIOWLR0"
keywords:
  - Pyodide
  - xlwings Lite
  - JupyterLite
  - Google Colab
  - Anaconda Code
  - WebAssembly Python
  - dartlab 브라우저
  - 엑셀 파이썬 함수
  - dartlab-lite
---

<script>
  import YouTube from '$lib/components/YouTube.svelte';
</script>

<YouTube id="epzGLIOWLR0" title="엑셀·브라우저·노트북에서 설치 없이 dartlab 쓰기 — Pyodide" />

**dartlab은 파이썬 패키지다.** 그런데 파이썬이 설치돼 있지 않은 환경에서도 돌아간다. 엑셀 웹 버전, 사내 웹 주피터, 크롬 탭 하나 — 어디서든 `import dartlab` 한 줄로 삼성전자의 손익계산서가 나온다. 지난 2년 사이 조용히 퍼진 한 인프라, **Pyodide** 덕분이다.

이 글에서는 dartlab의 Pyodide 지원(이하 **dartlab-lite**)이 어떤 환경에서 어떻게 돌아가는지, 그리고 엑셀에서 사용자 정의 함수로 쓰는 실제 화면을 두 장 보여준다. 더불어 Pyodide가 뭔지, 어떤 제약이 있는지도 정확히 짚는다. 설치형 dartlab과 **같은 API**, **같은 데이터**인데 배포만 브라우저 안에서 이뤄진다.

> **이 글을 끝까지 읽으면**, 아래에서 미리 세팅된 **데모 엑셀**을 열어 직접 빠르게 테스트해볼 수 있다. 설치·계정 설정 전부 생략하고 결과만 보고 싶다면 엑셀 섹션이 끝나는 지점의 체험 링크를 쓰면 된다.

---

## Pyodide가 뭔가

**Pyodide는 CPython을 WebAssembly(WASM)로 컴파일한 런타임이다.** 모질라가 2018년에 시작해 지금은 독립 프로젝트로 운영 중이다. 핵심 한 줄:

![일반 Python vs Pyodide — 같은 CPython, 런타임이 내 컴퓨터냐 브라우저 탭이냐 하나의 차이](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/81/81870f17dba90592326db964b0db6bdb95dd7a087f11a975696ebc39aeb68470.svg)

> **브라우저 탭 하나 안에서 진짜 CPython이 돈다.** `numpy`·`pandas`·`scipy`·`polars` 같은 네이티브 확장까지 포함해서.

**WebAssembly(WASM)가 뭔가** — 브라우저가 JavaScript 외에 **추가로** 돌릴 수 있는 저수준 실행 형식이다. C·Rust·파이썬 같은 언어로 짠 프로그램을 `.wasm` 바이너리로 컴파일해 두면, 브라우저가 그걸 네이티브 앱에 가까운 속도로 실행한다. 별도 플러그인 없이, Chrome·Edge·Safari·Firefox 전부 표준 지원한다.

그래서 **파이썬 인터프리터 자체를 하나의 `.wasm` 파일로 말아 브라우저에 배포**할 수 있다. 사용자가 페이지를 여는 순간 인터프리터가 다운로드되고, 그 이후부터는 내 노트북에 파이썬이 설치된 것처럼 동작한다. 서버 왕복 없음. 코드는 내 컴퓨터의 브라우저 안에서만 실행된다. JS는 `pyodide.runPython("...")`으로 파이썬을 호출하고, 파이썬 객체가 그대로 JS에 노출된다. `fetch` 같은 브라우저 API도 파이썬에서 `await`로 쓸 수 있다.

덕분에 **"파이썬이 설치된 런타임"이라는 전제가 브라우저에 딸려 온다.** Pyodide가 이 전제를 만들어 놓자, 이를 재료로 삼아 "브라우저 안의 Python IDE"를 만드는 도구들이 최근 2년 사이 쏟아졌다. xlwings Lite는 그 도구들 중 **엑셀에 꽂는 플러그인**이다.

![일반 Python 5단계 vs Pyodide 1단계 — 중간 4단계가 증발하는 이유](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/a3/a3753bb552a5c8ebfe7d539f270b276540f2dc3db67dfcbb1b3afb7ffdca7056.svg)

| 제품 | 무엇 | 어떻게 쓰나 |
|---|---|---|
| **xlwings Lite** | Excel(웹·데스크톱 통합) 안에서 파이썬 실행 | 엑셀 사이드바에서 `@script` / `@func` 데코레이터로 함수 작성 |
| **Anaconda Code** | Excel 추가기능(Anaconda에서 배포) | 엑셀에서 파이썬 셀로 분석, 결과를 그대로 시트에 반환 |
| **JupyterLite** | 서버 없는 Jupyter — 전부 브라우저에서 | 정적 호스팅만 하면 노트북 환경 배포 |
| **Google Colab (WASM 런타임)** | 로컬 런타임 옵션으로 브라우저 Python 지원 | 기존 노트북 UX 그대로 |
| **marimo (pyodide 모드)** | 반응형 노트북을 정적 페이지로 배포 | `marimo export html-wasm` 한 줄 |

공통점: **서버 없이 파이썬이 돈다.** 사용자는 "파이썬 설치"를 거치지 않고도 코드를 돌릴 수 있다.

---

## dartlab-lite — 같은 API, 다른 배포

dartlab은 v0.9.9부터 Pyodide 전용 wheel을 함께 배포한다. [pyodide/README.md](https://github.com/eddmpython/dartlab/blob/master/pyodide/README.md)에 빌드 파이프라인 전부가 있다. 핵심은 세 가지.

- **CPython 계열 의존성은 Pyodide 내장** — `numpy`·`pandas`·`polars`·`pyarrow`는 Pyodide가 제공하는 WASM 빌드를 쓴다. dartlab wheel은 이들을 다시 다운로드하지 않는다.
- **parquet 로드 경로만 우회** — polars의 WASM 빌드는 `read_parquet`/`write_parquet`가 비활성화돼 있다. dartlab-lite는 `pyarrow.parquet.read_table(BytesIO) → pl.from_arrow()`로 한 단계 우회한다.
- **데이터는 HuggingFace에서 직접 fetch** — 사용자가 `Company("005930")`을 부르면 JS가 HF URL에서 parquet를 받아 `pyodide.FS.writeFile("/data/dart/finance/005930.parquet")`로 MEMFS에 놓고, 파이썬이 그걸 읽는다.

사용자 입장에서는 import 구문 하나 늘어날 뿐 차이를 못 느낀다.

```python
# 어떤 환경이든 — 데스크톱, xlwings Lite, JupyterLite, Colab WASM
import dartlab

c = dartlab.Company("005930")
c.panel("IS")
c.analysis("financial", "수익성")
c.story("수익성").toMarkdown()
```

---

## xlwings Lite — 두 가지 사용 모드

엑셀에서 dartlab을 쓰는 방법은 xlwings Lite가 제공하는 두 개의 데코레이터로 갈린다. **스크립트형**(`@script`)과 **함수형**(`@func`)이다. 같은 dartlab 호출을 어떻게 포장하느냐의 차이다.

### 1. 스크립트형 — 버튼 누르면 시트에 채운다

`@script`는 엑셀 사이드바에 **버튼**을 만든다. 사용자가 버튼을 누르면 파이썬 함수가 실행되고, 시트를 직접 조작한다. "이 데이터를 저 셀부터 채워라"라는 **명령형** 스타일이다.

![xlwings Lite — @script 모드, dartlab으로 삼성SDI IS를 A3 셀부터 채운다](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/7f/7f6a2360cb3cd1a504aa7c6ada333e5f3ad88284d668d31740f73bf5b0a306c8.webp)

```python
import dartlab
import xlwings as xw
from xlwings import arg, func, script

@script(name="isTest")
def finance(book: xw.Book):
    c = dartlab.Company('000020')
    df = c.panel('IS')
    data = [list(df.columns)] + [list(r) for r in df.iter_rows()]

    sheet = book.sheets.active
    sheet["A3"].value = data
```

- `@script(name="isTest")` — xlwings Lite 사이드바 드롭다운에 "isTest" 항목이 뜬다
- `book: xw.Book` — 엑셀 워크북 자체를 파이썬 객체로 받는다. 시트·범위 전체를 제어 가능
- `sheet["A3"].value = data` — 헤더 한 줄 + 값 행을 A3부터 한번에 붙여넣는다

사용 흐름: **엑셀 사이드바 → isTest 버튼 → 시트에 손익계산서가 찍힌다.** 파이썬은 "실행되는 스크립트"로 취급된다.

### 2. 함수형 — 엑셀 셀에 수식처럼 쓴다

`@func`는 완전히 다르다. 파이썬 함수가 **엑셀 사용자 정의 함수(UDF)**로 등록된다. 그래서 사용자는 셀에 `=GETFINANCE("005930")`처럼 **수식**을 입력하면 되고, 결과가 스필(spill) 배열로 주변 셀까지 자동으로 채워진다.

![xlwings Lite func 모드, 셀에 GETFINANCE 수식 입력 즉시 SK하이닉스 IS가 5분기 분량 자동 스필](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/b0/b0e0b8a141f1e954822c1c145f39be4a8e01c9ea0acf58f7af1d6fda91f99277.webp)

```python
@func
def getFinance(code: str):
    c = dartlab.Company(code)
    df = c.panel('IS')
    data = [list(df.columns)] + [list(r) for r in df.iter_rows()]
    return data
```

- `@func` — 이 함수가 엑셀 전체에서 수식처럼 호출 가능한 UDF가 된다
- 반환값이 2D 배열이면 스필 범위로 자동 배치됨 (`A5`에 입력 → `A5:G22` 전체에 IS가 펼쳐진다)
- 셀 수식이므로 **재계산도 자동** — 인수(종목코드) 바꾸면 값이 전부 갱신된다

이게 xlwings Lite가 데이터 분석 도구로 가지는 결정적 매력이다. dartlab을 **엑셀 네이티브 함수로 끼워 넣는다.** VLOOKUP과 나란히 `=GETFINANCE`가 동작한다.

> **핵심 차이**: `@script`는 버튼형·명령형(시트를 고쳐 쓴다), `@func`는 수식형·선언형(셀이 호출한다). dartlab은 둘 다 지원한다. **xlwings Lite에서 제공하는 함수형이 dartlab을 가장 엑셀답게 쓰는 방법이다.**

---

## 처음부터 — xlwings Lite 설치 5단계

프로그래밍 경험이 없어도 따라할 수 있다. 엑셀 데스크톱이 없어도 된다. 구글 검색창 하나로 시작한다.

### 1단계. 웹 엑셀 열기

구글에서 **"엑셀"**을 검색하고 맨 위 [**excel.cloud.microsoft**](https://excel.cloud.microsoft/) 링크를 클릭한다. Microsoft 계정(outlook·hotmail·라이브·학교/회사 계정 다 됨)으로 로그인하면 브라우저 엑셀이 바로 열린다. 로컬 설치 0줄.

![엑셀 웹 버전 검색 — 구글에서 '엑셀' 첫 결과가 excel.cloud.microsoft](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/f3/f3678eb678d50bec8a3eb6079ce5587b4df412063a3457a26656d19963d1dbec.webp)

### 2단계. 빈 통합 문서 만들기

로그인 후 "빈 통합 문서 만들기"를 누르거나 기존 Book을 연다. 새 워크북이 열리면 화면 상단 메뉴가 뜬다.

![Excel Web — '빈 통합 문서 만들기' 버튼으로 새 워크북 시작](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/2c/2c06274c72583c93b0719d989c11a71abe93cb7a0425ba9c822c36a5a9516cf7.webp)

### 3단계. xlwings Lite 추가 기능 설치

엑셀 상단 리본의 **추가 기능(홈 > 추가 기능)** 아이콘을 누르고 검색창에 **"xlwings"**를 입력한다. 검색 결과의 **xlwings Lite** 항목에서 "추가"를 누른다. 처음 한 번만 하면 된다. 계정에 종속되므로 다른 워크북을 열어도 따라온다.

![xlwings Lite 추가 기능 — 엑셀 추가기능 검색창에서 'xlwings' 검색 후 추가 버튼](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/d2/d2100f10ddca94e665ad8b3309f931993c651eaa084706707bc46af489070346.webp)

### 4단계. requirements.txt에 dartlab 한 줄 추가

화면 오른쪽에 **xlwings Lite 사이드바**가 뜬다. 사이드바 상단 탭에서 `requirements.txt`를 클릭하고 맨 아래 줄에 **`dartlab`**이라고만 쓴다. 줄바꿈 후 저장(Ctrl+S). 이게 xlwings Lite에게 "이 워크북에서 dartlab 패키지를 쓰겠다"고 알리는 방법이다. 재시작이 필요하다 — 사이드바 메뉴 버튼에서 "Python 커널 재시작"을 누르면 Pyodide가 dartlab을 자동으로 받아 올린다.

![xlwings Lite requirements.txt — 맨 아래 줄에 `dartlab` 한 줄만 추가](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/b6/b61c1dc7751f3a0479db06dc1c0687c9ffc97f68c293870e9a1bdac7cc7a8e9c.webp)

### 5단계. main.py에 코드 쓰고 실행

사이드바의 `main.py` 탭으로 돌아가 아래 코드를 그대로 붙여넣는다. 상단 초록 버튼 옆 드롭다운에 `is`(스크립트 이름)가 뜨면 정상. 버튼을 누르면 시트에 삼성SDI 손익계산서가 `A3`부터 채워진다.

```python
import dartlab
import xlwings as xw
from xlwings import arg, func, script

@script(name="is")
def finance(book: xw.Book):
    c = dartlab.Company('000020')
    df = c.panel('IS')
    data = [list(df.columns)] + [list(r) for r in df.iter_rows()]

    sheet = book.sheets.active
    sheet["A3"].value = data
```

![xlwings Lite main.py — @script 작성 후 버튼에 'is'가 떠 있으면 성공](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/5c/5cf5976ee70d2c1f5c25bc86c5238388e4270def2f3cc18f2a89dd903f814411.webp)

여기까지 5단계. **로컬 파이썬 0줄, uv 0줄, venv 0줄.** 브라우저 한 탭으로 dartlab 풀 스택이 돈다.

> 바로 써보고 싶으면 위 OneDrive 링크를 열면 된다. 설치 4단계가 다 끝나 있는 워크북이다.

---

## xlwings Lite에서 dartlab 깔기 (고급)

`requirements.txt`에 `dartlab`만 써도 자동 설치되지만, 버전을 고정하거나 pyodide 전용 wheel을 직접 지정하고 싶다면 첫 셀에서 `micropip`을 쓰면 된다. 이 이후 `import dartlab`이 동작한다.

```python
import micropip
await micropip.install(["diff-match-patch", "openpyxl"])
await micropip.install(
    "https://huggingface.co/eddmpython/dartlab-data/resolve/main/pyodide/dartlab-latest-py3-none-any.whl",
    deps=False,
)
```

- `deps=False` — dartlab wheel의 의존성 중 `numpy`·`polars`·`pyarrow`는 Pyodide가 이미 제공한다. 중복 설치 방지
- `diff-match-patch`·`openpyxl`은 dartlab의 선택 의존성 중 xlwings Lite 환경에서 필요한 최소 집합
- URL의 `dartlab-latest`는 자동 최신화 심볼릭 — 고정 버전이 필요하면 `dartlab-0.9.13-py3-none-any.whl`처럼 박아 쓰면 된다

HuggingFace에서 받는 `.parquet`(공시·재무 데이터)도 동일 도메인이라 **CORS 설정 0줄**로 동작한다.

---

<div style="margin:36px 0;padding:28px 32px;background:linear-gradient(135deg,rgba(234,70,71,0.10),rgba(251,191,36,0.06));border:1px solid rgba(234,70,71,0.30);border-radius:14px;">
  <div style="font-size:13px;font-weight:600;letter-spacing:0.5px;color:#fbbf24;text-transform:uppercase;margin-bottom:10px;">데모 워크북</div>
  <div style="font-size:20px;font-weight:700;color:#f1f5f9;line-height:1.4;margin-bottom:8px;">설치 없이 지금 엑셀에서 바로 돌려보기</div>
  <div style="font-size:15px;color:#cbd5e1;line-height:1.6;margin-bottom:20px;">xlwings Lite 설치·requirements 설정·스크립트 배치까지 이미 끝낸 워크북을 공유한다. Microsoft 계정으로 웹 엑셀을 열 수만 있으면 바로 돌아간다.</div>
  <a href="https://1drv.ms/x/c/4e17617bfea66347/IQB9zW91TaD4TJvHM8LRQTh4ARj0gHMapx4LVhCCSbBz92Q?e=HQ4E7d" target="_blank" rel="noopener" style="display:inline-block;padding:14px 32px;background:#ea4647;color:#ffffff;font-size:16px;font-weight:700;border-radius:10px;text-decoration:none;box-shadow:0 4px 14px rgba(234,70,71,0.35);">▶ 데모 워크북 열기 (OneDrive)</a>
  <div style="font-size:12px;color:#94a3b8;margin-top:14px;">열리지 않으면 Microsoft 계정 로그인 후 다시 시도. 파일 권한은 "보기 전용" — 자유롭게 복제해서 실험해도 된다.</div>
</div>

## JupyterLite / Colab / HTML 임베드에서 쓰기

xlwings Lite가 아니라도 원리는 같다. Pyodide 런타임 위에 `micropip install`로 dartlab wheel을 올리면 끝이다.

**JupyterLite** — `pyproject.toml`의 `dependencies`나 첫 셀에서 동일 `micropip.install(...)` 호출. 노트북을 정적 호스팅하면(`jupyter lite build`) 어떤 CDN이든 풀린다.

**Google Colab (WASM 런타임)** — "로컬 런타임 연결" 드롭다운에서 Pyodide를 선택하면 첫 셀에서 `!pip install micropip` 대신 `import micropip; await micropip.install(...)`로 동일하게 깐다.

**순수 HTML 페이지에 임베드** — 웹페이지 하나에 dartlab을 얹고 싶다면 dartlab이 준비한 `loader.js`를 불러오면 된다.

```html
<script src="https://cdn.jsdelivr.net/pyodide/v0.27.5/full/pyodide.js"></script>
<script type="module">
  import { initDartlab } from "https://raw.githubusercontent.com/eddmpython/dartlab/master/pyodide/loader.js";

  const { run } = await initDartlab({ stockCode: "005930", onLog: console.log });
  await run(`print(c.panel("IS"))`);
  await run(`print(c.analysis("financial", "수익성"))`);
</script>
```

`initDartlab`이 런타임 부팅, wheel 설치, 데이터 프리페치까지 한 번에 해준다. 사내 포털 어딘가에 분석 패널 하나를 붙이는 가장 빠른 방법이다.

---

## Pyodide의 제약 — 되는 것, 안 되는 것

Pyodide는 "브라우저 안의 CPython"이지 서버 파이썬이 아니다. **네 가지 근본 제약**이 있고, dartlab-lite의 기능 범위도 이 선을 따른다.

### 1. 스레드가 없다

브라우저 자바스크립트 스레드 하나에 파이썬이 얹힌다. `threading.Thread`는 생성은 되지만 실제 병렬 실행은 안 된다. 그래서 dartlab은 Pyodide 환경에서 **순차 실행**만 쓴다. `ThreadPoolExecutor`·`asyncio.to_thread` 경로는 전부 동기 fallback을 탄다.

### 2. 파일시스템이 휘발성이다

Pyodide의 파일시스템은 **MEMFS**다. 탭을 닫으면 사라진다. 그래서 dartlab-lite의 로컬 캐시는 세션 단위로만 유효하다. 같은 종목을 두 번째 조회할 땐 빠르지만, 새로고침하면 다시 HF에서 받는다. 매우 큰 사전 빌드 데이터를 로컬에 계속 두고 쓰는 패턴은 불가능하다.

- 해결: 자주 쓰는 parquet는 IndexedDB로 지속화 가능(별도 플러그인 필요). dartlab은 기본값에선 MEMFS만 쓴다.

### 3. CORS가 붙지 않은 외부 API는 못 부른다

브라우저는 `fetch`를 통해서만 네트워크에 접근한다. 그런데 브라우저에는 **CORS**(Cross-Origin Resource Sharing)라는 안전장치가 있다. 비유하자면 **A 사이트에서 B 사이트의 데이터를 브라우저가 직접 받으려면, B가 "나는 A에게 데이터를 줘도 된다"고 허락 도장을 찍어야 한다.** 도장이 없으면 브라우저가 요청을 막는다. 서버 파이썬에는 없는 제약이다.

그래서 Naver·Yahoo·Google News처럼 일반 웹 서비스용으로 만든 데이터 소스는 `allow origin` 도장을 외부에 안 찍어 주고, 브라우저에서 직접 부를 수 없다. 반면 HuggingFace parquet, Gemini·OpenAI REST API는 CORS를 허용해 놨다. dartlab의 엔진도 이 경계선을 따라 갈린다.

![CORS — 허락 도장이 있으면 데이터가 흐르고, 없으면 브라우저가 요청을 차단한다](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/objects/sha256/61/610350d1e34241bff9a0925c75c9958287b41a558c97da80e8b1e538a1e2c97d.svg)

| 엔진 | Pyodide에서 | 이유 |
|---|:---:|---|
| `Company(code)` + `c.panel()` | ✅ | HF parquet (CORS OK) |
| `c.analysis(...)` · `c.story(...)` · `c.credit(...)` | ✅ | Company 데이터만 있으면 로컬 계산 |
| `dartlab.ask(...)` | ✅ | Gemini·OpenAI REST는 CORS 허용 — API 키만 있으면 됨 |
| `dartlab.scan(...)` | ❌ | 사전 빌드 parquet 271MB — **일반 웹페이지(2~3MB)의 100배** 이상, 모바일 데이터로 돌리기엔 시간·요금 모두 비현실적 |
| `dartlab.gather("price"/"news")` | ❌ | Naver·Yahoo·Google News 측 CORS 차단 |
| `dartlab.search(...)` | ⚠ | 인덱스 다운로드만 가능, 베타 |

`scan`은 서버 프록시를 따로 두면 풀 수 있지만, dartlab-lite의 배포 철학("서버 없이 그대로 동작")에 어긋난다. 그래서 당분간은 **Company 중심 워크플로우만 Pyodide 범위**로 둔다.

### 4. AI는 되지만 키가 있어야 한다

`dartlab.ask()`는 브라우저에서도 돈다. 단, API 키를 직접 설정해야 한다.

```python
import os
os.environ["GEMINI_API_KEY"] = "your-key"
dartlab.ask("삼성전자 수익성 분석해줘", provider="gemini")
```

[Gemini API 키 받기](https://aistudio.google.com/app/apikey) · [OpenAI API 키](https://platform.openai.com/api-keys). **키를 공개 페이지에 박아 넣지 말 것** — 로컬 개발/사내 도구에서만 쓸 것.

---

## 그래서 어디서 쓰나

세 가지 정리된 시나리오가 있다.

1. **재무팀의 Excel 파이썬 UDF** — `=GETFINANCE("005930")`을 셀에 쓰고 VLOOKUP과 엮어 분기별 트렌드 시트를 자동 갱신한다. xlwings Lite + `@func`.
2. **사내 위키 / 리포트 페이지** — 마크다운 뷰어 안에 분석 위젯을 임베드. `initDartlab` 하나로 공시·재무 요약을 실시간 생성한다.
3. **학교·세미나 교재 (JupyterLite)** — 수강생이 파이썬 설치 없이 링크만 열면 dartlab 튜토리얼이 그대로 돈다. 로컬 환경 세팅에 세션 첫 30분을 쓰지 않아도 된다.

---

## 정리

- Pyodide가 CPython·numpy·polars까지 브라우저 WASM 런타임으로 포팅했고, 그 위에 xlwings Lite·Anaconda Code·JupyterLite·Colab·marimo가 올라탔다.
- dartlab은 v0.9.9부터 Pyodide 전용 wheel을 HF에 올려, **같은 API로 브라우저에서도 동작**한다.
- xlwings Lite에서는 두 모드를 다 쓸 수 있다. **`@script`는 버튼형, `@func`는 수식형**. 함수형이 dartlab을 엑셀답게 쓰는 방식이다.
- 제약은 넷 — 스레드 없음, MEMFS 휘발, CORS 미허용 API 불가, AI는 API 키 필요. 그래서 `scan`·`gather` 일부는 빠지지만 **Company 중심 분석 · story · ask는 전부 돈다.**

설치 없는 분석이 기본값이 되고 있다. dartlab-lite는 그 흐름에 얹히는 가장 얕은 레이어다. 엑셀 셀에 `=GETFINANCE("005930")`을 쳐 보면 감이 온다.

---

**참고**

- [pyodide/README.md — 빌드·임베드 가이드](https://github.com/eddmpython/dartlab/blob/master/pyodide/README.md)
- [xlwings Lite 공식 문서](https://lite.xlwings.org/)
- [Pyodide 공식 문서](https://pyodide.org/)
- [JupyterLite](https://jupyterlite.readthedocs.io/)
- [Anaconda Code for Excel](https://www.anaconda.com/products/code-for-excel)
