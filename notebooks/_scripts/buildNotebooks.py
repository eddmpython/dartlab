"""Generate expanded colab + marimo notebooks for all 11 engines.

Plan v10 P11 — notebook 동기화. 사용자 surface 만 사용 (panel/select/sections/...).
"""

import json
from pathlib import Path

ROOT = Path("notebooks")

NOTEBOOKS = {
    "01_company": [
        ("md", "# Company\n\npanel 사상 — `c.panel` 을 잡는 순간 항목×기간 격자. 모든 공시/재무에 단일 표면."),
        ("code", "%pip install -q dartlab"),
        ("code", 'import dartlab\nc = dartlab.Company("005930")\nc.corpName'),
        ("md", "## 격자 + 행 검색"),
        ("code", "# 전체 공시 수평화 격자 (항목 × 기간)\nc.panel()"),
        ("code", '# 항목명 행 검색 (raw 공시)\nc.panel("매출")'),
        ("md", "## native 재무제표 (소문자) / finance (대문자)"),
        ("code", '# native 손익 — 사업보고서 항목 그대로, XBRL+옛 통합 (2013~)\nc.panel("is", freq="year")'),
        ("code", '# finance 손익 — XBRL 정규화 숫자\nc.panel("IS", freq="year")'),
        ("md", "## native 재무비율 (소문자) / finance 비율 (대문자)"),
        ("code", '# native 비율 — 5표 항목으로 계산 (깊은 history)\nc.panel("ratios")'),
        ("code", '# finance 비율\nc.panel("RATIOS")'),
        ("md", "## 공시 / 본문 검색"),
        ("code", "c.filings().head(10)"),
        ("code", '# 본문 전체 검색\nc.panel.search("재고")'),
    ],
    "02_gather": [
        ("md", "# Gather\n\n외부 시장 데이터 수집 — 주가/매크로/뉴스/수급."),
        ("code", "%pip install -q dartlab"),
        ("code", "import dartlab\ndartlab.gather()"),
        ("md", "## 주가"),
        ("code", 'dartlab.gather("price", "005930")'),
        ("code", 'dartlab.gather("price", "KOSPI")'),
        ("md", "## 매크로"),
        ("code", 'dartlab.gather("macro")'),
        ("md", "## 수급 (KR 전용)"),
        ("code", '# 최근 수급 (기본 5거래일)\ndartlab.gather("flow", "005930")'),
        (
            "code",
            '# 2010년부터 최신 거래일까지 — 자동 페이지네이션\ndartlab.gather(\n    "flow",\n    "005930",\n    start="2010-01-04",\n    sleepSec=1.0,\n)',
        ),
        (
            "code",
            '# 가능한 전체 이력은 오래 걸릴 수 있어 필요할 때만 실행:\n# dartlab.gather("flow", "005930", all=True, sleepSec=1.0)\n# 여러 종목은 종목 단위 병렬 수집:\n# dartlab.gather("flow", targets=["005930", "000660"], limit=30, parallel=2)\n# 사용자 프록시가 필요하면 병렬 수집에도 같은 호출 범위로 적용:\n# dartlab.gather("flow", targets=["005930", "000660"], limit=30, parallel=2, proxy="http://user:pass@host:port")',
        ),
        ("md", "## 뉴스"),
        ("code", 'dartlab.gather("news", "삼성전자")'),
    ],
    "03_scan": [
        ("md", "# Scan\n\n전 종목 횡단 분석 — 시장 전체를 한 번에. 13축."),
        ("code", "%pip install -q dartlab"),
        ("code", "import dartlab\ndartlab.scan()"),
        ("md", "## 수익성 횡단"),
        ("code", 'dartlab.scan("profitability")'),
        ("md", "## 지배구조"),
        ("code", 'dartlab.scan("governance")'),
        ("md", "## 부채/리스크"),
        ("code", 'dartlab.scan("debt")'),
    ],
    "04_quant": [
        ("md", "# Quant\n\n주가 기술적 분석 — 25지표 + 9신호."),
        ("code", "%pip install -q dartlab"),
        ("code", 'import dartlab\nc = dartlab.Company("005930")\nc.quant()'),
        ("md", "## 종합 판단"),
        ("code", 'c.quant("종합")'),
        ("md", "## 모멘텀 / RSI"),
        ("code", 'c.quant("모멘텀")'),
    ],
    "05_analysis": [
        ("md", "# Analysis\n\n14축 재무 분석 + forecast + valuation. 6막 인과 구조."),
        ("code", "%pip install -q dartlab"),
        ("code", 'import dartlab\nc = dartlab.Company("005930")\nc.analysis()'),
        ("md", "## financial 그룹"),
        ("code", 'c.analysis("수익성")'),
        ("code", 'c.analysis("성장성")'),
        ("code", 'c.analysis("안정성")'),
        ("code", 'c.analysis("현금흐름")'),
        ("md", "## forecast / valuation"),
        ("code", 'c.analysis("매출전망")'),
        ("code", 'c.analysis("가치평가")'),
    ],
    "06_macro": [
        ("md", "# Macro\n\n시장 레벨 매크로 해석 — 사이클/금리/자산/심리/유동성."),
        ("code", "%pip install -q dartlab"),
        ("code", "import dartlab\ndartlab.macro()"),
        ("code", 'dartlab.macro("사이클")'),
        ("code", 'dartlab.macro("금리")'),
    ],
    "07_credit": [
        ("md", "# Credit\n\n독립 신용평가 엔진 — 7축 dCR 등급."),
        ("code", "%pip install -q dartlab"),
        ("code", 'import dartlab\nc = dartlab.Company("005930")\nc.credit()'),
        ("code", 'c.credit("등급")'),
        ("code", 'c.credit("수익성")'),
        ("code", 'c.credit("부채")'),
    ],
    "08_story": [
        ("md", "# Story\n\n4엔진 조립 보고서 — analysis + credit + macro + quant. 6막 서사."),
        ("code", "%pip install -q dartlab"),
        ("code", 'import dartlab\nc = dartlab.Company("005930")'),
        ("md", "## 단일 섹션 (메모리 안전 — 추천)"),
        ("code", 'print(c.story("수익성").toMarkdown())'),
        ("code", 'print(c.story("성장성").toMarkdown())'),
        ("md", "## AI 종합의견은 dartlab.ask() 로"),
        ("code", '# dartlab.ask("삼성전자 반도체 사이클 관점에서 평가해줘")'),
    ],
    "09_ai": [
        ("md", "# AI\n\nLLM 기반 적극적 분석가. dartlab 엔진을 도구로 호출."),
        ("code", "%pip install -q dartlab"),
        (
            "code",
            '# import dartlab\n# AI provider 키 필요 (GEMINI_API_KEY, GROQ_API_KEY 등)\n# dartlab.ask("삼성전자 수익성 분석해줘")',
        ),
        ("code", '# Company-bound 대화\n# dartlab.chat("005930", "배당 추세는?")'),
    ],
    "10_search": [
        ("md", "# Search\n\n전체 공시 원문 검색 — stem ID 역인덱스. 모델 불필요, cold start 0ms."),
        ("code", "%pip install -q dartlab"),
        ("code", 'import dartlab\ndartlab.search("유상증자")'),
        ("code", 'dartlab.search("대표이사 변경", corp="005930")'),
        ("code", 'dartlab.searchName("삼성")'),
    ],
    "11_listing": [
        ("md", "# Listing\n\n상장 종목 / 공시 메타데이터 카탈로그."),
        ("code", "%pip install -q dartlab"),
        ("code", "import dartlab\ndartlab.listing()"),
        ("code", 'dartlab.listing("all")'),
        ("code", 'dartlab.listing("filings", corp="005930")'),
    ],
}


def write_colab(name: str, cells) -> None:
    out_cells = []
    for kind, content in cells:
        if kind == "md":
            out_cells.append({"cell_type": "markdown", "metadata": {}, "source": content})
        else:
            out_cells.append(
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": content,
                    "outputs": [],
                    "execution_count": None,
                }
            )
    nb = {
        "cells": out_cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    p = ROOT / "colab" / f"{name}.ipynb"
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")


def _needs_dartlab(content: str) -> bool:
    return "dartlab" in content and "import dartlab" not in content


def _needs_c(content: str) -> bool:
    return "c." in content and "c = dartlab" not in content


def _provides_dartlab(content: str) -> bool:
    return "import dartlab" in content


def _provides_c(content: str) -> bool:
    return "c = dartlab" in content


def write_marimo(name: str, cells) -> None:
    lines = [
        "# /// script",
        '# requires-python = ">=3.12"',
        '# dependencies = ["dartlab", "marimo"]',
        "# ///",
        "",
        "import marimo",
        "",
        '__generated_with = "0.22.0"',
        'app = marimo.App(width="medium")',
        "",
    ]

    # 마리모는 설명을 주석으로 (mo.md 셀 대신) — 다음 code 셀 위에 모아 단다.
    pending_comments: list[str] = []

    def _comment_lines(md: str) -> list[str]:
        out: list[str] = []
        for raw in md.split("\n"):
            s = raw.rstrip()
            if not s:
                out.append("#")
            else:
                s = s.lstrip("#").strip()  # md 헤더 마커(#) 제거 → 깔끔한 주석
                out.append(f"# {s}" if s else "#")
        return out

    for kind, content in cells:
        if kind == "md":
            pending_comments.extend(_comment_lines(content))
            continue

        if content.strip().startswith("%pip install"):
            continue

        body_lines = [ln for ln in content.split("\n") if ln.strip()]
        if not body_lines:
            continue

        params = []
        if _needs_dartlab(content):
            params.append("dartlab")
        if _needs_c(content):
            params.append("c")

        lines.append("")
        if pending_comments:  # 셀 위에 설명 주석
            lines.extend(pending_comments)
            pending_comments = []
        lines.append("@app.cell")
        if params:
            lines.append(f"def _({', '.join(params)}):")
        else:
            lines.append("def _():")
        for ln in body_lines:
            lines.append(f"    {ln}")

        rets = []
        if _provides_dartlab(content):
            rets.append("dartlab")
        if _provides_c(content):
            rets.append("c")
        if rets:
            if len(rets) == 1:
                lines.append(f"    return ({rets[0]},)")
            else:
                lines.append(f"    return ({', '.join(rets)})")
        else:
            lines.append("    return")

    if pending_comments:  # 끝에 남은 설명 주석 (뒤 code 셀 없음)
        lines.append("")
        lines.extend(pending_comments)
    lines.extend(["", "", 'if __name__ == "__main__":', "    app.run()", ""])
    p = ROOT / "marimo" / f"{name}.py"
    p.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    for name, cells in NOTEBOOKS.items():
        write_colab(name, cells)
        write_marimo(name, cells)
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
