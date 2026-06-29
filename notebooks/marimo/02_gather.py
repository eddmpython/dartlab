# /// script
# requires-python = ">=3.12"
# dependencies = ["dartlab", "marimo"]
# ///

import marimo

__generated_with = "0.23.11"
app = marimo.App(width="medium")


@app.cell
def _():
    import dartlab

    dartlab.gather()
    return (dartlab,)


@app.cell
def _(dartlab):
    dartlab.gather("price", "005930")
    return


@app.cell
def _(dartlab):
    dartlab.gather("price", "KOSPI")
    return


@app.cell
def _(dartlab):
    dartlab.gather("macro")
    return


@app.cell
def _(dartlab):
    # 최근 수급 (기본 5거래일)
    dartlab.gather("flow", "005930")
    return


@app.cell
def _(dartlab):
    # 2010년부터 최신 거래일까지 — 자동 페이지네이션
    dartlab.gather(
        "flow",
        "005930",
        start="2026-01-04",
        sleepSec=1.0,
    )
    return


@app.cell
def _():
    # 가능한 전체 이력은 오래 걸릴 수 있어 필요할 때만 실행:
    # dartlab.gather("flow", "005930", all=True, sleepSec=1.0)
    # 여러 종목은 종목 단위 병렬 수집:
    # dartlab.gather("flow", targets=["005930", "000660"], limit=30, parallel=2)
    # 사용자 프록시가 필요하면 병렬 수집에도 같은 호출 범위로 적용:
    # dartlab.gather("flow", targets=["005930", "000660"], limit=30, parallel=2, proxy="http://user:pass@host:port")
    return


@app.cell
def _(dartlab):
    dartlab.gather("news", "삼성전자")
    return


@app.cell
def _(dartlab):
    # ── 네이버 분류/목록 (로컬 개인용 — 재배포 금지) ──────────────────────
    # 테마: 기본은 전 테마(약 266)를 개별 수집해 하나의 DataFrame 으로 결합.
    # 전수 크롤이 무거워(수 분) 결과를 7일간 로컬 저장 — 같은 호출 재실행은 즉시 직독.
    dartlab.gather("naverTheme")
    return


@app.cell
def _(dartlab):
    # 목록만(가볍게) · 특정 테마만 · 신선도/강제 재크롤
    dartlab.gather("naverTheme", "list")  # 테마 목록 (groupNo/groupName/url)
    # dartlab.gather("naverTheme", "리튬")        # 리튬 테마 편입종목만 (라이브)
    # dartlab.gather("naverTheme", refresh=True)  # 7일 안이라도 강제 재크롤
    # dartlab.gather("naverTheme", maxAgeDays=1)  # 신선도 윈도우 1일
    return


@app.cell
def _(dartlab):
    # 업종 — 테마와 동일 sise_group 구조 (편입사유는 없음)
    dartlab.gather("naverIndustry", "반도체")
    return


@app.cell
def _(dartlab):
    # ETF/ETN — 단일 호출 상품목록 (장중 가격이라 저장 없이 매번 라이브). target=종목명 필터.
    dartlab.gather("naverEtf", "KODEX")
    # dartlab.gather("naverEtn")  # 전체 ETN
    return


@app.cell
def _():
    # 느린 전수 크롤은 프록시 풀로 분산 (round-robin). 프록시 없으면 도메인 단위 안전 직렬(IP 보호):
    # dartlab.gather("naverTheme", proxies=["http://a:1", "http://b:1"], refresh=True)
    #
    # 결합 결과 → wide(테마기준) 행렬 / 종목기준 전치:
    # df = dartlab.gather("naverTheme")
    # wide = df.pivot(values="reason", index="stockCode", on="groupName")
    return


if __name__ == "__main__":
    app.run()
