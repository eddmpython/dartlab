# DartLab for Visual Studio Code

DART 전자공시 & EDGAR AI 기업분석 — VS Code에서 바로.

AI-powered financial analysis for Korean (DART) and US (EDGAR) public companies, directly inside VS Code.

---

## 주요 기능

### AI 기업분석 채팅

종목코드 하나로 재무제표, 지배구조, 밸류에이션까지 — 자연어로 질문하면 AI가 실시간 데이터를 가져와 분석합니다.

- **종목코드 하나면 끝** — `005930` 입력하면 재무·공시·시장 데이터를 자동 수집
- **코드 실행** — AI가 Python 코드를 작성하고 실행하여 테이블과 차트를 생성
- **14축 재무분석** — 수익성, 안정성, 성장성, 현금흐름, 신용평가 등
- **스트리밍 응답** — 도구 실행 과정이 Claude Code 스타일로 실시간 표시

### AI Provider

무료 Provider 포함, 원하는 AI를 선택할 수 있습니다:

| Provider | 비용 | 비고 |
|----------|------|------|
| Gemini | 무료 | Gemini 2.5 Pro/Flash |
| Groq | 무료 | LLaMA 3.3 70B |
| Cerebras | 무료 | LLaMA 3.3 70B |
| Mistral | 무료 | Mistral Small |
| OpenAI | 유료 | GPT-4o |
| Ollama | 무료 | 로컬 실행 |

### 채팅 인터페이스

- **슬래시 커맨드** — `/new`, `/clear`, `/model`, `/provider`, `/help`
- **모듈 선택** — financial, growth, valuation, risk 등 분석 모듈 지정
- **관심종목** — 자주 분석하는 종목을 워치리스트에 저장
- **대화 관리** — 검색, 이름변경, 그룹 분류, 이어서 대화
- **입력 히스토리** — 방향키(↑↓)로 이전 질문 탐색

### MCP 통합

DartLab은 MCP 서버로 자동 등록되어, Claude Code · GitHub Copilot 등 MCP 호환 클라이언트에서 DartLab 도구를 바로 사용할 수 있습니다.

---

## 설치

1. **dartlab** Python 패키지 설치:
   ```
   pip install dartlab
   ```
2. VS Code에서 **DartLab** 확장 설치
3. Activity Bar의 DartLab 아이콘 클릭 (또는 `Ctrl+Shift+D`)
4. AI Provider 선택 (무료 옵션 있음)
5. 종목코드 또는 질문 입력 → 분석 시작

**요구사항:** Python 3.12+

확장이 Python 환경을 자동 감지합니다. 실패 시 `설정 > DartLab > Python Path`에서 직접 지정.

## 단축키

| 단축키 | 동작 |
|--------|------|
| `Ctrl+Shift+D` | DartLab 채팅 열기 |
| `Ctrl+N` | 새 대화 (패널 포커스 시) |
| `↑/↓` | 입력 히스토리 탐색 |

## 설정

| 설정 | 설명 | 기본값 |
|------|------|--------|
| `dartlab.pythonPath` | Python 실행 경로 | 자동 감지 |
| `dartlab.autoStart` | 활성화 시 자동 시작 | `true` |

## 데이터 소스

- **DART** — 한국 전자공시 (stable)
- **EDGAR** — 미국 SEC 공시 (beta)

모든 데이터는 공식 소스에서 실시간 수집. 기본 사용에 API 키 불필요.

## 링크

- [Documentation](https://eddmpython.github.io/dartlab/)
- [GitHub](https://github.com/eddmpython/dartlab)
- [PyPI](https://pypi.org/project/dartlab/)
- [Blog](https://eddmpython.github.io/dartlab/blog)
- [Issues](https://github.com/eddmpython/dartlab/issues)

## License

MIT
