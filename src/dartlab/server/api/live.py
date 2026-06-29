from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from time import time
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

router = APIRouter()

_KST = ZoneInfo("Asia/Seoul")
_CODE_RE = re.compile(r"^[0-9A-Z]{1,10}$")
_NAVER_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
}
_KIS_BASE = os.environ.get("DARTLAB_KIS_BASE") or os.environ.get("KIS_BASE") or "https://openapi.koreainvestment.com:9443"
_KIS_APP_KEY_PATH = Path(os.environ.get("DARTLAB_KIS_APP_KEY_PATH") or os.environ.get("KIS_APP_KEY_PATH") or "~/.config/kis/app_key").expanduser()
_KIS_APP_SECRET_PATH = Path(os.environ.get("DARTLAB_KIS_APP_SECRET_PATH") or os.environ.get("KIS_APP_SECRET_PATH") or "~/.config/kis/app_secret").expanduser()
_KIS_TOKEN_CACHE = Path(os.environ.get("DARTLAB_KIS_TOKEN_CACHE") or os.environ.get("KIS_TOKEN_CACHE") or "~/.cache/dartlab/kis_access_token.json").expanduser()
_KIS_QUOTE_TR_ID = os.environ.get("DARTLAB_KIS_QUOTE_TR_ID") or os.environ.get("KIS_TR_ID") or "FHKST01010100"
_KIS_MINUTE_TR_ID = os.environ.get("DARTLAB_KIS_MINUTE_TR_ID") or "FHKST03010200"
_KIS_TOKEN_GRACE_SEC = int(os.environ.get("DARTLAB_KIS_TOKEN_TTL_GRACE_SEC") or os.environ.get("KIS_TOKEN_TTL_GRACE_SEC") or "300")
_KIS_QUOTE_INTERVAL_MS = max(500, int(os.environ.get("DARTLAB_KIS_QUOTE_INTERVAL_MS") or "500"))
_KIS_QUOTE_CACHE_MS = max(250, int(os.environ.get("DARTLAB_KIS_QUOTE_CACHE_MS") or "500"))
_KIS_MINUTE_CACHE_MS = max(1000, int(os.environ.get("DARTLAB_KIS_MINUTE_CACHE_MS") or "5000"))
_KIS_MINUTE_MAX_BARS = max(120, int(os.environ.get("DARTLAB_KIS_MINUTE_MAX_BARS") or "450"))

_kis_token_lock = asyncio.Lock()
_kis_quote_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_kis_minute_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def _json(data: Any, *, cache_control: str = "no-store") -> JSONResponse:
    return JSONResponse(data, headers={"Cache-Control": cache_control})


def _num(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        n = float(value)
        return n if n == n and n not in (float("inf"), float("-inf")) else None
    if value is None:
        return None
    text = str(value).replace(",", "").replace("%", "").replace(" ", "").replace("\u2212", "-")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _int(value: Any) -> int | None:
    n = _num(value)
    return int(n) if n is not None else None


def _normalize_code(code: str) -> str:
    c = re.sub(r"[^0-9A-Za-z]", "", code or "").upper()
    if not c or not _CODE_RE.match(c):
        raise HTTPException(status_code=400, detail="invalid_code")
    return c


def _market_label(status: str | None) -> str:
    if status == "OPEN":
        return "장중"
    if status == "CLOSE":
        return "마감"
    if status == "PREPARE":
        return "개장 준비"
    return status or "확인 중"


def _kis_available() -> bool:
    disabled = os.environ.get("DARTLAB_KIS_DISABLE", "").strip().lower() in {"1", "true", "yes"}
    return not disabled and _KIS_APP_KEY_PATH.is_file() and _KIS_APP_SECRET_PATH.is_file()


def _read_secret(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _save_json_private(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _token_expires_at(payload: dict[str, Any]) -> int | None:
    raw = payload.get("expires_at")
    if isinstance(raw, (int, float)):
        return int(raw)
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)

    text = str(payload.get("access_token_token_expired") or "").strip()
    if text:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return int(datetime.strptime(text[:19], fmt).replace(tzinfo=_KST).timestamp())
            except ValueError:
                continue
    return None


def _cached_kis_token() -> str | None:
    payload = _load_json(_KIS_TOKEN_CACHE)
    if not payload:
        return None
    token = str(payload.get("access_token") or "").strip()
    expires_at = _token_expires_at(payload)
    if token and expires_at and expires_at - int(time()) > _KIS_TOKEN_GRACE_SEC:
        return token
    return None


async def _issue_kis_token(client: httpx.AsyncClient, app_key: str, app_secret: str) -> str:
    resp = await client.post(
        f"{_KIS_BASE.rstrip('/')}/oauth2/tokenP",
        json={"grant_type": "client_credentials", "appkey": app_key, "appsecret": app_secret},
        headers={"content-type": "application/json; charset=utf-8"},
    )
    body = resp.json()
    token = str(body.get("access_token") or "").strip()
    if not resp.is_success or not token:
        msg = body.get("msg_cd") or body.get("error_code") or body.get("error") or resp.status_code
        raise RuntimeError(f"kis_token_failed:{msg}")

    issued_at = int(time())
    expires_in = int(_num(body.get("expires_in")) or 86400)
    payload = {
        "access_token": token,
        "token_type": body.get("token_type") or "Bearer",
        "issued_at": issued_at,
        "expires_at": issued_at + max(1, min(expires_in, 86400)),
        "expires_in": expires_in,
    }
    _save_json_private(_KIS_TOKEN_CACHE, payload)
    return token


async def _kis_token(client: httpx.AsyncClient) -> str:
    cached = _cached_kis_token()
    if cached:
        return cached

    async with _kis_token_lock:
        cached = _cached_kis_token()
        if cached:
            return cached
        return await _issue_kis_token(client, _read_secret(_KIS_APP_KEY_PATH), _read_secret(_KIS_APP_SECRET_PATH))


def _market_status_now() -> tuple[str, str, bool]:
    now = datetime.now(_KST)
    minutes = now.hour * 60 + now.minute
    if now.weekday() >= 5:
        return ("CLOSE", "휴장", False)
    if 9 * 60 <= minutes <= 15 * 60 + 30:
        return ("OPEN", "장중", True)
    if 8 * 60 <= minutes < 9 * 60:
        return ("PREPARE", "개장 준비", False)
    return ("CLOSE", "마감", False)


def _date_candidates(days: int = 8) -> list[str]:
    today = datetime.now(_KST).date()
    return [(today - timedelta(days=i)).strftime("%Y%m%d") for i in range(days)]


def _local_dt(value: Any) -> datetime | None:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) < 12:
        return None
    if len(digits) == 12:
        digits += "00"
    try:
        return datetime.strptime(digits[:14], "%Y%m%d%H%M%S").replace(tzinfo=_KST)
    except ValueError:
        return None


def _bar_from_naver(item: dict[str, Any]) -> dict[str, Any] | None:
    dt = _local_dt(item.get("localDateTime"))
    close = _num(item.get("currentPrice"))
    if dt is None or close is None or close <= 0:
        return None
    return {
        "t": dt.isoformat(),
        "o": _num(item.get("openPrice")) or close,
        "h": _num(item.get("highPrice")) or close,
        "l": _num(item.get("lowPrice")) or close,
        "c": close,
        "v": _int(item.get("accumulatedTradingVolume")) or 0,
    }


def _kis_minute_hour_now() -> str:
    now = datetime.now(_KST)
    minutes = now.hour * 60 + now.minute
    if now.weekday() < 5 and 9 * 60 <= minutes <= 15 * 60 + 30:
        return now.strftime("%H%M%S")
    return "153000"


def _bar_from_kis_minute(item: dict[str, Any]) -> dict[str, Any] | None:
    date = re.sub(r"\D", "", str(item.get("stck_bsop_date") or ""))[:8]
    hour = re.sub(r"\D", "", str(item.get("stck_cntg_hour") or ""))[:6]
    if len(date) != 8 or len(hour) < 4:
        return None
    if len(hour) == 4:
        hour += "00"
    try:
        dt = datetime.strptime(date + hour[:6], "%Y%m%d%H%M%S").replace(tzinfo=_KST)
    except ValueError:
        return None

    close = _num(item.get("stck_prpr"))
    if close is None or close <= 0:
        return None
    open_ = _num(item.get("stck_oprc")) or close
    high = _num(item.get("stck_hgpr")) or close
    low = _num(item.get("stck_lwpr")) or close
    return {
        "t": dt.isoformat(),
        "o": open_,
        "h": max(open_, high, low, close),
        "l": min(open_, high, low, close),
        "c": close,
        "v": _int(item.get("cntg_vol")) or _int(item.get("acml_vol")) or 0,
    }


def _aggregate_bars(bars: list[dict[str, Any]], minutes: int) -> list[dict[str, Any]]:
    if minutes <= 1:
        return bars
    buckets: dict[str, list[dict[str, Any]]] = {}
    for bar in bars:
        dt = datetime.fromisoformat(str(bar["t"]))
        start = dt.replace(minute=(dt.minute // minutes) * minutes, second=0, microsecond=0)
        buckets.setdefault(start.isoformat(), []).append(bar)

    out: list[dict[str, Any]] = []
    for key in sorted(buckets):
        group = buckets[key]
        out.append(
            {
                "t": key,
                "o": group[0]["o"],
                "h": max(float(x["h"]) for x in group),
                "l": min(float(x["l"]) for x in group),
                "c": group[-1]["c"],
                "v": sum(int(x.get("v") or 0) for x in group),
            }
        )
    return out


async def _get_json(url: str, *, timeout: float = 5.0) -> Any:
    async with httpx.AsyncClient(headers=_NAVER_HEADERS, timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def _naver_quote_payload(stock_code: str) -> dict[str, Any]:
    url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{stock_code}"
    data = await _get_json(url, timeout=5.0)

    item = (data.get("datas") or [None])[0] if isinstance(data, dict) else None
    if not isinstance(item, dict):
        raise HTTPException(status_code=404, detail="quote_not_found")

    price = _num(item.get("closePriceRaw")) or _num(item.get("closePrice"))
    change = _num(item.get("compareToPreviousClosePriceRaw")) or _num(item.get("compareToPreviousClosePrice"))
    change_rate = _num(item.get("fluctuationsRatioRaw")) or _num(item.get("fluctuationsRatio"))
    if price is None or change is None or change_rate is None:
        raise HTTPException(status_code=502, detail="quote_parse_failed")

    exchange = item.get("stockExchangeType") or {}
    market_status = str(item.get("marketStatus") or "")
    delay_time = _num(exchange.get("delayTime")) if isinstance(exchange, dict) else None
    payload = {
        "code": stock_code,
        "name": item.get("stockName") or stock_code,
        "provider": "naver",
        "currency": "KRW",
        "price": price,
        "changeAmount": change,
        "changeRate": change_rate,
        "open": _num(item.get("openPriceRaw")) or _num(item.get("openPrice")),
        "high": _num(item.get("highPriceRaw")) or _num(item.get("highPrice")),
        "low": _num(item.get("lowPriceRaw")) or _num(item.get("lowPrice")),
        "volume": _int(item.get("accumulatedTradingVolumeRaw")) or _int(item.get("accumulatedTradingVolume")),
        "tradedValue": _int(item.get("accumulatedTradingValueRaw")),
        "marketCap": _int(item.get("marketValueFullRaw")) or _int(item.get("marketValueFull")),
        "marketStatus": market_status,
        "marketStatusLabel": _market_label(market_status),
        "isLive": delay_time == 0 and market_status == "OPEN",
        "refreshIntervalMs": max(1000, _int(data.get("pollingInterval")) or 7000),
        "tradedAt": item.get("localTradedAt") or datetime.now(_KST).isoformat(),
        "updatedAt": datetime.now(_KST).isoformat(),
    }
    return payload


async def _kis_quote_payload(stock_code: str) -> dict[str, Any]:
    now_ms = time() * 1000
    cached = _kis_quote_cache.get(stock_code)
    if cached and now_ms - cached[0] < _KIS_QUOTE_CACHE_MS:
        return {**cached[1], "cached": True}

    app_key = _read_secret(_KIS_APP_KEY_PATH)
    app_secret = _read_secret(_KIS_APP_SECRET_PATH)
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": stock_code}
    async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
        token = await _kis_token(client)
        resp = await client.get(
            f"{_KIS_BASE.rstrip('/')}/uapi/domestic-stock/v1/quotations/inquire-price",
            params=params,
            headers={
                "content-type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": app_key,
                "appsecret": app_secret,
                "tr_id": _KIS_QUOTE_TR_ID,
                "custtype": "P",
            },
        )
        body = resp.json()

    output = body.get("output") if isinstance(body, dict) else None
    if not resp.is_success or not isinstance(output, dict) or body.get("rt_cd") not in (None, "0"):
        msg = body.get("msg_cd") if isinstance(body, dict) else resp.status_code
        raise RuntimeError(f"kis_quote_failed:{msg}")

    price = _num(output.get("stck_prpr"))
    change = _num(output.get("prdy_vrss"))
    change_rate = _num(output.get("prdy_ctrt"))
    if price is None or change is None or change_rate is None:
        raise RuntimeError("kis_quote_parse_failed")

    market_status, market_status_label, is_live = _market_status_now()
    payload = {
        "code": stock_code,
        "name": output.get("hts_kor_isnm") or stock_code,
        "provider": "kis",
        "currency": "KRW",
        "price": price,
        "changeAmount": change,
        "changeRate": change_rate,
        "open": _num(output.get("stck_oprc")),
        "high": _num(output.get("stck_hgpr")),
        "low": _num(output.get("stck_lwpr")),
        "volume": _int(output.get("acml_vol")),
        "tradedValue": _int(output.get("acml_tr_pbmn")),
        "marketCap": _int(output.get("hts_avls")),
        "marketStatus": market_status,
        "marketStatusLabel": market_status_label,
        "isLive": is_live,
        "refreshIntervalMs": _KIS_QUOTE_INTERVAL_MS,
        "tradedAt": datetime.now(_KST).isoformat(),
        "updatedAt": datetime.now(_KST).isoformat(),
    }
    _kis_quote_cache[stock_code] = (now_ms, payload)
    return payload


async def _kis_minute_1m_bars(stock_code: str) -> list[dict[str, Any]]:
    now_ms = time() * 1000
    cached = _kis_minute_cache.get(stock_code)
    if cached and now_ms - cached[0] < _KIS_MINUTE_CACHE_MS:
        return cached[1]

    app_key = _read_secret(_KIS_APP_KEY_PATH)
    app_secret = _read_secret(_KIS_APP_SECRET_PATH)
    headers_base = {
        "content-type": "application/json; charset=utf-8",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": _KIS_MINUTE_TR_ID,
        "custtype": "P",
    }
    seen: dict[str, dict[str, Any]] = {}
    basis_date: str | None = None
    hour = _kis_minute_hour_now()

    async with httpx.AsyncClient(timeout=7.0, follow_redirects=True) as client:
        token = await _kis_token(client)
        headers = {**headers_base, "authorization": f"Bearer {token}"}
        for _ in range(14):
            resp = await client.get(
                f"{_KIS_BASE.rstrip('/')}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
                params={
                    "FID_ETC_CLS_CODE": "",
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": stock_code,
                    "FID_INPUT_HOUR_1": hour,
                    "FID_PW_DATA_INCU_YN": "Y",
                },
                headers=headers,
            )
            body = resp.json()
            if not resp.is_success or not isinstance(body, dict) or body.get("rt_cd") not in (None, "0"):
                msg = body.get("msg_cd") if isinstance(body, dict) else resp.status_code
                raise RuntimeError(f"kis_minute_failed:{msg}")

            rows = body.get("output2") or body.get("output") or []
            if not isinstance(rows, list) or not rows:
                break

            page_all: list[dict[str, Any]] = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                bar = _bar_from_kis_minute(row)
                if bar:
                    page_all.append(bar)
            if not page_all:
                break
            if basis_date is None:
                basis_date = max(str(bar["t"])[:10] for bar in page_all)
            page = [bar for bar in page_all if str(bar["t"]).startswith(basis_date)]
            if not page:
                break
            for bar in page:
                seen[str(bar["t"])] = bar

            earliest = min(page, key=lambda x: str(x["t"]))
            earliest_dt = datetime.fromisoformat(str(earliest["t"]))
            next_dt = earliest_dt - timedelta(minutes=1)
            if next_dt.date() != earliest_dt.date() or next_dt.hour < 9:
                break
            hour = next_dt.strftime("%H%M%S")
            if len(seen) >= _KIS_MINUTE_MAX_BARS:
                break
            await asyncio.sleep(0.25)

    all_bars = sorted(seen.values(), key=lambda x: str(x["t"]))
    if not all_bars:
        raise RuntimeError("kis_minute_empty")
    latest_date = basis_date or max(str(bar["t"])[:10] for bar in all_bars)
    bars = [bar for bar in all_bars if str(bar["t"]).startswith(latest_date)][-_KIS_MINUTE_MAX_BARS:]
    if len(bars) < 2:
        raise RuntimeError("kis_minute_empty")
    _kis_minute_cache[stock_code] = (now_ms, bars)
    return bars


async def _kis_minute_payload(stock_code: str, timeframe: str, minutes: int) -> dict[str, Any]:
    bars_1m = await _kis_minute_1m_bars(stock_code)
    bars = _aggregate_bars(bars_1m, minutes)
    latest = bars[-1]["t"]
    basis_date = str(latest)[:10]
    return {
        "code": stock_code,
        "provider": "kis",
        "currency": "KRW",
        "basisDate": basis_date,
        "isFallbackDate": basis_date != datetime.now(_KST).strftime("%Y-%m-%d"),
        "timeframe": timeframe,
        "bars": bars,
        "updatedAt": datetime.now(_KST).isoformat(),
    }


@router.get("/api/dartlab/live/quote")
async def live_quote(code: str = Query(..., min_length=1)) -> JSONResponse:
    stock_code = _normalize_code(code)
    if _kis_available():
        try:
            return _json(await _kis_quote_payload(stock_code))
        except (httpx.HTTPError, OSError, RuntimeError, ValueError):
            pass

    try:
        return _json(await _naver_quote_payload(stock_code))
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"quote_failed: {exc}") from exc


@router.get("/api/dartlab/live/minute")
async def live_minute(
    code: str = Query(..., min_length=1),
    timeframe: str = Query("1m", pattern="^(1m|3m|5m)$"),
) -> JSONResponse:
    stock_code = _normalize_code(code)
    minutes = int(timeframe.removesuffix("m"))
    last_error: Exception | None = None

    if _kis_available():
        try:
            return _json(await _kis_minute_payload(stock_code, timeframe, minutes), cache_control="no-store")
        except (httpx.HTTPError, OSError, RuntimeError, ValueError) as exc:
            last_error = exc

    for idx, date in enumerate(_date_candidates()):
        url = (
            "https://api.stock.naver.com/chart/domestic/item/"
            f"{stock_code}/minute?startDateTime={date}0900&endDateTime={date}1530"
        )
        try:
            data = await _get_json(url, timeout=7.0)
            if not isinstance(data, list):
                raise ValueError("minute_payload_not_list")
            bars = [_bar_from_naver(item) for item in data if isinstance(item, dict)]
            bars = [bar for bar in bars if bar is not None]
            if len(bars) < 2:
                raise ValueError("minute_bars_too_short")
            bars.sort(key=lambda x: str(x["t"]))
            return _json(
                {
                    "code": stock_code,
                    "provider": "naver",
                    "currency": "KRW",
                    "basisDate": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                    "isFallbackDate": idx > 0,
                    "timeframe": timeframe,
                    "bars": _aggregate_bars(bars, minutes),
                    "updatedAt": datetime.now(_KST).isoformat(),
                },
                cache_control="no-store",
            )
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            continue

    raise HTTPException(status_code=502, detail=f"minute_failed: {last_error}")
