# ChaniNotebook Specification

## 1. Overview

ChaniNotebook은 eddmpython 학습 플랫폼 전용 인터랙티브 노트북 에디터이다.
marimo의 셀 기반 구조와 API를 참고하되, 교육 특화 기능과 자체 UI 디자인을 적용한다.

- Route: `/eddmlab`
- Runtime: Pyodide (브라우저 WASM, 서버 불필요)
- Editor: CodeMirror 6
- Design: shadcn zinc 테마 (CSS 변수 기반)
- File Format: marimo `.py` + Jupyter `.ipynb` + ChaniNotebook `.json`

---

## 2. Architecture

```
frontend/src/lib/features/notebook/
├── NotebookEditor.svelte           # 메인 에디터 (embedded 모드 지원)
├── SPEC.md                         # 이 파일
├── MARIMO_COMPAT_PRD.md            # marimo 호환 위젯 기획서
│
├── components/                     # UI 컴포넌트
│   ├── Cell.svelte                 # 셀 래퍼 (타입별 렌더링 분기)
│   ├── CodeCell.svelte             # 코드 셀 (CodeMirror 6)
│   ├── MarkdownCell.svelte         # 마크다운 셀 (marked.js)
│   ├── GuideCell.svelte            # 교육 가이드 셀 (미션/힌트/정답)
│   ├── OutputPanel.svelte          # 실행 결과 패널 (text/html/image/df/widget)
│   ├── CellToolbar.svelte          # 셀 상단 도구 모음
│   ├── AddCellButton.svelte        # 셀 추가 버튼
│   └── DataFrameTable.svelte       # pandas DataFrame 테이블 렌더링
│
├── stores/                         # Svelte 상태 관리
│   ├── notebookStore.ts            # 셀/노트북 CRUD, 저장/로딩
│   ├── executionStore.ts           # 실행 엔진 상태, 반응형 실행
│   ├── sidebarStore.ts             # 사이드바 패널 상태
│   ├── userStore.ts                # 사용자 인증 상태
│   └── cloudStore.ts               # 클라우드 저장 상태
│
├── engine/                         # 실행 엔진
│   ├── executionEngine.ts          # ExecutionEngine 인터페이스
│   ├── pyodideEngine.ts            # Pyodide 구현체 (WASM)
│   ├── dataflow.ts                 # DAG 기반 셀 의존성 분석
│   └── marimoShim.ts               # marimo Python shim (40+ 파일)
│
├── widgets/                        # marimo 호환 위젯 시스템 (20종)
│   ├── WidgetBridge.ts             # Python ↔ Svelte 값 동기화
│   ├── WidgetRenderer.svelte       # 위젯 타입별 라우팅 (20 타입)
│   ├── inputs/                     # 입력 위젯
│   │   ├── SliderWidget.svelte
│   │   ├── DropdownWidget.svelte
│   │   ├── TextWidget.svelte
│   │   ├── TextAreaWidget.svelte
│   │   ├── NumberWidget.svelte
│   │   ├── CheckboxWidget.svelte
│   │   ├── SwitchWidget.svelte
│   │   ├── RadioWidget.svelte
│   │   ├── ButtonWidget.svelte
│   │   ├── DateWidget.svelte
│   │   ├── MultiselectWidget.svelte
│   │   ├── RangeSliderWidget.svelte
│   │   ├── FileWidget.svelte
│   │   └── CodeEditorWidget.svelte
│   ├── data/                       # 데이터 위젯
│   │   └── TableWidget.svelte
│   └── composite/                  # 복합 위젯
│       ├── FormWidget.svelte
│       ├── DictionaryWidget.svelte
│       ├── ArrayWidget.svelte
│       └── BatchWidget.svelte
│
├── toolbar/
│   └── NotebookToolbar.svelte      # 상단 도구 모음 (floating controls)
│
├── sidebar/                        # 사이드바 패널
│   ├── Sidebar.svelte              # 사이드바 컨테이너
│   ├── TableOfContents.svelte      # 목차 네비게이션
│   └── panels/
│       ├── VariablesPanel.svelte   # 변수 목록
│       ├── PackagesPanel.svelte    # 패키지 관리
│       ├── DocsPanel.svelte        # 문서 조회
│       ├── DependenciesPanel.svelte # 셀 의존성 그래프
│       └── FilesPanel.svelte       # 가상 파일시스템
│
└── utils/                          # 유틸리티
    ├── notebookFormat.ts           # 직렬화 + 3종 포맷 import/export
    ├── marimoParser.ts             # marimo .py → Cell[] 파서
    ├── marimoWriter.ts             # Cell[] → marimo .py 라이터
    ├── jupyterParser.ts            # Jupyter .ipynb → Cell[] 파서
    └── jupyterWriter.ts            # Cell[] → Jupyter .ipynb 라이터
```

Backend:
```
core/notebook/
├── __init__.py
├── notebookModel.py                # Notebook, Cell, GuideData 모델
├── notebookService.py              # CRUD 서비스 (파일 기반 + GCS)
├── notebookStore.py                # 저장소 추상화
├── contentConverter.py             # YAML 학습 콘텐츠 → 노트북 변환
├── validators.py                   # 정답 검증 로직
└── PRD.md                          # 초기 기획서
```

---

## 3. Data Models

### 3.1 Notebook

```typescript
interface Notebook {
  id: string;
  title: string;
  cells: Cell[];
  workspaceFiles?: WorkspaceFile[];
  metadata: {
    category?: string;
    contentId?: string;
    notebookFilePath?: string;
    createdAt: string;
    updatedAt: string;
  };
}
```

### 3.2 Cell

```typescript
interface Cell {
  id: string;
  type: 'code' | 'markdown' | 'guide';
  content: string;
  output?: CellOutput;
  guide?: GuideData;
  executionCount?: number;
  executionTime?: number;
}
```

### 3.3 CellOutput

```typescript
interface CellOutput {
  type: 'text' | 'html' | 'image' | 'error' | 'dataframe' | 'widget';
  data: string;
  executedAt: string;
}
```

출력 타입별 data 형식:
- `text`: 문자열 (stdout + repr)
- `html`: HTML 문자열 (plotly 차트 등)
- `image`: `data:image/png;base64,...` (matplotlib) / stdout + `__STDOUT_END__` 구분자
- `error`: 에러 메시지 문자열
- `dataframe`: JSON (totalRows, columns, data) / stdout + `__STDOUT_END__` 구분자
- `widget`: 위젯 JSON (WidgetDescriptor) / stdout + `__STDOUT_END__` 구분자

### 3.4 GuideData

```typescript
interface GuideData {
  mission: string;
  hints: string[];
  answer?: string;
  expectedOutput?: string;
}
```

### 3.5 Widget Types

```typescript
interface WidgetDescriptor {
  id: string;
  type: string;
  config: Record<string, unknown>;
  value: unknown;
}
```

지원 위젯 타입 (20종):

| 카테고리 | type 값 | Svelte 컴포넌트 |
|---------|---------|----------------|
| Input | `slider` | SliderWidget |
| Input | `dropdown` | DropdownWidget |
| Input | `text` | TextWidget |
| Input | `text_area` | TextAreaWidget |
| Input | `number` | NumberWidget |
| Input | `checkbox` | CheckboxWidget |
| Input | `switch` | SwitchWidget |
| Input | `radio` | RadioWidget |
| Input | `button`, `run_button` | ButtonWidget |
| Input | `date` | DateWidget |
| Input | `multiselect` | MultiselectWidget |
| Input | `range_slider` | RangeSliderWidget |
| Input | `file` | FileWidget |
| Input | `code_editor` | CodeEditorWidget |
| Data | `table` | TableWidget |
| Composite | `form` | FormWidget |
| Composite | `dictionary` | DictionaryWidget |
| Composite | `array` | ArrayWidget |
| Composite | `batch` | BatchWidget |

---

## 4. Execution Engine

### 4.1 ExecutionEngine Interface

```typescript
interface ExecutionEngine {
  name: string;
  isReady: boolean;
  initialize(): Promise<void>;
  execute(code: string): Promise<CellOutput>;
  interrupt(): void;
  destroy(): void;
  getVariable(name: string): Promise<unknown>;
  getVariableNames(): Promise<string[]>;
  getVariablesWithInfo(): Promise<VariableInfo[]>;
  getCompletions(objName: string): Promise<CompletionItem[]>;
  installPackage(packageName: string): Promise<void>;
  getInstalledPackages(): Promise<PackageInfo[]>;
  getDocstring(name: string): Promise<DocResult | null>;
  updateWidgetValue(widgetId: string, value: unknown): Promise<void>;
  listFiles(path: string): Promise<FileEntry[]>;
  readFile(path: string): Promise<string>;
  writeFile(path: string, content: string): Promise<void>;
  mkdir(path: string): Promise<void>;
  removeFile(path: string): Promise<void>;
}
```

### 4.2 PyodideEngine

- Pyodide v0.27.5 CDN
- stdout/stderr 캡처
- `micropip`으로 패키지 설치
- 마지막 표현식 자동 캡처 (`__eddmlab_result__`)
- 결과 감지 순서: widget → matplotlib → plotly → DataFrame/Series → html → repr
- `/workspace` 가상 파일시스템 (Emscripten FS)
- 모든 디렉토리에 자동 `__init__.py` 생성 (import 지원)

### 4.3 DAG Reactive Execution (dataflow.ts)

셀 간 변수 의존성을 정적 분석하여 DAG를 구축하고, 셀 실행 시 하위 의존 셀을 자동 재실행한다.

- `analyzeCell(cellId, code)` → defines (=, def, class, import, for) / uses 분석
- `buildGraph(cells)` → 전체 DAG (children, parents)
- `getReactiveCells(cellId, cells)` → 토폴로지 정렬된 하위 셀 목록
- Python 키워드/빌트인은 uses에서 제외

### 4.4 Execution Flow

1. 사용자 Shift+Enter → `executeCell(cellId, code)`
2. `executeSingleCell()` → Pyodide execute → CellOutput 업데이트
3. 성공 시 reactiveMode ON이면 → `getReactiveCells()` → 하위 셀 순차 실행
4. widget 출력 감지 시 → `registerWidgetCell(widgetId, cellId)`
5. 위젯 값 변경 시 → `triggerWidgetReactive(definingCellId)` → 하위 셀만 재실행 (정의 셀 제외)

---

## 5. Widget System (marimo Compatible)

### 5.1 Python API

`import marimo as mo` 후 marimo API 문법 그대로 사용:

```python
slider = mo.ui.slider(1, 10, value=5, label="Value")
dropdown = mo.ui.dropdown(["A", "B", "C"], value="A")
text = mo.ui.text(placeholder="Enter...", label="Name")
number = mo.ui.number(start=0, stop=100, step=1)
checkbox = mo.ui.checkbox(label="Enable")
switch = mo.ui.switch(label="Toggle")
radio = mo.ui.radio(["Option 1", "Option 2"])
button = mo.ui.button(label="Click")
date = mo.ui.date(label="Date")
multiselect = mo.ui.multiselect(["A", "B", "C"])
range_slider = mo.ui.range_slider(0, 100)
table = mo.ui.table([{"name": "Alice", "age": 30}])
file = mo.ui.file(filetypes=[".csv"])
code_editor = mo.ui.code_editor(language="python")
form = mo.ui.form(slider, label="Submit")
dictionary = mo.ui.dictionary({"x": slider, "y": dropdown})
array = mo.ui.array([slider, dropdown])
batch = mo.ui.batch(html_template, widgets={"s": slider})
```

### 5.2 Python → Svelte Pipeline

```
Python UIElement._to_json()
    → JSON {"__chani_widget__": true, "id": "w1", "type": "slider", "config": {...}, "value": 5}
    → pyodideEngine.formatResult() 감지
    → CellOutput type='widget'
    → OutputPanel.svelte widgetParsed
    → WidgetRenderer.svelte → SliderWidget.svelte
```

### 5.3 Svelte → Python Pipeline

```
사용자 슬라이더 드래그
    → onChange(newValue) → WidgetBridge.onWidgetValueChange(widgetId, value)
    → pyodide.runPython('UIElement._set_value(widgetId, value)')
    → 200ms debounce → triggerWidgetReactive(definingCellId)
    → DAG 하위 셀 재실행
```

### 5.4 marimo Shim Structure

Pyodide FS `/lib/python3.12/marimo/`에 설치되는 Python shim:

```
marimo/
├── __init__.py              # mo.md(), mo.Html(), mo.hstack() 등 공개 API
├── _ui/
│   ├── __init__.py          # mo.ui namespace (20 위젯 타입 import)
│   ├── base.py              # UIElement 베이스 클래스 (registry, _to_json, _set_value)
│   ├── slider.py            # mo.ui.slider
│   ├── dropdown.py          # mo.ui.dropdown
│   ├── text.py              # mo.ui.text, mo.ui.text_area
│   ├── number.py            # mo.ui.number
│   ├── checkbox.py          # mo.ui.checkbox, mo.ui.switch
│   ├── radio.py             # mo.ui.radio
│   ├── button.py            # mo.ui.button, mo.ui.run_button
│   ├── date.py              # mo.ui.date
│   ├── multiselect.py       # mo.ui.multiselect
│   ├── range_slider.py      # mo.ui.range_slider
│   ├── table.py             # mo.ui.table (list-of-dicts, DataFrame)
│   ├── file.py              # mo.ui.file
│   ├── code_editor.py       # mo.ui.code_editor
│   ├── form.py              # mo.ui.form (inner widget + submit)
│   ├── dictionary.py        # mo.ui.dictionary (named widget dict)
│   ├── array.py             # mo.ui.array (widget list)
│   └── batch.py             # mo.ui.batch (HTML template + widgets)
├── _output/
│   ├── __init__.py
│   ├── md.py                # mo.md() (마크다운 → HTML, 위젯 인터폴레이션)
│   ├── html.py              # mo.Html()
│   ├── media.py             # mo.image(), mo.video(), mo.audio()
│   └── display.py           # mo.as_html()
├── _layout/
│   ├── __init__.py
│   ├── stacks.py            # mo.hstack(), mo.vstack()
│   ├── callout.py           # mo.callout()
│   ├── accordion.py         # mo.accordion()
│   └── tabs.py              # mo.tabs()
├── _state.py                # mo.state() (getter/setter 패턴)
└── _control.py              # mo.stop(), MarimoStopError
```

### 5.5 html_composite Mode

`mo.md(f"text {widget}")` 패턴에서 마크다운 내 위젯 삽입:

1. Python: `{slider}` → `slider._repr_html_()` → `<chani-widget data-widget-id="w1">{json}</chani-widget>`
2. JS: `extractWidgetsFromHtml(html)` → placeholder를 `<div class="chani-widget-slot">` 로 교체
3. Svelte: `{@html cleanHtml}` + 별도 `WidgetRenderer` 마운트

---

## 6. File Format Compatibility

### 6.1 marimo .py Parser (marimoParser.ts)

marimo `.py` 파일 → ChaniNotebook Cell[] 변환:

- `import marimo` / `app = marimo.App()` 헤더 스킵
- `@app.cell` 데코레이터로 셀 경계 분리
- 함수 body 자동 dedent → 코드 셀 content
- `return (var,)` 튜플 자동 제거 (DAG가 자동 분석)
- `import marimo as mo` 셀 자동 필터링
- `mo.md("""...""")` 단독 셀 → markdown 셀 변환
- `App()` config 파싱 (width, app_title)
- `if __name__ == "__main__":` 푸터 스킵

### 6.2 marimo .py Writer (marimoWriter.ts)

ChaniNotebook Cell[] → marimo `.py` 파일 생성:

- `dataflow.ts` `analyzeCell()`로 defines/uses 분석
- uses → 함수 파라미터 (+ mo), defines → return 튜플
- markdown 셀 → `mo.md("""...""")` 코드 셀로 변환
- guide 셀 → `@app.cell(hide_code=True)` + `mo.md()` 변환 (mission/hints/answer 포함)
- 헤더: `import marimo` + `app = marimo.App()`
- 첫 셀: `import marimo as mo` 자동 삽입
- 푸터: `if __name__ == "__main__": app.run()`
- `return ()` 대신 `return` 사용 (marimo 호환)

### 6.3 Jupyter .ipynb Parser (jupyterParser.ts)

Jupyter nbformat v4 `.ipynb` → ChaniNotebook Cell[] 변환:

- `cell_type: "code"` → code 셀 (output 포함 변환)
- `cell_type: "markdown"` → markdown 셀
- `cell_type: "raw"` → code 셀로 변환
- Output 변환: stream → text, display_data → html/image, execute_result → text, error → error
- ANSI 이스케이프 코드 자동 제거 (traceback)
- base64 이미지 (image/png) → `data:image/png;base64,...`
- SVG → html output
- execution_count 보존

### 6.4 Jupyter .ipynb Writer (jupyterWriter.ts)

ChaniNotebook Cell[] → Jupyter nbformat v4 `.ipynb` 생성:

- code 셀 → `cell_type: "code"` + outputs 변환
- markdown 셀 → `cell_type: "markdown"`
- guide 셀 → `cell_type: "markdown"` (mission/hints/answer를 `<details>` HTML로 변환)
- Output 역변환: text → stream, error → error, image → display_data, html → display_data
- kernelspec metadata 자동 생성 (Python 3)
- cell id sanitize (UUID → `[a-zA-Z0-9-_]` 64자)

### 6.5 UI Integration (NotebookToolbar)

Settings 메뉴:
- **New notebook** — 새 노트북 생성
- **Export .json** — ChaniNotebook 네이티브 JSON
- **Import marimo .py** — marimo 파일 선택 → 파싱 → 노트북 로드
- **Export marimo .py** — marimo 호환 `.py` 다운로드
- **Import Jupyter .ipynb** — Jupyter 파일 선택 → 파싱 → 노트북 로드
- **Export Jupyter .ipynb** — nbformat v4 `.ipynb` 다운로드

---

## 7. Embedding Mode

NotebookEditor는 독립 페이지(`/eddmlab`)와 다른 페이지에 임베딩 모두 지원한다.

### 7.1 Props

```typescript
interface Props {
  embedded?: boolean;        // 임베딩 모드 (min-height 제거, 패딩 축소)
  showHome?: boolean;        // 홈 버튼 표시 (기본: true)
  homeHref?: string;         // 홈 링크 경로 (기본: '/')
  initialNotebook?: Notebook | null;  // 초기 노트북 데이터
  showSidebar?: boolean;     // 사이드바 표시 (기본: true)
  showToolbar?: boolean;     // 툴바 표시 (기본: true)
}
```

### 7.2 독립 사용 (기본)

```svelte
<NotebookEditor />
```

- 서버에서 노트북 로딩 (`loadFromStorage`)
- 전체 UI (사이드바, 툴바, 홈 버튼, TOC)

### 7.3 교육용 임베딩

```svelte
<NotebookEditor
  embedded
  showHome={false}
  showSidebar={false}
  initialNotebook={lessonNotebook}
/>
```

- 서버 로딩 없이 `initialNotebook` 직접 주입
- 사이드바/홈 버튼 숨김
- 컴팩트 패딩, 컨테이너에 맞춤

---

## 8. Toolbar & Controls

### 8.1 Floating Controls

| 위치 | 컨트롤 | 기능 |
|------|--------|------|
| top-center | Filepath | 노트북 경로 (클릭하여 편집) |
| top-right | Status badge | 엔진 상태 (Loading/Running/Error) |
| top-right | Settings | 메뉴 (New/Export/Import 6종) |
| top-right | Theme | 다크/라이트 토글 |
| top-right | Home | 홈 페이지로 이동 |
| bottom-left | Width | 셀 너비 (compact/medium/full) |
| bottom-right | User | 로그인/프로필 |
| bottom-right | Reactive | 반응형 모드 ON/OFF |
| bottom-right | Run All | 모든 셀 실행 |
| bottom-right | Save | 로컬/클라우드 저장 |
| bottom-right | Coffee | Buy me a coffee 링크 |

### 8.2 Keyboard Shortcuts

| 단축키 | 동작 |
|--------|------|
| Shift+Enter | 현재 셀 실행 + 다음 셀 이동 |
| Ctrl+Enter | 현재 셀 실행 (이동 없음) |
| Ctrl+Shift+Enter | 모든 셀 실행 |
| Ctrl+S | 저장 |

---

## 9. Sidebar Panels

| 패널 | 기능 |
|------|------|
| Variables | 현재 네임스페이스 변수 목록 (이름/타입/값) |
| Packages | micropip 패키지 설치/목록 |
| Docs | 함수/객체 docstring 조회 |
| Dependencies | 셀 간 의존성 DAG 시각화 |
| Files | /workspace 가상 파일시스템 CRUD |

---

## 10. Backend API

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/notebook/list` | 노트북 목록 (사용자별) |
| GET | `/api/notebook/{id}` | 노트북 로딩 |
| POST | `/api/notebook/save` | 노트북 저장 (로컬 파일 + 인증 시 GCS) |
| DELETE | `/api/notebook/{id}` | 노트북 삭제 |

---

## 11. Implementation Status

### 11.1 Completed

| 기능 | 파일 |
|------|------|
| 셀 시스템 (code/markdown/guide) | notebookStore.ts, Cell.svelte |
| CodeMirror 6 에디터 | CodeCell.svelte |
| Pyodide 실행 엔진 | pyodideEngine.ts |
| DAG 반응형 실행 | dataflow.ts, executionStore.ts |
| matplotlib/plotly 차트 출력 | pyodideEngine.ts formatResult |
| DataFrame 테이블 출력 | DataFrameTable.svelte |
| 가상 파일시스템 + import | pyodideEngine.ts FS, FilesPanel |
| 노트북 저장/로딩 (서버 API) | notebookStore.ts, notebookService.py |
| 사이드바 (Variables/Packages/Docs/Deps/Files) | sidebar/ |
| 다크/라이트 테마 | NotebookToolbar.svelte |
| 셀 너비 조절 | NotebookToolbar.svelte, notebookStore.ts |
| 노트북 경로 시스템 | executionStore.ts, NotebookToolbar.svelte |
| 사용자 인증 연동 | userStore.ts, cloudStore.ts |
| 교육 가이드 셀 | GuideCell.svelte |
| marimo 위젯 20종 (Python shim + Svelte UI) | widgets/, marimoShim.ts |
| 위젯 ↔ Svelte 값 동기화 | WidgetBridge.ts |
| 위젯 반응형 재실행 | executionStore.ts triggerWidgetReactive |
| html_composite 위젯 모드 | OutputPanel.svelte, WidgetBridge.ts |
| marimo .py 파서/라이터 | marimoParser.ts, marimoWriter.ts |
| Jupyter .ipynb 파서/라이터 | jupyterParser.ts, jupyterWriter.ts |
| Import/Export UI (marimo + Jupyter + JSON) | NotebookToolbar.svelte |
| 홈 버튼 (우측 상단) | NotebookToolbar.svelte |
| Embedding 모드 | NotebookEditor.svelte Props |

### 11.2 Not Yet Implemented

| 기능 | 우선순위 | 설명 |
|------|---------|------|
| mo.stop() 실행 제어 | Medium | 조건부 셀 실행 중단 |
| 위젯 값 localStorage persist | Medium | 새로고침 시 위젯 값 복원 |
| mo.hstack/vstack 레이아웃 렌더링 | Medium | HTML은 생성되지만 CSS 최적화 필요 |
| mo.accordion/tabs 레이아웃 | Low | Svelte 컴포넌트 필요 |
| mo.state() 고급 상태 관리 | Low | getter/setter 패턴 |
| YAML 학습 콘텐츠 → 노트북 변환 | Low | contentConverter.py 확장 |
| SandboxEngine (서버 격리 환경) | Future | 컨테이너 기반 실행 |
| 노트북 공유/협업 | Future | 실시간 공유 |

---

## 12. Design Tokens

노트북은 자체 CSS 변수 시스템 사용 (`--nb-*` prefix):

```css
--nb-bg              /* 배경 */
--nb-card            /* 셀 카드 배경 */
--nb-surface         /* 표면 (hover 등) */
--nb-border          /* 테두리 */
--nb-text            /* 메인 텍스트 */
--nb-text-secondary  /* 보조 텍스트 */
--nb-text-muted      /* 뮤트 텍스트 */
--nb-pink            /* 강조색 (메인 브랜드) */
--nb-pink-bright     /* 밝은 핑크 */
--nb-pink-dim        /* 어두운 핑크 */
--nb-pink-subtle     /* 미묘한 핑크 배경 */
--nb-success         /* 성공 */
--nb-error           /* 에러 */
--nb-code-bg         /* 코드 배경 */
```

---

## 13. Key Patterns

### 13.1 stdout + structured data 구분

stdout 출력과 구조화된 데이터(image/df/widget)가 동시에 있을 때 `__STDOUT_END__\n` 구분자로 분리:

```
print output here
__STDOUT_END__
{structured data json or base64}
```

### 13.2 Widget Local Override

WidgetRenderer에서 사용자 인터랙션 시 즉각 반영을 위한 패턴:

```typescript
let localValue = $state<unknown>(undefined);
let hasLocalOverride = $state(false);
const currentValue = $derived(hasLocalOverride ? localValue : descriptor.value);
$effect(() => { hasLocalOverride = false; });
```

### 13.3 Debounced Widget Reactive

슬라이더 드래그 중 과도한 재실행 방지 (200ms debounce):

```typescript
debounceTimers.set(widgetId, setTimeout(async () => {
    debounceTimers.delete(widgetId);
    await triggerReactive!(cellId);
}, 200));
```
