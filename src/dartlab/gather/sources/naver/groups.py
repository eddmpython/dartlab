"""네이버 sise_group 컬렉터 — 테마·업종 공통 (list→detail→결합, freshness 저장).

⚠ 데이터 출처 고지
    네이버 금융의 그룹 *분류* 와 *편입사유* 는 네이버의 편집저작물이다. 로컬 개인 분석은
    무방하나 수집 결과의 재배포·공개(HF 적재·서비스 배포·제3자 공개)는 데이터베이스제작자의
    권리(저작권법 제4장)·저작권 문제가 발생할 수 있다. dartlab 은 호스팅·재배포하지 않고
    호출 시점에 직독한다 — HF SSOT 미적재·공개 터미널 미배선.

구조 (실측 2026-06-29)
    테마·업종 동일 — ``sise_group.naver?type=theme|upjong`` (한 페이지 전체, 페이지네이션 없음:
    테마 266·업종 79) + ``sise_group_detail.naver?type=<type>&no=`` (편입종목). 테마는 편입사유
    (info_txt) 있고 업종은 없음 — reason 옵션.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import polars as pl

from ...infra.http import GatherHttpClient

log = logging.getLogger(__name__)

_LIST_URL = "https://finance.naver.com/sise/sise_group.naver"
_DETAIL_URL = "https://finance.naver.com/sise/sise_group_detail.naver"
_HEADERS = {"Referer": "https://finance.naver.com/sise/"}

_GROUP_LINK_RE = re.compile(r'<a href="/sise/sise_group_detail\.naver\?type=(\w+)&no=(\d+)">(.*?)</a>')
_TR_RE = re.compile(r"<tr.*?>(.*?)</tr>", re.DOTALL)
_STOCK_RE = re.compile(r'<a href="/item/main\.naver\?code=(\d+)">(.*?)</a>')
_REASON_RE = re.compile(r'<p class="info_txt">(.*?)</p>', re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")

_LIST_SCHEMA: dict[str, pl.DataType] = {"groupNo": pl.Int64, "groupName": pl.Utf8, "url": pl.Utf8}
_STOCKS_SCHEMA: dict[str, pl.DataType] = {
    "groupNo": pl.Int64,
    "groupName": pl.Utf8,
    "stockCode": pl.Utf8,
    "stockName": pl.Utf8,
    "reason": pl.Utf8,
}


@dataclass(frozen=True)
class _GroupSpec:
    """그룹 종류 명세 — naver type 파라미터·표시 명사·저장 카테고리."""

    typeParam: str  # naver ?type= 값 ("theme" | "upjong")
    noun: str  # 진행/로그 표시 ("테마" | "업종")
    category: str  # persist 카테고리 ("naver/theme")


_GROUP_SPECS: dict[str, _GroupSpec] = {
    "theme": _GroupSpec("theme", "테마", "naver/theme"),
    "industry": _GroupSpec("upjong", "업종", "naver/industry"),
}


def _clean(text: str) -> str:
    """HTML 조각의 잔여 태그·기본 엔티티·공백 정리."""
    text = _TAG_RE.sub("", text)
    text = text.replace("&amp;", "&").replace("&nbsp;", " ").replace("&gt;", ">").replace("&lt;", "<")
    return text.strip()


def _parseGroupListHtml(html: str, typeParam: str) -> list[dict]:
    """그룹 리스트 HTML → groupNo/groupName/url dict 리스트 (typeParam 필터·중복 제거). 순수 파싱."""
    seen: set[int] = set()
    out: list[dict] = []
    for t, no, name in _GROUP_LINK_RE.findall(html):
        if t != typeParam:
            continue
        groupNo = int(no)
        if groupNo in seen:
            continue
        seen.add(groupNo)
        out.append({"groupNo": groupNo, "groupName": _clean(name), "url": f"{_DETAIL_URL}?type={typeParam}&no={no}"})
    return out


def _parseGroupDetailHtml(html: str) -> list[dict]:
    """그룹 상세 HTML → 편입종목 dict 리스트(stockCode/stockName/reason). per-tr 파싱 — 종목별
    편입사유 정확 매핑(테마), 사유 없으면 빈 문자열(업종)."""
    rows: list[dict] = []
    for tr in _TR_RE.findall(html):
        stock = _STOCK_RE.search(tr)
        if not stock:
            continue
        reason = _REASON_RE.search(tr)
        rows.append(
            {
                "stockCode": stock.group(1),
                "stockName": _clean(stock.group(2)),
                "reason": _clean(reason.group(1)) if reason else "",
            }
        )
    return rows


async def fetchGroupList(client: GatherHttpClient, groupKey: str, *, limit: int | None = None) -> list[dict]:
    """네이버 sise_group 그룹 리스트 수집 (한 페이지 전체).

    Capabilities: ``sise_group.naver?type=<typeParam>`` 1회 fetch → 그룹 링크 파싱(중복 제거).
    AIContext: collectGroup 의 리스트/이름매핑 backend.
    Guide: 페이지네이션 없음 — 전체가 한 응답. 테마 266·업종 79 (실측).
    When: collectGroup 가 리스트/이름매핑/전체크롤을 위해 호출.
    How: client.get(_LIST_URL, type) → _parseGroupListHtml → limit.

    Args:
        client: GatherHttpClient (도메인 rate limit/jitter 자체 처리 — 프록시 미사용 시 안전 직렬).
        groupKey: "theme" | "industry".
        limit: 반환 그룹 수 상한 (None=전체).

    Returns:
        list[dict] — {groupNo:int, groupName:str, url:str}.

    Raises:
        없음 — 빈 결과는 collectGroup 이 흡수.

    Example::

        groups = await fetchGroupList(client, "theme")

    Requires:
        네트워크 (finance.naver.com 무인증). 산출물 재배포 금지(DB권/저작권).

    See Also:
        fetchGroupStocks : 단일 그룹 편입종목.
        collectGroup : target 분기 오케스트레이터.
    """
    spec = _GROUP_SPECS[groupKey]
    resp = await client.get(_LIST_URL, params={"type": spec.typeParam}, headers=_HEADERS)
    groups = _parseGroupListHtml(resp.text, spec.typeParam)
    return groups if limit is None else groups[:limit]


async def fetchGroupStocks(client: GatherHttpClient, groupKey: str, no: int, *, limit: int | None = None) -> list[dict]:
    """단일 그룹의 편입종목(+테마는 편입사유) 수집.

    Capabilities: ``sise_group_detail.naver?type=<typeParam>&no=`` fetch → 종목/사유 파싱.
    AIContext: collectGroup 의 그룹별 편입종목 backend.
    Guide: 테마는 편입사유(info_txt) 매핑, 업종은 없음(빈 문자열).
    When: collectGroup 가 선택 그룹마다 호출.
    How: client.get(_DETAIL_URL, type+no) → _parseGroupDetailHtml → limit.

    Args:
        client: GatherHttpClient.
        groupKey: "theme" | "industry".
        no: 그룹 번호 (리스트의 groupNo).
        limit: 반환 종목 수 상한 (None=전체).

    Returns:
        list[dict] — {stockCode:str, stockName:str, reason:str}.

    Raises:
        없음.

    Example::

        rows = await fetchGroupStocks(client, "theme", 523)

    Requires:
        네트워크 (finance.naver.com 무인증). 산출물 재배포 금지(DB권/저작권).

    See Also:
        fetchGroupList : 그룹 리스트.
        collectGroup : target 분기 오케스트레이터.
    """
    spec = _GROUP_SPECS[groupKey]
    resp = await client.get(_DETAIL_URL, params={"type": spec.typeParam, "no": no}, headers=_HEADERS)
    rows = _parseGroupDetailHtml(resp.text)
    return rows if limit is None else rows[:limit]


async def _crawlGroups(
    client: GatherHttpClient, groupKey: str, selected: list[tuple[int, str]], *, progress: bool
) -> list[dict]:
    """선택 그룹들의 편입종목 순회 수집 — 다중(>1)이면 SSOT core.progress 진행바(현재 그룹명)."""
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
    """네이버 그룹(테마/업종) 수집 오케스트레이터 — 기본은 전 그룹 결합 + freshness 저장.

    Capabilities:
        - target None/""/"all" : 전 그룹을 개별 수집 → 하나의 long DataFrame 결합. freshness-gated
          로컬 저장(collectedAt, 디폴트 7일) — 7일 내면 크롤 없이 직독.
        - target "list"        : 그룹 *리스트* 만 (groupNo/groupName/url) — 라이브.
        - target 숫자          : 해당 groupNo 그룹의 편입종목만 — 라이브.
        - target 문자열        : 그룹명 exact → 없으면 contains 매칭 — 라이브.
        - 매칭 0 : 빈 DataFrame (스키마 유지).

    AIContext: gather('naverTheme'/'naverIndustry') handler 의 backend — theme/industry 공통.
    Guide: 전수 크롤이 무거워 ``data/naver/<key>`` 에 저장, maxAgeDays 신선도로 재크롤 가름.
        wide(그룹기준)=``df.pivot(values="reason", index="stockCode", on="groupName")``.
    When: handleNaverTheme/handleNaverIndustry 가 runAsync 로 호출.
    How: 전수면 loadOrCollectAsync(crawl)→신선 직독/재크롤, 부분이면 fetchGroupList+필터.

    Args:
        client: GatherHttpClient (rate limit·jitter 자체 — 프록시 미사용 시 안전 직렬).
        groupKey: "theme" | "industry".
        target: None/"all"=전수(저장) · "list"=목록 · 그룹명/번호=해당만(라이브).
        progress: 다중 크롤 시 rich 진행바 (core.progress SSOT, 기본 True).
        maxAgeDays: 저장 신선도 윈도우(일). 기본 7.
        refresh: True 면 강제 재크롤.

    Returns:
        pl.DataFrame — "list"=_LIST_SCHEMA, 전수=_STOCKS_SCHEMA+collectedAt, 부분=_STOCKS_SCHEMA.

    Raises:
        KeyError — 미등록 groupKey.

    Example::

        await collectGroup(client, "theme", None)       # 전 테마 결합 (7일 내 직독)
        await collectGroup(client, "industry", "list")   # 업종 목록
        await collectGroup(client, "theme", "2차전지")    # 해당 테마만 (라이브)

    Requires:
        네트워크 (finance.naver.com 무인증). 산출물 재배포 금지(DB권/저작권).

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
        log.info("collectGroup(%r, %r): 매칭 그룹 없음 — 빈 결과", groupKey, target)
        return pl.DataFrame(schema=_STOCKS_SCHEMA)

    records = await _crawlGroups(client, groupKey, selected, progress=progress)
    return pl.DataFrame(records, schema=_STOCKS_SCHEMA)
