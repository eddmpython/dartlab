# dartlab — Pyodide (브라우저/Excel)

dartlab을 브라우저에서 실행. 설치 없이 재무분석.

## 빠른 시작 (브라우저)

```html
<script src="https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js"></script>
<script type="module">
  import { initDartlab } from "https://raw.githubusercontent.com/.../pyodide/loader.js";

  const { py, run } = await initDartlab({
    stockCode: "005930",
    onLog: console.log,
  });

  await run(`print(c.panel("IS"))`);
  await run(`print(c.analysis("financial", "수익성"))`);
  await run(`print(c.story("수익성").toMarkdown())`);
</script>
```

## 빠른 시작 (xlwings lite)

```python
import micropip
# dartlab wheel 한 줄. deps(diff-match-patch·openpyxl 등)는 wheel 메타데이터로 micropip 이 자동 해소.
# 빌트인 C 확장(polars·pyarrow·lxml·numpy)도 emscripten Requires-Dist 마커로 자동 로드된다.
await micropip.install("https://huggingface.co/.../pyodide/dartlab-0.10.8-py3-none-any.whl")

import dartlab
c = dartlab.Company("005930")
c.panel("IS")
```

## 아키텍처

```
JS: fetch(HF URL) → pyodide.FS.writeFile("/data/dart/{cat}/{code}.parquet")
Python: pyarrow.parquet.read_table(BytesIO) → pl.from_arrow()
```

- polars WASM: `read_parquet`/`write_parquet` 비활성 → pyarrow 경유
- threading 불가 → 순차 실행
- 파일시스템: pyodide MEMFS (비영속)

## 지원 기능

| 기능 | 상태 |
|---|---|
| `Company(code)` | ✅ |
| `c.panel("IS"/"BS"/"CF")` | ✅ |
| `c.analysis("수익성")` | ✅ |
| `c.story("수익성")` | ✅ |
| `dartlab.ask(...)` | ✅ (API 키 필요) |
| `dartlab.scan(...)` | ❌ (scan 프리빌드 271MB) |
| `dartlab.gather(...)` | ❌ (외부 API CORS) |

## AI (API 키 방식)

```python
import os
os.environ["GEMINI_API_KEY"] = "your-key"
dartlab.ask("삼성전자 수익성 분석해줘", provider="gemini")
```

| Provider | 브라우저 |
|---|---|
| gemini | ✅ CORS OK |
| openai | ✅ CORS OK |

## 빌드/업로드

```bash
# wheel 빌드만
python pyodide/build.py

# wheel 빌드 + HF 업로드
python pyodide/build.py --upload
```
