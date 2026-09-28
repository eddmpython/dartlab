"""증권사 리서치 메타 수집 — GatherHttpClient 경유 보드 fetch + parse + 해소 (async).

본문은 받지 않고 메타만(제목·URL·날짜·구분·종목). 카테고리별 실패는 격리하고,
(증권사·제목·발간일) 해시로 중복 제거한다. 빅3+하나는 SPA 라 enabled=False(deferred).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .config import BROKERS
from .parse import PARSERS
from .resolve import _extractOpinion, _resolveTicker
from .schema import ReportMeta

if TYPE_CHECKING:
    from ...infra.http import GatherHttpClient

log = logging.getLogger(__name__)

# 직전 수집(_fetchAsync)의 카테고리별 fetch 결과. broker → {카테고리 라벨: "ok" | "network: 사유" | "error: 사유"}.
# 헬스 게이트가 '0 행' 을 셀렉터 깨짐과 네트워크 장애로 가르는 근거라 수집마다 비우고 다시 채운다.
# report_type 을 행별로 재라벨하는 증권사(NH)도 요청 단위 결과는 config 라벨로 남는다.
_fetchOutcomes: dict[str, dict[str, str]] = {}


def _isNetworkFailure(exc: BaseException) -> bool:
    """예외 사슬(__cause__/__context__)에 전송 계층 장애(연결·DNS·타임아웃)나 그 결과인 circuit open 이 있으면 True.

    HTTP 상태 오류(404 등 보드 URL 변경)와 파서 예외는 False 라 기존대로 깨짐으로 남는다.
    """
    import httpx

    from ...types import CircuitOpenError

    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, (httpx.TransportError, OSError, CircuitOpenError)):
            return True
        current = current.__cause__ or current.__context__
    return False


def _lastFetchOutcomes() -> dict[str, dict[str, str]]:
    """직전 수집의 카테고리별 fetch 결과 사본 (sync 헬스 게이트용)."""
    return {broker: dict(outcomes) for broker, outcomes in _fetchOutcomes.items()}


def _networkFailures(enabledCats: dict[str, list[str]], fetchOutcomes: dict[str, dict[str, str]]) -> list[str]:
    """enabled 증권사의 네트워크 장애 카테고리 목록 ("broker/라벨: 사유"). 깨짐이 아니라 경고 대상이다."""
    notices: list[str] = []
    for broker in enabledCats:
        for label, outcome in fetchOutcomes.get(broker, {}).items():
            if outcome.startswith("network"):
                notices.append(f"{broker}/{label}: {outcome.removeprefix('network: ')}")
    return notices


def _decode(content: bytes, text: str, enc: str | None) -> str:
    """enc 지정 시 raw bytes 를 해당 인코딩으로 디코드, 아니면 httpx 가 고른 text 사용."""
    if enc:
        return content.decode(enc, errors="replace")
    return text


def _healthProblems(
    catCounts: dict[str, dict[str, int]],
    completeness: dict[str, float],
    enabledCats: dict[str, list[str]],
    *,
    minCompleteness: float = 0.9,
    fetchOutcomes: dict[str, dict[str, str]] | None = None,
) -> list[str]:
    """수율·완전성 헬스 판정 — 깨짐 사유 목록 반환(빈 리스트=정상). PRD 03 §4.

    스크래핑이 죽는 가장 흔한 방식 = '200 OK + 0행/malformed' 조용한 깨짐(HTML 구조 변경).
    예외 기반 circuit breaker 가 못 보는 이걸 3 신호로 잡아 운영자에게 surface 한다:
      (1) 증권사 전체 0행 — 사이트 차단/다운 또는 전체 셀렉터 깨짐(report_type 전체 합으로 판정).
      (2) 일부 카테고리만 0행(증권사는 살아있음) — 그 보드 URL/셀렉터 깨짐.
      (3) 파싱 완전성(필수필드 비율) < 임계 — 부분 셀렉터 깨짐(필드 누락).

    ``fetchOutcomes`` 가 있으면 네트워크 장애(DNS·연결·타임아웃)로 받지 못한 카테고리의 0 행은 깨짐으로
    세지 않는다(2026-09-15 bookook DNS 실패가 셀렉터 깨짐으로 보고됐다). 대신 전 증권사가 0 행이면 원인과
    무관하게 깨짐 1 건을 남겨 실제 장애가 조용히 넘어가지 않게 한다.

    Args:
        catCounts: broker → {report_type: 수집행수}.
        completeness: broker → 필수필드(title·url·pubDate) 채워진 비율 0~1 (0행이면 0.0).
        enabledCats: broker → 검사할 카테고리 라벨 목록. **빈 리스트면 카테고리별 검사 생략**
            (NH 처럼 report_type 을 행별 동적 재라벨해 config 라벨과 안 맞는 브로커 → 총량만).
        minCompleteness: 완전성 하한(기본 0.9). 미만이면 깨짐.
        fetchOutcomes: broker → {카테고리 라벨: "ok" | "network: 사유" | "error: 사유"}
            (``_lastFetchOutcomes()``). None 이면 예전처럼 0 행을 모두 깨짐으로 본다.

    Returns:
        list[str] — 사람이 읽는 깨짐 사유. 빈 리스트면 전 증권사 정상.
    """
    problems: list[str] = []
    outcomesByBroker = fetchOutcomes or {}
    for broker, cats in enabledCats.items():
        counts = catCounts.get(broker, {})
        outcomes = outcomesByBroker.get(broker, {})
        networkLabels = {label for label, outcome in outcomes.items() if outcome.startswith("network")}
        if sum(counts.values()) == 0:  # 전체 report_type 합 — 동적 라벨 브로커 오탐 방지
            if outcomes and networkLabels == set(outcomes):
                continue  # 모든 요청이 네트워크 장애. 깨짐이 아니라 _networkFailures 경고 대상
            problems.append(f"{broker}: 전체 0행 — 사이트 차단/다운 또는 전체 셀렉터 깨짐")
            continue
        for c in cats:  # cats=[] (동적 라벨) 면 생략
            if counts.get(c, 0) == 0 and c not in networkLabels:
                problems.append(f"{broker}/{c}: 0행 — 보드 URL/셀렉터 깨짐 의심")
        comp = completeness.get(broker, 1.0)
        if comp < minCompleteness:
            problems.append(f"{broker}: 파싱 완전성 {comp:.0%} < {minCompleteness:.0%} — 필드 누락(부분 깨짐)")
    if enabledCats and not problems and all(sum(catCounts.get(b, {}).values()) == 0 for b in enabledCats):
        problems.append("전 증권사 0행: 네트워크 장애로 수집 전체 실패")
    return problems


async def _fetchBroker(key: str, cfg: dict, client: "GatherHttpClient") -> list[ReportMeta]:
    """증권사 1곳의 모든 카테고리를 fetch+parse. 카테고리별 실패는 격리하고 결과를 _fetchOutcomes 에 남긴다."""
    parser = PARSERS.get(key)
    if parser is None:
        return []
    out: list[ReportMeta] = []
    outcomes = _fetchOutcomes.setdefault(key, {})
    for label, url in cfg["categories"].items():
        try:
            resp = await client.get(url)
            html = _decode(resp.content, resp.text, cfg.get("enc"))
            out.extend(parser(html, label, url))
            outcomes[label] = "ok"
        except Exception as exc:  # noqa: BLE001 — 카테고리별 실패 격리
            kind = "network" if _isNetworkFailure(exc) else "error"
            outcomes[label] = f"{kind}: {type(exc).__name__}: {exc}"
            log.warning("brokerage %s/%s fetch 실패: %s", key, label, exc)
    return out


async def _fetchAsync(
    client: "GatherHttpClient",
    *,
    brokers: list[str] | None = None,
    resolveTickers: bool = True,
    limit: int | None = None,
) -> list[ReportMeta]:
    """enabled 증권사 리서치 메타 수집 → ReportMeta 리스트 (증권사별 실패 격리 + dedup).

    Args:
        client: GatherHttpClient (rate limit + retry).
        brokers: 수집할 broker key 리스트. None 이면 enabled 전체.
        resolveTickers: True 면 제목→종목코드 해소(명시코드 우선·corpCode graceful).
        limit: 반환 최대 건수. None 이면 무제한 (수집된 전체).

    Returns:
        list[ReportMeta] — (증권사·제목·발간일) 기준 중복 제거. limit 지정 시 앞 N건.

    Raises:
        없음 — 증권사·카테고리별 실패는 격리(로그 후 skip).

    Example::

        items = await fetchAsync(client, brokers=["miraeasset"], limit=50)
    """
    keys = brokers or [k for k, v in BROKERS.items() if v.get("enabled")]
    _fetchOutcomes.clear()
    seen: set[str] = set()
    out: list[ReportMeta] = []
    for key in keys:
        cfg = BROKERS.get(key)
        if cfg is None:
            continue
        try:
            rows = await _fetchBroker(key, cfg, client)
        except Exception as exc:  # noqa: BLE001 — 증권사별 실패 격리
            log.warning("brokerage %s fetch 실패: %s", key, exc)
            rows = []
        for r in rows:
            rid = r.reportId()
            if rid in seen:
                continue
            seen.add(rid)
            r.opinion = _extractOpinion(r.title)
            if resolveTickers:
                r.ticker = _resolveTicker(r.title)
            out.append(r)
            if limit is not None and len(out) >= limit:
                return out
    return out
