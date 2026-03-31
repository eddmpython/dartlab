# 코드 규칙

dartlab 전체에 적용되는 코드 스타일, 독스트링, 테스트, 릴리즈 규칙.

## 네이밍

- 기존 코드의 네이밍 패턴을 따른다
- 이동된 기존 snake_case는 하위호환 유지 (shim)
- **최신 먼저 역순** — 데이터 정렬 기본값

## 독스트링 9섹션

공개 API 함수는 아래 구조를 따른다:

```python
def analysis(axis: str, company: Company) -> dict:
    """수익구조 분석.

    축별 재무 데이터를 구조화하여 스토리 데이터로 변환한다.

    Parameters
    ----------
    axis : str
        분석 축 이름 (예: "수익구조", "수익성").
    company : Company
        분석 대상 기업.

    Returns
    -------
    dict
        분석 결과. 키별 금액/비율/YoY/플래그.

    Raises
    ------
    ValueError
        알 수 없는 축 이름.

    Examples
    --------
    >>> c.analysis("수익구조")

    Notes
    -----
    basePeriod로 기준 기간 지정 가능.

    Guide
    -----
    인자 없이 호출하면 사용 가능한 축 목록을 안내한다.

    See Also
    --------
    review : analysis 결과를 보고서로 조립.
    insight : 등급 카드 요약.
    """
```

9섹션: Summary, Description, Parameters, Returns, Raises, Examples, Notes, Guide, See Also

## CAPABILITIES — 단일 진실의 원천

```
5 surface (Python API, CLI, Server, Data Modules, AI Tools)
    ↓ scripts/generateSpec.py (코드에서 자동 수집)
    ├── CAPABILITIES.md                  (루트 총괄 스펙맵)
    ├── landing/static/llms.txt          (AI 크롤러용)
    └── .claude/skills/dartlab/reference.md (Claude Code 스킬)
```

- **CAPABILITIES.md, llms.txt, reference.md는 직접 수정하지 않는다** → `scripts/generateSpec.py`로만 생성
- 모듈 추가/변경 시: `uv run python scripts/generateSpec.py` 실행
- 릴리즈 전 반드시 실행하여 문서-코드 동기화 확인
- "없다/범위밖" 판단 전에 CAPABILITIES 먼저 확인한다
- registry 소비처: Company property, Excel export, LLM tool, Server API, Skills, CAPABILITIES, llms.txt (7곳)

## 문서/생성물 정합성

- 공개 문서, 스펙, 생성물은 모두 같은 구조를 말해야 한다
- 문서와 코드가 충돌하면 **코드 구조를 기준**으로 문서를 즉시 맞춘다
- 공개 문서에서 내부 클래스명(`DartCompany`, `EdgarCompany` 등) 노출하지 않는다

## 예외 처리

- 구체적 예외 타입을 명시한다 (`except Exception:` 대신 `except ValueError:` 등)
- 사용자 입력 검증은 early return으로 처리
- 에러를 삼키지 않는다

## 테스트

- `test-lock.sh` 필수, 그룹별 분리 실행 (unit → integration → heavy)
- GPU/Ollama 의존 테스트는 mock
- fixture scope는 `module` (session scope 사용하지 않는다)
- 전 기간 데이터로 테스트한다

## 릴리즈

- semver 준수 (구조 변경 = minor, 패치 = patch)
- GitHub Actions trusted publishing
- 절차: `pyproject.toml` 버전 → 커밋 → `git tag vX.Y.Z && git push origin vX.Y.Z`
- CHANGELOG.md + docs/changelog.md 동시 업데이트 (상세하게 — GitHub Release 노트로 사용)

## Git

- AI 흔적 커밋 메시지/코드/주석에 포함하지 않는다 (pre-commit hook 자동 차단)
- 커밋 메시지는 한국어 또는 영어
- force push 하지 않는다
