"""시나리오 연쇄 : 8층 DAG-as-data + 관계 전파 + 재계산 계약 (L2.5 simulate).

8층 연쇄(1 데이터·2 프로파일·3 경제·4 산업·5 관계·6 회사판독·7 sweep·8 DAG)를 표시물이 아니라
재계산 계약으로 낸다 (11 §4). 층은 파이프가 아니라 각 층 산출이 독립 판독으로 봉인·채점되고,
층간 연결(탄성·전파 계수)은 전부 가정 축(AssumptionLedgerRow)으로 선언되어 sweep 이 흔든다.
노드 = 각 층 판독(refs·성적표·가정 id), 엣지 = 전파 채널(탄성 값 + 가정 id + provenance).
관계 전파(§3)는 프로파일러 축2 엣지 위에서 "먼저 움직인 노드 x 엣지 가중 x 탄성 = 추종 노드
판독"(표면 cascade.groupLeadLag)을 낸다. 경제·산업 층은 상위 엔진(L2) 판독을 주입받아(하향
import 유지) 노드로 얹는다. 재계산 계약: 노드는 단위 재계산 가능하고 가정 편집 시 그 노드부터
하류만 dirty 전파 재실행(결정론 코어 byte 재현) = 뷰어가 아니라 시뮬레이터 제작기.

Layer: L2.5 simulate. reading·profile·board·assume 소비 (하향). 순수 조립 (부작용 0).
"""

from __future__ import annotations

import polars as pl

from dartlab.simulate.assume import AssumptionLedgerRow


def companyCascade(
    code: str,
    week: int,
    readings: pl.DataFrame,
    profileState: dict,
    *,
    surfaceWeights: dict[str, float] | None = None,
    scorecardByStanceSurface: dict[str, dict] | None = None,
) -> dict:
    """한 회사의 연쇄 DAG (노드/엣지). 재계산 계약: 노드는 단위 재계산 가능한 형태로 남긴다.

    Args:
        code: 종목코드.
        week: 대상 주.
        readings: 그 회사·그 주의 표면 판독 (code, surface, direction, score).
        profileState: profile.profile() 산출 (형질 상태).
        surfaceWeights: 표면 가중 (합의 엣지 가중).
        scorecardByStanceSurface: {surface: 성적표 dict} (노드 성적 인용).

    Returns:
        {"code", "week", "nodes": [...], "edges": [...]}. 노드 layer =
        "profile" | "surface" | "decision". 엣지 = 표면→결정 기여, 형질→표면 조건.
    """
    rows = readings.filter(pl.col("code") == code) if "code" in readings.columns else readings
    weights = surfaceWeights or {}
    nodes: list[dict] = []
    edges: list[dict] = []

    # 프로파일 층 노드 (형질 상태, 예측 아님 = 봉인·채점 대상 아님)
    nodes.append(
        {
            "id": f"profile:{code}",
            "layer": "profile",
            "label": "회사 형질",
            "state": {
                "fundStaleness": profileState.get("fund", {}).get("stalenessDays"),
                "financing": profileState.get("financing", {}),
                "sizePctile": profileState.get("market", {}).get("sizePctile"),
            },
        }
    )

    # 표면 판독 층 노드 + 결정으로의 기여 엣지
    decisionId = f"decision:{code}:{week}"
    consensus = 0.0
    for r in rows.iter_rows(named=True):
        surface = r["surface"]
        w = float(weights.get(surface, 1.0))
        strength = abs((r["score"] or 0.5) - 0.5) * 2
        contrib = w * r["direction"] * strength
        consensus += contrib
        sid = f"surface:{surface}:{code}"
        nodes.append(
            {
                "id": sid,
                "layer": "surface",
                "label": surface,
                "direction": r["direction"],
                "score": r["score"],
                "scorecard": (scorecardByStanceSurface or {}).get(surface),
            }
        )
        edges.append(
            {
                "from": sid,
                "to": decisionId,
                "channel": "consensus",
                "weight": w,
                "contribution": contrib,
            }
        )
        # 형질 조건 엣지 (예: 자금조달 이력 → 이벤트/재무 표면 조건부 정밀화)
        if surface.startswith(("event.", "fund.")):
            edges.append({"from": f"profile:{code}", "to": sid, "channel": "traitConditioning", "weight": None})

    nodes.append(
        {
            "id": decisionId,
            "layer": "decision",
            "label": "합의 판독",
            "consensus": consensus,
            "nSurfaces": rows.height,
        }
    )
    return {"code": code, "week": week, "nodes": nodes, "edges": edges}


# 관계 전파 표면 id (§3, 일반 판독과 동일 봉인·채점).
GROUP_LEAD_LAG_SURFACE = "cascade.groupLeadLag"


def relationshipPropagate(
    moverImpacts: dict[str, float], edges: list[dict], *, elasticity: float = 1.0
) -> pl.DataFrame:
    """관계 전파: 먼저 움직인 노드 충격 x 엣지 가중 x 탄성 → 추종 노드 판독 (§3, 축2 그래프 위).

    Args:
        moverImpacts: {code: 충격} 먼저 움직인 노드(대형 실적·충격)의 방향성 충격 (-1~1).
        edges: [{"from": mover, "to": follower, "weight": w}] 프로파일러 축2 관계 엣지.
        elasticity: 전파 탄성 (가정 축, sweep 대상). 사전 선언된 계수.

    Returns:
        (code, surface, direction, score) 추종 노드 전파 판독. delta = sum(충격 x 가중 x 탄성),
        direction = sign, score = (delta clip[-1,1] + 1)/2. 일반 판독과 동일 계약(봉인·채점).
    """
    acc: dict[str, float] = {}
    for e in edges:
        mv = moverImpacts.get(e.get("from"))
        if mv is None:
            continue
        follower = e.get("to")
        acc[follower] = acc.get(follower, 0.0) + mv * float(e.get("weight", 0.0)) * elasticity
    if not acc:
        return pl.DataFrame(schema={"code": pl.Utf8, "surface": pl.Utf8, "direction": pl.Int64, "score": pl.Float64})
    rows = []
    for code, delta in acc.items():
        d = max(-1.0, min(1.0, delta))
        rows.append(
            {
                "code": code,
                "surface": GROUP_LEAD_LAG_SURFACE,
                "direction": int((delta > 0) - (delta < 0)),
                "score": (d + 1) / 2,
            }
        )
    return pl.DataFrame(rows)


def interLayerAssumptions(connections: dict[str, float]) -> list[AssumptionLedgerRow]:
    """층간 연결(탄성·전파 계수)을 AssumptionLedgerRow 로 선언 (11 §1, sweep 대상).

    Args:
        connections: {connectionId: elasticity} 예 {"economy->industry": 0.6, "relationship": 0.4}.

    Returns:
        AssumptionLedgerRow 목록. 층간 연결이 sweep 이 흔드는 가정임을 계약으로 봉인.
    """
    return [
        AssumptionLedgerRow(
            assumptionId=f"cascade:{cid}",
            dimension="layerElasticity",
            value=str(val),
            unit="elasticity",
            period="weekly",
            source=f"cascade:{cid}",
            status="candidate",
            falsification="전파 판독 OOS 중앙값 <= 0 3분기 연속",
        )
        for cid, val in connections.items()
    ]


def assembleCascade(
    code: str,
    week: int,
    *,
    profileState: dict,
    surfaceReadings: pl.DataFrame,
    economyReading: dict | None = None,
    industryReading: dict | None = None,
    relationshipReadings: pl.DataFrame | None = None,
    elasticities: dict[str, float] | None = None,
    surfaceWeights: dict[str, float] | None = None,
) -> dict:
    """8층 DAG-as-data 조립 (경제→산업→관계→회사판독→결정). 재계산 계약 노드/엣지 JSON.

    Args:
        code/week: 대상. profileState: profile() 산출. surfaceReadings: 그 회사 표면 판독.
        economyReading/industryReading: 상위 엔진(L2) 판독 주입 (하향 import 유지, {direction,score}).
        relationshipReadings: relationshipPropagate 산출 (이 회사 추종 판독).
        elasticities: 층간 탄성 {connectionId: value} (가정 축).
        surfaceWeights: 표면 가중 (합의 엣지).

    Returns:
        companyCascade 위에 경제·산업·관계 층 노드 + 층간 전파 엣지(탄성·가정 id)를 얹은 DAG.
        노드 layer = economy|industry|relationship|profile|surface|decision. value 필드로 재계산 가능.
    """
    base = companyCascade(code, week, surfaceReadings, profileState, surfaceWeights=surfaceWeights)
    el = elasticities or {}
    decisionId = f"decision:{code}:{week}"
    if economyReading is not None:
        base["nodes"].append(
            {"id": "economy", "layer": "economy", "label": "경제 시나리오", "value": economyReading.get("score", 0.5)}
        )
    if industryReading is not None:
        base["nodes"].append(
            {
                "id": f"industry:{code}",
                "layer": "industry",
                "label": "산업 시나리오",
                "value": industryReading.get("score", 0.5),
            }
        )
        if economyReading is not None:
            base["edges"].append(
                {
                    "from": "economy",
                    "to": f"industry:{code}",
                    "channel": "economyToIndustry",
                    "elasticity": el.get("economy->industry"),
                    "assumptionId": "cascade:economy->industry",
                }
            )
        base["edges"].append(
            {
                "from": f"industry:{code}",
                "to": decisionId,
                "channel": "industryToCompany",
                "elasticity": el.get("industry->company"),
                "assumptionId": "cascade:industry->company",
            }
        )
    if relationshipReadings is not None and relationshipReadings.height:
        rel = (
            relationshipReadings.filter(pl.col("code") == code)
            if "code" in relationshipReadings.columns
            else relationshipReadings
        )
        for r in rel.iter_rows(named=True):
            rid = f"relationship:{code}"
            base["nodes"].append(
                {
                    "id": rid,
                    "layer": "relationship",
                    "label": "관계 전파",
                    "direction": r["direction"],
                    "value": r["score"],
                }
            )
            base["edges"].append(
                {
                    "from": rid,
                    "to": decisionId,
                    "channel": "relationshipPropagation",
                    "elasticity": el.get("relationship"),
                    "assumptionId": "cascade:relationship",
                }
            )
    return base


def recompute(dag: dict, edits: dict[str, float]) -> dict:
    """재계산 계약 (11 §4, "뷰어가 아니라 제작기"): 가정 편집 → 그 노드부터 하류만 dirty 재실행.

    Args:
        dag: assembleCascade/companyCascade 산출.
        edits: {nodeId: newValue} 편집된 노드 값 (예 경제 노드·표면 값·탄성).

    Returns:
        {"nodes","edges","dirty": [재계산된 노드 id]}. 결정론: 같은 편집 = 같은 재계산. 하류
        노드 value 는 incoming 엣지(upstream.value x weight x elasticity) 합으로 재산출.
    """
    nodes = {n["id"]: dict(n) for n in dag["nodes"]}
    edges = dag["edges"]
    downstream: dict[str, list[dict]] = {}
    incoming: dict[str, list[dict]] = {}
    for e in edges:
        downstream.setdefault(e["from"], []).append(e)
        incoming.setdefault(e["to"], []).append(e)
    # dirty = 편집 노드 + 도달 가능한 전 하류 (BFS).
    dirty: set[str] = set(edits)
    frontier = list(edits)
    while frontier:
        nid = frontier.pop()
        for e in downstream.get(nid, []):
            if e["to"] not in dirty:
                dirty.add(e["to"])
                frontier.append(e["to"])
    for nid, val in edits.items():
        if nid in nodes:
            nodes[nid]["value"] = val
    # 위상 순서: dirty 노드는 그 노드의 dirty upstream 이 전부 재계산된 뒤에만 재산출 (순서 안정).
    recomputed = set(edits)
    for _ in range(len(dirty) + 1):
        progressed = False
        for nid in list(dirty - recomputed):
            ins = incoming.get(nid, [])
            if any(e["from"] in dirty and e["from"] not in recomputed for e in ins):
                continue  # dirty upstream 미확정 → 다음 라운드
            total = 0.0
            for e in ins:
                up = nodes.get(e["from"], {})
                w = 1.0 if e.get("weight") is None else float(e["weight"])
                elv = 1.0 if e.get("elasticity") is None else float(e["elasticity"])
                total += float(up.get("value", up.get("consensus", 0.0)) or 0.0) * w * elv
            if ins:
                key = "consensus" if nodes[nid].get("layer") == "decision" else "value"
                nodes[nid][key] = total
            recomputed.add(nid)
            progressed = True
        if not progressed:
            break
    return {"nodes": list(nodes.values()), "edges": edges, "dirty": sorted(dirty)}
