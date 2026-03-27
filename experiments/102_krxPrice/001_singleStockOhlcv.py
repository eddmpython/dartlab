"""
실험 ID: 102-001
실험명: KRX 개별 종목 OHLCV 직접 호출

목적:
- pykrx 의존 없이 data.krx.co.kr POST 엔드포인트로 삼성전자 OHLCV를 직접 가져올 수 있는지 검증
- 응답 구조, 숫자 포맷, 속도를 확인

가설:
1. KRX POST API는 bld + isuCd + 날짜 파라미터만으로 OHLCV JSON을 반환한다
2. 응답 시간 2초 이내
3. 숫자는 콤마 포함 문자열로 내려오므로 정제 필요

방법:
1. ticker → ISIN 변환 (finder_stkisu)
2. 개별종목시세 API (MDCSTAT01701) 호출
3. 응답 구조 분석 + Polars DataFrame 변환
4. Naver chart OHLCV와 데이터 비교

결과 (실험 후 작성):
- tickerToIsin("005930") → KR7005930003 성공 (3.51초, finder_stkisu 비로그인 허용)
- fetchOhlcv(MDCSTAT01701) → HTTP 400 "LOGOUT" 실패
- KRX가 2026-02-27부터 dbms/MDC/STAT/* 경로에 로그인 필수화
- dbms/comm/finder/* (종목검색)만 비로그인 허용
- pykrx도 현재 깨진 상태 (PyPI v1.2.4, 로그인 PR #282 미머지)

결론:
- 기각: KRX 직접 스크래핑은 회원 로그인 세션 없이 OHLCV 불가
- 개별 종목 price는 기존 Naver → Yahoo fallback 유지
- KRX 계정 기반 세션 로그인은 별도 실험으로 분리 필요

실험일: 2026-03-27
"""

import httpx
import time
import polars as pl
import re


KRX_URL = "https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd",
}


def cleanNumber(s: str) -> float | None:
    """KRX 응답의 콤마 포함 문자열 → float."""
    if not s or s == "-":
        return None
    cleaned = re.sub(r"[^\d.\-]", "", s)
    if not cleaned or cleaned == "-":
        return None
    return float(cleaned)


def tickerToIsin(ticker: str) -> str | None:
    """6자리 종목코드 → ISIN 변환."""
    t0 = time.perf_counter()
    resp = httpx.post(
        KRX_URL,
        headers=HEADERS,
        data={
            "bld": "dbms/comm/finder/finder_stkisu",
            "locale": "ko_KR",
            "mktsel": "ALL",
            "searchText": ticker,
            "typeNo": "0",
        },
        timeout=10,
    )
    elapsed = time.perf_counter() - t0
    data = resp.json()
    items = data.get("block1", [])
    print(f"[tickerToIsin] {ticker} → {len(items)}건 응답, {elapsed:.2f}s")

    for item in items:
        if item.get("short_code") == ticker:
            isin = item["full_code"]
            print(f"  ISIN: {isin}, 종목명: {item.get('codeName')}")
            return isin
    return None


def fetchOhlcv(isin: str, startDate: str, endDate: str, adjusted: bool = True) -> list[dict]:
    """KRX 개별종목시세 API → OHLCV list."""
    t0 = time.perf_counter()
    resp = httpx.post(
        KRX_URL,
        headers=HEADERS,
        data={
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01701",
            "isuCd": isin,
            "strtDd": startDate,
            "endDd": endDate,
            "adjStkPrc": "2" if adjusted else "1",
        },
        timeout=10,
    )
    elapsed = time.perf_counter() - t0
    data = resp.json()
    rows = data.get("output", [])
    print(f"[fetchOhlcv] {len(rows)}행 응답, {elapsed:.2f}s")

    if rows:
        print(f"  첫 행 keys: {list(rows[0].keys())}")
        print(f"  첫 행 sample: {rows[0]}")

    result = []
    for row in rows:
        result.append({
            "date": row.get("TRD_DD", "").replace("/", "-"),
            "open": cleanNumber(row.get("TDD_OPNPRC", "")),
            "high": cleanNumber(row.get("TDD_HGPRC", "")),
            "low": cleanNumber(row.get("TDD_LWPRC", "")),
            "close": cleanNumber(row.get("TDD_CLSPRC", "")),
            "volume": int(cleanNumber(row.get("ACC_TRDVOL", "")) or 0),
            "tradingValue": cleanNumber(row.get("ACC_TRDVAL", "")),
            "changePct": cleanNumber(row.get("FLUC_RT", "")),
            "marketCap": cleanNumber(row.get("MKTCAP", "")),
            "shares": cleanNumber(row.get("LIST_SHRS", "")),
        })
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("KRX 개별 종목 OHLCV 직접 호출 실험")
    print("=" * 60)

    # 1) ticker → ISIN
    isin = tickerToIsin("005930")
    if not isin:
        print("ISIN 변환 실패")
        exit(1)

    # 2) 최근 1개월 OHLCV
    rows = fetchOhlcv(isin, "20260301", "20260327")

    # 3) Polars DataFrame
    if rows:
        df = pl.DataFrame(rows)
        print(f"\n[DataFrame] shape={df.shape}")
        print(df.head(10))
        print(f"\n최신 종가: {rows[0].get('close')}")
        print(f"최신 시총: {rows[0].get('marketCap')}")
    else:
        print("데이터 없음")
