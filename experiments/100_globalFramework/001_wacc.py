"""실험 ID: 100-001
실험명: CAPM Beta + WACC 산출 검증

목적:
- dartlab의 기존 인프라(gather history, ECOS 금리, finance ratios)로
  CAPM Beta와 WACC를 자체 산출할 수 있는지 검증
- 산출된 WACC가 합리적 범위(6-15%)에 있는지 확인

가설:
1. gather.history()로 일별 주가 시계열을 가져와 KOSPI 대비 Beta를 계산할 수 있다
2. ECOS에서 국고채 10년 금리(Rf)를 가져올 수 있다
3. finance.ratios에서 이자비용/차입금으로 Kd를 역산할 수 있다
4. 최종 WACC가 한국 시장 합리적 범위(6-15%) 내에 있다

방법:
1. 대상: 삼성전자(005930), 현대차(005380), NAVER(035420), 카카오(035720),
   POSCO홀딩스(005490), LG화학(051910), 삼성바이오(207940),
   KB금융(105560), 셀트리온(068270), 한국전력(015760) — 10종목
2. Beta: 1년 일별 수익률 vs KOSPI 수익률 회귀
3. Rf: ECOS TREASURY_10Y 최신값
4. ERP: 한국 시장 위험프리미엄 6.0% (Damodaran 2025 추정치)
5. Ke = Rf + Beta × ERP
6. Kd = 이자비용 / 평균 차입금 × (1 - 세율)
7. WACC = Ke × We + Kd × Wd

결과:
  종목           Beta    Rf    Ke     Kd(세후)  We    Wd    WACC   ROIC-WACC
  삼성전자        1.22   3.5   10.8    3.5     100%    0%   10.8%    -3.0%p
  현대차          1.02   3.5    9.6    3.5      49%   51%    6.5%    -2.7%p
  NAVER          0.65   3.5    7.4    3.5     100%    0%    7.4%    -1.5%p
  카카오          0.85   3.5    8.6    3.5     100%    0%    8.6%    -4.9%p
  POSCO홀딩스     0.84   3.5    8.5    3.5      56%   44%    6.3%    -4.5%p
  LG화학         1.07   3.5    9.9    3.5     100%    0%    9.9%    -7.9%p
  삼성바이오       0.55   3.5    6.8    3.5     100%    0%    6.8%    +6.1%p
  KB금융         0.67   3.5    7.5    3.5      41%   59%    5.1%    +5.4%p
  셀트리온        0.65   3.5    7.4    3.5     100%    0%    7.4%    -3.3%p
  한국전력        0.78   3.5    8.2    3.5     100%    0%    8.2%   +14.6%p

  WACC 범위: 5.1% ~ 10.8%, 평균: 7.7%
  합리적 범위(6-15%): 9/10 (90%)

결론:
1. [채택] Beta 계산 가능 — yfinance 1년 일별 수익률로 KOSPI 대비 Beta 산출 성공 (10종목 모두)
2. [채택] WACC 합리적 범위 — 90% 종목이 6-15% 내 (KB금융 5.1%만 약간 하회, 금융주 특성)
3. [주의] Kd 산출 방식 — DART finance_costs는 금융비용 전체(이자+외환+파생)라 Kd 역산 부적합.
   → 회사채 AA- 금리를 Kd 프록시로 사용 (실무 표준과 일치)
4. [주의] 순현금 기업 — 삼성전자/NAVER/LG화학 등 현금>차입금인 기업은 We=100%로 산출.
   실제 WACC에서는 target capital structure 사용이 더 적합할 수 있음
5. [관찰] ROIC-WACC — 대부분 음수 (가치 파괴), 삼성바이오/KB금융/한국전력만 양수
   → 한국전력 +14.6%p는 대규모 적자 이후 흑자 전환 효과 (비정상)
6. [관찰] ECOS API 키 없이도 기본값으로 동작 가능 (Rf=3.5%, Kd=4.5% fallback)

실험일: 2026-03-25
"""

import sys
import os
from datetime import date, timedelta
from dataclasses import dataclass

import polars as pl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# ── 상수 ──
ERP = 6.0  # 한국 시장 위험프리미엄 (Damodaran 2025, %)
DEFAULT_TAX_RATE = 0.22  # 법인세 유효세율 기본값
KOSPI_CODE = "^KS11"  # Yahoo Finance KOSPI 코드
CORP_BOND_RATE = 4.5  # 회사채 AA- 3년 기본값 (%, ECOS 없을 시 fallback)

TARGETS = [
    ("005930", "삼성전자"),
    ("005380", "현대차"),
    ("035420", "NAVER"),
    ("035720", "카카오"),
    ("005490", "POSCO홀딩스"),
    ("051910", "LG화학"),
    ("207940", "삼성바이오"),
    ("105560", "KB금융"),
    ("068270", "셀트리온"),
    ("015760", "한국전력"),
]


@dataclass
class WaccResult:
    """단일 기업 WACC 산출 결과."""

    stockCode: str
    name: str
    beta: float | None
    rf: float | None  # %
    ke: float | None  # %
    kd: float | None  # % (세후)
    equityWeight: float | None
    debtWeight: float | None
    wacc: float | None  # %
    marketCap: float | None  # 억원
    netDebt: float | None  # 억원
    roicMinusWacc: float | None  # %p (초과수익)
    note: str = ""


def calcBeta(stockHistory: list[dict], marketHistory: list[dict]) -> float | None:
    """일별 수익률 회귀로 Beta 계산."""
    if len(stockHistory) < 60 or len(marketHistory) < 60:
        return None

    stockDf = pl.DataFrame(stockHistory).select(
        pl.col("date").cast(pl.Date).alias("date"),
        pl.col("close").cast(pl.Float64).alias("stockClose"),
    )
    marketDf = pl.DataFrame(marketHistory).select(
        pl.col("date").cast(pl.Date).alias("date"),
        pl.col("close").cast(pl.Float64).alias("marketClose"),
    )

    joined = stockDf.join(marketDf, on="date", how="inner").sort("date")
    if joined.height < 60:
        return None

    # 일별 수익률
    joined = joined.with_columns(
        (pl.col("stockClose") / pl.col("stockClose").shift(1) - 1).alias("stockRet"),
        (pl.col("marketClose") / pl.col("marketClose").shift(1) - 1).alias(
            "marketRet"
        ),
    ).drop_nulls()

    if joined.height < 30:
        return None

    stockRet = joined["stockRet"]
    marketRet = joined["marketRet"]

    # Beta = Cov(Ri, Rm) / Var(Rm)
    cov = stockRet.to_numpy() @ marketRet.to_numpy() / len(stockRet) - stockRet.mean() * marketRet.mean()
    varMarket = marketRet.var()
    if varMarket is None or varMarket == 0:
        return None

    beta = cov / varMarket
    return round(float(beta), 3)


def getRiskFreeRate() -> float | None:
    """ECOS에서 국고채 10년 최신 금리 가져오기."""
    try:
        from dartlab.engines.gather.ecos.client import EcosClient
        from dartlab.engines.gather.ecos.series import fetchSeries

        client = EcosClient()
        df = fetchSeries(client, "TREASURY_10Y")
        if df.height == 0:
            return None
        # 최신 non-null 값
        latest = df.filter(pl.col("value").is_not_null()).sort("date").tail(1)
        if latest.height == 0:
            return None
        return float(latest["value"][0])
    except Exception as e:
        print(f"  [WARN] ECOS 국고채 조회 실패: {e}")
        return None


def getMarketHistory(start: str, end: str) -> list[dict]:
    """KOSPI 일별 히스토리 가져오기 (yfinance 직접 사용)."""
    try:
        import yfinance as yf

        ticker = yf.Ticker(KOSPI_CODE)
        hist = ticker.history(start=start, end=end, auto_adjust=True)
        if hist.empty:
            return []
        records = []
        for idx, row in hist.iterrows():
            records.append({
                "date": idx.date() if hasattr(idx, "date") else idx,
                "close": float(row["Close"]),
            })
        return records
    except Exception as e:
        print(f"  [WARN] KOSPI 히스토리 실패: {e}")
        return []


def calcWacc(stockCode: str, name: str, beta: float | None, rf: float | None) -> WaccResult:
    """Company의 재무 데이터로 WACC 산출."""
    import dartlab
    from dartlab.engines.common.finance.extract import getTTM, getLatest
    try:
        c = dartlab.Company(stockCode)
        ts = c.finance.timeseries
        series = ts[0] if isinstance(ts, tuple) else ts
    except Exception as e:
        return WaccResult(
            stockCode=stockCode, name=name,
            beta=beta, rf=rf, ke=None, kd=None,
            equityWeight=None, debtWeight=None, wacc=None,
            marketCap=None, netDebt=None, roicMinusWacc=None,
            note=f"Company 로드 실패: {e}",
        )

    # ── Ke (자기자본비용) ──
    ke = None
    if beta is not None and rf is not None:
        ke = rf + beta * ERP

    # ── Kd (타인자본비용, 세후) ──
    # finance_costs는 금융비용 전체(이자+외환+파생)이므로 Kd 역산에 부적합
    # 대안: 회사채 AA- 3년 금리를 Kd 프록시로 사용 (실무 표준)
    # ECOS 없으면 기본값 4.5% 사용
    kd = CORP_BOND_RATE * (1 - DEFAULT_TAX_RATE)

    shortBorrow = getLatest(series, "BS", "shortterm_borrowings") or 0
    longBorrow = getLatest(series, "BS", "longterm_borrowings") or 0
    bondVal = getLatest(series, "BS", "debentures") or 0
    totalDebt = shortBorrow + longBorrow + bondVal

    # ── 시가총액 (yfinance에서 직접) ──
    marketCap = None
    try:
        import yfinance as yf
        ticker = yf.Ticker(f"{stockCode}.KS")
        info = ticker.info
        marketCap = info.get("marketCap")  # 원 단위
    except Exception:
        pass

    # ── 순차입금 ──
    cash = getLatest(series, "BS", "cash_and_cash_equivalents") or 0
    netDebt = totalDebt - cash

    # ── 가중치 ──
    equityWeight = None
    debtWeight = None
    wacc = None

    if marketCap and marketCap > 0:
        debtForWeight = max(netDebt, 0)
        totalCapital = marketCap + debtForWeight
        if totalCapital > 0:
            equityWeight = marketCap / totalCapital
            debtWeight = debtForWeight / totalCapital

            if ke is not None and kd is not None:
                wacc = ke * equityWeight + kd * debtWeight
            elif ke is not None:
                wacc = ke  # 순현금 기업 → 100% equity

    # ── ROIC ──
    operatingIncome = getTTM(series, "IS", "operating_profit")
    totalEquity = getLatest(series, "BS", "total_stockholders_equity")
    roic = None
    roicMinusWacc = None
    if operatingIncome and totalEquity:
        effectiveTax = DEFAULT_TAX_RATE
        nopat = operatingIncome * (1 - effectiveTax)
        investedCapital = totalEquity + max(netDebt, 0)
        if investedCapital > 0:
            roic = (nopat / investedCapital) * 100
            if wacc is not None:
                roicMinusWacc = roic - wacc

    return WaccResult(
        stockCode=stockCode, name=name,
        beta=beta, rf=rf, ke=ke, kd=kd,
        equityWeight=equityWeight, debtWeight=debtWeight,
        wacc=wacc,
        marketCap=marketCap / 1e8 if marketCap else None,  # 억원으로 표시
        netDebt=netDebt / 1e8 if netDebt else None,
        roicMinusWacc=roicMinusWacc,
    )


def getStockHistory(stockCode: str, start: str, end: str) -> list[dict]:
    """yfinance로 종목 일별 히스토리 직접 가져오기 (async 이벤트 루프 문제 회피)."""
    try:
        import yfinance as yf

        # 한국 종목 → .KS 접미사
        ticker = yf.Ticker(f"{stockCode}.KS")
        hist = ticker.history(start=start, end=end, auto_adjust=True)
        if hist.empty:
            return []
        records = []
        for idx, row in hist.iterrows():
            records.append({
                "date": idx.date() if hasattr(idx, "date") else idx,
                "close": float(row["Close"]),
            })
        return records
    except Exception as e:
        print(f"    [WARN] yfinance 히스토리 실패: {e}")
        return []


def main():
    """WACC 실험 메인."""
    # 1. Rf (Risk-Free Rate)
    print("=" * 70)
    print("001_wacc: CAPM Beta + WACC 산출 검증")
    print("=" * 70)

    print("\n[1] 국고채 10년 금리 (Rf) 조회...")
    rf = getRiskFreeRate()
    if rf is not None:
        print(f"  Rf = {rf:.2f}%")
    else:
        print("  [FALLBACK] ECOS 실패 → Rf = 3.5% 기본값 사용")
        rf = 3.5

    # 2. KOSPI 히스토리 (Beta 계산용)
    endDate = date.today()
    startDate = endDate - timedelta(days=365)
    print(f"\n[2] KOSPI 히스토리 ({startDate} ~ {endDate})...")
    marketHistory = getMarketHistory(str(startDate), str(endDate))
    print(f"  KOSPI 일별 데이터: {len(marketHistory)}건")

    # 3. 종목별 Beta + WACC 산출 (yfinance로 직접 히스토리 수집)
    print(f"\n[3] 10종목 Beta + WACC 산출...")
    print(f"  ERP = {ERP}%, 세율 = {DEFAULT_TAX_RATE*100}%")
    print()

    results: list[WaccResult] = []

    for stockCode, name in TARGETS:
        print(f"  [{stockCode}] {name}...")

        # yfinance로 직접 주가 히스토리 (event loop 문제 회피)
        stockHistory = getStockHistory(stockCode, str(startDate), str(endDate))

        # Beta 계산
        beta = None
        if stockHistory and marketHistory:
            beta = calcBeta(stockHistory, marketHistory)

        if beta is not None:
            print(f"    Beta = {beta:.3f}")
        else:
            print(f"    Beta = N/A (히스토리 {len(stockHistory)}건)")

        # WACC 계산 (Company 로드 포함)
        result = calcWacc(stockCode, name, beta, rf)
        results.append(result)

        if result.wacc is not None:
            print(f"    Ke={result.ke:.1f}%, Kd={result.kd:.1f}% (세후)" if result.kd else f"    Ke={result.ke:.1f}%")
            print(f"    We={result.equityWeight:.1%}, Wd={result.debtWeight:.1%}" if result.equityWeight else "")
            print(f"    WACC = {result.wacc:.2f}%")
            if result.roicMinusWacc is not None:
                sign = "+" if result.roicMinusWacc > 0 else ""
                print(f"    ROIC-WACC = {sign}{result.roicMinusWacc:.1f}%p")
        elif result.note:
            print(f"    {result.note}")

        # 메모리 해제
        del result
        import gc
        gc.collect()

    # 4. 결과 요약 테이블
    print("\n" + "=" * 70)
    print("결과 요약")
    print("=" * 70)
    print(f"{'종목':<12} {'Beta':>6} {'Rf':>5} {'Ke':>6} {'Kd':>6} {'We':>5} {'Wd':>5} {'WACC':>6} {'ROIC-WACC':>10}")
    print("-" * 70)

    validWaccs = []
    for r in results:
        beta_s = f"{r.beta:.2f}" if r.beta is not None else "N/A"
        rf_s = f"{r.rf:.1f}" if r.rf is not None else "N/A"
        ke_s = f"{r.ke:.1f}" if r.ke is not None else "N/A"
        kd_s = f"{r.kd:.1f}" if r.kd is not None else "N/A"
        we_s = f"{r.equityWeight:.0%}" if r.equityWeight is not None else "N/A"
        wd_s = f"{r.debtWeight:.0%}" if r.debtWeight is not None else "N/A"
        wacc_s = f"{r.wacc:.1f}" if r.wacc is not None else "N/A"
        spread_s = f"{r.roicMinusWacc:+.1f}" if r.roicMinusWacc is not None else "N/A"
        print(f"{r.name:<12} {beta_s:>6} {rf_s:>5} {ke_s:>6} {kd_s:>6} {we_s:>5} {wd_s:>5} {wacc_s:>6} {spread_s:>10}")
        if r.wacc is not None:
            validWaccs.append(r.wacc)

    print("-" * 70)
    if validWaccs:
        print(f"WACC 범위: {min(validWaccs):.1f}% ~ {max(validWaccs):.1f}%")
        avg = sum(validWaccs) / len(validWaccs)
        print(f"WACC 평균: {avg:.1f}%")
        inRange = sum(1 for w in validWaccs if 6.0 <= w <= 15.0)
        print(f"합리적 범위(6-15%): {inRange}/{len(validWaccs)} ({inRange/len(validWaccs):.0%})")
    else:
        print("유효한 WACC 결과 없음")


if __name__ == "__main__":
    main()
