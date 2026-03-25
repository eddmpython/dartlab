# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///
"""Gather 엔진 — 멀티소스 시장 데이터 수집.

실행: marimo edit notebooks/marimo/gatherEngine.py

NOTE: Marimo는 async event loop 위에서 실행된다.
dartlab은 내부에서 persistent loop을 사용하므로
Marimo 환경에서도 정상 동작한다.
"""

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")

with app.setup:
    import dartlab


@app.cell
def _():
    # 주가 스냅샷 — naver → yahoo_direct → yahoo fallback 체인
    dartlab.price("005930")
    return


@app.cell
def _():
    # 컨센서스 — 목표가, 투자의견
    dartlab.consensus("005930")
    return


@app.cell
def _():
    # 수급 — 외국인/기관 매매 동향
    dartlab.flow("005930")
    return


@app.cell
def _():
    # 뉴스 — Google News RSS, circuit breaker 적용
    dartlab.news("삼성전자")
    return


@app.cell
def _():
    # US 뉴스
    dartlab.news("AAPL", market="US", days=7)
    return


@app.cell
def _():
    # 거시 지표 — ECOS (ECOS_API_KEY 환경변수 필요)
    dartlab.macro("KR")
    return


@app.cell
def _():
    # 거시 지표 — FRED (FRED_API_KEY 환경변수 필요)
    dartlab.macro("US")
    return


if __name__ == "__main__":
    app.run()
