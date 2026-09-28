"""네이버증권 그룹 컬렉터. 테마·업종 공통 (목록 → 편입종목 → 결합, freshness 저장).

⚠ 데이터 출처 고지
    네이버증권의 그룹 *분류* 와 *편입사유* 는 네이버의 편집저작물이다. 로컬 개인 분석은
    무방하나 수집 결과의 재배포·공개(HF 적재·서비스 배포·제3자 공개)는 데이터베이스제작자의
    권리(저작권법 제4장)·저작권 문제가 발생할 수 있다. dartlab 은 호스팅·재배포하지 않고
    호출 시점에 직독한다. HF SSOT 미적재·공개 터미널 미배선.

구조 (실측 2026-09-28)
    2026-09 네이버가 ``finance.naver.com/sise/sise_group*.naver`` HTML 페이지를 SPA 화면
    (``stock.naver.com/market/stock/kr/<kind>/<no>``) 로 옮기면서 서버가 그려 주던 표가 사라졌다.
    그래서 같은 화면이 쓰는 JSON API 로 수집한다.

    - 목록: ``m.stock.naver.com/api/stocks/<kind>?page=&pageSize=`` → ``groups[].no/name`` +
      ``totalCount``. 테마 264·업종 79.
    - 편입종목: ``m.stock.naver.com/api/stocks/<kind>/<no>?page=&pageSize=`` → ``stocks[].itemCode/
      stockName`` + ``totalCount``. 테마는 ``themeItemInfoMap`` (종목코드 → 편입사유) 가 동행하고
      업종은 없다 (reason 빈 문자열).
    - pageSize 상한은 100 (101 이상은 400) 이고, 마지막 다음 페이지는 404 를 돌려준다.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import polars as pl

from ...infra.http import GatherHttpClient

log = logging.getLogger(__name__)

_API_BASE = "https://m.stock.naver.com/api/stocks"
_PAGE_URL = "https://stock.naver.com/market/stock/kr"
_HEADERS = {"Referer": "https://m.stock.naver.com/", "Accept": "application/json"}
# 서버 pageSize 상한. 오작동 서버가 꽉 찬 페이지를 끝없이 돌려줘도 멈추도록 페이지 수 상한을 둔다
# (가장 큰 그룹인 업종 "기타" 1,538 종목이 16 페이지).
_PAGE_SIZE = 100
_MAX_PAGES = 50

_LIST_SCHEMA = {
    "groupNo": pl.Int64,
    "groupName": pl.Utf8,
    "url": pl.Utf8,
    "source": pl.Utf8,
    "fetchedAt": pl.Utf8,
}
_STOCKS_SCHEMA = {
    "groupNo": pl.Int64,
    "groupName": pl.Utf8,
    "stockCode": pl.Utf8,
    "stockName": pl.Utf8,
    "reason": pl.Utf8,
    "source": pl.Utf8,
    "fetchedAt": pl.Utf8,
}


@dataclass(frozen=True)
class _GroupSpec:
    """그룹 종류 명세. API·화면 경로, 표시 명사, 저장 카테고리."""

    kind: str  # API·화면 경로 조각 ("theme" | "industry")
    noun: str  # 진행/로그 표시 ("테마" | "업종")
    category: str  # persist 카테고리 ("naver/theme")


_GROUP_SPECS: dict[str, _GroupSpec] = {
    "theme": _GroupSpec("theme", "테마", "naver/theme"),
    "industry": _GroupSpec("industry", "업종", "naver/industry"),
}


def _readPayload(resp: Any, what: str) -> dict:
    """응답 본문을 JSON object 로 해석한다. 빈 본문·HTML 대체 응답은 유효한 0건이 아니라 ValueError."""
    try:
        data = resp.json()
    except ValueError as exc:  # json.JSONDecodeError 포함
        raise ValueError(f"{what} 응답을 해석할 수 없습니다") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{what} 응답을 해석할 수 없습니다")
    return data


async def _fetchPages(client: GatherHttpClient, url: str, listKey: str, what: str) -> tuple[list[dict], list[dict]]:
    """페이지를 끝까지 모아 (listKey 항목, 페이지별 payload) 를 반환한다.

    마지막 다음 페이지는 404 라서 짧은 페이지를 받거나 ``totalCount`` 에 닿으면 멈춘다.
    """
    items: list[dict] = []
    payloads: list[dict] = []
    for page in range(1, _MAX_PAGES + 1):
        resp = await client.get(url, params={"page": page, "pageSize": _PAGE_SIZE}, headers=_HEADERS)
        data = _readPayload(resp, what)
        rows = data.get(listKey)
        if not isinstance(rows, list):
            raise ValueError(f"{what} 응답을 해석할 수 없습니다")
        payloads.append(data)
        items.extend(row for row in rows if isinstance(row, dict))
        total = data.get("totalCount")
        if len(rows) < _PAGE_SIZE or (isinstance(total, int) and len(items) >= total):
            break
    else:
        log.warning("%s: 페이지 상한 %d 에 닿아 수집을 멈춤 (일부 누락 가능)", what, _MAX_PAGES)
    return items, payloads


def _parseGroupList(groups: list[dict], kind: str) -> list[dict]:
    """목록 API ``groups`` → groupNo/groupName/url dict 리스트 (번호 중복·결측 제거). 순수 파싱."""
    seen: set[int] = set()
    out: list[dict] = []
    for group in groups:
        try:
            groupNo = int(group.get("no"))
        except (TypeError, ValueError):
            continue
        groupName = str(group.get("name") or "").strip()
        if groupNo <= 0 or not groupName or groupNo in seen:
            continue
        seen.add(groupNo)
        out.append({"groupNo": groupNo, "groupName": groupName, "url": f"{_PAGE_URL}/{kind}/{groupNo}"})
    return out


def _parseGroupStocks(stocks: list[dict], reasons: dict) -> list[dict]:
    """편입종목 API ``stocks`` → stockCode/stockName/reason dict 리스트 (코드 중복 제거). 순수 파싱.

    ``reasons`` 는 테마의 ``themeItemInfoMap`` (종목코드 → 편입사유). 업종은 빈 dict 라 사유가 빈 문자열.
    """
    seen: set[str] = set()
    rows: list[dict] = []
    for stock in stocks:
        stockCode = str(stock.get("itemCode") or "").strip()
        if not stockCode or stockCode in seen:
            continue
        seen.add(stockCode)
        reason = reasons.get(stockCode)
        rows.append(
            {
                "stockCode": stockCode,
                "stockName": str(stock.get("stockName") or "").strip(),
                "reason": reason.strip() if isinstance(reason, str) else "",
            }
        )
    return rows


async def fetchGroupList(client: GatherHttpClient, groupKey: str, *, limit: int | None = None) -> list[dict]:
    """네이버증권 그룹(테마/업종) 목록 수집.

    Capabilities: ``api/stocks/<kind>`` 페이지 순회 → 그룹 번호·이름 파싱(중복 제거) + 화면 URL.
    AIContext: collectGroup 의 리스트/이름매핑 backend.
    Guide: pageSize 100 단위 페이지네이션 (테마 3 페이지·업종 1 페이지, 실측 2026-09-28).
    When: collectGroup 가 리스트/이름매핑/전체크롤을 위해 호출.
    How: _fetchPages(목록 API) → _parseGroupList → limit.

    Args:
        client: GatherHttpClient (도메인 rate limit/jitter 자체 처리, 프록시 미사용 시 안전 직렬).
        groupKey: "theme" | "industry".
        limit: 반환 그룹 수 상한 (None=전체).

    Returns:
        list[dict]: {groupNo: int, groupName: str, url: str (stock.naver.com 화면), source: "naver",
        fetchedAt: str (UTC ISO8601)}.

    Raises:
        KeyError: 미등록 groupKey.
        ValueError: 응답에서 그룹 목록을 해석할 수 없을 때 (빈 본문·JSON 아님·groups 없음·0건).
        SourceUnavailableError: HTTP 재시도 소진.

    Example::

        groups = await fetchGroupList(client, "theme")

    Requires:
        네트워크 (m.stock.naver.com 무인증). 산출물 재배포 금지(DB권/저작권).

    See Also:
        fetchGroupStocks : 단일 그룹 편입종목.
        collectGroup : target 분기 오케스트레이터.
    """
    spec = _GROUP_SPECS[groupKey]
    what = f"Naver {spec.noun} 목록"
    items, _payloads = await _fetchPages(client, f"{_API_BASE}/{spec.kind}", "groups", what)
    groups = _parseGroupList(items, spec.kind)
    if not groups:
        raise ValueError(f"{what} 응답을 해석할 수 없습니다")
    fetchedAt = datetime.now(timezone.utc).isoformat()
    groups = [{**group, "source": "naver", "fetchedAt": fetchedAt} for group in groups]
    return groups if limit is None else groups[:limit]


async def fetchGroupStocks(client: GatherHttpClient, groupKey: str, no: int, *, limit: int | None = None) -> list[dict]:
    """단일 그룹의 편입종목(+테마는 편입사유) 수집.

    Capabilities: ``api/stocks/<kind>/<no>`` 페이지 순회 → 종목코드·종목명 + 테마 편입사유 매핑.
    AIContext: collectGroup 의 그룹별 편입종목 backend.
    Guide: 테마는 themeItemInfoMap 으로 사유 매핑, 업종은 사유 없음(빈 문자열). 100 종목 초과 그룹은
        여러 페이지를 받는다.
    When: collectGroup 가 선택 그룹마다 호출.
    How: _fetchPages(편입종목 API) → themeItemInfoMap 병합 → _parseGroupStocks → limit.

    Args:
        client: GatherHttpClient.
        groupKey: "theme" | "industry".
        no: 그룹 번호 (리스트의 groupNo).
        limit: 반환 종목 수 상한 (None=전체).

    Returns:
        list[dict]: {stockCode: str, stockName: str, reason: str (업종은 ""), source: "naver",
        fetchedAt: str (UTC ISO8601)}.

    Raises:
        KeyError: 미등록 groupKey.
        ValueError: 응답에서 편입 종목을 해석할 수 없을 때 (빈 본문·JSON 아님·stocks 없음·0건).
        SourceUnavailableError: HTTP 재시도 소진.

    Example::

        rows = await fetchGroupStocks(client, "theme", 523)

    Requires:
        네트워크 (m.stock.naver.com 무인증). 산출물 재배포 금지(DB권/저작권).

    See Also:
        fetchGroupList : 그룹 리스트.
        collectGroup : target 분기 오케스트레이터.
    """
    spec = _GROUP_SPECS[groupKey]
    groupNo = int(no)
    what = f"Naver {spec.noun} {groupNo} 상세"
    items, payloads = await _fetchPages(client, f"{_API_BASE}/{spec.kind}/{groupNo}", "stocks", what)
    reasons: dict = {}
    for payload in payloads:
        infoMap = payload.get("themeItemInfoMap")
        if isinstance(infoMap, dict):
            reasons.update(infoMap)
    rows = _parseGroupStocks(items, reasons)
    if not rows:
        raise ValueError(f"{what} 응답을 해석할 수 없습니다")
    total = payloads[0].get("totalCount")
    if isinstance(total, int) and len(rows) < total:
        # 장중에는 페이지 사이에 정렬이 바뀌어 일부 종목이 빠질 수 있다. 조용히 넘기지 않고 남긴다.
        log.warning("%s: 편입종목 %d/%d 건만 수집", what, len(rows), total)
    fetchedAt = datetime.now(timezone.utc).isoformat()
    rows = [{**row, "source": "naver", "fetchedAt": fetchedAt} for row in rows]
    return rows if limit is None else rows[:limit]


async def _crawlGroups(
    client: GatherHttpClient, groupKey: str, selected: list[tuple[int, str]], *, progress: bool
) -> list[dict]:
    """선택 그룹들의 편입종목 순회 수집. 다중(>1)이면 SSOT core.progress 진행바(현재 그룹명)."""
    spec = _GROUP_SPECS[groupKey]
    total = len(selected)
    records: list[dict] = []
    if not (progress and total > 1):
        for no, name in selected:
            for stock in await fetchGroupStocks(client, groupKey, no):
                records.append({"groupNo": no, "groupName": name, **stock})
        return records
    from dartlab.core.progress import progressBar

    with progressBar(total, desc=f"{spec.noun} 수집", detailed=True) as bar:
        for no, name in selected:
            bar.update(item=name)
            for stock in await fetchGroupStocks(client, groupKey, no):
                records.append({"groupNo": no, "groupName": name, **stock})
            bar.advance()
    return records


async def collectGroup(
    client: GatherHttpClient,
    groupKey: str,
    target: str | None,
    *,
    progress: bool = True,
    maxAgeDays: float = 7.0,
    refresh: bool = False,
) -> pl.DataFrame:
    """네이버 그룹(테마/업종) 수집 오케스트레이터. 기본은 전 그룹 결합 + freshness 저장.

    Capabilities:
        - target None/""/"all" : 전 그룹을 개별 수집 → 하나의 long DataFrame 결합. freshness-gated
          로컬 저장(collectedAt, 디폴트 7일). 7일 내면 크롤 없이 직독.
        - target "list"        : 그룹 *리스트* 만 (groupNo/groupName/url). 라이브.
        - target 숫자          : 해당 groupNo 그룹의 편입종목만. 라이브.
        - target 문자열        : 그룹명 exact → 없으면 contains 매칭. 라이브.
        - 매칭 0 : 빈 DataFrame (스키마 유지).

    AIContext: gather('naverTheme'/'naverIndustry') handler 의 backend. theme/industry 공통.
    Guide: 전수 크롤이 무거워 ``data/naver/<key>`` 에 저장, maxAgeDays 신선도로 재크롤 가름.
        wide(그룹기준)=``df.pivot(values="reason", index="stockCode", on="groupName")``.
    When: handleNaverTheme/handleNaverIndustry 가 runAsync 로 호출.
    How: 전수면 loadOrCollectAsync(crawl)→신선 직독/재크롤, 부분이면 fetchGroupList+필터.

    Args:
        client: GatherHttpClient (rate limit·jitter 자체, 프록시 미사용 시 안전 직렬).
        groupKey: "theme" | "industry".
        target: None/"all"=전수(저장) · "list"=목록 · 그룹명/번호=해당만(라이브).
        progress: 다중 크롤 시 rich 진행바 (core.progress SSOT, 기본 True).
        maxAgeDays: 저장 신선도 윈도우(일). 기본 7.
        refresh: True 면 강제 재크롤.

    Returns:
        pl.DataFrame: source/fetchedAt 동행. "list"=_LIST_SCHEMA,
        전수=_STOCKS_SCHEMA+collectedAt, 부분=_STOCKS_SCHEMA.

    Raises:
        KeyError: 미등록 groupKey.
        ValueError: 목록·편입종목 응답을 해석할 수 없을 때 (fetchGroupList/fetchGroupStocks 전파).

    Example::

        await collectGroup(client, "theme", None)       # 전 테마 결합 (7일 내 직독)
        await collectGroup(client, "industry", "list")   # 업종 목록
        await collectGroup(client, "theme", "2차전지")    # 해당 테마만 (라이브)

    Requires:
        네트워크 (m.stock.naver.com 무인증). 산출물 재배포 금지(DB권/저작권).

    See Also:
        fetchGroupList / fetchGroupStocks : 본 함수가 호출하는 수집기.
        dartlab.core.persist.loadOrCollectAsync : freshness-gated 저장.
    """
    spec = _GROUP_SPECS[groupKey]
    norm = "" if target is None else str(target).strip()

    if norm in ("", "all"):
        from dartlab.core.persist import loadOrCollectAsync

        async def _crawlAll() -> pl.DataFrame:
            groups = await fetchGroupList(client, groupKey)
            selected = [(g["groupNo"], g["groupName"]) for g in groups]
            records = await _crawlGroups(client, groupKey, selected, progress=progress)
            return pl.DataFrame(records, schema=_STOCKS_SCHEMA)

        return await loadOrCollectAsync(spec.category, _crawlAll, maxAgeDays=maxAgeDays, refresh=refresh)

    groupList = await fetchGroupList(client, groupKey)
    nameByNo = {g["groupNo"]: g["groupName"] for g in groupList}
    if norm.lower() == "list":
        return pl.DataFrame(groupList, schema=_LIST_SCHEMA)
    if norm.isdigit() and int(norm) in nameByNo:
        no = int(norm)
        selected = [(no, nameByNo[no])]
    else:
        exact = [g for g in groupList if g["groupName"] == norm]
        matches = exact or [g for g in groupList if norm in g["groupName"]]
        selected = [(g["groupNo"], g["groupName"]) for g in matches]

    if not selected:
        log.info("collectGroup(%r, %r): 매칭 그룹 없음, 빈 결과", groupKey, target)
        return pl.DataFrame(schema=_STOCKS_SCHEMA)

    records = await _crawlGroups(client, groupKey, selected, progress=progress)
    return pl.DataFrame(records, schema=_STOCKS_SCHEMA)
