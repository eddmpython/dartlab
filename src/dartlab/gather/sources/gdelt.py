"""GDELT 2.0 Global Knowledge Graph (GKG) downloader — Phase D backfill.

5 년 글로벌 뉴스 narrative 백필 SSOT. GDELT 2.0 GKG 는 매 15 분 글로벌 뉴스
사이트 articles 의 URL + source + sentiment + themes + locations + persons +
organizations 메타데이터 박제.

http://data.gdeltproject.org/gdeltv2/{YYYYMMDDHHMMSS}.gkg.csv.zip

ToS: GDELT 는 명시적으로 학술/상업 사용 모두 무료 (https://www.gdeltproject.org/about.html).
url + 메타데이터만 박는 본 도구는 *완전 합법*.

본 모듈은 download + parse 만. backfill 진입은 syncGdeltBackfill.py.
"""

from __future__ import annotations

import io
import logging
import time
import zipfile
from datetime import date as _date
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import polars as pl

from ..types import SourceUnavailableError
from .newsSchema import NEWS_ARCHIVE_SCHEMA

log = logging.getLogger(__name__)

_BASE_URL = "http://data.gdeltproject.org/gdeltv2"

# GKG CSV 컬럼 순서 (GDELT 2.0 spec) — 27 columns, tab-separated.
# 본 모듈은 narrative 에 필요한 7 컬럼만 추출.
_GKG_COLUMNS = [
    "GKGRECORDID",
    "DATE",
    "SourceCollectionIdentifier",
    "SourceCommonName",
    "DocumentIdentifier",
    "Counts",
    "V2Counts",
    "Themes",
    "V2Themes",
    "Locations",
    "V2Locations",
    "Persons",
    "V2Persons",
    "Organizations",
    "V2Organizations",
    "V2Tone",
    "Dates",
    "GCAM",
    "SharingImage",
    "RelatedImages",
    "SocialImageEmbeds",
    "SocialVideoEmbeds",
    "Quotations",
    "AllNames",
    "Amounts",
    "TranslationInfo",
    "Extras",
]

# archive 스키마 = newsSchema.NEWS_ARCHIVE_SCHEMA(17 canonical). gdelt 는 description 만
# null 추가하면 정확히 일치 (옛 16컬럼 로컬 _ARCHIVE_SCHEMA 폐기).


def _toneToSentiment(toneRaw: float) -> tuple[float, str]:
    """GDELT V2Tone[0] (-10~+10) → sentiment_score (-1~+1) + label.

    Sig: ``_toneToSentiment(toneRaw) -> (score, label)``

    Capabilities: GDELT tone scale 정규화 + 3 단 label.
    AIContext: enriched parquet 의 sentiment_score 와 동일 scale.
    Guide: GDELT tone 0.5 이상 양극단 (10 만점에 5+) 은 강한 감정.
    When: _parseGkgRow.
    How: tone / 10 clamp [-1, +1] + 임계 0.1 분기.

    Args:
        toneRaw: GDELT V2Tone[0].

    Returns:
        (sentiment_score: float, label: pos/neg/neutral).

    Raises:
        없음.

    Example::

        _toneToSentiment(3.5)  # → (0.35, "pos")

    Requires:
        없음.

    See Also:
        ``fetchGdeltGkg``: caller.
    """
    score = max(-1.0, min(1.0, toneRaw / 10.0))
    if score > 0.1:
        label = "pos"
    elif score < -0.1:
        label = "neg"
    else:
        label = "neutral"
    return score, label


def _domainToMarket(source: str) -> str:
    """SourceCommonName TLD → market 추정 (KR/US/JP/CN/GLOBAL).

    Sig: ``_domainToMarket(source) -> str``

    Capabilities: 도메인 끝자락 매칭 + 미매칭 GLOBAL.
    AIContext: narrative archive 의 market 컬럼 채움 — KR 필터 효율.
    Guide: yna.co.kr → KR / nytimes.com → US / 그 외 → GLOBAL.
    When: _parseGkgRow.
    How: 도메인 suffix 매칭 dict.

    Args:
        source: SourceCommonName (예: "yna.co.kr").

    Returns:
        "KR" | "US" | "JP" | "CN" | "GLOBAL".

    Raises:
        없음.

    Example::

        _domainToMarket("yna.co.kr")  # → "KR"
        _domainToMarket("nytimes.com")  # → "US"

    Requires:
        없음.

    See Also:
        ``fetchGdeltGkg``: caller.
    """
    s = (source or "").lower().strip()
    if s.endswith(".kr") or ".co.kr" in s:
        return "KR"
    if s.endswith(".jp") or ".co.jp" in s:
        return "JP"
    if s.endswith(".cn") or ".com.cn" in s:
        return "CN"
    if s.endswith(".com") or s.endswith(".net") or s.endswith(".org") or s.endswith(".us"):
        return "US"
    return "GLOBAL"


def _parseV2Tone(rawTone: str) -> float:
    """V2Tone 컬럼 (CSV 7-tuple) → 첫 값 (overall tone)."""
    if not rawTone:
        return 0.0
    parts = rawTone.split(",")
    try:
        return float(parts[0])
    except (ValueError, IndexError):
        return 0.0


def _parseV2Themes(rawThemes: str, topN: int = 5) -> list[str]:
    """V2Themes 컬럼 (semicolon-separated theme,offset pairs) → 상위 topN theme 리스트."""
    if not rawThemes:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for entry in rawThemes.split(";"):
        if not entry:
            continue
        theme = entry.split(",")[0].strip()
        if theme and theme not in seen:
            out.append(theme)
            seen.add(theme)
            if len(out) >= topN:
                break
    return out


def fetchGdeltGkg(
    timestamp: datetime,
    *,
    markets: list[str] | None = None,
    timeout: float = 30.0,
    limit: int | None = None,
) -> pl.DataFrame:
    """단일 GKG 15-min 슬롯 download + parse + market 필터.

    Capabilities:
        - URL 직접 다운로드 (`data.gdeltproject.org/gdeltv2/{YYYYMMDDHHMMSS}.gkg.csv.zip`)
        - unzip + CSV 파싱 (tab-separated, 27 컬럼)
        - V2Tone → sentiment_score, V2Themes top 5 → themes, SourceCommonName → market
        - markets 필터 (None 이면 전 시장 반환)
        - 결과 schema 는 newsHeadlines/newsEnriched 와 *호환* — narrativePulse 직접 입력 가능

    AIContext:
        Phase D backfill SSOT. syncGdeltBackfill.py 가 시간대 루프 + 본 함수 호출.
        Sprint 4 PIT 호환 — captured_at = download time, date = GDELT pub date.

    Guide:
        timestamp 는 GKG 15-min 슬롯 시각 (00/15/30/45 분, UTC). 임의 시각 입력 시
        자동 정렬 (floor to nearest 15 min).
        markets=["KR","US"] 형식. None 이면 전체 (대용량 — 1 슬롯 ≈ 5만 row).

    When:
        - syncGdeltBackfill.py 시간대 루프
        - 단일 시점 분석 ad-hoc

    How:
        timestamp → URL → httpx GET → zipfile.ZipFile in-memory → CSV parse →
        market 필터 → polars DataFrame.

    Args:
        timestamp: UTC 시각 (GDELT 슬롯 — 15 분 단위).
        markets: ["KR","US","JP","CN","GLOBAL"] 필터. None=전체.
        timeout: HTTP timeout (초).
        limit: 반환 행 상한 (date·url 정렬 후 head). None=전체 (1 슬롯 ≈ 5만 row).

    Returns:
        pl.DataFrame — newsSchema.NEWS_ARCHIVE_SCHEMA canonical 17 컬럼 (date/title/
        source/url/market/query/captured_at/description/sentiment_score/sentiment_label/
        model_version/topic_id/topic_label/topic_prob/themes/language/tone_raw).
        title·description 은 None (GKG 미보유).

    Raises:
        SourceUnavailableError: HTTP, ZIP 또는 CSV 파싱 실패.

    Example::

        from datetime import datetime, timezone
        df = fetchGdeltGkg(datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc), markets=["KR","US"])

    Requires:
        httpx + 네트워크. zipfile (표준).

    See Also:
        ``syncGdeltBackfill``: range backfill caller.
        ``newsHeadlines.loadNewsArchive``: 호환 schema 로 통합 로드.
    """
    # floor to nearest 15 min
    minute = (timestamp.minute // 15) * 15
    ts = timestamp.replace(minute=minute, second=0, microsecond=0)
    tsStr = ts.strftime("%Y%m%d%H%M%S")
    url = f"{_BASE_URL}/{tsStr}.gkg.csv.zip"
    capturedAt = datetime.now(tz=timezone.utc)

    try:
        import httpx

        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            resp = client.get(url)
            if resp.status_code == 404:
                log.debug("GDELT 슬롯 %s 미존재 (아직 publish 안 됨 또는 옛 데이터)", tsStr)
                return pl.DataFrame(schema=NEWS_ARCHIVE_SCHEMA)
            resp.raise_for_status()
            data = resp.content
    except Exception as exc:
        raise SourceUnavailableError(f"GDELT GKG 슬롯을 가져올 수 없습니다: {tsStr}") from exc

    # unzip in-memory
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
            if not names:
                raise SourceUnavailableError(f"GDELT GKG ZIP이 비어 있습니다: {tsStr}")
            csvBytes = zf.read(names[0])
    except SourceUnavailableError:
        raise
    except (zipfile.BadZipFile, OSError) as exc:
        raise SourceUnavailableError(f"GDELT GKG ZIP을 해석할 수 없습니다: {tsStr}") from exc

    # parse CSV — tab-separated, no header
    try:
        rawDf = pl.read_csv(
            io.BytesIO(csvBytes),
            separator="\t",
            has_header=False,
            new_columns=_GKG_COLUMNS,
            truncate_ragged_lines=True,
            ignore_errors=True,
            schema_overrides={c: pl.Utf8 for c in _GKG_COLUMNS},
        )
    except Exception as exc:
        raise SourceUnavailableError(f"GDELT GKG CSV를 해석할 수 없습니다: {tsStr}") from exc

    if rawDf.is_empty():
        return pl.DataFrame(schema=NEWS_ARCHIVE_SCHEMA)

    # row-wise 변환 (V2Tone/V2Themes parse 가 Python 함수라 to_dicts)
    rows: list[dict] = []
    marketsSet = set(markets) if markets else None
    for r in rawDf.iter_rows(named=True):
        source = r.get("SourceCommonName") or ""
        market = _domainToMarket(source)
        if marketsSet is not None and market not in marketsSet:
            continue
        url_doc = r.get("DocumentIdentifier") or ""
        if not url_doc:
            continue
        dateStr = (r.get("DATE") or "")[:8]
        if len(dateStr) != 8:
            continue
        try:
            d = _date(int(dateStr[:4]), int(dateStr[4:6]), int(dateStr[6:8]))
        except ValueError:
            continue
        tone = _parseV2Tone(r.get("V2Tone") or "")
        sentScore, sentLabel = _toneToSentiment(tone)
        themes = _parseV2Themes(r.get("V2Themes") or "")
        rows.append(
            {
                "date": d,
                "title": None,
                "source": source,
                "url": url_doc,
                "market": market,
                "query": "gdelt_gkg",
                "captured_at": capturedAt,
                "description": None,
                "sentiment_score": sentScore,
                "sentiment_label": sentLabel,
                "model_version": "gdelt_v2tone",
                "topic_id": -1,
                "topic_label": themes[0] if themes else "untagged",
                "topic_prob": 1.0 if themes else 0.0,
                "themes": themes,
                "language": (r.get("TranslationInfo") or "").split(";")[0][:8] or "und",
                "tone_raw": tone,
            }
        )

    if not rows:
        return pl.DataFrame(schema=NEWS_ARCHIVE_SCHEMA)
    df = pl.DataFrame(rows, schema=NEWS_ARCHIVE_SCHEMA)
    # url dedup (같은 article 이 여러 record 로 분리될 수 있음)
    df = df.unique(subset=["url"], keep="first")
    df = df.sort(["date", "url"])
    return df.head(limit) if limit is not None else df


def iterGdeltSlots(start: datetime, end: datetime, *, stepMinutes: int = 15) -> list[datetime]:
    """[start..end] 범위 GDELT 슬롯 시각 리스트 (UTC, 15 분 단위 floor).

    Sig: ``iterGdeltSlots(start, end, *, stepMinutes=15) -> list[datetime]``

    Capabilities: timestamp range 를 GDELT 슬롯 정수 단위로 enumerate.
    AIContext: backfill caller 가 시간대 루프 시 사용.
    Guide: stepMinutes=15 → 모든 슬롯, 60 → 시간당 1 슬롯, 360 → 6 시간당 1 (24h × 4 sample/day).
    When: syncGdeltBackfill.py.
    How: start 부터 stepMinutes 씩 증가 + 분 단위 정렬.

    Args:
        start: 시작 UTC datetime.
        end: 종료 UTC datetime (포함).
        stepMinutes: 슬롯 간격. 15 (전수) / 60 (시간) / 360 (6 시간) / 1440 (일).

    Returns:
        list[datetime] — UTC 시각 리스트.

    Raises:
        없음.

    Example::

        from datetime import datetime, timezone
        slots = iterGdeltSlots(
            datetime(2026, 5, 28, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 5, 28, 23, 45, tzinfo=timezone.utc),
            stepMinutes=360,
        )
        # → 4 slots (00:00, 06:00, 12:00, 18:00)

    Requires:
        없음.

    See Also:
        ``fetchGdeltGkg``: caller.
        ``syncGdeltBackfill.main``: backfill 진입.
    """
    minute = (start.minute // 15) * 15
    cur = start.replace(minute=minute, second=0, microsecond=0)
    out: list[datetime] = []
    while cur <= end:
        out.append(cur)
        cur += timedelta(minutes=stepMinutes)
    return out


# ── GDELT DOC 2.0 API (질의 기반 뉴스) — GKG 벌크와 다른 엔드포인트 ────────────────────
# DOC 2.0 는 회사명 질의 → 제목·URL·날짜(스니펫 없음, ~2017 과거 커버, 무료·키 불필요). GKG(시간슬롯·
# 회사키 없음)와 별개라 같은 GDELT source 모듈 안에 둔다. online fetch=gather(Extract) SSOT — sync 글루가
# 자체 httpx 로 재구현하던 별도빌드를 본 위치로 환원(buildNaverCompanyNews 가 위임 호출).
_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
_DOC_MAX_RECORDS = 250  # DOC API 상한
_DOC_FLOOR_YEAR = 2017  # DOC 인덱스 시작 연도


def _docYearWindow(year: int) -> tuple[str, str]:
    """연도 → (startdatetime, enddatetime) GDELT 형식 (YYYYMMDDHHMMSS)."""
    return f"{year}0101000000", f"{year}1231235959"


def _docDomain(url: str) -> str:
    """URL → 도메인(www. 제거). 파싱 실패 시 빈 문자열."""
    try:
        return (urlparse(url).netloc or "").replace("www.", "")
    except Exception:  # noqa: BLE001
        return ""


def _docFetchOne(client, name: str, year: int) -> list[dict]:
    """회사명×연도 1 질의 → article dict 리스트. 정상 무결과는 빈 목록."""
    start, end = _docYearWindow(year)
    params = {
        "query": f'"{name}" sourcecountry:southkorea',
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(_DOC_MAX_RECORDS),
        "sort": "datedesc",
        "startdatetime": start,
        "enddatetime": end,
    }
    try:
        resp = client.get(_DOC_URL, params=params)
        if resp.status_code != 200:
            raise SourceUnavailableError(
                f"GDELT DOC 응답 상태가 올바르지 않습니다: name={name}, year={year}, status={resp.status_code}"
            )
        try:
            payload = resp.json()  # 결과 0 일 때 빈 본문/비-JSON 가능 → 방어
        except Exception as exc:  # noqa: BLE001
            raise SourceUnavailableError(f"GDELT DOC JSON을 해석할 수 없습니다: name={name}, year={year}") from exc
    except SourceUnavailableError:
        raise
    except Exception as exc:  # noqa: BLE001 — 네트워크/타임아웃은 그 질의만 skip
        raise SourceUnavailableError(f"GDELT DOC 질의에 실패했습니다: name={name}, year={year}") from exc
    if not isinstance(payload, dict):
        raise SourceUnavailableError(f"GDELT DOC 응답 schema가 객체가 아닙니다: name={name}, year={year}")
    articles = payload.get("articles")
    if articles is None:
        return []
    if not isinstance(articles, list):
        raise SourceUnavailableError(f"GDELT DOC articles가 배열이 아닙니다: name={name}, year={year}")
    return articles


def fetchGdeltDoc(
    nameToCode: dict[str, str],
    *,
    years: int = 1,
    perQuery: float = 5.0,  # ⚠ GDELT DOC API rate limit = 5초당 1회 — 더 빠르면 대부분 throttle(빈 응답).
    timeout: float = 30.0,
    budgetSec: float | None = None,
) -> pl.DataFrame:
    """회사명→코드 매핑의 각 회사를 GDELT DOC API 로 질의 → 뉴스 archive df (gdelt 트랙).

    최근 ``years`` 개 연도를 회사별로 질의(daily=1=올해, backfill=5=2021~). 반환 컬럼은 naver archive 와
    호환(date/title/source/url/query/description/market/captured_at) — description 은 항상 빈 문자열.
    전 종목(~2800)은 한 job 에 다 못 도므로 ``budgetSec`` 시간예산 초과 시 중단(누적이라 다음 run 이 이어감).
    online fetch=gather SSOT — sync 글루(buildNaverCompanyNews)가 본 함수를 위임 호출한다.

    Capabilities: 회사명 질의 GDELT DOC 2.0 API fanout → naver 호환 뉴스 archive df(+__code) 수집.
    AIContext: internal source fetch — AI 직접 호출 X. 뉴스 archive 빌더(buildNaverCompanyNews) sink 가 소비.
    Guide: GKG 벌크(fetchGdeltGkg)와 다른 질의 기반 엔드포인트 — 제목+링크만(스니펫 없음), 한국 커버리지 부분적.
    When: gdelt 트랙 뉴스 archive 증분/백필(buildNaverCompanyNews) 수집 시.
    How: nameToCode 순회 × yearList 질의(_docFetchOne) → 행 누적 → url 중복 제거 df.

    Args:
        nameToCode: 회사명 → 종목코드. query=회사명, 결과행에 stockCode 동봉(``__code``).
        years: 최근 몇 개 연도를 질의할지 (1=올해만 증분, ≥2=과거 backfill).
        perQuery: 질의 간 sleep(초) — DOC API rate 보호.
        timeout: httpx 타임아웃.
        budgetSec: 전체 fetch 시간예산(초). 초과 시 그때까지 모은 것 반환(부분). None=무제한.

    Returns:
        pl.DataFrame — gdelt 트랙 뉴스(빈 결과면 빈 df, ``__code`` 컬럼 포함). url 기준 중복 제거.

    Raises:
        SourceUnavailableError: 질의별 네트워크, 응답 상태 또는 JSON schema 실패.

    Example:
        >>> import polars as pl
        >>> isinstance(fetchGdeltDoc({}), pl.DataFrame)  # 빈 입력 → 빈 df
        True

    Requires:
        네트워크 (``api.gdeltproject.org/api/v2/doc``). 키 불필요. stdlib + httpx + polars.

    SeeAlso:
        fetchGdeltGkg : GKG 벌크(시간슬롯·tone) 자매 트랙.
        _docFetchOne : 회사×연도 단일 질의 하위 단계.
    """
    if not nameToCode:
        return pl.DataFrame()
    import httpx

    nowYear = datetime.now(tz=timezone.utc).year
    yearList = [y for y in range(nowYear, nowYear - max(1, years), -1) if y >= _DOC_FLOOR_YEAR]
    capturedAt = datetime.now(tz=timezone.utc)
    started = time.monotonic()
    rows: list[dict] = []
    done = 0
    with httpx.Client(follow_redirects=True, timeout=timeout, headers={"User-Agent": "dartlab/news"}) as client:
        for name, code in nameToCode.items():
            if budgetSec is not None and time.monotonic() - started > budgetSec:
                log.info("GDELT DOC 시간예산 %ss 초과 — %d/%d 종목에서 중단(누적)", budgetSec, done, len(nameToCode))
                break
            done += 1
            for year in yearList:
                for art in _docFetchOne(client, name, year):
                    url = art.get("url") or ""
                    title = (art.get("title") or "").strip()
                    seen = art.get("seendate") or ""
                    if not url or not title or len(seen) < 8:
                        continue
                    try:
                        d = _date(int(seen[:4]), int(seen[4:6]), int(seen[6:8]))
                    except ValueError:
                        continue
                    rows.append(
                        {
                            "date": d,
                            "title": title,
                            "source": art.get("domain") or _docDomain(url),
                            "url": url,
                            "query": name,
                            "description": "",
                            "market": "KR",
                            "captured_at": capturedAt,
                            "__code": str(code).strip(),
                        }
                    )
                time.sleep(perQuery)
    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows).unique(subset=["url"], keep="first")
