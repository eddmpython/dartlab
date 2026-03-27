"""
실험 ID: 102-002
실험명: 네이버 API로 전체 시장 일별 스냅샷

목적:
- KRX data.krx.co.kr는 2026-02-27부터 로그인 필수 → 스크래핑 불가
- 네이버 m.stock.naver.com/api/stocks/marketValue 엔드포인트로 전종목 데이터 수집 가능성 검증
- 비로그인, 페이지네이션(100건씩) 방식

가설:
1. KOSPI ~2400 + KOSDAQ ~1800 = ~4200종목을 전부 가져올 수 있다
2. 종목코드, 현재가, 등락률, 거래량, 거래대금, 시가총액 포함
3. 비동기 병렬 호출로 5초 이내 전체 수집 가능

방법:
1. marketValue API — KOSPI/KOSDAQ 각각 page=1부터 순차/병렬 호출
2. 응답 구조 분석 → Polars DataFrame 변환
3. 거래대금 상위, 시총 분포, 등락률 통계 확인
4. 속도 측정 (동기 순차 vs 비동기 병렬)

결과 (실험 후 작성):
- 네이버 m.stock.naver.com/api/stocks/marketValue/{market} 엔드포인트 사용
- pageSize=100 고정 (200 이상은 400 에러)
- KOSPI 2417종목(25페이지) + KOSDAQ 1821종목(19페이지) = 4238종목
- 비동기 병렬 수집: 0.81~0.92초 (44 HTTP 요청)
- 제공 필드: ticker, name, close, changePct, volume, tradingValue, marketCap, marketStatus
- OHLCV 중 open/high/low 없음 — close, 등락률, 거래량, 거래대금, 시총만 제공
- 장중 실시간 데이터 포함 (marketStatus=OPEN 확인)
- 등락률: 평균 -0.63%, 상승 1119 / 하락 2785 / 보합 334 (하락장)

결론:
- 채택: 네이버 marketValue API로 전체 시장 일별 스냅샷 수집 가능
- 1초 이내 전종목 수집 — 속도 충분
- 제한: open/high/low 미제공 → 완전한 OHLCV가 아닌 "시장 스냅샷"
- KRX data.krx.co.kr는 2026-02-27부터 로그인 필수 → 비로그인 스크래핑 불가
- 전체 시장 스냅샷 기능으로 충분히 활용 가능 (거래대금 순위, 시총 순위, 등락률 분포 등)

실험일: 2026-03-27
"""

import httpx
import time
import math
import re
import asyncio
import polars as pl


BASE_URL = "https://m.stock.naver.com/api/stocks/marketValue"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PAGE_SIZE = 100


def cleanNumber(s: str | None) -> float | None:
    """콤마 포함 문자열 → float."""
    if s is None or s == "N/A":
        return None
    if isinstance(s, (int, float)):
        return float(s)
    cleaned = re.sub(r"[^\d.\-]", "", str(s))
    if not cleaned or cleaned == "-":
        return None
    return float(cleaned)


def parseStock(s: dict) -> dict:
    """네이버 API 응답 → 표준 dict."""
    return {
        "ticker": s.get("itemCode", ""),
        "name": s.get("stockName", ""),
        "close": cleanNumber(s.get("closePrice")),
        "changePct": cleanNumber(s.get("fluctuationsRatio")),
        "volume": int(cleanNumber(s.get("accumulatedTradingVolume")) or 0),
        "tradingValue": cleanNumber(s.get("accumulatedTradingValue")),
        "marketCap": cleanNumber(s.get("marketValue")),
        "marketStatus": s.get("marketStatus"),
    }


async def fetchAllStocks(market: str = "KOSPI") -> list[dict]:
    """네이버 시총순위 API로 전종목 수집."""
    async with httpx.AsyncClient(headers=HEADERS, timeout=10) as client:
        # 1) 첫 페이지 → totalCount 확인
        r = await client.get(f"{BASE_URL}/{market}?page=1&pageSize={PAGE_SIZE}")
        data = r.json()
        total = data.get("totalCount", 0)
        stocks = [parseStock(s) for s in data.get("stocks", [])]
        totalPages = math.ceil(total / PAGE_SIZE)
        print(f"[{market}] total={total}, pages={totalPages}")

        if totalPages <= 1:
            return stocks

        # 2) 나머지 페이지 병렬 호출
        tasks = []
        for page in range(2, totalPages + 1):
            tasks.append(client.get(f"{BASE_URL}/{market}?page={page}&pageSize={PAGE_SIZE}"))

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for resp in responses:
            if isinstance(resp, BaseException):
                print(f"  page error: {resp}")
                continue
            try:
                d = resp.json()
                stocks.extend(parseStock(s) for s in d.get("stocks", []))
            except Exception as e:
                print(f"  parse error: {e}")

    return stocks


async def main():
    print("=" * 60)
    print("네이버 API 전체 시장 스냅샷 실험")
    print("=" * 60)

    t0 = time.perf_counter()

    # KOSPI + KOSDAQ 병렬
    kospiTask = fetchAllStocks("KOSPI")
    kosdaqTask = fetchAllStocks("KOSDAQ")
    kospi, kosdaq = await asyncio.gather(kospiTask, kosdaqTask)

    elapsed = time.perf_counter() - t0
    print(f"\n수집 완료: KOSPI {len(kospi)} + KOSDAQ {len(kosdaq)} = {len(kospi)+len(kosdaq)}종목, {elapsed:.2f}s")

    # Polars DataFrame
    allStocks = kospi + kosdaq
    if not allStocks:
        print("데이터 없음")
        return

    df = pl.DataFrame(allStocks)
    print(f"\nDataFrame: {df.shape}")

    # 거래대금 상위 10
    top10 = df.filter(pl.col("tradingValue").is_not_null()).sort("tradingValue", descending=True).head(10)
    print("\n[거래대금 상위 10]")
    print(top10.select("ticker", "name", "close", "changePct", "volume", "tradingValue", "marketCap"))

    # 시총 상위 10
    topMcap = df.filter(pl.col("marketCap").is_not_null()).sort("marketCap", descending=True).head(10)
    print("\n[시총 상위 10]")
    print(topMcap.select("ticker", "name", "close", "marketCap"))

    # 등락률 통계
    pctCol = df.filter(pl.col("changePct").is_not_null())["changePct"]
    if pctCol.len() > 0:
        print(f"\n[등락률 통계]")
        print(f"  평균: {pctCol.mean():.2f}%")
        print(f"  중앙값: {pctCol.median():.2f}%")
        print(f"  상승: {(pctCol > 0).sum()}, 하락: {(pctCol < 0).sum()}, 보합: {(pctCol == 0).sum()}")

    # 삼성전자
    samsung = df.filter(pl.col("ticker") == "005930")
    if samsung.height > 0:
        print(f"\n[삼성전자]")
        print(samsung)


if __name__ == "__main__":
    asyncio.run(main())
