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

from dartlab.simulate.factors import baseScoreExpr, factorBetaMap


def _factorBeta() -> dict[str, str]:
    """팩터→베타컬럼 (factors 레지스트리 SSOT 소비, 호출 시점 = 등록 팩터 자동흡수)."""
    return factorBetaMap()


@dataclass(frozen=True)
class MacroScenario:
    """매크로 시나리오 = 가정(팩터 충격) + 조건(레짐 태그). 디시전 트리 분기의 원자 정의.

    Args:
        scenarioId: 식별자. label: 사람용 이름. shocks: {factor: change} 팩터 충격. 단위 = 팩터
            시리즈 고유 단위 (factors.macroChange 와 동일): price 팩터(oil·fx) = 수익률(0.30 = +30%),
            level 팩터(rate) = %p (1.0 = +100bp. 시리즈가 percent 단위 0.5~5.25 라 0.01 이 아님.
            2026-07-06 실측: 0.01 로 금리 시나리오 전반응 0.00% 결함).
        condition: 레짐 조건 태그 (조건부 채점 연동, None = 무조건).
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
    "rateHike": MacroScenario("rateHike", "금리 +100bp", {"rate": 1.0}, "rateHike"),
    "rateCut": MacroScenario("rateCut", "금리 -100bp", {"rate": -1.0}, "rateCut"),
    "wonWeak": MacroScenario("wonWeak", "원화 -10%(약세)", {"fx": 0.10}, "wonWeak"),
    "wonStrong": MacroScenario("wonStrong", "원화 +10%(강세)", {"fx": -0.10}, "wonStrong"),
    "riskOff": MacroScenario(
        "riskOff", "리스크오프(유가↓·원화약세·금리↑)", {"oil": -0.15, "fx": 0.08, "rate": 0.5}, "riskOff"
    ),
    "reflation": MacroScenario("reflation", "리플레이션(유가↑·금리↑)", {"oil": 0.20, "rate": 0.8}, "reflation"),
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
    for factor, betaCol in _factorBeta().items():
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
    """baseScores 를 (code, baseScore) 로 정규화 (factors.baseScoreExpr SSOT 위임)."""
    return baseScores.select("code", baseScore=baseScoreExpr(baseScores))


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
    for factor, betaCol in _factorBeta().items():
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


def decisionNetwork(
    baseScores: pl.DataFrame,
    betaByCode: pl.DataFrame,
    industryMap: pl.DataFrame,
    shocks: dict[str, float],
    *,
    topK: int = 15,
    macroTilt: float = 1.0,
) -> dict:
    """전 유니버스 결정 네트워크를 데이터로 방출 (GUI 표시 계약, 11 §4 DAG-as-data). GUI 미포함.

    "수천 갈래가 발화해 결과로 좁혀지는" 신경망식 그래프의 데이터. 층 = 입력(매크로 팩터) → 회사 →
    업종 → 결정. 노드 = {id, layer, label, activation}, 엣지 = {from, to, weight}. 활성 = 시나리오
    하 회사 조정 점수(발화 강도), 매크로→회사 엣지 가중 = 측정 노출 베타. GUI(나중)가 fetch 로 소비해
    발화·수렴을 렌더한다. 엔진은 데이터·활성만 낸다 (표시 방식은 프론트 선택, 계약 불변).

    Args:
        baseScores: (code, score|consensus) 기저. betaByCode: table.macroBetaByCodeWide.
        industryMap: table.industryMap. shocks: 시나리오 충격. topK: 결정 선택 수. macroTilt: 매크로 가중.

    Returns:
        {"nodes": [...], "edges": [...], "stats": {nNodes, nEdges, nCompanies, nInput, nIndustry, topK}}.
        노드 layer = input|company|industry|output. 회사 노드 inTopK = 결정 진입 여부. 스케일 =
        수천 노드·수만 엣지 (전 유니버스 = 신경망식 규모, stats 로 실측). 결정론.

    Guide:
        - GUI 데이터: net = decisionNetwork(base, betas, imap, {"oil": 0.3}); net["stats"] 로 규모 확인.
    """
    adj = adjustedScores(baseScores, betaByCode, shocks, macroTilt=macroTilt)
    top = set(adj.sort("adjusted", descending=True).head(topK)["code"].to_list())
    indBy = {
        r["industry"]: r["response"] for r in industryResponse(betaByCode, industryMap, shocks).iter_rows(named=True)
    }
    codeInd = {r["code"]: r["industry"] for r in industryMap.iter_rows(named=True)}
    betaMap = {r["code"]: r for r in betaByCode.iter_rows(named=True)}
    nodes: list[dict] = [
        {"id": f"macro:{f}", "layer": "input", "label": f, "activation": float(v)} for f, v in shocks.items()
    ]
    edges: list[dict] = []
    for r in adj.iter_rows(named=True):
        code = r["code"]
        nodes.append(
            {
                "id": f"company:{code}",
                "layer": "company",
                "label": code,
                "activation": float(r["adjusted"]),
                "inTopK": code in top,
            }
        )
        b = betaMap.get(code, {})
        for f in shocks:
            beta = b.get(_factorBeta().get(f))
            if beta is not None:
                edges.append({"from": f"macro:{f}", "to": f"company:{code}", "weight": float(beta)})
        ind = codeInd.get(code)
        if ind is not None:
            edges.append({"from": f"company:{code}", "to": f"industry:{ind}", "weight": 1.0})
    for ind, resp in indBy.items():
        nodes.append({"id": f"industry:{ind}", "layer": "industry", "label": ind, "activation": float(resp)})
        edges.append({"from": f"industry:{ind}", "to": "decision", "weight": float(resp)})
    nodes.append({"id": "decision", "layer": "output", "label": "결정(top-K)", "topK": sorted(top)})
    for code in sorted(top):
        edges.append({"from": f"company:{code}", "to": "decision", "weight": 1.0, "channel": "selected"})
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "nNodes": len(nodes),
            "nEdges": len(edges),
            "nCompanies": adj.height,
            "nInput": len(shocks),
            "nIndustry": len(indBy),
            "topK": topK,
        },
    }


def industryElasticity(
    grid: pl.DataFrame,
    macro: pl.DataFrame,
    industryMap: pl.DataFrame,
    *,
    minQuarters: int = 16,
    minFirms: int = 5,
    tGate: float = 3.0,
) -> pl.DataFrame:
    """업종 x 팩터 매출 성장 탄성 → (industry, factor, beta, t, n). |t| >= tGate 통과만.

    업종-분기 중앙 YoY 로그성장을 분기 공통효과 차감(전업종 중앙) 후 팩터 분기 변화에 시계열
    회귀한다. 공통 차감 없으면 공통 명목추세(인플레·경기)가 rate 와 동행해 가짜 탄성이 붙는다
    (2026-07-06 실측: 차감 전 t>=3 30쌍 전부 rate 양(+) = 교란, 차감 후 7쌍 = 성장주 금리 음(-)
    듀레이션 채널 등 경제적 정합). 풀링 회귀 금지: 같은 분기 기업들은 팩터를 공유하므로 업종-분기
    집계 후 시계열 df 가 정직한 검정력이다.

    Args:
        grid: estimate.quarterGrid 산출. macro: table.macroDaily 산출. industryMap: (code, industry).
        minQuarters: 회귀 최소 분기 수. minFirms: 업종-분기 최소 기업 수. tGate: 통과 |t| 하한.

    Returns:
        통과 쌍만 (미통과 = 무행 = 조건부 E 기권 대상). beta 단위 = 팩터 1단위당 로그성장.

    Guide:
        - 조건부 E 탄성: industryElasticity(quarterGrid(), macroDaily(), industryMap()).
    """
    import numpy as np

    from dartlab.simulate import estimate as _est
    from dartlab.simulate.factors import factorNames, macroChange

    facs = factorNames()
    mq = (
        macro.with_columns(
            qi=pl.col("date").str.slice(0, 4).cast(pl.Int64) * 4
            + (pl.col("date").str.slice(4, 2).cast(pl.Int64) - 1) // 3
        )
        .sort("date")
        .group_by("qi", maintain_order=True)
        .agg([pl.col(f).drop_nulls().last() for f in facs])
        .sort("qi")
        .with_columns([macroChange(f).alias(f"d_{f}") for f in facs])
    )
    rev = _est._withQi(grid.filter(pl.col("account") == "revenue")).sort(["code", "qi"])
    rev = rev.with_columns(v4=pl.col("amount").shift(4).over("code"), qi4=pl.col("qi").shift(4).over("code")).filter(
        (pl.col("qi4") == pl.col("qi") - 4) & (pl.col("amount") > 0) & (pl.col("v4") > 0)
    )
    rev = rev.with_columns(g=(pl.col("amount") / pl.col("v4")).log()).filter(pl.col("g").abs() < 2.0)
    ind = (
        rev.join(industryMap, on="code", how="inner")
        .group_by(["industry", "qi"])
        .agg(g=pl.col("g").median(), nFirm=pl.len())
        .filter(pl.col("nFirm") >= minFirms)
    )
    empty = pl.DataFrame(
        schema={"industry": pl.Utf8, "factor": pl.Utf8, "beta": pl.Float64, "t": pl.Float64, "n": pl.Int64}
    )
    if ind.height == 0:
        return empty
    common = ind.group_by("qi").agg(gCommon=pl.col("g").median())
    ind = (
        ind.join(common, on="qi", how="inner")
        .with_columns(g=pl.col("g") - pl.col("gCommon"))
        .join(mq.select(["qi"] + [f"d_{f}" for f in facs]), on="qi", how="inner")
    )
    rows: list[dict] = []
    for (industry,), sub in ind.group_by("industry"):
        for f in facs:
            d = sub.select("g", x=pl.col(f"d_{f}")).drop_nulls()
            n = d.height
            if n < minQuarters:
                continue
            x, y = d["x"].to_numpy(), d["g"].to_numpy()
            vx = float(x.var())
            if vx <= 0 or n <= 2:
                continue
            beta = float(np.cov(x, y, ddof=0)[0, 1] / vx)
            resid = y - y.mean() - beta * (x - x.mean())
            se = float(np.sqrt(resid.var(ddof=2) / (n * vx)))
            t = beta / se if se > 0 else 0.0
            if abs(t) >= tGate:
                rows.append({"industry": industry, "factor": f, "beta": beta, "t": t, "n": n})
    return pl.DataFrame(rows, schema=empty.schema) if rows else empty


def conditionalE(
    eFrame: pl.DataFrame, shocks: dict[str, float], elasticity: pl.DataFrame, industryMap: pl.DataFrame
) -> pl.DataFrame:
    """시나리오 조건부 E: 인증 탄성 업종의 매출 E 분위를 exp(Σ beta x shock) 배 이동 (운영자 개념 4번).

    측정 없는 탄성 조작 금지: industryElasticity 통과(|t|>=게이트) (업종, 팩터) 쌍만 움직이고,
    나머지 행은 그대로 + conditioned=False (기권 명시). 탄성은 매출 성장에서 측정됐으므로 매출(E)
    계정만 조건화한다 (다른 계정 무변).

    Args:
        eFrame: estimate.estimateQuarters 산출. shocks: 시나리오 충격 (MacroScenario.shocks 단위).
        elasticity: industryElasticity 산출. industryMap: (code, industry).

    Returns:
        eFrame + (conditioned, shiftLog) 열. 조건 행은 p5~p95 전 분위 x exp(shiftLog) (단조 보존).

    Guide:
        - 리스크오프 매출 E: conditionalE(e, DEFAULT_SCENARIOS["riskOff"].shocks, elas, imap).
    """
    base = eFrame.with_columns(conditioned=pl.lit(False), shiftLog=pl.lit(0.0))
    if not shocks or elasticity.height == 0 or eFrame.height == 0:
        return base
    el = elasticity.filter(pl.col("factor").is_in(list(shocks)))
    if el.height == 0:
        return base
    shift = (
        el.with_columns(shockV=pl.col("factor").replace_strict({k: float(v) for k, v in shocks.items()}, default=0.0))
        .with_columns(part=pl.col("beta") * pl.col("shockV"))
        .group_by("industry")
        .agg(shiftLog=pl.col("part").sum())
    )
    j = (
        base.drop(["conditioned", "shiftLog"])
        .join(industryMap, on="code", how="left")
        .join(shift, on="industry", how="left")
        .with_columns(
            conditioned=(pl.col("account") == "revenue") & pl.col("shiftLog").is_not_null(),
            shiftLog=pl.when((pl.col("account") == "revenue") & pl.col("shiftLog").is_not_null())
            .then(pl.col("shiftLog"))
            .otherwise(0.0),
        )
        .drop("industry")
    )
    mult = pl.col("shiftLog").exp()
    return j.with_columns([(pl.col(f"p{p}") * mult).alias(f"p{p}") for p in (5, 25, 50, 75, 95)])
