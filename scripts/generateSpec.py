"""registry 기반 자동 문서 생성.

registry.py (단일 진실의 원천)에서 다음 파일을 자동 생성한다:
- src/dartlab/API_SPEC.md  — 개발자용 API 레퍼런스
- landing/static/llms.txt  — AI 크롤러용 구조화 문서
- .claude/skills/dartlab/reference.md — Claude Code 스킬 레퍼런스

실행:
    uv run python scripts/generateSpec.py

릴리즈 시 CI에서 자동 실행하여 수동 관리 포인트를 제거한다.
"""

from __future__ import annotations

import dataclasses
import sys
import textwrap
from pathlib import Path
from typing import get_type_hints

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dartlab.core.registry import DataEntry, getCategories, getEntries


def _inspectDataclass(cls: type) -> list[tuple[str, str, str]]:
    """dataclass의 (필드명, 타입, docstring근사) 목록 반환."""
    rows = []
    hints = get_type_hints(cls)
    for f in dataclasses.fields(cls):
        typeName = hints.get(f.name, "")
        if hasattr(typeName, "__name__"):
            typeName = typeName.__name__
        else:
            typeName = str(typeName).replace("typing.", "")
        defaultStr = ""
        if f.default is not dataclasses.MISSING:
            defaultStr = str(f.default)
        elif f.default_factory is not dataclasses.MISSING:
            defaultStr = "[]" if "list" in typeName.lower() else "{}"
        rows.append((f.name, typeName, defaultStr))
    return rows


def _dataclassTable(cls: type, title: str) -> str:
    """dataclass를 마크다운 테이블로."""
    rows = _inspectDataclass(cls)
    lines = [f"### {title}\n"]
    doc = cls.__doc__
    if doc:
        lines.append(f"{doc.strip()}\n")
    lines.append("| 필드 | 타입 | 기본값 |")
    lines.append("|------|------|--------|")
    for name, typ, default in rows:
        lines.append(f"| `{name}` | `{typ}` | {default} |")
    lines.append("")
    return "\n".join(lines)


def _categoryLabel(cat: str) -> str:
    labels = {
        "finance": "시계열 재무제표",
        "report": "공시 파싱 모듈",
        "disclosure": "서술형 공시",
        "notes": "K-IFRS 주석",
        "raw": "원본 데이터",
        "analysis": "분석 엔진",
    }
    return labels.get(cat, cat)


def _entryRow(e: DataEntry) -> str:
    """단일 엔트리를 마크다운 테이블 행으로."""
    return f"| `{e.name}` | {e.label} | `{e.dataType}` | {e.description} |"


def _registrySection() -> str:
    """registry 엔트리를 카테고리별 테이블로."""
    lines = ["## 데이터 레지스트리\n"]
    lines.append("`core/registry.py`에 등록된 전체 데이터 소스 목록.\n")
    lines.append("모듈 추가 = registry에 DataEntry 한 줄 추가 → Company, Excel, LLM, Server, Skills 전부 자동 반영.\n")

    for cat in getCategories():
        entries = getEntries(category=cat)
        lines.append(f"### {_categoryLabel(cat)} ({cat})\n")
        lines.append("| name | label | dataType | description |")
        lines.append("|------|-------|----------|-------------|")
        for e in entries:
            lines.append(_entryRow(e))
        lines.append("")
    return "\n".join(lines)


def _dataclassesSection() -> str:
    """주요 dataclass 스키마."""
    lines = ["## 주요 데이터 타입\n"]

    from dartlab.engines.common.finance.ratios import RatioResult

    lines.append(_dataclassTable(RatioResult, "RatioResult"))

    from dartlab.engines.analysis.insight.types import AnalysisResult, Anomaly, Flag, InsightResult

    lines.append(_dataclassTable(InsightResult, "InsightResult"))
    lines.append(_dataclassTable(Anomaly, "Anomaly"))
    lines.append(_dataclassTable(Flag, "Flag"))
    lines.append(_dataclassTable(AnalysisResult, "AnalysisResult"))

    from dartlab.engines.analysis.sector.types import SectorInfo, SectorParams

    lines.append(_dataclassTable(SectorInfo, "SectorInfo"))
    lines.append(_dataclassTable(SectorParams, "SectorParams"))

    from dartlab.engines.analysis.rank.rank import RankInfo

    lines.append(_dataclassTable(RankInfo, "RankInfo"))

    return "\n".join(lines)


def _companySection() -> str:
    """Company facade + 엔진 Company 사용법."""
    return textwrap.dedent("""\
    ## Company (통합 facade)

    입력을 자동 판별하여 DART 또는 EDGAR 시장 전용 Company를 생성한다.
    현재 DART Company의 공개 진입점은 **index → show(topic) → trace(topic)** 이다.
    `profile`은 향후 terminal/notebook 문서형 보고서 뷰로 확장될 예정이다.

    ```python
    import dartlab

    kr = dartlab.Company("005930")
    kr = dartlab.Company("삼성전자")
    us = dartlab.Company("AAPL")

    kr.market                    # "KR"
    us.market                    # "US"
    ```

    ### 판별 규칙

    | 입력 | 결과 | 예시 |
    |------|------|------|
    | 6자리 숫자 | DART Company | `Company("005930")` |
    | 한글 포함 | DART Company | `Company("삼성전자")` |
    | 영문 1~5자리 | EDGAR Company | `Company("AAPL")` |

    ## DART Company

    ### 현재 공개 진입점

    | surface | 설명 |
    |---------|------|
    | `index` | 회사 데이터 구조 인덱스 DataFrame |
    | `show(topic)` | topic의 실제 데이터 payload 조회 |
    | `trace(topic, period)` | docs / finance / report source provenance 조회 |
    | `docs` | pure docs source namespace |
    | `finance` | authoritative finance source namespace |
    | `report` | authoritative structured disclosure source namespace |
    | `profile` | 향후 보고서형 렌더용 예약 뷰 |

    ### 정적 메서드

    | 메서드 | 반환 | 설명 |
    |--------|------|------|
    | `dartlab.engines.company.dart.Company.listing()` | DataFrame | KRX 전체 상장법인 목록 |
    | `dartlab.engines.company.dart.Company.search(keyword)` | DataFrame | 회사명 부분 검색 |
    | `dartlab.engines.company.dart.Company.status()` | DataFrame | 로컬 보유 전체 종목 인덱스 |
    | `dartlab.engines.company.dart.Company.resolve(codeOrName)` | str \\| None | 종목코드/회사명 → 종목코드 |

    ### 핵심 property

    | property | 반환 | 설명 |
    |----------|------|------|
    | `BS` | DataFrame | 재무상태표 |
    | `IS` | DataFrame | 손익계산서 |
    | `CIS` | DataFrame | 포괄손익계산서 |
    | `CF` | DataFrame | 현금흐름표 |
    | `SCE` | tuple \\| DataFrame | 자본변동표 |
    | `sections` | DataFrame | merged topic x period company table |
    | `timeseries` | (series, periods) | 분기별 standalone 시계열 |
    | `annual` | (series, years) | 연도별 시계열 |
    | `ratios` | RatioResult | 재무비율 |
    | `index` | DataFrame | 회사 구조 인덱스 |
    | `docs` | Accessor | pure docs source |
    | `finance` | Accessor | authoritative finance source |
    | `report` | Accessor | authoritative report source |
    | `profile` | _BoardView | 향후 보고서형 뷰 예약 |
    | `sector` | SectorInfo | 섹터 분류 |
    | `insights` | AnalysisResult | 7영역 인사이트 등급 |
    | `rank` | RankInfo | 시장 순위 |
    | `notes` | Notes | K-IFRS 주석 접근 |
    | `market` | str | `"KR"` |

    ### 메서드

    | 메서드 | 반환 | 설명 |
    |--------|------|------|
    | `get(name)` | Result | 모듈 전체 Result 객체 |
    | `all()` | dict | 전체 데이터 dict |
    | `show(topic, period=None, raw=False)` | Any | topic payload 조회 |
    | `trace(topic, period=None)` | dict \\| None | 선택 source provenance 조회 |
    | `fsSummary(period)` | AnalysisResult | 요약재무정보 |
    | `getTimeseries(period, fsDivPref)` | (series, periods) | 커스텀 시계열 |
    | `getRatios(fsDivPref)` | RatioResult | 커스텀 비율 |

    `index`는 회사 전체 구조를 먼저 보여주고, `show(topic)`가 실제 데이터를 연다.
    `trace(topic)`는 같은 topic에서 docs / finance / report 중 어떤 source가 채택됐는지 설명한다.
    docs가 없는 회사는 `docsStatus` 안내 row와 `현재 사업보고서 부재` notice가 표시된다.

    report/disclosure property는 registry에서 자동 디스패치된다 (`_MODULE_REGISTRY`).
    등록된 모든 property는 아래 "데이터 레지스트리" 섹션 참조.

    ## EDGAR Company

    ```python
    import dartlab

    us = dartlab.Company("AAPL")
    us.ticker                    # "AAPL"
    us.cik                       # "0000320193"
    ```

    ### property

    | property | 반환 | 설명 |
    |----------|------|------|
    | `timeseries` | (series, periods) | 분기별 standalone 시계열 |
    | `annual` | (series, years) | 연도별 시계열 |
    | `ratios` | RatioResult | 재무비율 |
    | `insights` | AnalysisResult | 7영역 인사이트 등급 |
    | `market` | str | `"US"` |
    """)


def _header(title: str, description: str) -> str:
    return f"# {title}\n\n{description}\n\n"


def generateApiSpec() -> str:
    """API_SPEC.md 생성."""
    parts = [
        _header(
            "dartlab API 스펙", "이 문서는 `scripts/generateSpec.py`에 의해 자동 생성됩니다. 직접 수정하지 마세요."
        ),
        _companySection(),
        _registrySection(),
        _dataclassesSection(),
    ]
    return "\n---\n\n".join(parts)


def generateLlmsTxt() -> str:
    """llms.txt 생성 — AI 크롤러용."""
    lines = [
        "# DartLab — DART + EDGAR Disclosure Analysis Python Library",
        "",
        "> Turn Korean DART and US SEC EDGAR filings into one structured company map.",
        "> 한국 DART 전자공시와 미국 SEC EDGAR 공시를 하나의 회사 맵으로 바꾸는 Python 라이브러리.",
        "",
        "DartLab parses corporate disclosure filings — annual reports, 10-K, 10-Q — into structured,",
        "comparable data. Financial statements (BS/IS/CF), 47 financial ratios, 7-area insight grades,",
        "narrative text, and structured reports are all accessible with a single stock code.",
        "Covers 2,700+ Korean listed companies and 970+ US companies.",
        "",
        "## Install",
        "",
        "```bash",
        "pip install dartlab",
        "# or",
        "uv add dartlab",
        "```",
        "",
        "## Quick Start",
        "",
        "```python",
        "import dartlab",
        "",
        "# Korean company (DART)",
        'c = dartlab.Company("005930")       # Samsung Electronics',
        "c.index                              # company structure index",
        'c.show("BS")                         # balance sheet',
        'c.show("executiveCompensation")      # topic payload',
        'c.trace("dividend")                  # source provenance',
        "c.ratios                             # 47 financial ratios",
        "c.insights                           # 7-area A~F grades",
        "",
        "# US company (EDGAR)",
        'us = dartlab.Company("AAPL")         # Apple Inc.',
        "us.BS                                # balance sheet",
        "us.ratios                            # financial ratios",
        "us.sections                          # 10-K sections map",
        "```",
        "",
        "## Key Features",
        "",
        "- **Sections-first architecture**: Every company becomes a topic × period DataFrame",
        "- **Dual market**: DART (Korea) + EDGAR (US) with identical interface",
        "- **One stock code**: `dartlab.Company('005930')` or `dartlab.Company('AAPL')`",
        "- **Financial statements**: BS, IS, CF, CIS, SCE — XBRL-normalized, quarterly standalone",
        "- **47 financial ratios**: ROE, ROA, operating margin, debt ratio, PER, PBR, FCF, etc.",
        "- **7-area insight grades**: Performance, profitability, stability, cash flow, governance, risk, opportunity",
        "- **AI analysis**: `dartlab ask '삼성전자 분석해줘'` — natural language company analysis",
        "- **MCP server**: Expose company data as MCP tools for Claude Desktop, ChatGPT, Cursor",
        "- **329 topics per company**: From dividend policy to segment breakdown",
        "",
        "## Data Modules",
        "",
    ]

    for cat in getCategories():
        entries = getEntries(category=cat)
        lines.append(f"### {_categoryLabel(cat)}")
        lines.append("")
        for e in entries:
            lines.append(f"- **{e.name}** ({e.label}): {e.description}")
        lines.append("")

    lines.extend(
        [
            "## Analysis Engines",
            "",
            "- **Sector classification**: WICS 11 sectors (override → keyword → KSIC 3-stage)",
            "- **Insight grades**: 7-area A~F grades (performance, profitability, stability, cash flow, governance, risk, opportunity)",
            "- **Market rank**: Revenue/assets/growth ranking — overall + within sector",
            "- **Financial ratios**: ROE, ROA, operating margin, debt ratio, PER, PBR, FCF — auto-calculated",
            "- **Supply chain**: Disclosed supplier/customer relationship mapping",
            "- **ESG**: ESG disclosure extraction and scoring",
            "- **Event study**: Abnormal return around disclosure dates",
            "",
            "## Links",
            "",
            "- Documentation: https://eddmpython.github.io/dartlab/docs/",
            "- GitHub: https://github.com/eddmpython/dartlab",
            "- PyPI: https://pypi.org/project/dartlab/",
            "- Demo: https://huggingface.co/spaces/eddmpython/dartlab",
            "",
        ]
    )

    return "\n".join(lines)


def generateSkillRef() -> str:
    """Claude Code 스킬용 reference.md 생성."""
    parts = [
        _header("dartlab API Reference (Skills용)", "이 문서는 `scripts/generateSpec.py`에 의해 자동 생성됩니다."),
        _companySection(),
        _registrySection(),
        _dataclassesSection(),
    ]
    return "\n---\n\n".join(parts)


def main():
    apiSpecPath = ROOT / "src" / "dartlab" / "API_SPEC.md"
    llmsTxtPath = ROOT / "landing" / "static" / "llms.txt"
    skillRefPath = ROOT / ".claude" / "skills" / "dartlab" / "reference.md"

    skillRefPath.parent.mkdir(parents=True, exist_ok=True)

    apiSpec = generateApiSpec()
    apiSpecPath.write_text(apiSpec, encoding="utf-8")
    print(f"  API_SPEC.md  ({len(apiSpec):,} chars) → {apiSpecPath}")

    llmsTxt = generateLlmsTxt()
    llmsTxtPath.write_text(llmsTxt, encoding="utf-8")
    print(f"  llms.txt     ({len(llmsTxt):,} chars) → {llmsTxtPath}")

    skillRef = generateSkillRef()
    skillRefPath.write_text(skillRef, encoding="utf-8")
    print(f"  reference.md ({len(skillRef):,} chars) → {skillRefPath}")

    print("\n  완료.")


if __name__ == "__main__":
    main()
