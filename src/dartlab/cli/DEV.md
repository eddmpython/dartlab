# CLI 개발 문서

## 구조

```
cli/
├── main.py          # 엔트리포인트 (dartlab 명령어)
├── parser.py        # argparse 빌더, COMMAND_SPECS 등록
├── context.py       # CommandSpec, DEPRECATED_ALIASES
├── commands/        # 서브커맨드 모듈 (1파일 = 1커맨드)
│   ├── ask.py       # LLM 질의
│   ├── collect.py   # DART 공시문서 수집
│   ├── excel.py     # Excel 내보내기
│   ├── mcp.py       # MCP 서버
│   ├── modules.py   # 모듈 목록
│   ├── profile.py   # company index/facts
│   ├── report.py    # 분석 보고서 생성
│   ├── search.py    # 종목 검색
│   ├── sections.py  # docs sections 출력
│   ├── setup.py     # provider 설치 안내
│   ├── show.py      # topic 데이터 조회
│   ├── statement.py # 재무제표 출력
│   ├── status.py    # LLM 연결 상태
│   └── ai.py        # AI 웹 인터페이스
└── services/        # 공통 유틸 (출력, provider 감지, runtime)
```

## 커맨드 추가 방법

1. `commands/` 아래에 파일 생성 (예: `foo.py`)
2. `configure_parser(subparsers)` + `run(args)` 구현
3. `parser.py`의 `COMMAND_SPECS`에 `CommandSpec("foo", "dartlab.cli.commands.foo")` 추가
4. `test_cli.py`의 커맨드 목록 문자열 업데이트

## collect 커맨드

DART 공시문서를 직접 크롤링하여 parquet로 저장. 기존 eddmpython DartDocs.py를 포팅.

### 핵심 구조

- **collector 본체**: `engines/dart/openapi/collector.py` (DartClient 재사용)
- **CLI 래퍼**: `commands/collect.py`

### 명령어 매핑 (eddmpython → dartlab)

| 용도 | eddmpython | dartlab |
|------|-----------|---------|
| 단일 종목 | `slow 005930 5` | `dartlab collect 005930 -q 5` |
| 여러 종목 | `slow 005930,000660 8` | `dartlab collect 005930 000660 -q 8` |
| 미수집 자동 | `slow-auto 코스피 10 50` | `dartlab collect --auto --limit 50 -q 10` |
| 대형주 50분기 | `slow-top100 50 200` | `dartlab collect --auto --limit 200 -q 50` |
| 사업보고서만 | — | `dartlab collect 005930 --annual-only` |
| 수집 현황 | `stats` | `dartlab collect --stats` |
| 미수집 목록 | `uncollected 코스피 20` | `dartlab collect --uncollected --limit 20` |

### 딜레이 옵션

- `--min-delay` / `--max-delay`: 요청 간 랜덤 대기 (기본 5~10초)
- IP 차단 방지를 위해 반드시 딜레이 유지
- 종목 간 대기: collectMultiple 내부에서 30~60초 랜덤

### 데이터 흐름

```
DART API (DartClient.getDf → listFilings)
  ↓ 공시 목록 (rcept_no)
DART 웹사이트 (requests.get)
  ↓ 하위 섹션 URL 파싱 (정규식)
DART viewer (requests.get)
  ↓ HTML → 텍스트 변환 (BeautifulSoup + 마크다운)
Polars DataFrame
  ↓ parquet 원자적 교체
{dataDir}/dart/docs/{stockCode}.parquet
```

### 출력 parquet 스키마 (11 컬럼)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| corp_code | String | DART 기업코드 |
| corp_name | String | 회사명 |
| stock_code | String | 종목코드 |
| year | String | 공시 연도 |
| rcept_date | String | 접수일 (YYYYMMDD) |
| rcept_no | String | 공시번호 (고유 ID) |
| report_type | String | 보고서 유형 |
| section_order | Int64 | 섹션 순번 |
| section_title | String | 섹션 제목 |
| section_url | String | DART viewer URL |
| section_content | String | 추출된 텍스트 |

기존 GitHub Release의 docs parquet과 동일한 스키마.

### 의존성

- `requests` (동기 HTTP) — 프록시 없이 직접 크롤링
- `beautifulsoup4` + `lxml` (HTML 파싱)
- `alive-progress` (진행률 표시)
- 전부 pyproject.toml 기존 의존성

### API 키

`DartClient`를 재사용하므로 openapi 체계 그대로:
- 환경변수 `DART_API_KEY` 또는 `DART_API_KEYS`
- `Dart(apiKey="...")` 또는 `.dartlab.yml`
