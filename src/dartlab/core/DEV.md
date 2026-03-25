# Core — 데이터 로딩 + 레지스트리 + 설정

## 구조

```
core/
├── registry.py        # 단일 진실의 원천 (DataEntry 목록)
├── _entries.py        # 44개 모듈 정의
├── capabilities.py    # AI capability 레지스트리
├── constants.py       # 상수
├── dataConfig.py      # HuggingFace 데이터셋 URL 중앙 설정
├── dataLoader.py      # parquet 다운로드 + 캐싱
├── memory.py          # 메모리 모니터링 (Polars용)
├── plugins.py         # 플러그인 시스템
├── resolve.py         # 종목 이름 → 코드 (strict/fuzzy)
├── tableParser.py     # 공시 테이블 → DataFrame 파싱
├── notesExtractor.py  # K-IFRS 주석 파싱
├── reportSelector.py  # 정기보고서 선택 로직
└── ai/                # AI 설정
    ├── providers.py   # 7개 LLM provider 설정
    ├── secrets.py     # API 키 관리
    ├── detect.py      # 질문 분류
    ├── routing.py     # provider 선택 로직
    ├── guide.py       # 설정 가이드
    └── profile.py     # AI 프로필 관리
```

## 핵심 원칙

1. **registry = 단일 진실의 원천**: `DataEntry` 목록이 모든 모듈 메타데이터의 기준
2. **자동 생성**: `scripts/generateSpec.py`가 registry → API_SPEC.md, llms.txt, reference.md 생성
3. **registry 직접 수정 금지**: API_SPEC.md 등은 직접 수정하지 않고 generateSpec.py로만 생성

## registry 소비처 (7곳)

```
core/registry.py (DataEntry)
  ├── Company property dispatch
  ├── Excel export (시트 생성)
  ├── LLM tools (도구 바인딩)
  ├── Server API (/api/spec)
  ├── Skills (reference.md)
  ├── API_SPEC.md
  └── llms.txt
```

## capabilities 체계

- `CapabilityKind`: DATA / ANALYSIS / WORKFLOW / UI_ACTION / CODING / SYSTEM
- `CapabilityChannel`: CHAT / MCP / CLI / UI
- `WidgetSpec`: AI 렌더링용 위젯 정의

## 데이터 릴리즈 Config

- `DATA_RELEASES` dict가 HuggingFace 데이터셋 디렉토리/라벨 중앙 관리
- 단건: `_download(stockCode)` → HF에서 개별 parquet (ETag 캐시)
- 전체: `downloadAll(category)` → `huggingface_hub` `snapshot_download` (resume/병렬)
- 변경 시 `dataConfig.py` + `landing/src/lib/brand.ts` 2곳만 수정

## 메모리 안전

- `check_memory_and_gc()`: Polars 힙은 Python gc.collect()로 회수 불가
- `BoundedCache`: 무제한 dict 대신 사용 (pressure_mb=800)
- 1200MB 초과 시 conftest.py에서 pytest.exit()
