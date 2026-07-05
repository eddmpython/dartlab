"""시나리오 연쇄 : DAG-as-data 조립 (노드/엣지 JSON) (L2.5 simulate).

8층 연쇄(경제→산업→관계→회사 판독→결정)를 표시물이 아니라 재계산 계약으로 낸다 (11 §4).
노드 = 각 층 판독(refs·성적표 인용·가정 id), 엣지 = 전파 채널(가중·provenance). 이 JSON 이
시뮬레이터 랩(13)의 캔버스 계약이며, 프론트는 트리·산키·그래프 무엇으로든 렌더한다 (표현
교체가 데이터 계약을 못 건드림). 관계 전파(계열 lead-lag)는 계열 데이터 배선 후 확장하는
엣지 종류이며, 본 골격은 회사 한 장의 층 구조(프로파일→표면 판독→합의 결정)를 조립한다.

Layer: L2.5 simulate. reading·profile·board·scorecard 소비 (하향). 순수 조립 (부작용 0).
"""

from __future__ import annotations

import polars as pl


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
