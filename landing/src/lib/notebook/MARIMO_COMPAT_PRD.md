# ChaniNotebook — marimo 호환 위젯 시스템 기획서

## 1. 목표

marimo의 `mo.ui` 위젯 API 문법을 그대로 따라가되, GUI 디자인은 ChaniNotebook 자체 디자인 시스템(shadcn zinc 테마)을 사용한다.

**핵심 원칙**:
- marimo에서 작성한 `.py` 파일을 ChaniNotebook에서 열 수 있어야 한다
- ChaniNotebook에서 작성한 노트북을 marimo `.py` 형식으로 내보낼 수 있어야 한다
- Python API(`mo.ui.slider`, `mo.md` 등)는 marimo와 동일하게 동작한다
- 렌더링(HTML/CSS)은 ChaniNotebook 자체 Svelte 컴포넌트로 한다

---

## 2. 현재 상태 분석

### 2.1 이미 구현된 것

| 기능 | 상태 | 위치 |
|---|---|---|
| 셀 기반 노트북 구조 | O | `notebookStore.ts` |
| Pyodide 실행 엔진 | O | `pyodideEngine.ts` |
| DAG 기반 반응형 실행 | O | `dataflow.ts` (변수 정의/사용 분석, 위상 정렬) |
| 셀 간 변수 공유 | O | Pyodide 글로벌 네임스페이스 |
| 코드/마크다운/가이드 셀 | O | `notebookStore.ts` Cell 타입 |
| matplotlib/plotly 차트 출력 | O | `pyodideEngine.ts` formatResult |
| DataFrame 테이블 출력 | O | `DataFrameTable.svelte` |
| 가상 파일시스템 + import | O | `/workspace` + `__init__.py` |
| localStorage/서버 저장 | O | `notebookStore.ts` save/load |

### 2.2 아직 없는 것 (이 기획서에서 다룸)

| 기능 | 설명 |
|---|---|
| `mo` Python 모듈 | Pyodide 내에서 `import marimo as mo` 가능하게 하는 shim |
| `mo.ui.*` 위젯 | slider, dropdown, text, checkbox 등 인터랙티브 위젯 |
| 위젯 ↔ Svelte 브릿지 | Python 위젯 값 변경 → Svelte UI 렌더 → 값 변경 → 셀 재실행 |
| `mo.md()` / `mo.Html()` | 마크다운/HTML 출력 (위젯 인터폴레이션 포함) |
| 레이아웃 함수 | `mo.hstack`, `mo.vstack`, `mo.accordion`, `mo.tabs` 등 |
| marimo `.py` 파서/라이터 | `@app.cell` 데코레이터 파일 형식 파싱/생성 |
| `mo.stop()` / `mo.state()` | 실행 제어 및 고급 상태 관리 |

---

## 3. 아키텍처 설계

### 3.1 전체 흐름

```
[Python Code in Cell]
    │
    ▼
[Pyodide 실행] ← mo 모듈 (Python shim)
    │
    ├─ mo.ui.slider(1,10) → WidgetProxy 객체 생성
    │    │
    │    ▼
    │  __repr_html__() → JSON 직렬화
    │    │
    │    ▼
    ├─ 셀 반환값에 WidgetProxy 포함 감지
    │
    ▼
[executionStore.ts] ← 출력 타입 'widget' 감지
    │
    ▼
[OutputPanel.svelte] → WidgetRenderer.svelte
    │
    ├─ type='slider' → SliderWidget.svelte
    ├─ type='dropdown' → DropdownWidget.svelte
    ├─ type='text' → TextWidget.svelte
    └─ ...
    │
    ▼ (사용자 인터랙션)
    │
[값 변경 이벤트] → executionStore.ts
    │
    ▼
[Pyodide: widget.value 업데이트]
    │
    ▼
[DAG 하위 셀 자동 재실행] (기존 dataflow.ts 활용)
```

### 3.2 Python 측: `mo` 모듈 (Pyodide shim)

Pyodide 가상 파일시스템에 `/lib/python/marimo/` 패키지를 생성하여 `import marimo as mo`가 동작하도록 한다.

```
/lib/python/marimo/
├── __init__.py          # mo.md(), mo.Html(), mo.hstack() 등
├── _ui/
│   ├── __init__.py      # mo.ui namespace
│   ├── slider.py        # mo.ui.slider
│   ├── dropdown.py      # mo.ui.dropdown
│   ├── text.py          # mo.ui.text, mo.ui.text_area
│   ├── checkbox.py      # mo.ui.checkbox, mo.ui.switch
│   ├── number.py        # mo.ui.number
│   ├── radio.py         # mo.ui.radio
│   ├── button.py        # mo.ui.button, mo.ui.run_button
│   ├── date.py          # mo.ui.date
│   ├── table.py         # mo.ui.table
│   ├── dataframe.py     # mo.ui.dataframe
│   ├── file.py          # mo.ui.file
│   ├── multiselect.py   # mo.ui.multiselect
│   ├── range_slider.py  # mo.ui.range_slider
│   ├── form.py          # mo.ui.form
│   └── base.py          # UIElement 베이스 클래스
├── _output/
│   ├── __init__.py
│   ├── md.py            # mo.md()
│   ├── html.py          # mo.Html()
│   └── media.py         # mo.image(), mo.video(), mo.audio()
├── _layout/
│   ├── __init__.py
│   ├── stacks.py        # mo.hstack(), mo.vstack()
│   ├── accordion.py     # mo.accordion()
│   ├── tabs.py          # mo.tabs()
│   └── callout.py       # mo.callout()
├── _state.py            # mo.state()
└── _control.py          # mo.stop(), MarimoStopError
```

### 3.3 UIElement 베이스 클래스 설계

```python
class UIElement:
    _widget_registry = {}    # widget_id → UIElement 인스턴스
    _next_id = 0

    def __init__(self, widget_type, **kwargs):
        UIElement._next_id += 1
        self._id = f"w{UIElement._next_id}"
        self._type = widget_type
        self._config = kwargs
        self._value = kwargs.get('value')
        UIElement._widget_registry[self._id] = self

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_val):
        self._value = new_val

    def _repr_json_(self):
        return {
            "__chani_widget__": True,
            "id": self._id,
            "type": self._type,
            "config": self._config,
            "value": self._value
        }

    def _repr_html_(self):
        import json
        data = json.dumps(self._repr_json_())
        return f'<div data-chani-widget="{self._id}">{data}</div>'

    def __repr__(self):
        return f"mo.ui.{self._type}(value={self._value!r})"
```

### 3.4 JS 측: 위젯 브릿지

`pyodideEngine.ts`의 `formatResult()`에서 위젯 JSON을 감지하고 새 출력 타입 `'widget'`으로 전달한다.

```typescript
// CellOutput 타입 확장
type: 'text' | 'html' | 'image' | 'error' | 'dataframe' | 'widget'

// widget 출력 데이터 형식
interface WidgetOutputData {
    widgets: WidgetDescriptor[];
    html?: string;        // mo.md() 등에서 위젯이 포함된 HTML
    stdout?: string;
}

interface WidgetDescriptor {
    id: string;           // "w1", "w2", ...
    type: string;         // "slider", "dropdown", ...
    config: Record<string, unknown>;
    value: unknown;
}
```

### 3.5 Svelte 위젯 컴포넌트 구조

```
frontend/src/lib/features/notebook/
├── widgets/
│   ├── WidgetRenderer.svelte    # 위젯 타입별 라우팅
│   ├── WidgetBridge.ts          # Python ↔ Svelte 값 동기화
│   ├── inputs/
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
│   │   ├── FileWidget.svelte
│   │   ├── MultiselectWidget.svelte
│   │   └── RangeSliderWidget.svelte
│   ├── data/
│   │   ├── TableWidget.svelte
│   │   └── DataFrameWidget.svelte
│   ├── composite/
│   │   ├── FormWidget.svelte
│   │   ├── DictionaryWidget.svelte
│   │   └── ArrayWidget.svelte
│   └── layout/
│       ├── HStack.svelte
│       ├── VStack.svelte
│       ├── AccordionLayout.svelte
│       ├── TabsLayout.svelte
│       └── CalloutLayout.svelte
```

### 3.6 위젯 값 변경 → 반응형 재실행 플로우

```
1. 사용자가 SliderWidget 드래그
2. SliderWidget → WidgetBridge.updateValue(widgetId, newValue)
3. WidgetBridge:
   a. Pyodide에서 widget._value 업데이트:
      pyodide.runPython(`
          from marimo._ui.base import UIElement
          UIElement._widget_registry["${widgetId}"]._value = ${newValue}
      `)
   b. 해당 위젯을 정의한 셀 ID 조회
   c. executionStore.triggerReactiveUpdate(definingCellId)
4. executionStore:
   a. dataflow.getReactiveCells(definingCellId, cells) 호출
   b. 의존 셀들 토폴로지 순서대로 재실행
   c. 재실행 시 widget.value는 이미 업데이트된 상태
```

**중요**: 위젯을 정의한 셀 자체는 재실행하지 않는다 (marimo 동작과 동일). 위젯 값을 **참조하는** 하위 셀만 재실행한다.

### 3.7 위젯 ID ↔ 셀 매핑

executionStore에 위젯 레지스트리를 추가한다:

```typescript
// executionStore.ts에 추가
const widgetCellMap = writable<Map<string, string>>(new Map());
// key: widgetId ("w1"), value: definingCellId

// 셀 실행 후 위젯 등록
async function registerWidgets(cellId: string): Promise<void> {
    const widgetIds = await engine.execute(`
        import json
        from marimo._ui.base import UIElement
        json.dumps([wid for wid, w in UIElement._widget_registry.items()
                    if not hasattr(w, '_registered')])
    `);
    // 새 위젯들을 cellId에 매핑
}
```

---

## 4. marimo `.py` 파일 호환

### 4.1 marimo 파일 형식

```python
import marimo

app = marimo.App()

@app.cell
def _(mo):
    slider = mo.ui.slider(1, 10, value=5, label="Value")
    slider
    return (slider,)

@app.cell
def _(mo, slider):
    mo.md(f"## 결과: {slider.value * 2}")
    return ()

if __name__ == "__main__":
    app.run()
```

### 4.2 파서 (marimo `.py` → ChaniNotebook 셀)

`utils/marimoParser.ts`에 구현:

```
입력: marimo .py 파일 텍스트
출력: Cell[] 배열

파싱 단계:
1. `import marimo` / `app = marimo.App()` 헤더 스킵
2. `@app.cell` 데코레이터로 셀 경계 분리
3. 각 셀의 함수 body를 코드 셀 content로 변환
4. 함수 파라미터 → 의존성 정보 (참고용, DAG는 런타임에 빌드)
5. return 튜플 → 정의 변수 (참고용)
6. `if __name__ == "__main__":` 푸터 스킵
```

**변환 규칙**:
- `def _(mo):` → 파라미터에서 `mo` 제거 (자동 import)
- `def _(mo, slider):` → 파라미터에서 `mo` 제거, `slider`는 의존성
- `return (slider,)` → 코드에서 제거 (ChaniNotebook은 자동 분석)
- 함수 이름 `_` → 일반 셀, 이름 있으면 → 셀 메타데이터로 보존

### 4.3 라이터 (ChaniNotebook 셀 → marimo `.py`)

`utils/marimoWriter.ts`에 구현:

```
입력: Cell[] 배열
출력: marimo 호환 .py 파일 텍스트

생성 단계:
1. 헤더: `import marimo\napp = marimo.App()\n`
2. 첫 셀: `import marimo as mo` (없으면 자동 추가)
3. 각 코드 셀:
   a. dataflow.ts로 defines/uses 분석
   b. uses → 함수 파라미터 (+ mo)
   c. defines → return 튜플
   d. `@app.cell\ndef _(mo, param1, param2):\n    {코드}\n    return (var1, var2,)`
4. 마크다운 셀: `mo.md("""...""")` 코드 셀로 변환
5. 푸터: `if __name__ == "__main__":\n    app.run()`
```

### 4.4 호환성 한계 (의도적 차이)

| marimo 기능 | ChaniNotebook 대응 | 비고 |
|---|---|---|
| `@app.cell` 데코레이터 | 셀 배열 (런타임 DAG) | 파일 import/export 시만 변환 |
| 함수 return 튜플 | 자동 변수 분석 | `dataflow.ts`가 자동 처리 |
| `marimo.App()` config | notebook metadata | width, title 등 매핑 |
| `mo.sidebar()` | 사이드바 패널 | 자체 디자인 |
| `mo.nav_menu()` | 미지원 (Phase 3) | 멀티페이지 앱은 범위 밖 |
| anywidget | 미지원 (Phase 3) | 커스텀 위젯 확장 |

---

## 5. `mo.md()` 위젯 인터폴레이션

marimo의 핵심 패턴: `mo.md(f"Value: {slider}")` — 마크다운 안에 위젯 삽입.

### 5.1 동작 방식

```python
slider = mo.ui.slider(1, 10)
mo.md(f"## 설정\n값을 선택하세요: {slider}\n현재: {slider.value}")
```

위 코드에서:
- `{slider}` → 위젯의 `_repr_html_()` 호출 → 인터랙티브 슬라이더 렌더링
- `{slider.value}` → 현재 값의 문자열 표현

### 5.2 구현 방법

```python
# mo.md() 구현
def md(text):
    import markdown
    html = markdown.markdown(text)
    return Html(html)
```

마크다운 HTML 안에 `<div data-chani-widget="w1">...</div>` 플레이스홀더가 포함되면, Svelte 측에서 해당 div를 찾아 위젯 컴포넌트로 교체한다.

`OutputPanel.svelte`에서:
1. `type === 'widget'`이면 HTML 파싱
2. `data-chani-widget` 속성이 있는 요소 탐색
3. 각 플레이스홀더를 해당 Svelte 위젯 컴포넌트로 마운트

---

## 6. 레이아웃 함수

### 6.1 `mo.hstack()` / `mo.vstack()`

```python
mo.hstack([slider1, slider2, slider3], gap=1)
mo.vstack([title, chart, table], gap=0.5)
```

Python 측에서 레이아웃 JSON 생성:

```python
class HStack:
    def __init__(self, items, gap=0.5, justify='start', align='center'):
        self.items = items
        self.gap = gap
        self.justify = justify
        self.align = align

    def _repr_json_(self):
        return {
            "__chani_layout__": True,
            "type": "hstack",
            "items": [item._repr_json_() if hasattr(item, '_repr_json_') else str(item) for item in self.items],
            "gap": self.gap,
            "justify": self.justify,
            "align": self.align
        }
```

Svelte 측 `HStack.svelte`:
```svelte
<div class="hstack" style="gap: {gap}rem; justify-content: {justify}; align-items: {align};">
    {#each items as item}
        <WidgetRenderer descriptor={item} />
    {/each}
</div>
```

### 6.2 `mo.accordion()` / `mo.tabs()`

```python
mo.accordion({
    "기본 설정": mo.vstack([slider, dropdown]),
    "고급 설정": mo.vstack([checkbox1, checkbox2])
})

mo.tabs({
    "차트": chart_output,
    "테이블": table_output
})
```

shadcn zinc 테마의 Accordion/Tabs 컴포넌트로 렌더링한다.

### 6.3 `mo.callout()`

```python
mo.callout("주의: 이 작업은 되돌릴 수 없습니다.", kind="warn")
```

kind별 스타일:
- `neutral` → zinc-700 border
- `info` → blue-500 accent
- `warn` → amber-500 accent
- `success` → green-500 accent
- `danger` → red-500 accent

---

## 7. 실행 제어

### 7.1 `mo.stop()`

```python
def stop(predicate, output=None):
    if predicate:
        raise MarimoStopError(output)
```

`executionStore.ts`에서 `MarimoStopError`를 감지하면:
- 현재 셀 실행 중단
- output이 있으면 표시
- **하위 의존 셀 실행 스킵** (중요)

### 7.2 `mo.state()`

```python
get_count, set_count = mo.state(0)
```

- `get_count()` → 현재 값 반환, 호출한 셀을 의존 셀로 등록
- `set_count(new_val)` → 값 변경 + 의존 셀 재실행 트리거

구현: `_state.py`에서 state 레지스트리 관리, setter 호출 시 JS 측에 이벤트 발행.

### 7.3 `mo.ui.run_button()`

```python
button = mo.ui.run_button(label="실행")
mo.stop(not button.value)
# 비용이 큰 연산...
```

run_button은 클릭 시 `.value`가 True가 되고, 의존 셀 실행 후 다시 False로 리셋된다.

---

## 8. 구현 단계 (Phase 계획)

### Phase 1: 코어 위젯 + 브릿지 (MVP)

**목표**: `mo.ui.slider` 하나가 동작하는 end-to-end 파이프라인 완성

| 순서 | 작업 | 파일 |
|---|---|---|
| 1-1 | `UIElement` 베이스 클래스 | `/lib/python/marimo/_ui/base.py` |
| 1-2 | `mo.ui.slider` 구현 | `/lib/python/marimo/_ui/slider.py` |
| 1-3 | `mo` 모듈 __init__ | `/lib/python/marimo/__init__.py` |
| 1-4 | Pyodide 초기화 시 marimo 패키지 설치 | `pyodideEngine.ts` |
| 1-5 | `formatResult()`에 위젯 감지 추가 | `pyodideEngine.ts` |
| 1-6 | CellOutput에 `'widget'` 타입 추가 | `executionEngine.ts`, `notebookStore.ts` |
| 1-7 | `WidgetRenderer.svelte` 라우터 | `widgets/WidgetRenderer.svelte` |
| 1-8 | `SliderWidget.svelte` | `widgets/inputs/SliderWidget.svelte` |
| 1-9 | `WidgetBridge.ts` (값 동기화) | `widgets/WidgetBridge.ts` |
| 1-10 | 위젯 값 변경 → 반응형 재실행 연결 | `executionStore.ts` |

**검증**: 셀1에서 `slider = mo.ui.slider(1,10)`, 셀2에서 `print(slider.value)` → 슬라이더 드래그 시 셀2 자동 재실행

### Phase 2: 기본 위젯 세트

| 순서 | 작업 |
|---|---|
| 2-1 | `mo.ui.dropdown` + `DropdownWidget.svelte` |
| 2-2 | `mo.ui.text` + `TextWidget.svelte` |
| 2-3 | `mo.ui.text_area` + `TextAreaWidget.svelte` |
| 2-4 | `mo.ui.number` + `NumberWidget.svelte` |
| 2-5 | `mo.ui.checkbox` + `CheckboxWidget.svelte` |
| 2-6 | `mo.ui.switch` + `SwitchWidget.svelte` |
| 2-7 | `mo.ui.radio` + `RadioWidget.svelte` |
| 2-8 | `mo.ui.button` + `ButtonWidget.svelte` |
| 2-9 | `mo.ui.date` + `DateWidget.svelte` |
| 2-10 | `mo.ui.multiselect` + `MultiselectWidget.svelte` |
| 2-11 | `mo.ui.range_slider` + `RangeSliderWidget.svelte` |

### Phase 3: 출력 + 레이아웃

| 순서 | 작업 |
|---|---|
| 3-1 | `mo.md()` (마크다운 렌더링 + 위젯 인터폴레이션) |
| 3-2 | `mo.Html()` (raw HTML 출력) |
| 3-3 | `mo.hstack()` + `HStack.svelte` |
| 3-4 | `mo.vstack()` + `VStack.svelte` |
| 3-5 | `mo.accordion()` + `AccordionLayout.svelte` |
| 3-6 | `mo.tabs()` + `TabsLayout.svelte` |
| 3-7 | `mo.callout()` + `CalloutLayout.svelte` |
| 3-8 | `mo.image()`, `mo.video()`, `mo.audio()` |
| 3-9 | `mo.stat()` |

### Phase 4: 데이터 위젯 + 컴포지트

| 순서 | 작업 |
|---|---|
| 4-1 | `mo.ui.table` + `TableWidget.svelte` (기존 DataFrameTable 확장) |
| 4-2 | `mo.ui.dataframe` + `DataFrameWidget.svelte` |
| 4-3 | `mo.ui.file` + `FileWidget.svelte` |
| 4-4 | `mo.ui.form` + `FormWidget.svelte` |
| 4-5 | `mo.ui.dictionary` + `DictionaryWidget.svelte` |
| 4-6 | `mo.ui.array` + `ArrayWidget.svelte` |

### Phase 5: 실행 제어 + 파일 호환

| 순서 | 작업 |
|---|---|
| 5-1 | `mo.stop()` + `MarimoStopError` |
| 5-2 | `mo.state()` (getter/setter 패턴) |
| 5-3 | `mo.ui.run_button` + 실행 게이팅 |
| 5-4 | marimo `.py` 파서 (`marimoParser.ts`) |
| 5-5 | marimo `.py` 라이터 (`marimoWriter.ts`) |
| 5-6 | 파일 import/export UI (toolbar에 추가) |

---

## 9. 기술적 고려사항

### 9.1 Pyodide에서 marimo 패키지 로딩

실제 marimo PyPI 패키지는 서버 의존성이 있어 Pyodide에서 사용 불가. 대신 경량 shim 패키지를 Pyodide 가상 FS에 직접 작성한다.

```typescript
// pyodideEngine.ts initialize() 에서
async function installMarimoShim(): Promise<void> {
    const files = {
        '/lib/python3.12/marimo/__init__.py': MARIMO_INIT_PY,
        '/lib/python3.12/marimo/_ui/__init__.py': MARIMO_UI_INIT_PY,
        '/lib/python3.12/marimo/_ui/base.py': MARIMO_UI_BASE_PY,
        '/lib/python3.12/marimo/_ui/slider.py': MARIMO_UI_SLIDER_PY,
        // ...
    };
    for (const [path, content] of Object.entries(files)) {
        this.pyodide.FS.writeFile(path, content, { encoding: 'utf8' });
    }
}
```

Python 소스 코드는 TypeScript 파일에 문자열 상수로 포함하거나, 별도 `.py` 파일로 관리 후 빌드 시 번들링한다.

**권장**: `engine/marimoShim/` 폴더에 `.py` 파일로 관리 → Vite raw import로 번들링.

```
engine/
├── marimoShim/
│   ├── __init__.py
│   ├── _ui/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── slider.py
│   │   └── ...
│   ├── _output/
│   │   └── ...
│   └── _layout/
│       └── ...
├── executionEngine.ts
└── pyodideEngine.ts
```

### 9.2 위젯 감지 전략

`formatResult()`에서 반환값이 UIElement인지 확인:

```python
# 반환값 검사
result = namespace.get('__eddmlab_result__')
if hasattr(result, '__chani_widget__') or hasattr(result, '_repr_json_'):
    # 위젯 또는 레이아웃 객체
    return result._repr_json_()
```

다중 위젯이 포함된 경우 (mo.md 인터폴레이션):
- HTML 문자열 내 `data-chani-widget` 속성으로 위젯 위치 마킹
- JS 측에서 해당 위치에 Svelte 컴포넌트 동적 마운트

### 9.3 위젯 값 변경 디바운싱

슬라이더 드래그 같은 빈번한 이벤트에 대해:
- 위젯 값 업데이트: 즉시 (UI 반영)
- 셀 재실행 트리거: 300ms 디바운스
- 재실행 중 새 값이 들어오면: 현재 실행 취소 + 새 값으로 재실행

### 9.4 위젯 상태 persist

노트북 저장 시 위젯 현재 값도 함께 저장:

```typescript
interface Cell {
    // 기존 필드...
    widgetStates?: Record<string, unknown>;  // widgetId → value
}
```

노트북 로드 시 위젯 상태 복원:
1. 셀 실행 → 위젯 생성
2. 저장된 widgetStates로 값 복원
3. 복원된 값으로 하위 셀 실행

---

## 10. 디자인 가이드라인

### 10.1 위젯 스타일 원칙

- 모든 위젯은 `tokens.css` CSS 변수 사용
- 다크/라이트 모드 자동 전환
- 컴팩트 디자인 (노트북 셀 안에 자연스럽게 녹아드는 크기)
- 포커스/호버 상태 명확한 시각적 피드백
- 라벨은 위젯 왼쪽 또는 위에 위치

### 10.2 marimo vs ChaniNotebook 디자인 차이

| 요소 | marimo | ChaniNotebook |
|---|---|---|
| 컬러 | 자체 파란색 계열 | zinc 계열 (shadcn) |
| 슬라이더 | 기본 브라우저 + 커스텀 | shadcn Slider 스타일 |
| 버튼 | 자체 디자인 | shadcn Button 스타일 |
| 테이블 | ag-grid 기반 | 자체 DataFrameTable 확장 |
| 레이아웃 | CSS grid | flexbox + tokens.css |
| 다크모드 | 지원 | `data-theme="dark"` 자동 |

### 10.3 위젯 크기 옵션

`full_width` 파라미터 지원:
- `full_width=False` (기본): 위젯 내용에 맞는 크기
- `full_width=True`: 셀 너비 100%

---

## 11. 테스트 시나리오

### 11.1 Phase 1 MVP 검증

```python
# 셀 1
import marimo as mo
slider = mo.ui.slider(1, 100, value=50, label="값 선택")
slider

# 셀 2
print(f"선택된 값: {slider.value}")
result = slider.value ** 2
print(f"제곱: {result}")
```

기대 동작:
1. 셀 1 실행 → 슬라이더 UI 렌더링
2. 셀 2 실행 → "선택된 값: 50", "제곱: 2500" 출력
3. 슬라이더 드래그 → 셀 2 자동 재실행 → 새 값 표시

### 11.2 레이아웃 검증

```python
import marimo as mo

x = mo.ui.slider(0, 10, value=5, label="X")
y = mo.ui.slider(0, 10, value=3, label="Y")
op = mo.ui.dropdown(["더하기", "곱하기"], value="더하기", label="연산")

mo.hstack([x, y, op], gap=1)
```

### 11.3 marimo 파일 호환 검증

1. marimo에서 작성한 `.py` 파일을 ChaniNotebook에서 열기
2. 위젯이 정상 렌더링되고 인터랙션 동작 확인
3. ChaniNotebook에서 수정 후 marimo `.py` 형식으로 내보내기
4. marimo에서 내보낸 파일이 정상 동작하는지 확인

---

## 12. 우선순위 및 일정 추정

| Phase | 범위 | 우선순위 |
|---|---|---|
| Phase 1 | 코어 브릿지 + slider MVP | 최우선 |
| Phase 2 | 기본 입력 위젯 11종 | 높음 |
| Phase 3 | 출력 + 레이아웃 | 중간 |
| Phase 4 | 데이터 위젯 + 컴포지트 | 중간 |
| Phase 5 | 실행 제어 + 파일 호환 | 낮음 (나중) |
| **Phase 6** | **누락 레이아웃 + 추가 위젯** | **중간** |

Phase 1 완료 후 Phase 2~3을 병렬 진행 가능하다. Phase 5의 marimo 파일 호환은 위젯이 충분히 구현된 후에 의미가 있으므로 마지막에 진행한다.

---

## 13. 구현 현황 감사 (2026-02-15 기준)

### 13.1 marimo 공식 API 전수 조사

아래는 marimo 공식 문서(https://docs.marimo.io/api/) 기준 전체 API 목록과 ChaniNotebook 구현 현황이다.
초기 PRD 작성 시 누락된 항목이 다수 존재하며, 이 섹션에서 완전히 기록한다.

### 13.2 입력 위젯 (`mo.ui.*`) — 29종

| # | marimo API | Python shim | Svelte 컴포넌트 | 상태 |
|---|-----------|:-----------:|:---------------:|:----:|
| 1 | `mo.ui.slider` | O | `SliderWidget.svelte` | **완료** |
| 2 | `mo.ui.dropdown` | O | `DropdownWidget.svelte` | **완료** |
| 3 | `mo.ui.text` | O | `TextWidget.svelte` | **완료** |
| 4 | `mo.ui.text_area` | O | `TextAreaWidget.svelte` | **완료** |
| 5 | `mo.ui.number` | O | `NumberWidget.svelte` | **완료** |
| 6 | `mo.ui.checkbox` | O | `CheckboxWidget.svelte` | **완료** |
| 7 | `mo.ui.switch` | O | `SwitchWidget.svelte` | **완료** |
| 8 | `mo.ui.radio` | O | `RadioWidget.svelte` | **완료** |
| 9 | `mo.ui.button` | O | `ButtonWidget.svelte` | **완료** |
| 10 | `mo.ui.run_button` | O | ButtonWidget 재사용 | **완료** |
| 11 | `mo.ui.date` | O | `DateWidget.svelte` | **완료** |
| 12 | `mo.ui.multiselect` | O | `MultiselectWidget.svelte` | **완료** |
| 13 | `mo.ui.range_slider` | O | `RangeSliderWidget.svelte` | **완료** |
| 14 | `mo.ui.file` | O | `FileWidget.svelte` | **완료** |
| 15 | `mo.ui.code_editor` | O | `CodeEditorWidget.svelte` | **완료** |
| 16 | `mo.ui.table` | O | `TableWidget.svelte` | **완료** |
| 17 | `mo.ui.form` | O | `FormWidget.svelte` | **완료** |
| 18 | `mo.ui.dictionary` | O | `DictionaryWidget.svelte` | **완료** |
| 19 | `mo.ui.array` | O | `ArrayWidget.svelte` | **완료** |
| 20 | `mo.ui.batch` | O | `BatchWidget.svelte` | **완료** |
| 21 | `mo.ui.tabs` | O (HTML) | X (HTML 출력 방식) | **부분** |
| 22 | `mo.ui.dataframe` | X | X | **미구현** |
| 23 | `mo.ui.data_explorer` | X | X | **미구현** |
| 24 | `mo.ui.datetime` | X | X | **미구현** |
| 25 | `mo.ui.date_range` | X | X | **미구현** |
| 26 | `mo.ui.file_browser` | X | X | **미구현** |
| 27 | `mo.ui.chat` | X | X | **미구현** |
| 28 | `mo.ui.microphone` | X | X | **미구현** |
| 29 | `mo.ui.refresh` | X | X | **미구현** |

### 13.3 레이아웃 함수 — 17종 (Stateless)

| # | marimo API | 시그니처 | Python shim | Svelte 컴포넌트 | 상태 |
|---|-----------|---------|:-----------:|:---------------:|:----:|
| 1 | `mo.hstack()` | `hstack(items, *, gap, justify, align, widths)` | O (HTML) | X | **부분** |
| 2 | `mo.vstack()` | `vstack(items, *, gap, justify, align, heights)` | O (HTML) | X | **부분** |
| 3 | `mo.accordion()` | `accordion(items, *, multiple, lazy)` | O (HTML) | X | **부분** |
| 4 | `mo.callout()` | `callout(content, *, kind)` | O (HTML) | X | **부분** |
| 5 | `mo.carousel()` | `carousel(items) -> Html` | O (HTML) | X | **완료** |
| 6 | `mo.stat()` | `stat(value, *, label, caption, direction, bordered, target_direction, slot)` | O (HTML) | X | **완료** |
| 7 | `mo.tree()` | `tree(items, *, label)` | O (HTML) | X | **완료** |
| 8 | `mo.center()` | `center(item)` | O (HTML) | X | **완료** |
| 9 | `mo.left()` | `left(item)` | O (HTML) | X | **완료** |
| 10 | `mo.right()` | `right(item)` | O (HTML) | X | **완료** |
| 11 | `mo.plain()` | `plain(item)` | O (HTML) | X | **완료** |
| 12 | `mo.lazy()` | `lazy(item)` | O (HTML) | X | **완료** |
| 13 | `mo.json()` | `json(data)` | O (HTML) | X | **완료** |
| 14 | `mo.sidebar()` | `sidebar(items)` | X | X | **미구현** (범위 밖) |
| 15 | `mo.nav_menu()` | `nav_menu(items)` | X | X | **미구현** (범위 밖) |
| 16 | `mo.outline()` | `outline(items)` | X | X | **미구현** (범위 밖) |
| 17 | `mo.routes()` | `routes(items)` | X | X | **미구현** (범위 밖) |

### 13.4 출력 함수

| # | marimo API | Python shim | 상태 |
|---|-----------|:-----------:|:----:|
| 1 | `mo.md()` | O | **완료** |
| 2 | `mo.Html()` | O | **완료** |
| 3 | `mo.as_html()` | O | **완료** |
| 4 | `mo.image()` | O | **완료** |
| 5 | `mo.video()` | O | **완료** |
| 6 | `mo.audio()` | O | **완료** |

### 13.5 상태/제어 함수

| # | marimo API | Python shim | JS 측 연동 | 상태 |
|---|-----------|:-----------:|:----------:|:----:|
| 1 | `mo.stop()` | O | X (MarimoStopError 감지 미구현) | **부분** |
| 2 | `mo.state()` | O | X (setter→재실행 트리거 미구현) | **부분** |

### 13.6 상태 표시 함수

| # | marimo API | 시그니처 | 상태 |
|---|-----------|---------|:----:|
| 1 | **`mo.status.progress_bar()`** | `progress_bar(collection, *, title, subtitle, total, show_rate, show_eta)` | **미구현** |
| 2 | **`mo.status.spinner()`** | `spinner(*, title, subtitle, remove_on_exit)` | **미구현** |

### 13.7 파서/라이터

| # | 기능 | 파일 | 상태 |
|---|------|------|:----:|
| 1 | marimo `.py` 파서 | `marimoParser.ts` | **완료** |
| 2 | marimo `.py` 라이터 | `marimoWriter.ts` | **완료** |
| 3 | Jupyter `.ipynb` 파서 | `jupyterParser.ts` | **완료** (PRD 외 추가) |
| 4 | Jupyter `.ipynb` 라이터 | `jupyterWriter.ts` | **완료** (PRD 외 추가) |

---

## 14. Phase 6: 누락 레이아웃 + 추가 위젯

초기 PRD에서 누락된 marimo 공식 API를 보완하는 단계.

### Phase 6-A: 핵심 레이아웃 (완료)

| 순서 | 작업 | 설명 | 상태 |
|------|------|------|:----:|
| 6A-1 | `mo.carousel()` | 슬라이드쇼. 이전/다음 네비게이션 + 아이템 순환. Python shim (HTML) | **완료** |
| 6A-2 | `mo.stat()` | 통계 카드 표시. value/label/caption/direction/bordered. Python shim (HTML) | **완료** |
| 6A-3 | `mo.tree()` | 중첩 리스트/딕트/튜플을 트리 구조로 렌더링. details/summary 기반 | **완료** |
| 6A-4 | `mo.json()` | JSON 데이터를 인터랙티브 트리로 표시. tree 내부 함수 재사용 | **완료** |

### Phase 6-B: 정렬/유틸 레이아웃 (완료)

| 순서 | 작업 | 설명 | 상태 |
|------|------|------|:----:|
| 6B-1 | `mo.center()` | CSS `text-align: center` 래퍼 | **완료** |
| 6B-2 | `mo.left()` | CSS `text-align: left` 래퍼 | **완료** |
| 6B-3 | `mo.right()` | CSS `text-align: right` 래퍼 | **완료** |
| 6B-4 | `mo.plain()` | 스타일 없이 raw 출력 | **완료** |
| 6B-5 | `mo.lazy()` | 패스스루 래퍼 (Pyodide 환경 특성상 즉시 렌더) | **완료** |

### Phase 6-C: 추가 위젯 (낮음)

| 순서 | 작업 | 설명 |
|------|------|------|
| 6C-1 | `mo.ui.datetime` | 날짜+시간 선택 |
| 6C-2 | `mo.ui.date_range` | 날짜 범위 선택 |
| 6C-3 | `mo.ui.dataframe` | 인터랙티브 DataFrame 편집 |
| 6C-4 | `mo.ui.data_explorer` | 데이터 탐색 UI |
| 6C-5 | `mo.ui.refresh` | 자동 새로고침 타이머 위젯 |

### Phase 6-D: 범위 밖 (현재 미계획)

아래 기능은 ChaniNotebook의 사용 패턴과 맞지 않아 현재 구현하지 않는다:

| 기능 | 미구현 이유 |
|------|------------|
| `mo.sidebar()` | ChaniNotebook 자체 사이드바 사용 |
| `mo.nav_menu()` | 멀티페이지 앱 기능, 노트북에 불필요 |
| `mo.outline()` | ChaniNotebook 자체 TOC 사용 |
| `mo.routes()` | SPA 라우팅, 노트북에 불필요 |
| `mo.ui.chat` | LLM 채팅 위젯, 별도 기능으로 검토 |
| `mo.ui.microphone` | 오디오 녹음, Pyodide 제약 |
| `mo.ui.file_browser` | 로컬 FS 브라우징, Pyodide 제약 |
| `mo.status.progress_bar()` | Pyodide 단일 스레드에서 실시간 업데이트 제약 |
| `mo.status.spinner()` | 동일 제약 |

---

## 15. `mo.carousel()` 상세 설계

### 15.1 marimo 원본 구현

```python
def carousel(items: Sequence[object]) -> Html:
    item_content = "".join(
        [
            (md(item).text if isinstance(item, str) else as_html(item).text)
            for item in items
        ]
    )
    return Html(
        build_stateless_plugin(
            component_name="marimo-carousel",
            args={},
            slotted_html=item_content,
        )
    )
```

marimo는 `<marimo-carousel>` 웹 컴포넌트를 사용하지만, ChaniNotebook에서는 Python shim + `_repr_html_()` → Svelte 컴포넌트로 구현한다.

### 15.2 ChaniNotebook 구현 방안

**Python shim** (`_layout/carousel.py`):

```python
class Carousel:
    def __init__(self, items):
        self.items = items

    def _repr_html_(self):
        slides = []
        for item in self.items:
            if hasattr(item, '_repr_html_'):
                slides.append(item._repr_html_())
            else:
                slides.append(f'<div>{item}</div>')
        slides_html = ''.join(
            f'<div class="chani-carousel-slide" data-index="{i}">{s}</div>'
            for i, s in enumerate(slides)
        )
        total = len(slides)
        return (
            f'<div class="chani-carousel" data-total="{total}">'
            f'<div class="chani-carousel-track">{slides_html}</div>'
            f'<div class="chani-carousel-nav">'
            f'<button class="chani-carousel-prev" onclick="this.closest(\'.chani-carousel\').dispatchEvent(new CustomEvent(\'prev\'))">&#8249;</button>'
            f'<span class="chani-carousel-counter">1 / {total}</span>'
            f'<button class="chani-carousel-next" onclick="this.closest(\'.chani-carousel\').dispatchEvent(new CustomEvent(\'next\'))">&#8250;</button>'
            f'</div></div>'
        )
```

**Svelte 측**: OutputPanel에서 `chani-carousel` 클래스 감지 시 JS로 이전/다음 슬라이드 전환 처리. 또는 위젯과 동일하게 `<chani-widget>` 태그 방식으로 처리.

### 15.3 UI 스펙

- 이전/다음 화살표 버튼 (좌우)
- 현재 슬라이드 인디케이터 (예: "3 / 7")
- 키보드 좌/우 화살표 지원
- 슬라이드 전환 애니메이션 (CSS transform)
- shadcn zinc 테마 통합

---

## 16. `mo.stat()` 상세 설계

### 16.1 marimo 원본 시그니처

```python
def stat(
    value: str | int | float,
    label: str | None = None,
    caption: str | None = None,
    direction: Literal["increase", "decrease"] | None = None,
    bordered: bool = False,
    target_direction: Literal["increase", "decrease"] | None = "increase",
    slot: Html | None = None,
) -> Html
```

### 16.2 ChaniNotebook 구현 방안

**Python shim** (`_layout/stat.py`):

```python
class Stat:
    def __init__(self, value, label=None, caption=None, direction=None,
                 bordered=False, target_direction="increase", slot=None):
        self.value = value
        self.label = label
        self.caption = caption
        self.direction = direction
        self.bordered = bordered
        self.target_direction = target_direction
        self.slot = slot

    def _repr_html_(self):
        # direction에 따른 화살표 아이콘
        # target_direction과 일치 여부에 따른 색상 (긍정/부정)
        # bordered일 때 border 스타일
        # slot이 있으면 옆에 배치
```

### 16.3 UI 스펙

- 큰 숫자(value) + 작은 라벨(label)
- caption 서브텍스트
- direction 화살표 (↑ increase, ↓ decrease)
- target_direction과 일치하면 긍정색, 불일치면 부정색 (색상 하드코딩 금지, CSS 변수 사용)
- bordered: 1px solid border 카드
