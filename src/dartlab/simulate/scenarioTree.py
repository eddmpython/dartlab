"""시나리오 디시전 트리 : 가정·조건별 분기 재계산 + 책임 가정 역추적 (L2.5 simulate).

"진짜 시뮬레이터"의 결정 축 (PRD 13 §7b ScenarioTree). 매크로 시나리오(가정 = 유가·환율·금리
충격 + 조건 = 레짐 태그)를 주면, 각 회사가 R4 노출벡터(측정 베타)만큼 반응하고, 산업별로 뭉치고,
board 결정(top-K)이 바뀐다. 트리의 각 노드는 누적 시나리오의 결정이며, 부모 대비 진입/이탈 종목과
그 변화를 일으킨 책임 팩터(어느 가정이 결정을 바꿨나)를 역추적한다.

핵심 = 회사 반응이 손 가정이 아니라 측정 노출(macroBetaByCodeWide)에서 나온다: 유가 민감주는 유가
충격에 크게 반응하고, 그 반응이 랭킹을 재편한다. 산업층(industryMap)이 회사 반응을 업종으로 집계해
"유가 +30% = 에너지 업종 상방"을 낸다. 분기는 누적(부모 충격 위에 증분)이라 경로 = 복합 시나리오.

Layer: L2.5 simulate. table(노출베타·업종맵)·polars 만 의존 (하향). 순수 재점수 (부작용 0).
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

# 팩터 → macroBetaByCodeWide 컬럼. 충격 단위: 유가·환율 = 수익률, 금리 = %p 변화.
_FACTOR_BETA = {"rate": "rateBeta", "fx": "fxBeta", "oil": "oilBeta"}


@dataclass(frozen=True)
class MacroScenario:
    """매크로 시나리오 = 가정(팩터 충격) + 조건(레짐 태그). 디시전 트리 분기의 원자 정의.

    Args:
        scenarioId: 식별자. label: 사람용 이름. shocks: {factor: change} 팩터 충격
            (유가·환율 수익률, 금리 %p). condition: 레짐 조건 태그 (조건부 채점 연동, None = 무조건).
    """

    scenarioId: str
    label: str
    shocks: dict
    condition: str | None = None


# 기본 시나리오 레지스트리 (가정·조건). 고정목록 아님 = registerScenario 로 확장.
DEFAULT_SCENARIOS: dict[str, MacroScenario] = {
    "baseline": MacroScenario("baseline", "기준(무충격)", {}, None),
    "oilShockUp": MacroScenario("oilShockUp", "유가 +30%", {"oil": 0.30}, "oilUp"),
    "oilShockDown": MacroScenario("oilShockDown", "유가 -30%", {"oil": -0.30}, "oilDown"),
    "rateHike": MacroScenario("rateHike", "금리 +100bp", {"rate": 0.01}, "rateHike"),
    "rateCut": MacroScenario("rateCut", "금리 -100bp", {"rate": -0.01}, "rateCut"),
    "wonWeak": MacroScenario("wonWeak", "원화 -10%(약세)", {"fx": 0.10}, "wonWeak"),
    "wonStrong": MacroScenario("wonStrong", "원화 +10%(강세)", {"fx": -0.10}, "wonStrong"),
    "riskOff": MacroScenario(
        "riskOff", "리스크오프(유가↓·원화약세·금리↑)", {"oil": -0.15, "fx": 0.08, "rate": 0.005}, "riskOff"
    ),
    "reflation": MacroScenario("reflation", "리플레이션(유가↑·금리↑)", {"oil": 0.20, "rate": 0.008}, "reflation"),
}


@dataclass(frozen=True)
class ScenarioBranch:
    """디시전 트리 분기 노드 = 시나리오 + 부모(누적 경로). shocks 는 부모 충격 위 증분.

    Args:
        branchId: 트리 내 고유 id. label: 사람용. shocks: 이 노드의 증분 충격.
        condition: 레짐 조건 태그. parent: 부모 branchId (None = 루트 직속, 누적 시작).
    """

    branchId: str
    label: str
    shocks: dict
    condition: str | None = None
    parent: str | None = None


def scenarioResponse(betaByCode: pl.DataFrame, shocks: dict[str, float]) -> pl.DataFrame:
    """회사별 시나리오 반응 = Σ 노출베타 x 충격 → (code, response). 측정 베타 기반 기대 초과.

    Args:
        betaByCode: table.macroBetaByCodeWide 산출 (code, rateBeta, fxBeta, oilBeta).
        shocks: {factor: change} 시나리오 충격.

    Returns:
        (code, response). response = Σ_factor beta[factor] x shock[factor]. 손 가정이 아니라
        측정 노출로 도출 = 유가 민감주가 유가 충격에 크게 반응 (R4 노출벡터의 시뮬 소비).

    Guide:
        - "유가 +30% 반응" -> scenarioResponse(betas, {"oil": 0.30}).
    """
    expr = pl.lit(0.0)
    for factor, betaCol in _FACTOR_BETA.items():
        if factor in shocks and betaCol in betaByCode.columns:
            expr = expr + pl.col(betaCol).fill_null(0.0) * float(shocks[factor])
    return betaByCode.select("code", response=expr)


def industryResponse(betaByCode: pl.DataFrame, industryMap: pl.DataFrame, shocks: dict[str, float]) -> pl.DataFrame:
    """업종별 시나리오 반응 (산업층 집계) → (industry, response, nCodes). 회사 반응의 업종 중앙값.

    Args:
        betaByCode: 노출베타 (code, ...Beta). industryMap: table.industryMap (code, industry).
        shocks: 시나리오 충격.

    Returns:
        (industry, response, nCodes) 반응 내림차순. 산업 노드의 시나리오 상태 = 그 업종이 이 충격에
        구조적으로 수혜/피해인가 (예 유가↑ -> 에너지·화학 상방, 항공·해운 하방).

    Guide:
        - "유가 충격이 어느 업종 유리?" -> industryResponse(betas, imap, {"oil": 0.30}).head().
    """
    resp = scenarioResponse(betaByCode, shocks)
    j = resp.join(industryMap, on="code", how="inner")
    return (
        j.group_by("industry")
        .agg(response=pl.col("response").median(), nCodes=pl.len())
        .sort("response", descending=True)
    )


def _baseScoreCol(baseScores: pl.DataFrame) -> pl.DataFrame:
    """baseScores 를 (code, baseScore) 로 정규화 (consensus|score|baseScore 컬럼 흡수)."""
    for cand in ("baseScore", "score", "consensus"):
        if cand in baseScores.columns:
            return baseScores.select("code", baseScore=pl.col(cand).cast(pl.Float64))
    raise ValueError("baseScores 에 score/consensus/baseScore 컬럼 필요")


def adjustedScores(
    baseScores: pl.DataFrame, betaByCode: pl.DataFrame, shocks: dict[str, float], *, macroTilt: float = 1.0
) -> pl.DataFrame:
    """base 신호(z) + macroTilt x 시나리오 반응(z) → (code, adjusted, response, baseScore).

    Args:
        baseScores: (code, score|consensus) 기저 판독 합의. betaByCode: 노출베타.
        shocks: 시나리오 충격. macroTilt: 매크로 반응 가중 (가정 축, 0 = 무시, 1 = base 와 동급 표준편차).

    Returns:
        (code, adjusted, response, baseScore). adjusted = z(base) + macroTilt x z(response). 랭킹은
        z-space 결합이라 단위 무관 (신호 점수와 기대수익 혼합 문제 해소). macroTilt 는 sweep 대상.
    """
    resp = scenarioResponse(betaByCode, shocks)
    j = _baseScoreCol(baseScores).join(resp, on="code", how="left").with_columns(pl.col("response").fill_null(0.0))
    j = j.with_columns(
        baseZ=(pl.col("baseScore") - pl.col("baseScore").mean()) / (pl.col("baseScore").std() + 1e-12),
        respZ=(pl.col("response") - pl.col("response").mean()) / (pl.col("response").std() + 1e-12),
    ).with_columns(adjusted=pl.col("baseZ") + float(macroTilt) * pl.col("respZ"))
    return j.select("code", "adjusted", "response", "baseScore")


def _responsibleFactor(betaByCode: pl.DataFrame, shocks: dict[str, float]) -> dict[str, dict]:
    """회사별 지배 팩터(책임 가정) → {code: {"factor", "contribution"}}. |beta x shock| 최대 팩터."""
    parts = []
    for factor, betaCol in _FACTOR_BETA.items():
        if factor in shocks and betaCol in betaByCode.columns:
            parts.append(
                betaByCode.select(
                    "code",
                    factor=pl.lit(factor),
                    contribution=pl.col(betaCol).fill_null(0.0) * float(shocks[factor]),
                )
            )
    if not parts:
        return {}
    allc = pl.concat(parts).with_columns(absc=pl.col("contribution").abs())
    dom = allc.sort(["absc", "factor"], descending=[True, False]).unique("code", keep="first")
    return {
        r["code"]: {"factor": r["factor"], "contribution": float(r["contribution"])} for r in dom.iter_rows(named=True)
    }


def _cumulativeShocks(byId: dict, branchId: str) -> dict[str, float]:
    """루트까지 부모 체인 충격을 합산 (누적 경로 = 복합 시나리오). 결정론."""
    acc: dict[str, float] = {}
    chain, cur = [], branchId
    while cur is not None and cur in byId:
        chain.append(byId[cur])
        cur = byId[cur].parent
    for b in reversed(chain):
        for k, v in b.shocks.items():
            acc[k] = acc.get(k, 0.0) + float(v)
    return acc


def _topoOrder(branches: list) -> list:
    """부모가 자식보다 먼저 오도록 정렬 (누적 결정 계산 순서 안정). 부모 부재는 루트 직속."""
    byId = {b.branchId: b for b in branches}
    ordered, seen = [], set()

    def visit(b):
        """부모 먼저 방문(DFS post-order) 후 자신 추가 = 부모가 자식보다 앞서도록."""
        if b.branchId in seen:
            return
        if b.parent is not None and b.parent in byId:
            visit(byId[b.parent])
        seen.add(b.branchId)
        ordered.append(b)

    for b in branches:
        visit(b)
    return ordered


def buildDecisionTree(
    baseScores: pl.DataFrame,
    betaByCode: pl.DataFrame,
    branches: list,
    *,
    topK: int = 10,
    macroTilt: float = 1.0,
) -> dict:
    """가정·조건별 디시전 트리 → {nodes, edges}. 각 노드 = 누적 시나리오 top-K + 진입/이탈 + 책임 팩터.

    Args:
        baseScores: (code, score|consensus) 기저 결정. betaByCode: table.macroBetaByCodeWide.
        branches: ScenarioBranch 목록 (parent 로 트리 구성). topK: 결정 종목 수.
        macroTilt: 매크로 반응 가중 (가정 축).

    Returns:
        {"nodes": [{branchId, label, cumShocks, condition, topK[codes], entrants, exiters,
        responsible{code: {factor, contribution}}}], "edges": [{parent, child}]}. 루트 = 기준(무충격)
        top-K. 각 분기는 부모 대비 진입/이탈 종목과 그 변화의 책임 팩터(어느 가정이 결정을 바꿨나)를
        역추적한다. 결정론: 같은 (baseScores, betaByCode, branches) = 같은 트리.

    Guide:
        - 유가 트리: branches=[ScenarioBranch("oilUp","유가+30%",{"oil":0.3}), ...] -> buildDecisionTree(...).
        - 노드의 entrants = 그 시나리오에서 새로 top-K 진입한 종목, responsible[code] = 그 진입의 책임 팩터.
    """
    byId = {b.branchId: b for b in branches}
    rootAdj = adjustedScores(baseScores, betaByCode, {}, macroTilt=macroTilt)
    rootTop = rootAdj.sort("adjusted", descending=True).head(topK)["code"].to_list()
    nodes = [
        {
            "branchId": "root",
            "label": "기준(무충격)",
            "cumShocks": {},
            "condition": None,
            "topK": rootTop,
            "entrants": [],
            "exiters": [],
            "responsible": {},
        }
    ]
    edges: list[dict] = []
    decisionBy = {"root": set(rootTop)}
    for b in _topoOrder(branches):
        cs = _cumulativeShocks(byId, b.branchId)
        adj = adjustedScores(baseScores, betaByCode, cs, macroTilt=macroTilt)
        top = adj.sort("adjusted", descending=True).head(topK)["code"].to_list()
        parentId = b.parent if (b.parent is not None and b.parent in byId) else "root"
        parentSet = decisionBy.get(parentId, set())
        entrants = [c for c in top if c not in parentSet]
        exiters = [c for c in parentSet if c not in top]
        resp = _responsibleFactor(betaByCode, cs)
        nodes.append(
            {
                "branchId": b.branchId,
                "label": b.label,
                "cumShocks": cs,
                "condition": b.condition,
                "topK": top,
                "entrants": entrants,
                "exiters": exiters,
                "responsible": {c: resp.get(c) for c in entrants if c in resp},
            }
        )
        edges.append({"parent": parentId, "child": b.branchId})
        decisionBy[b.branchId] = set(top)
    return {"nodes": nodes, "edges": edges}


def scenariosToBranches(scenarioIds: list[str], *, registry: dict | None = None) -> list:
    """시나리오 id 목록 → 루트 직속 분기(단층 트리). 복합 트리는 ScenarioBranch.parent 로 직접 구성.

    Args:
        scenarioIds: DEFAULT_SCENARIOS(또는 registry) 키 목록. registry: 시나리오 사전(None = 기본).

    Returns:
        ScenarioBranch 목록 (전부 루트 직속). baseline 은 제외(루트가 무충격 기준).

    Guide:
        - 단층 비교 트리: scenariosToBranches(["oilShockUp","oilShockDown","rateHike"]).
    """
    reg = registry or DEFAULT_SCENARIOS
    out = []
    for sid in scenarioIds:
        sc = reg.get(sid)
        if sc is None or not sc.shocks:
            continue
        out.append(ScenarioBranch(sc.scenarioId, sc.label, dict(sc.shocks), sc.condition, None))
    return out
