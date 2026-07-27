"""StoryTree — possible / plausible / probable 3 trajectory DCF (Phase 10 G2).

Damodaran "Narrative and Numbers" 3P 프레임워크:
- **Possible**: 이 서사가 성립할 수 있는가? (수학적 가능성)
- **Plausible**: 경제적/사업적으로 그럴듯한가? (산업 제약 반영)
- **Probable**: 일어날 가능성이 큰가? (base rate + evidence)

각 trajectory 는 다른 overrides 로 DCF 재실행 → 3 가치 + narrative.
"""

from __future__ import annotations

from typing import Any

_TRAJECTORY_OVERRIDES: dict[str, dict] = {
    "possible": {
        # 낙관 시나리오 — 서사의 최대 잠재력
        "terminalGrowth": 4.0,  # 명목 GDP 근접 (dFV 키: terminalGrowth)
        "growthRates": [12.0, 12.0, 10.0],  # 3-phase 고성장 지속
        "_label": "낙관 궤적",
        "_narrative": "서사가 성립하는 최대 잠재력. 업황 호전 + 점유율 확대 + 마진 유지.",
    },
    "plausible": {
        "terminalGrowth": 2.5,  # 한국 잠재성장률
        "growthRates": [6.0, 5.0, 4.0],
        "_label": "중도 궤적",
        "_narrative": "산업 평균으로 회귀. 경쟁 정상화 + 성장 둔화 + 마진 약간 하락.",
    },
    "probable": {
        "terminalGrowth": 1.5,
        "growthRates": [3.0, 2.0, 2.0],
        "_label": "보수 궤적",
        "_narrative": "base rate 지배. 성장 둔화 + 경쟁 심화 + 마진 압박.",
    },
}


def buildStoryTree(company: Any, *, basePeriod: str | None = None) -> dict:
    """3 trajectory DCF — possible/plausible/probable.

    Parameters
    ----------
    company : Company 객체
    basePeriod : 기준 기간 (None 이면 최신)

    Returns
    -------
    dict
        possible/plausible/probable 각각:
            dFV : float — 3 trajectory 별 정당가치
            narrative : str — 서사
            overrides : dict — 사용한 override
            label : str — 한글 라벨
        summary : dict — 3개 평균 + 분포
    """
    try:
        from dartlab.analysis.valuation.dFV import calcDFV
    except ImportError:
        return {}

    tree: dict = {}
    values = []
    for traj_key, ov in _TRAJECTORY_OVERRIDES.items():
        # _label/_narrative 는 override 아니므로 분리
        overrides = {k: v for k, v in ov.items() if not k.startswith("_") and v is not None}
        # Phase 12 A3: primary 전환은 dFV._selectPrimaryWithOverrides 가 자동 처리
        try:
            result = calcDFV(company, basePeriod=basePeriod, overrides=overrides)
            if result and result.get("dFV"):
                dFV = result["dFV"]
                values.append(dFV)
                tree[traj_key] = {
                    "dFV": dFV,
                    "narrative": ov["_narrative"],
                    "overrides": overrides,
                    "label": ov["_label"],
                }
            else:
                tree[traj_key] = {
                    "dFV": None,
                    "narrative": ov["_narrative"],
                    "overrides": overrides,
                    "label": ov["_label"],
                    "error": "dFV 계산 실패",
                }
        except (AttributeError, ValueError, TypeError, KeyError):
            tree[traj_key] = {
                "dFV": None,
                "narrative": ov["_narrative"],
                "overrides": overrides,
                "label": ov["_label"],
                "error": "예외",
            }

    # 요약 — 분포
    if values:
        tree["summary"] = {
            "min": min(values),
            "max": max(values),
            "spread": max(values) - min(values),
            "spreadPct": (max(values) - min(values)) / min(values) * 100 if min(values) > 0 else 0,
            "mean": sum(values) / len(values),
            "count": len(values),
        }
    else:
        tree["summary"] = {"count": 0}

    return tree


def narrateStoryTree(tree: dict) -> str:
    """StoryTree 결과를 한 단락 narrative 로."""
    if not tree or not tree.get("summary") or tree["summary"].get("count", 0) == 0:
        return "StoryTree 계산 실패 — 데이터 부족."

    parts = []
    for key in ("probable", "plausible", "possible"):
        entry = tree.get(key, {})
        if entry.get("dFV"):
            parts.append(f"{entry['label']}: {entry['dFV']:,.0f}원")

    summary = tree["summary"]
    spread_pct = summary.get("spreadPct")

    narrative = " / ".join(parts)
    # 격차를 못 구했을 때 0 으로 채우면 "격차 0%. 서사와 무관하게 안정" 이 붙는다.
    # 바로 앞에 세 배 차이 나는 가격 셋을 나열해 놓고 결과가 서사와 무관하다고 말하는 셈이다.
    # 모르면 그 문장을 아예 붙이지 않는다.
    if spread_pct is None:
        return narrative
    if spread_pct > 100:
        narrative += f". 궤적 간 격차 {spread_pct:.0f}%. 서사 민감도 매우 높음."
    elif spread_pct > 50:
        narrative += f". 궤적 간 격차 {spread_pct:.0f}%. 서사 선택이 중요."
    else:
        narrative += f". 궤적 간 격차 {spread_pct:.0f}%. 서사와 무관하게 안정."

    return narrative
