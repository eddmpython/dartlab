"""Generate all Colab notebooks from a single source-of-truth spec.

Rule (runtime.notebooks):
  - Colab cells mirror Marimo cell *code* 1:1
  - Colab adds a small number of concise markdown cells (intro + section dividers)
  - Marimo notebooks are hand-written and left untouched here

Run:
  uv run python notebooks/_scripts/syncColabFromMarimo.py
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path


def md(*lines: str) -> dict:
    return {
        "cell_type": "markdown",
        "id": uuid.uuid4().hex[:12],
        "metadata": {},
        "source": _as_source(lines),
    }


def code(*lines: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": uuid.uuid4().hex[:12],
        "metadata": {},
        "outputs": [],
        "source": _as_source(lines),
    }


def _as_source(lines: tuple[str, ...]) -> list[str]:
    text = "\n".join(lines)
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]]


def install_cell() -> dict:
    return code("%pip install -q dartlab")


NOTEBOOKS: dict[str, list[dict]] = {
    "01_company.ipynb": [
        md(
            "# 01 — Company: 종목코드 하나로 재무/공시",
            "",
            "`dartlab.Company(code)` 는 회사 데이터의 단일 입구다.",
            "재무제표·정형 공시·사업보고서 섹션이 한 객체에서 바로 열린다.",
        ),
        install_cell(),
        code(
            "import dartlab",
            "",
            'c = dartlab.Company("000020")',
            "c.corpName",
        ),
        code(
            "# 손익계산서 (분기)",
            'c.panel("IS")',
        ),
        code(
            "# 연간 합산",
            'c.panel("IS", freq="Y")',
        ),
        code(
            "# 행 필터",
            'c.select("IS")',
        ),
        md(
            "## 주석 · 정형 공시",
            "",
            "`panel` 은 재무제표뿐 아니라 재고·배당 같은 주석/정형 공시 토픽도 같은 방식으로 꺼낸다.",
        ),
        code(
            "# 주석 — 재고자산",
            'c.panel("inventory")',
        ),
        md(
            "## 사업보고서 섹션 · 공시 이력",
            "",
            "`topics` 로 보고서 토픽 catalog 를 확인하고 `panel(topic)` 으로 본문을 연다. `filings()` 는 제출 이력이다.",
        ),
        code("c.topics.head(20)", "c.panel('businessOverview').head(20)"),
        code("c.filings().head(10)"),
    ],
    "02_gather.ipynb": [
        md(
            "# 02 — gather: 가격·수급·매크로·뉴스",
            "",
            "`dartlab.gather(axis, key)` 는 시장 외부 데이터를 하나의 API 로 모은다.",
        ),
        install_cell(),
        code(
            "import dartlab",
            "",
            "# 가이드 — 어떤 축이 있는지",
            "dartlab.gather()",
        ),
        md(
            "## 가격",
            "",
            "종목 티커 또는 지수 이름을 넘기면 일봉 히스토리가 나온다.",
        ),
        code(
            "# 주가",
            'dartlab.gather("price", "005930")',
        ),
        code(
            "# 코스피 지수",
            'dartlab.gather("price", "KOSPI")',
        ),
        md(
            "## 매크로 · 수급 · 뉴스",
            "",
            "축 이름만 바꾸면 같은 형태로 꺼내진다.",
        ),
        code(
            "# 매크로",
            'dartlab.gather("macro")',
        ),
        code(
            "# 최근 수급 (기본 5거래일)",
            'dartlab.gather("flow", "005930")',
        ),
        code(
            "# 2010년부터 최신 거래일까지 — 자동 페이지네이션",
            'dartlab.gather(',
            '    "flow",',
            '    "005930",',
            '    start="2010-01-04",',
            "    sleepSec=1.0,",
            ")",
        ),
        code(
            "# 가능한 전체 이력은 오래 걸릴 수 있어 필요할 때만 실행:",
            '# dartlab.gather("flow", "005930", all=True, sleepSec=1.0)',
            "# 여러 종목은 종목 단위 병렬 수집:",
            '# dartlab.gather("flow", targets=["005930", "000660"], limit=30, parallel=2)',
            "# 사용자 프록시가 필요하면 병렬 수집에도 같은 호출 범위로 적용:",
            '# dartlab.gather("flow", targets=["005930", "000660"], limit=30, parallel=2, proxy="http://user:pass@host:port")',
        ),
        code(
            "# 뉴스",
            'dartlab.gather("news", "삼성전자")',
        ),
    ],
    "03_scan.ipynb": [
        md(
            "# 03 — scan: 전종목 횡단",
            "",
            "`dartlab.scan(axis, key)` 로 모든 상장사를 같은 계정·같은 지표로 비교한다.",
        ),
        install_cell(),
        code(
            "import dartlab",
            "",
            "# 가이드 — 13축",
            "dartlab.scan()",
        ),
        md("## 계정 횡단 — 특정 계정(매출액)을 전종목에서 뽑기"),
        code('dartlab.scan("account", "매출액")'),
    ],
    "04_quant.ipynb": [
        md(
            "# 04 — quant: 25지표 + 9신호",
            "",
            "`c.quant(axis)` 는 가격·모멘텀·가치·퀄리티 같은 계량 지표를 한 회사에 대해 한 번에 계산한다.",
        ),
        install_cell(),
        code(
            "import dartlab",
            "",
            'c = dartlab.Company("005930")',
            "# 가이드 — 25지표 + 9신호",
            "c.quant()",
        ),
        code(
            "# 종합 판단",
            'c.quant("종합")',
        ),
        code(
            "# 모멘텀 / RSI",
            'c.quant("모멘텀")',
        ),
    ],
    "05_analysis.ipynb": [
        md(
            "# 05 — analysis: 14축 + 전망 + 가치평가",
            "",
            "`c.analysis(axis)` 는 재무제표 기반 분석 엔진의 통합 입구다. 축 이름만 바꾸면 수익성·성장성·안정성·현금흐름·매출전망·가치평가가 같은 방식으로 나온다.",
        ),
        install_cell(),
        code(
            "import dartlab",
            "",
            'c = dartlab.Company("005930")',
            "# 가이드 — 14축 + forecast + valuation",
            "c.analysis()",
        ),
        md("## 수익성 / 성장성 / 안정성 / 현금흐름"),
        code(
            "# 수익성",
            'c.analysis("수익성")',
        ),
        code(
            "# 성장성",
            'c.analysis("성장성")',
        ),
        code(
            "# 안정성",
            'c.analysis("안정성")',
        ),
        code(
            "# 현금흐름",
            'c.analysis("현금흐름")',
        ),
        md("## 전망 · 가치평가"),
        code(
            "# 매출전망",
            'c.analysis("매출전망")',
        ),
        code(
            "# 가치평가",
            'c.analysis("가치평가")',
        ),
    ],
    "06_macro.ipynb": [
        md(
            "# 06 — macro: 사이클/금리/자산/심리/유동성",
            "",
            "`dartlab.macro(axis)` 는 경제 사이클·금리 같은 거시 축을 회사 분석과 동일한 패턴으로 제공한다.",
        ),
        install_cell(),
        code(
            "import dartlab",
            "",
            "# 가이드 — 사이클/금리/자산/심리/유동성",
            "dartlab.macro()",
        ),
        code(
            "# 사이클",
            'dartlab.macro("사이클")',
        ),
        code(
            "# 금리",
            'dartlab.macro("금리")',
        ),
    ],
    "07_credit.ipynb": [
        md(
            "# 07 — credit: dCR 7축 등급",
            "",
            "`c.credit(axis)` 는 dartlab 내부 신용평가 모델(dCR) 출력을 축별로 보여준다.",
        ),
        install_cell(),
        code(
            "import dartlab",
            "",
            'c = dartlab.Company("005930")',
            "# 가이드 — 7축 dCR 등급",
            "c.credit()",
        ),
        md("## 종합등급 · 수익성 · 부채"),
        code(
            "# 등급",
            'c.credit("등급")',
        ),
        code(
            "# 수익성",
            'c.credit("수익성")',
        ),
        code(
            "# 부채",
            'c.credit("부채")',
        ),
    ],
    "08_review.ipynb": [
        md(
            "# 08 — story: 구조화 보고서",
            "",
            "`c.story(section)` 은 숫자를 서술형 보고서로 조립한다. `toMarkdown()` 으로 문자열 출력.",
        ),
        install_cell(),
        code(
            "import dartlab",
            "",
            'c = dartlab.Company("005930")',
        ),
        md("## 섹션 단위 호출 — 메모리 안전"),
        code(
            "# 단일 섹션 (메모리 안전 — 추천)",
            'print(c.story("수익성").toMarkdown())',
        ),
        code('print(c.story("성장성").toMarkdown())'),
        md("## AI 종합의견 — provider 키 필요"),
        code(
            "# AI 종합의견은 ask 로 일원화",
            '# dartlab.ask("삼성전자 반도체 사이클 관점에서 평가해줘")',
        ),
    ],
    "09_ai.ipynb": [
        md(
            "# 09 — ai: ask · chat",
            "",
            "`dartlab.ask` 는 자연어 질문을 받아 내부 도구를 자동 호출한다.",
            "AI provider 키(`GEMINI_API_KEY` 또는 `GROQ_API_KEY`)가 필요하다.",
        ),
        install_cell(),
        code(
            "# AI provider 키 필요 (GEMINI_API_KEY, GROQ_API_KEY 등)",
            "import dartlab",
            "",
            'dartlab.ask("뭐할수있니")',
        ),
        code(
            "# Company-bound 대화",
            '# dartlab.chat("005930", "배당 추세는?")',
        ),
    ],
    "10_search.ipynb": [
        md(
            "# 10 — search: 공시 검색",
            "",
            "공시 제목·법인명 기반 검색. 키워드 + 회사 필터를 함께 쓸 수 있다.",
        ),
        install_cell(),
        code(
            "import dartlab",
            "",
            'dartlab.search("유상증자")',
        ),
        code('dartlab.search("대표이사 변경", corp="005930")'),
        code('dartlab.searchName("삼성")'),
    ],
    "11_listing.ipynb": [
        md(
            "# 11 — listing: 법인·공시 목록",
            "",
            "`dartlab.listing(axis, ...)` 로 상장 법인 마스터와 공시 목록을 꺼낸다.",
        ),
        install_cell(),
        code(
            "import dartlab",
            "",
            "dartlab.listing()",
        ),
        code('dartlab.listing("filings", corp="005930")'),
        code(
            "# DART 전체 법인 (비상장 포함, corp_code 8자리)",
            'dartlab.listing("dartlist")',
        ),
    ],
}


META = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {"name": "python", "version": "3.12.0"},
}


def build(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": META,
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    out = Path(__file__).resolve().parents[2] / "notebooks" / "colab"
    out.mkdir(parents=True, exist_ok=True)
    for name, cells in NOTEBOOKS.items():
        path = out / name
        path.write_text(
            json.dumps(build(cells), ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {path.relative_to(path.parents[2])}")


if __name__ == "__main__":
    main()
