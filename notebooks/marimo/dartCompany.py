# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""DART 한국 상장기업 탐색 — sections 중심 흐름.

실행: marimo edit startMarimo/dartCompany.py
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App()


# ── Company 생성 ────────────────────────────────────────────────
@app.cell
def _():
    import dartlab

    c = dartlab.Company("005930")  # 삼성전자
    c.corpName
    return (c,)


# ── sections: 회사 전체 맵 ──────────────────────────────────────
@app.cell
def _(c):
    # topic × period 수평화 DataFrame — 회사의 전체 지도
    c.sections
    return


@app.cell
def _(c):
    # 이 회사의 topic 목록
    c.topics
    return


# ── show: topic 열기 ────────────────────────────────────────────
@app.cell
def _(c):
    # 서술형 topic → 블록 목차
    c.show("overview")
    return


@app.cell
def _(c):
    # 블록 번호 지정 → 실제 데이터
    c.show("companyOverview", 3)
    return


# ── 재무제표 ────────────────────────────────────────────────────
@app.cell
def _(c):
    # 재무제표 topic → finance source (숫자 authoritative)
    c.show("IS")
    return


@app.cell
def _(c):
    c.BS  # 재무상태표
    return


@app.cell
def _(c):
    c.CF  # 현금흐름표
    return


@app.cell
def _(c):
    c.ratios  # 재무비율 시계열
    return


@app.cell
def _(c):
    # 특정 기간 비교 (항목 × 기간)
    c.show("IS", period=["2024Q4", "2023Q4"])
    return


# ── report 데이터 ──────────────────────────────────────────────
@app.cell
def _(c):
    # 배당 데이터
    c.show("dividend")
    return


# ── trace / diff ────────────────────────────────────────────────
@app.cell
def _(c):
    # 어떤 source(docs/finance/report)가 채택됐는지
    c.trace("stock")
    return


@app.cell
def _(c):
    # 전체 topic별 텍스트 변경률
    c.diff()
    return


@app.cell
def _(c):
    # 특정 topic 기간별 이력
    c.diff("businessOverview")
    return


# ── K-IFRS 주석 (Notes) ────────────────────────────────────────
@app.cell
def _(c):
    # K-IFRS 주석 — 12가지 항목
    c.notes.keys()
    return


@app.cell
def _(c):
    # 재고자산 주석
    c.notes.inventory
    return


# ── 분석 엔진 ──────────────────────────────────────────────────
@app.cell
def _(c):
    # 섹터 분류 (WICS 11대 업종)
    c.sector
    return


@app.cell
def _(c):
    # 인사이트 등급 (7영역 A~F)
    c.insights
    return


@app.cell
def _(c):
    # 시장 규모 순위
    c.rank
    return


# ── 네트워크 / 거버넌스 ────────────────────────────────────────
@app.cell
def _(c):
    # 관계사 네트워크 — 계열사 목록
    c.network("members")
    return


@app.cell
def _(c):
    # 지배구조 분석
    c.governance()
    return


# ── 테이블 파싱 ─────────────────────────────────────────────────
@app.cell
def _(c):
    # 서술형 블록 내 표를 구조화된 DataFrame으로 파싱
    c.table("employee")
    return


# ── 보고서 목록 ─────────────────────────────────────────────────
@app.cell
def _(c):
    c.filings()
    return


# ── 차트 (plotly 필요) ──────────────────────────────────────────
@app.cell
def _(c, dartlab):
    # 매출 차트 (plotly 필요: uv add "dartlab[charts]")
    dartlab.chart.revenue(c).show()
    return


if __name__ == "__main__":
    app.run()
