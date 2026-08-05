"""산업 컨텍스트 badge — Track E (5 phase 라이프사이클 + 밸류체인 peers).

Company.industry() (raw 산업 매핑) + industry.calcs.lifecycle (시계열 phase) 합성.
LLM tool 이 아니라 engineCall.Company.panel 응답에 자동 부착되는 헬퍼.

5 phase (UI 표시 SSOT — 플랜 결정 박음):
- 도입: yoy >= 30% — 강한 형성기
- 성장: 10% <= yoy < 30%
- 성숙: 0% <= yoy < 10%
- 재도약: 직전 쇠퇴 후 최근 성장으로 전환된 시계열 패턴 (별도 감지)
- 쇠퇴: yoy < 0%

backend lifecycle 은 4 phase (도입·성장·성숙·쇠퇴) 만 emit. "재도약" 은 본 모듈 안에서 시계열
3 행 패턴 (쇠퇴 → 성장/성숙) 으로 derive — 단일 YoY 로 안 잡히는 turnaround 신호.
"""

from __future__ import annotations

import logging
from typing import Any

from dartlab.ai.runtime.probeCache import SwrCache, backgroundRefresher
from dartlab.core.confidence import baseScore

_REBOUND_TRIGGER = ("쇠퇴",)
_REBOUND_FOLLOWERS = ("성장", "도입")


def _detectRebound(phases: list[str]) -> bool:
    """최근 2~3 phase 가 (쇠퇴 → 성장|도입) 패턴이면 재도약 신호."""
    if len(phases) < 2:
        return False
    last = phases[-1]
    if last not in _REBOUND_FOLLOWERS:
        return False
    prior = phases[-3:-1] if len(phases) >= 3 else phases[:-1]
    return any(p in _REBOUND_TRIGGER for p in prior)


def _latestPhase(industryId: str) -> tuple[str, list[str]]:
    """industry 시계열 → (현재 phase, 전체 phase 리스트). 실패 시 ('unknown', [])."""
    if not industryId:
        return "unknown", []
    try:
        from dartlab.industry.calcs.lifecycle import classifyLifecycle
    except ImportError:
        return "unknown", []
    try:
        df = classifyLifecycle(industryId)
    except Exception:
        return "unknown", []
    if df is None or df.is_empty() or "phase" not in df.columns:
        return "unknown", []
    rows = df.sort("연도").to_dicts()
    phases = [str(r.get("phase")) for r in rows if r.get("phase")]
    if not phases:
        return "unknown", []
    current = phases[-1]
    if _detectRebound(phases):
        current = "재도약"
    return current, phases


def getIndustryBadge(company: Any) -> dict[str, Any] | None:
    """Company → industry badge dict 또는 None.

    반환 키:
        industryId (str) — "semiconductor" 등 industry node id.
        industryName (str) — 한국어 표시명.
        stageName (str | None) — 공정 단계 (예: "전공정(FAB)").
        role (str | None) — 제조/설계 등.
        stream (str | None) — upstream/midstream/downstream.
        phase (str) — 도입/성장/성숙/재도약/쇠퇴/unknown (5 phase SSOT).
        peers (list[dict]) — 상위 3 종목 {stockCode, corpName}.
        confidence (int) — 0-100 (산업 매핑 confidence × 100 → int).
        confidenceMethod (str) — "ratio".

    Company.industry() 실패 시 None.
    """
    if company is None or not hasattr(company, "industry"):
        return None
    try:
        raw = company.industry()
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None
    industryId = str(raw.get("industry") or "")
    phase, _ = _latestPhase(industryId)
    rawConfidence = raw.get("confidence")
    if isinstance(rawConfidence, (int, float)):
        confInt = max(0, min(100, int(round(float(rawConfidence) * 100))))
    else:
        confInt = baseScore("ratio")
    peersRaw = raw.get("peers") or []
    peers: list[dict[str, Any]] = []
    for p in peersRaw[:3]:
        if not isinstance(p, dict):
            continue
        peers.append(
            {
                "stockCode": str(p.get("stockCode") or ""),
                "corpName": str(p.get("corpName") or ""),
            }
        )
    return {
        "industryId": industryId,
        "industryName": str(raw.get("industryName") or industryId),
        "stage": raw.get("stage"),
        "stageName": raw.get("stageName"),
        "role": raw.get("role"),
        "stream": raw.get("stream"),
        "phase": phase,
        "peers": peers,
        "confidence": confInt,
        "confidenceMethod": "ratio",
    }


# 업종 분포 계산은 횡단면 scan 을 두 번 돌아 5 초가 걸린다(실측 2026-08-06). 분포는 공시가
# 갱신될 때만 바뀌므로 오래 들고 있어도 사실이 흐려지지 않는다. 한 번 재고 나면 같은 회사와
# 같은 산업의 이어지는 질문은 공짜다.
_SECTOR_CACHE = SwrCache(3600.0)


def getSectorPosition(company: Any) -> dict[str, Any] | None:
    """수치 하나를 판단으로 바꾸는 업종 내 위치.

    "영업이익률 13.1%" 는 그 자체로 좋고 나쁨을 말하지 않는다. 같은 업종 회사들이 어디에
    있는지를 알아야 판단이 된다. 분포와 백분위가 이미 계산되어 있었지만 답변 표면에 오지
    않아 한 번도 쓰이지 않았다.

    Args:
        company: Company 객체. 종목코드와 산업 매핑이 필요하다.

    Returns:
        dict[str, Any] | None: 동종사 수, 분포, 백분위. 동종 3 사 미만이면 None 이다.

    Example:
        `position = getSectorPosition(company)`
    """
    stockCode = str(getattr(company, "stockCode", "") or "")
    if not stockCode:
        return None
    cached = _SECTOR_CACHE.peek(stockCode)
    if cached is not None:
        return cached.value or None

    # 아직 없으면 기다리지 않고 뒤에서 잰다. 실측(2026-08-06) 첫 계산이 9.5 초인데, 그것을
    # 임계 경로에 두면 모든 첫 조회가 그만큼 늦어진다. 분석 한 턴은 같은 회사를 여러 번
    # 조회하므로 두 번째 호출부터는 붙는다. 아는 것을 즉시 주고 느린 것은 따라오게 한다.
    def _compute() -> dict[str, Any]:
        from dartlab.industry.calcs.companyCalcs import calcSectorMetrics

        try:
            metrics = calcSectorMetrics(company)
        except Exception:
            logging.getLogger(__name__).debug("업종 위치 계산 실패", exc_info=True)
            metrics = None
        # 실패도 기억한다. 안 그러면 데이터 없는 회사마다 매 조회가 다시 재려 든다.
        _SECTOR_CACHE.put(stockCode, metrics or {})
        return metrics or {}

    backgroundRefresher().submit(f"sectorPosition:{stockCode}", _compute)
    return None


__all__ = ["getIndustryBadge", "getSectorPosition"]
