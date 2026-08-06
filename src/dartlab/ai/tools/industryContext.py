"""산업 컨텍스트 badge. Track E (5 phase 라이프사이클 + 밸류체인 peers).

Company.industry() (raw 산업 매핑) + industry.calcs.lifecycle (시계열 phase) 합성.
LLM tool 이 아니라 engineCall.Company.panel 응답에 자동 부착되는 헬퍼.

5 phase (UI 표시 SSOT, 플랜 결정 박음):
- 도입: yoy >= 30% (강한 형성기)
- 성장: 10% <= yoy < 30%
- 성숙: 0% <= yoy < 10%
- 재도약: 직전 쇠퇴 후 최근 성장으로 전환된 시계열 패턴 (별도 감지)
- 쇠퇴: yoy < 0%

backend lifecycle 은 4 phase (도입·성장·성숙·쇠퇴) 만 emit. "재도약" 은 본 모듈 안에서 시계열
3 행 패턴 (쇠퇴 → 성장/성숙) 으로 derive 한다. 단일 YoY 로 안 잡히는 turnaround 신호다.
"""

from __future__ import annotations

import logging
import time
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
        industryId (str): "semiconductor" 등 industry node id.
        industryName (str): 한국어 표시명.
        stageName (str | None): 공정 단계 (예: "전공정(FAB)").
        role (str | None): 제조/설계 등.
        stream (str | None): upstream/midstream/downstream.
        phase (str): 도입/성장/성숙/재도약/쇠퇴/unknown (5 phase SSOT).
        peers (list[dict]): 상위 3 종목 {stockCode, corpName}.
        confidence (int): 0-100 (산업 매핑 confidence × 100 → int).
        confidenceMethod (str): "ratio".

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


# 업종 분포는 시장 전체 횡단면을 다섯 번 읽어야 나온다. 분포는 공시가 갱신될 때만 바뀌므로
# 오래 들고 있어도 사실이 흐려지지 않는다. 한 번 재고 나면 이어지는 질문은 공짜다.
_SECTOR_CACHE = SwrCache(3600.0)
# 첫 조회에서 기다려 줄 상한. 넘기면 앵커 없이 답을 내보내고 다음 조회에 붙인다.
# 25 초는 실측(2026-08-06)에서 나왔다. 표를 처음 읽는 데 16 초가 들고, 느린 디스크를 감안해
# 여유를 뒀다. 이 값을 무는 것은 프로세스에서 처음 묻는 회사 한 번뿐이다.
_SECTOR_WAIT_SECONDS = 25.0
# 이보다 짧게밖에 못 기다리면 아예 재지 않는다. 못 쓸 계산을 시작하는 것은 비용만이다.
_MIN_USEFUL_WAIT_SECONDS = 1.0


def getSectorPosition(company: Any, *, budgetSeconds: float | None = None) -> dict[str, Any] | None:
    """수치 하나를 판단으로 바꾸는 업종 내 위치.

    "영업이익률 13.1%" 는 그 자체로 좋고 나쁨을 말하지 않는다. 같은 업종 회사들이 어디에
    있는지를 알아야 판단이 된다. 다섯 축을 준다. 수익성 셋(영업이익률·ROE·매출 성장률) 과
    건전성 둘(부채비율·유동비율) 이다. 건전성 축은 실측(2026-08-06) 에서 재무 건전성을 물은
    질문이 업종 기준을 하나도 못 받고 끝난 것을 보고 뒤늦게 채운 것이다. 수익성 축만으로는
    "부채비율 30% 가 높은 건가" 에 답할 수 없다.

    Args:
        company: Company 객체. 종목코드와 산업 매핑이 필요하다.
        budgetSeconds: 본체를 가져오는 데 든 시간. 곁들이는 재료를 본체보다 오래 기다리지
            않는다. 실데이터 조회는 수십 초라 여유가 있고, 대역으로 즉시 돌아오는 경로는
            기다리지 않고 그냥 지나간다.

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

    # 첫 계산이 9.5 초다(실측 2026-08-06). 배경으로만 돌리면 판단 기준이 붙느냐가 그 턴에서
    # 조회를 몇 번 했느냐에 좌우된다. 실측에서 조회 한 번짜리 질문은 앵커 없이 끝났다.
    # 판단 기준이 운에 달리면 안 되므로 상한을 둔 대기로 기다린다. 상한을 넘기면 그냥 없이
    # 간다. 늦는 것보다 없는 것이 낫고, 다음 조회에는 캐시가 채워져 있다.
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

    allowance = _SECTOR_WAIT_SECONDS if budgetSeconds is None else min(_SECTOR_WAIT_SECONDS, max(0.0, budgetSeconds))
    if allowance < _MIN_USEFUL_WAIT_SECONDS:
        # 기다릴 수 없으면 시작도 하지 않는다. 시장 전체 횡단면을 읽는 일이라 결과를
        # 못 쓸 것을 배경에서 돌리면 메모리만 먹는다. Polars 네이티브 메모리는 gc 로
        # 회수되지 않아 그 봉우리가 프로세스 상한을 그대로 민다. 실측(2026-08-06)에서
        # 이것이 테스트 워커를 죽였다.
        return None
    backgroundRefresher().submit(f"sectorPosition:{stockCode}", _compute)
    # 이 회사의 값만 기다린다. 실행기 전체를 기다리면 남의 느린 probe 에 조회가 묶인다.
    deadline = time.monotonic() + allowance
    while time.monotonic() < deadline:
        settled = _SECTOR_CACHE.peek(stockCode)
        if settled is not None:
            return settled.value or None
        time.sleep(0.02)
    return None


__all__ = ["getIndustryBadge", "getSectorPosition"]
