"""실험 ID: 014
실험명: scan 13축 데이터 품질 전수조사

목적:
- scan 리네임 + Scan callable class 통합 후, 13축의 실제 데이터 품질을 전수조사
- 각 축별 커버리지, 결측률, 이상치, 최신성을 정량 측정
- 분석에 실제 지장을 주는 이슈를 P0/P1/P2로 분류

가설:
1. debt가 4축 완성률 병목 (ICR null 비율 40%+)
2. signal 커버리지는 로컬 docs 보유 범위에 의존 (전체 상장사의 ~12%)
3. peers crossBorderPeers의 IT fallback 비율이 30%+

방법:
1. 13축 중 P0 축(debt, signal, peers) 우선 실측
2. P1 축(account, ratio, screen, network) 실측
3. P2 축(governance, workforce, capital, benchmark, digest, groupHealth) 실측
4. 축 간 교차 검증 (debt 부채비율 vs screen debtRatio)

결과 (2026-03-28):

[DART 축 전수조사 -- peers crossBorderPeers는 EDGAR 성격이라 배제]

| 축 | 종목수 | 실행시간 | 핵심 결측 | 판정 |
|---|---|---|---|---|
| governance | 2,711 | 2.8s | 지분율 7%, pay_ratio 9.8% | 양호 |
| workforce | 2,448 | 24.1s | 근속 33.7%, 최고보수 84.2%, 직원당매출 16.3% | 보통 (최고��수는 공개의무 기업만) |
| capital | 2,714 | 1.4s | 결측 거의 없음 | 양호 |
| debt | 2,575 | 16.5s | ICR 1.4%, 부채비율 15.5%, 사채잔액 68.8%(미발행) | 양호 (가설 기각) |
| signal | ~2,548 | 1,023s(17분!) | docs 커버리지 95.7% | 사용 불가 (성능+오탐) |
| account | 2,422~2,483 | 0.2~0.3s | 2025 null 79%(미제출) | 양호 (프리빌드 활용) |
| ratio | 2,421~2,479 | 0.4s | 2025 null 79%(미제출) | 양호 |
| screen | (미실측) | 3~5분 예�� | (기존 실험 003에서 검증) | 보통 (성능) |
| benchmark | (미실측) | screen 의존 | | |
| network | (미실측) | (기존 실험 004에서 검증) | | 양�� |
| groupHealth | (미실측) | network+screen 의존 | | |
| digest | (변환 전용) | N/A | | |

가설 검증:
1. debt ICR null 40%+ → **기각** (1.4% null, 98.6% 유효). 4축 완성률 병목은 ICR이 아님.
2. signal docs 커버리지 12% → **기각** (95.7%). 319사는 키워드 매칭 결과 기업수이지 docs 부족이 아님.
3. peers IT fallback 30%+ → **채택** (100% fallback). sector.classify() 실패. 단, EDGAR 배제로 중요도 하락.

P0 이슈 (분석 불가):
- signal 실행 17분 + AI 오탐률 50% → 프리빌드 필수 + 단어경계 매칭 필요

P1 이슈 (품질 저하):
- debt 위험등급 "주의" 50% 편중 (ICR 중앙값 0.82로 대부분 주의)
- workforce 근속 33.7% null, 직원당매출 16.3% null
- screen 빌드 3~5분 (기존 실험에서 확인)

P2 이슈 (개선 여지):
- account/ratio: snakeId 발견성 (revenue가 아니라 sales)
- 2025년 데이터 79% null (자연스러운 시차, 이슈 아님)
- workforce 최고보수 84.2% null (5억+ 공개 의무만)

결론:
- scan DART 축은 signal을 제외하면 **분석에 충분히 사용 가능한 수준**
- signal만 **P0 긴급 개선** 필요 (프리빌드 + 오탐 수정)
- 나머지는 P1/P2 점진 개선
- 가설 3개 중 2개 기각 -- 예상보다 데이터 품질 양호

실험일: 2026-03-28
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import polars as pl

# ── P0-1: debt 축 품질 ─────────────────────────────────────


def auditDebt() -> dict:
    """debt 축 전수조사."""
    from dartlab.scan.debt import scan_debt

    print("\n=== [P0] debt 축 품질 조사 ===")
    t0 = time.time()
    df = scan_debt(verbose=False)
    elapsed = time.time() - t0
    print(f"  실행: {elapsed:.1f}s, {df.height}행")

    total = df.height
    cols = df.columns
    print(f"  컬럼: {cols}")

    # 핵심 컬럼 결측률
    nullRates = {}
    for c in ["사채잔액", "단기잔액", "단기비중", "총부채", "부채비율", "ICR", "위험등급"]:
        if c in cols:
            nullCount = df[c].null_count()
            nullRates[c] = round(nullCount / total * 100, 1)
            print(f"  {c}: null {nullCount}/{total} ({nullRates[c]}%)")

    # ICR 분포 (핵심 병목)
    if "ICR" in cols:
        icrValid = df.filter(pl.col("ICR").is_not_null())
        print(f"\n  ICR 유효: {icrValid.height}사 ({icrValid.height/total*100:.1f}%)")
        if icrValid.height > 0:
            icrVals = icrValid["ICR"].cast(pl.Float64)
            print(f"  ICR 분포: min={icrVals.min():.2f}, p25={icrVals.quantile(0.25):.2f}, "
                  f"median={icrVals.median():.2f}, p75={icrVals.quantile(0.75):.2f}, max={icrVals.max():.2f}")
            negIcr = icrValid.filter(pl.col("ICR").cast(pl.Float64) < 0).height
            zeroIcr = icrValid.filter(pl.col("ICR").cast(pl.Float64) == 0).height
            print(f"  ICR<0: {negIcr}사, ICR=0: {zeroIcr}사")

    # 위험등급 분포
    if "위험등급" in cols:
        grades = df.filter(pl.col("위험등급").is_not_null()).group_by("위험등급").agg(pl.len().alias("n")).sort("n", descending=True)
        print(f"\n  위험등급 분포:")
        for row in grades.iter_rows(named=True):
            print(f"    {row['위험등급']}: {row['n']}사")

    # 부채비율 이상치 (IQR)
    if "부채비율" in cols:
        debtRatio = df.filter(pl.col("부채비율").is_not_null())["부채비율"].cast(pl.Float64)
        if debtRatio.len() > 0:
            q1, q3 = debtRatio.quantile(0.25), debtRatio.quantile(0.75)
            iqr = q3 - q1
            outlierHigh = (debtRatio > q3 + 1.5 * iqr).sum()
            outlierLow = (debtRatio < q1 - 1.5 * iqr).sum()
            print(f"\n  부채비율 IQR: Q1={q1:.1f}, Q3={q3:.1f}, 상한이상치={outlierHigh}사, 하한이상치={outlierLow}사")

    return {
        "total": total,
        "elapsed": elapsed,
        "nullRates": nullRates,
        "icrValid": df.filter(pl.col("ICR").is_not_null()).height if "ICR" in cols else 0,
    }


# ── P0-2: signal 축 품질 ────────────────────────────────────


def auditSignal() -> dict:
    """signal 축 전수조사."""
    from dartlab.scan.signal import scan_signal, KEYWORDS

    print("\n=== [P0] signal 축 품질 조사 ===")

    # docs 커버리지 확인
    from dartlab.core.dataLoader import _dataDir
    docsDir = Path(_dataDir("docs"))
    docsFiles = list(docsDir.glob("*.parquet")) if docsDir.exists() else []
    print(f"  로컬 docs 파일: {len(docsFiles)}개")

    # 전체 상장사 수
    try:
        import dartlab
        listing = dartlab.listing()
        totalListed = listing.height
    except Exception:
        totalListed = 2700
    print(f"  전체 상장사: {totalListed}사")
    print(f"  docs 커버리지: {len(docsFiles)}/{totalListed} ({len(docsFiles)/totalListed*100:.1f}%)")

    # 전체 signal 실행
    t0 = time.time()
    df = scan_signal(verbose=False)
    elapsed = time.time() - t0
    print(f"\n  전체 signal 실행: {elapsed:.1f}s")

    if df is not None and not df.is_empty():
        print(f"  결과: {df.height}행, 컬럼: {df.columns}")
        # 연도별 커버리지
        if "year" in df.columns and "companies" in df.columns:
            yearly = df.group_by("year").agg(pl.col("companies").sum()).sort("year")
            print(f"\n  연도별 기업수 합:")
            for row in yearly.iter_rows(named=True):
                print(f"    {row['year']}: {row['companies']}사")

        # 키워드별 총 언급수
        if "keyword" in df.columns and "totalMentions" in df.columns:
            topKw = df.group_by("keyword").agg(pl.col("totalMentions").sum().alias("mentions")).sort("mentions", descending=True).head(10)
            print(f"\n  키워드 TOP 10:")
            for row in topKw.iter_rows(named=True):
                print(f"    {row['keyword']}: {row['mentions']}건")
    else:
        print("  signal 결과 없음!")
        elapsed = 0

    # 부분매칭 오탐 체크 (AI)
    print("\n  === 부분매칭 오탐 검사 (AI 키워드) ===")
    sampleFiles = docsFiles[:5] if docsFiles else []
    falsePositives = 0
    truePositives = 0
    for p in sampleFiles:
        try:
            lf = pl.scan_parquet(str(p))
            schema = lf.collect_schema().names()
            textCol = "section_content" if "section_content" in schema else "content" if "content" in schema else None
            if textCol is None:
                continue
            texts = lf.select(textCol).collect()[textCol].drop_nulls().to_list()
            for text in texts[:20]:
                count = str(text).count("AI")
                if count > 0:
                    # 진짜 AI인지 체크 (앞뒤 문자가 영문이면 오탐 가능성)
                    import re
                    trueMatches = len(re.findall(r'(?<![A-Za-z])AI(?![A-Za-z])', str(text)))
                    falsePositives += (count - trueMatches)
                    truePositives += trueMatches
        except (pl.exceptions.PolarsError, OSError):
            continue

    print(f"  샘플 5종목: 진양성 {truePositives}건, 오탐 {falsePositives}건")
    if truePositives + falsePositives > 0:
        print(f"  오탐률: {falsePositives/(truePositives+falsePositives)*100:.1f}%")

    allKw = [kw for kws in KEYWORDS.values() for kw in kws]
    print(f"\n  등록 키워드: {len(allKw)}개 ({', '.join(sorted(KEYWORDS.keys()))})")

    return {
        "docsFiles": len(docsFiles),
        "totalListed": totalListed,
        "coverage": round(len(docsFiles) / totalListed * 100, 1),
        "elapsed": elapsed,
        "falsePositives": falsePositives,
        "truePositives": truePositives,
    }


# ── P0-3: peers 축 품질 ─────────────────────────────────────


def auditPeers() -> dict:
    """peers 축 전수조사."""
    print("\n=== [P0] peers 축 품질 조사 ===")

    # WICS→US 매핑 테이블 커버리지
    from dartlab.scan.peer.discover import _WICS_TO_US_PEERS
    print(f"  WICS→US 매핑 섹터: {len(_WICS_TO_US_PEERS)}개")
    for sector, tickers in sorted(_WICS_TO_US_PEERS.items()):
        print(f"    {sector}: {tickers}")

    # 전체 상장사 섹터 분류 성공률
    try:
        import dartlab
        listing = dartlab.listing()
        totalListed = listing.height
    except Exception:
        totalListed = 0
        listing = None

    # 섹터 분류 테스트 (표본 50개)
    if listing is not None and "stockCode" in listing.columns:
        codes = listing["stockCode"].to_list()[:50]
        classified = 0
        itFallback = 0
        failed = 0

        from dartlab.scan.peer.discover import crossBorderPeers
        for code in codes:
            try:
                result = crossBorderPeers(code, topK=3)
                if result is not None:
                    classified += 1
                    # IT fallback 감지: IT 디폴트 피어인지 확인
                    itDefault = _WICS_TO_US_PEERS.get("IT", [])
                    if result == itDefault[:3]:
                        itFallback += 1
                else:
                    failed += 1
            except (ValueError, KeyError, ImportError):
                failed += 1

        print(f"\n  표본 50사 결과:")
        print(f"    분류 성공: {classified}사")
        print(f"    IT fallback 의심: {itFallback}사 ({itFallback/max(classified,1)*100:.1f}%)")
        print(f"    실패: {failed}사")
    else:
        classified = 0
        itFallback = 0
        failed = 0

    return {
        "wicsSectors": len(_WICS_TO_US_PEERS),
        "sampleClassified": classified,
        "itFallback": itFallback,
        "failed": failed,
    }


# ── P1-1: account 축 품질 ───────────────────────────────────


def auditAccount() -> dict:
    """account 축 전수조사."""
    from dartlab.providers.dart.finance.scanAccount import scanAccount

    print("\n=== [P1] account 축 품질 조사 ===")

    testCases = [
        ("revenue", "매출액"),
        ("operatingIncome", "영업이익"),
        ("totalAssets", "자산총계"),
        ("totalEquity", "자본총계"),
    ]

    results = {}
    for snakeId, label in testCases:
        t0 = time.time()
        try:
            df = scanAccount(snakeId, annual=True)
            elapsed = time.time() - t0
            total = df.height
            nullAmt = df.filter(pl.col("amount").is_null()).height if "amount" in df.columns else 0
            uniqueCodes = df["stockCode"].n_unique() if "stockCode" in df.columns else 0
            print(f"  {label}({snakeId}): {total}행, {uniqueCodes}종목, null={nullAmt}, {elapsed:.1f}s")

            # 기간 분포
            if "period" in df.columns:
                periods = df["period"].unique().sort().to_list()
                print(f"    기간: {periods[:5]}{'...' if len(periods) > 5 else ''}")

            results[snakeId] = {"total": total, "uniqueCodes": uniqueCodes, "nullAmt": nullAmt, "elapsed": elapsed}
        except (ValueError, KeyError) as e:
            print(f"  {label}({snakeId}): 실패 - {e}")
            results[snakeId] = {"error": str(e)}

    return results


# ── P1-2: ratio 축 품질 ─────────────────────────────────────


def auditRatio() -> dict:
    """ratio 축 전수조사."""
    from dartlab.providers.dart.finance.scanAccount import scanRatio, scanRatioList

    print("\n=== [P1] ratio 축 품질 조사 ===")

    ratioNames = scanRatioList()
    print(f"  사용 가능 비율: {len(ratioNames)}개")
    print(f"    {ratioNames}")

    testRatios = ["roe", "debtRatio", "operatingMargin", "currentRatio"]
    results = {}
    for name in testRatios:
        if name not in ratioNames:
            print(f"  {name}: 목록에 없음!")
            continue
        t0 = time.time()
        try:
            df = scanRatio(name, annual=True)
            elapsed = time.time() - t0
            total = df.height
            uniqueCodes = df["stockCode"].n_unique() if "stockCode" in df.columns else 0
            nullVal = df.filter(pl.col("value").is_null()).height if "value" in df.columns else 0
            vals = df.filter(pl.col("value").is_not_null())["value"].cast(pl.Float64) if "value" in df.columns else pl.Series([])

            print(f"  {name}: {total}행, {uniqueCodes}종목, null={nullVal} ({nullVal/max(total,1)*100:.1f}%), {elapsed:.1f}s")
            if vals.len() > 0:
                print(f"    분포: min={vals.min():.2f}, median={vals.median():.2f}, max={vals.max():.2f}")
                # 자본잠식 체크 (ROE)
                if name == "roe":
                    negEquity = vals.filter(vals < -100).len()
                    print(f"    ROE<-100% (자본잠식 의심): {negEquity}사")

            results[name] = {"total": total, "uniqueCodes": uniqueCodes, "nullRate": round(nullVal / max(total, 1) * 100, 1)}
        except (ValueError, KeyError) as e:
            print(f"  {name}: 실패 - {e}")
            results[name] = {"error": str(e)}

    return results


# ── P1-3: screen 축 품질 ────────────────────────────────────


def auditScreen() -> dict:
    """screen 축 품질 조사 (빌드 성능 + 비율 null률 + preset 건수)."""
    from dartlab.scan.screen.screen import screen, presets, benchmark, _buildMarketRatios, _RATIO_FIELDS

    print("\n=== [P1] screen 축 품질 조사 ===")

    # 빌드 시간 측정
    t0 = time.time()
    marketDf = _buildMarketRatios(verbose=False)
    buildTime = time.time() - t0
    print(f"  빌드: {buildTime:.1f}s, {marketDf.height}종목")

    # 29개 비율 null률
    print(f"\n  비율 null률 (상위 10):")
    nullRates = {}
    for field in _RATIO_FIELDS:
        if field in marketDf.columns:
            nullCount = marketDf[field].null_count()
            nullRates[field] = round(nullCount / marketDf.height * 100, 1)

    sortedNulls = sorted(nullRates.items(), key=lambda x: x[1], reverse=True)
    for field, rate in sortedNulls[:10]:
        print(f"    {field}: {rate}%")

    # preset별 건수
    print(f"\n  preset별 결과:")
    presetNames = presets()
    presetCounts = {}
    for name in presetNames:
        try:
            result = screen(name, verbose=False)
            presetCounts[name] = result.height
            print(f"    {name}: {result.height}사")
        except (ValueError, KeyError) as e:
            presetCounts[name] = f"실패: {e}"
            print(f"    {name}: 실패 - {e}")

    # 벤치마크
    t0 = time.time()
    bm = benchmark(verbose=False)
    bmTime = time.time() - t0
    print(f"\n  benchmark: {bm.height}섹터, {bmTime:.1f}s")

    return {
        "buildTime": buildTime,
        "totalCodes": marketDf.height,
        "nullRates": dict(sortedNulls[:10]),
        "presetCounts": presetCounts,
    }


# ── P2-1: governance/workforce/capital 축 ────────────────────


def auditCoreAxes() -> dict:
    """governance, workforce, capital 간략 조사."""
    results = {}

    for axisName, importFn in [
        ("governance", lambda: __import__("dartlab.scan.governance", fromlist=["scan_governance"]).scan_governance),
        ("workforce", lambda: __import__("dartlab.scan.workforce", fromlist=["scan_workforce"]).scan_workforce),
        ("capital", lambda: __import__("dartlab.scan.capital", fromlist=["scan_capital"]).scan_capital),
    ]:
        print(f"\n=== [P2] {axisName} 축 간략 조사 ===")
        try:
            fn = importFn()
            t0 = time.time()
            df = fn(verbose=False)
            elapsed = time.time() - t0
            print(f"  {df.height}행, {elapsed:.1f}s, 컬럼: {df.columns}")

            nullRates = {}
            for c in df.columns:
                if c == "종목코드":
                    continue
                nullCount = df[c].null_count()
                rate = round(nullCount / df.height * 100, 1)
                nullRates[c] = rate
                if rate > 20:
                    print(f"  [주의] {c}: null {rate}%")

            results[axisName] = {
                "total": df.height,
                "elapsed": elapsed,
                "highNullCols": {k: v for k, v in nullRates.items() if v > 20},
            }
        except (ImportError, ValueError, OSError) as e:
            print(f"  {axisName}: 실패 - {e}")
            results[axisName] = {"error": str(e)}

    return results


# ── 교차검증: debt 부채비율 vs screen debtRatio ──────────────


def crossValidateDebtVsScreen() -> dict:
    """debt 부채비율과 screen debtRatio 비교."""
    print("\n=== 교차검증: debt vs screen 부채비율 ===")

    from dartlab.scan.debt import scan_debt
    from dartlab.scan.screen.screen import _buildMarketRatios

    debtDf = scan_debt(verbose=False)
    screenDf = _buildMarketRatios(verbose=False)

    if "부채비율" not in debtDf.columns or "debtRatio" not in screenDf.columns:
        print("  필수 컬럼 없음")
        return {"error": "missing columns"}

    # join
    debtSub = debtDf.select(["종목코드", "부채비율"]).rename({"종목코드": "stockCode", "부채비율": "debtRatioDebt"})
    screenSub = screenDf.select(["stockCode", "debtRatio"]).rename({"debtRatio": "debtRatioScreen"})

    merged = debtSub.join(screenSub, on="stockCode", how="inner")
    both = merged.filter(pl.col("debtRatioDebt").is_not_null() & pl.col("debtRatioScreen").is_not_null())

    print(f"  교집합: {merged.height}사, 양쪽 유효: {both.height}사")

    if both.height > 0:
        diff = (both["debtRatioDebt"].cast(pl.Float64) - both["debtRatioScreen"].cast(pl.Float64)).abs()
        print(f"  차이 분포: median={diff.median():.2f}, mean={diff.mean():.2f}, max={diff.max():.2f}")
        bigDiff = (diff > 10).sum()
        print(f"  차이>10%p: {bigDiff}사 ({bigDiff/both.height*100:.1f}%)")

    return {
        "merged": merged.height,
        "bothValid": both.height,
        "bigDiffCount": int(bigDiff) if both.height > 0 else 0,
    }


# ── main ─────────────────────────────────────────────────────


if __name__ == "__main__":
    print("=" * 60)
    print("scan 13축 데이터 품질 전수조사")
    print("=" * 60)

    allResults = {}

    # Phase 선택 (메모리 안전)
    phase = sys.argv[1] if len(sys.argv) > 1 else "p0"

    if phase in ("p0", "all"):
        allResults["debt"] = auditDebt()
        allResults["signal"] = auditSignal()
        allResults["peers"] = auditPeers()

    if phase in ("p1", "all"):
        allResults["account"] = auditAccount()
        allResults["ratio"] = auditRatio()
        allResults["screen"] = auditScreen()

    if phase in ("p2", "all"):
        allResults["coreAxes"] = auditCoreAxes()

    if phase in ("cross", "all"):
        allResults["crossValidation"] = crossValidateDebtVsScreen()

    # 종합 출력
    print("\n" + "=" * 60)
    print("종합 결과")
    print("=" * 60)
    for k, v in allResults.items():
        print(f"\n[{k}]")
        if isinstance(v, dict):
            for kk, vv in v.items():
                print(f"  {kk}: {vv}")
