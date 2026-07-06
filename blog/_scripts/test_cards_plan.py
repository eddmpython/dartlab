"""cards.plan.json planning/gate tests.

실행: uv run python -X utf8 -m pytest blog/_scripts/test_cards_plan.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cards_plan as cp  # noqa: E402


def _write_post(blog_dir: Path, folder: str, *, slides: str) -> Path:
    d = blog_dir / folder
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.md").write_text(
        f"""---
title: "테스트회사는 왜 회원권으로 낮은 마진을 버틸까"
description: "블로그 산문과 카드 흐름을 같이 검토하는 테스트"
date: 2026-01-02
stockCode: "999999"
corpName: "테스트회사"
carousel:
  title: "테스트회사는 왜 회원권으로 낮은 마진을 버틸까"
  caption: |
    카드 캡션.
{slides}---
본문 산문. 숫자 21 과 7배.
""",
        encoding="utf-8",
    )
    return d


_TWO_SLIDES = """  slides:
    - layout: editorial
      line: "첫 장 훅"
    - layout: editorialStat
      kicker: "마진"
      bigNumber: "21%"
"""

_SEVEN_SLIDES = """  slides:
    - layout: editorial
      line: "계산대보다 먼저 회원권이 돈을 만듭니다"
    - layout: editorialBeat
      line: "이 구조는 낮은 가격을 약속할 때 작동합니다"
    - layout: editorialStat
      kicker: "분기 매출"
      bigNumber: "636"
      unit: "억달러"
      context: "이 숫자는 사람이 계속 매장으로 돌아왔다는 뜻입니다"
      visual:
        kind: table
        cols: ["기간", "값"]
        data:
          - 기간: "2025Q1"
            값: "636억달러"
    - layout: editorialBeat
      line: "그 돈은 낮은 마진을 버틸 시간을 만듭니다"
      visual:
        kind: table
        cols: ["구분", "의미"]
        data:
          - 구분: "마진"
            의미: "낮은 가격 전략을 버티는 이익 구조"
    - layout: editorialStat
      kicker: "회비"
      bigNumber: "12"
      unit: "억달러"
      context: "그 결과 회비가 이익의 중심을 더 선명하게 보여줍니다"
      visual:
        kind: table
        cols: ["기간", "값"]
        data:
          - 기간: "2025Q1"
            값: "12억달러"
    - layout: editorialBeat
      line: "하지만 회원이 줄면 낮은 가격 전략도 힘을 잃습니다"
    - layout: editorialBeat
      line: "결국 힘은 회비와 재방문이 같이 늘어나는지로 봐야 합니다"
"""


def _mark_passed(plan: dict) -> dict:
    plan = json.loads(json.dumps(plan, ensure_ascii=False))
    plan["reviewGate"]["status"] = "passed"
    for row in plan["reviewGate"]["requiredRounds"]:
        row["status"] = "passed"
    plan["reviewGate"]["loopEvidence"] = {
        "workflow": cp.LOOP_WORKFLOW_NAME,
        "rounds": [
            {
                "round": 1,
                "planner": "초안에서 낮은 마진과 회비 이익의 충돌을 잡았다.",
                "evaluator": "숫자와 시각 설명은 있으나 마지막 판단이 약해 revise 로 돌렸다.",
                "skeptic": "억지 수치와 과장 프레임은 없지만 독자 보상이 약하다고 지적했다.",
                "decision": "revise",
                "evaluatorScore": 84,
                "plannerRevision": "회비와 재방문을 마지막 판단으로 다시 묶었다.",
            },
            {
                "round": 2,
                "planner": "재작성안에서 회비 구조와 재방문 렌즈를 표지 약속과 연결했다.",
                "evaluator": "큰문장 흐름과 시각 근거가 통과선에 도달했다.",
                "skeptic": "하드 kill 축이 남지 않았다.",
                "decision": "passed",
                "evaluatorScore": 94,
                "plannerRevision": "평가 피드백을 반영한 최종안이다.",
            },
        ],
    }
    tc = plan.setdefault("planning", {}).setdefault("titleContract", {})
    selected = plan["target"]["title"]
    tc["workingTitle"] = selected
    tc["selectedTitle"] = selected
    tc["hookQuestion"] = "낮은 가격으로 파는 회사가 왜 회원권에서 이익을 만들까?"
    tc["readerGap"] = "싸게 팔면 마진이 낮아야 한다는 상식과 회비가 이익을 받친다는 구조 사이의 간격을 보여준다."
    tc["promise"] = "표지는 낮은 마진의 역설을 열고, 마지막은 회비와 재방문을 같이 봐야 한다는 판단으로 갚는다."
    tc["whySelected"] = "회사명과 왜 질문을 앞에 놓아 첫 장에서 바로 멈추게 하고, 답은 본문 끝까지 남겨 둔다."
    tc["candidates"] = [
        {
            "title": selected,
            "hook": "낮은 마진과 회비 이익의 충돌을 한 번에 건다.",
            "risk": "회원권 구조를 모르는 독자는 뒤 설명이 필요하다.",
        },
        {
            "title": "테스트회사는 싸게 팔수록 왜 회원권이 더 중요해질까",
            "hook": "싸게 판다는 행동과 회원권 이익을 연결해 궁금증을 만든다.",
            "risk": "마진 숫자의 긴장감은 현재 제목보다 약하다.",
        },
        {
            "title": "테스트회사 이익은 왜 계산대보다 회원권에서 먼저 보일까",
            "hook": "계산대와 회원권의 위치를 바꿔 의외성을 만든다.",
            "risk": "회사 전체보다 회비에만 시야가 좁아질 수 있다.",
        },
    ]
    # 발행 준비된 plan 은 insightContract(통념·반전·렌즈·근거)도 채워져 있어야 한다(v4+ 발행 게이트).
    ic = plan.setdefault("planning", {}).setdefault("insightContract", {})
    ic["commonBelief"] = "회원제 창고형 매장은 싸게 파니까 이익이 얇을 것이라고 여긴다."
    ic["twistFact"] = (
        "실제 이익의 중심은 상품 마진이 아니라 회비다. 낮은 상품 가격으로 재방문을 만들고 그 회비가 이익을 떠받친다."
    )
    ic["whatToWatch"] = "분기 상품 마진이 아니라 회비 매출과 재방문이 같이 늘어나는지를 본다."
    ic["evidenceRefs"] = ["분기 회비 매출 12억달러, 상품 매출 636억달러 대비 비중"]
    for item in plan["planning"].setdefault("visualPlan", []):
        if item.get("visualRole") != "dataEvidence":
            continue
        item["visualKind"] = "table"
        item["visualKinds"] = ["table"]
        item["visualCount"] = max(1, int(item.get("visualCount") or 0))
        item["dataExplanation"] = "이 카드의 숫자가 어떤 기간과 분모에서 나온 것인지 표로 바로 확인하게 한다."
        item["evidenceRefs"] = ["2025Q1 회원 매출 12억달러, 상품 매출 636억달러"]
        visuals = item.get("visuals")
        if not isinstance(visuals, list) or not visuals:
            visuals = [{"visualIndex": 1, "visualKind": "table", "proves": item.get("claim", "숫자 근거")}]
            item["visuals"] = visuals
        for visual_idx, visual in enumerate(visuals, start=1):
            if not isinstance(visual, dict):
                continue
            visual["visualIndex"] = visual_idx
            visual["visualKind"] = "table"
            visual["dataExplanation"] = "이 시각물은 카드의 숫자를 기간과 분모 기준으로 독자가 바로 검산하게 한다."
            visual["evidenceRefs"] = ["2025Q1 회원 매출 12억달러, 상품 매출 636억달러"]
            visual["proves"] = visual.get("proves") or item.get("claim", "숫자 근거")
    return plan


def _valid_big_sentence_slides() -> list[dict]:
    return [
        {"layout": "editorial", "line": "계산대보다 먼저 [[회원권]]이 돈을 만듭니다"},
        {
            "layout": "editorialBeat",
            "line": "이 구조는 [[낮은 가격]]을 약속할 때 작동합니다",
            "visual": {"kind": "table", "cols": ["기간", "값"], "data": [{"기간": "2025Q1", "값": "12억달러"}]},
        },
        {
            "layout": "editorialStat",
            "kicker": "분기 매출",
            "bigNumber": "636",
            "unit": "억달러",
            "context": "이 숫자는 사람이 계속 [[매장으로 돌아왔다는 뜻]]입니다",
            "visual": {"kind": "table", "cols": ["기간", "값"], "data": [{"기간": "2025Q1", "값": "636억달러"}]},
        },
        {
            "layout": "editorialBeat",
            "line": "그 돈은 [[낮은 마진]]을 버틸 시간을 만듭니다",
            "visual": {"kind": "table", "cols": ["구분", "의미"], "data": [{"구분": "마진", "의미": "낮은 가격 전략"}]},
        },
        {
            "layout": "editorialStat",
            "kicker": "회비",
            "bigNumber": "12",
            "unit": "억달러",
            "context": "그 결과 [[회비]]가 이익의 중심을 더 선명하게 보여줍니다",
            "visual": {"kind": "table", "cols": ["기간", "값"], "data": [{"기간": "2025Q1", "값": "12억달러"}]},
        },
        {"layout": "editorialBeat", "line": "하지만 [[회원이 줄면]] 낮은 가격 전략도 힘을 잃습니다"},
        {"layout": "editorialBeat", "line": "결국 힘은 [[회비와 재방문]]이 같이 늘어나는지로 봐야 합니다"},
    ]


def test_build_company_plan_defaults_to_seven_images(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    plan = cp.build_company_post_plan(post)
    assert plan["target"]["slug"] == "999999-test"
    assert plan["target"]["assetRoot"] == "sns/assets/999999"
    assert plan["version"] == cp.PLAN_VERSION
    assert plan["planning"]["narrativeContract"]["spine"] == "훅 -> 왜 지금 중요한가 -> 근거 -> 전환 -> 판단 질문"
    assert "체크리스트" in " ".join(plan["planning"]["narrativeContract"]["rules"])
    assert "구조명" in " ".join(plan["planning"]["narrativeContract"]["rules"])
    assert "제목도 기획 루프" in " ".join(plan["planning"]["titleContract"]["rules"])
    assert plan["planning"]["titleContract"]["selectedTitle"] == plan["target"]["title"]
    assert "큰문장" in " ".join(plan["planning"]["bigSentenceContract"]["rules"])
    assert "전문용어" in " ".join(plan["planning"]["plainLanguageContract"]["rules"])
    assert plan["planning"]["plainLanguageContract"]["preferredRewrites"]["ARR"] == "연간 반복 매출"
    assert "AI" not in plan["planning"]["plainLanguageContract"]["preferredRewrites"]
    assert len(plan["planning"]["visualPlan"]) == 2
    assert plan["planning"]["visualPlan"][1]["visualRole"] == "dataEvidence"
    assert len(plan["imagePlan"]) == 7
    assert all("/cards" in row["prompt"] for row in plan["imagePlan"])
    assert all("Asset key:" in row["prompt"] for row in plan["imagePlan"])
    assert all("Story specificity:" in row["prompt"] for row in plan["imagePlan"])
    assert all("avoid generic stock-finance imagery" in row["prompt"] for row in plan["imagePlan"])


def test_plan_validation_requires_passed_review(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = cp.build_company_post_plan(post, count=7)
    assert cp.validate_plan(planned, require_passed=False) == []
    errors = cp.validate_plan(planned, require_passed=True)
    assert any("reviewGate.status" in err for err in errors)
    assert cp.validate_plan(_mark_passed(planned), require_passed=True) == []


def test_plan_validation_requires_loop_evidence_after_review(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = _mark_passed(cp.build_company_post_plan(post, count=7))
    planned["reviewGate"].pop("loopEvidence")
    errors = cp.validate_plan(planned, require_passed=True)
    assert any("loopEvidence" in err for err in errors)


def test_plan_validation_requires_loop_score_92(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = _mark_passed(cp.build_company_post_plan(post, count=7))
    planned["reviewGate"]["loopEvidence"]["rounds"][-1]["evaluatorScore"] = 91
    errors = cp.validate_plan(planned, require_passed=True)
    assert any("< 92" in err for err in errors)


def test_plan_validation_requires_visual_plan_for_data_cards(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = _mark_passed(cp.build_company_post_plan(post, count=7))
    planned["planning"]["visualPlan"] = []
    errors = cp.validate_plan(planned, require_passed=True)
    assert any("planning.visualPlan" in err for err in errors)


def test_plan_validation_requires_data_explanation_and_refs(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = _mark_passed(cp.build_company_post_plan(post, count=7))
    for item in planned["planning"]["visualPlan"]:
        if item.get("visualRole") == "dataEvidence":
            item["dataExplanation"] = "짧음"
            item["evidenceRefs"] = []
            for visual in item.get("visuals", []):
                visual["dataExplanation"] = "짧음"
                visual["evidenceRefs"] = []
    errors = cp.validate_plan(planned, require_passed=True)
    assert any("dataExplanation" in err for err in errors)
    assert any("evidenceRefs" in err for err in errors)


def test_plan_validation_blocks_template_copy_after_review(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = _mark_passed(cp.build_company_post_plan(post, count=7))
    planned["target"]["title"] = "누가 돈을 버나"
    errors = cp.validate_plan(planned, require_passed=True)
    assert any("템플릿형 문구" in err for err in errors)


def test_plan_validation_requires_title_contract_after_review(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = _mark_passed(cp.build_company_post_plan(post, count=7))
    planned["planning"].pop("titleContract")
    errors = cp.validate_plan(planned, require_passed=True)
    assert any("planning.titleContract" in err for err in errors)


def test_plan_validation_blocks_weak_title_hook(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = _mark_passed(cp.build_company_post_plan(post, count=7))
    planned["target"]["title"] = "테스트회사 분석"
    planned["planning"]["titleContract"]["selectedTitle"] = "테스트회사 분석"
    planned["planning"]["titleContract"]["candidates"][0]["title"] = "테스트회사 분석"
    errors = cp.validate_plan(planned, require_passed=True)
    assert any("제목에 호기심 갭" in err or "제목이 설명형" in err for err in errors)


def test_plan_validation_requires_narrative_contract(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = cp.build_company_post_plan(post, count=7)
    planned["planning"].pop("narrativeContract")
    errors = cp.validate_plan(planned, require_passed=False)
    assert any("planning.narrativeContract" in err for err in errors)


def test_plan_validation_requires_plain_language_contract(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = cp.build_company_post_plan(post, count=7)
    planned["planning"].pop("plainLanguageContract")
    errors = cp.validate_plan(planned, require_passed=False)
    assert any("planning.plainLanguageContract" in err for err in errors)


def test_contract_readability_blocks_jargon_and_checklist() -> None:
    contract = {
        "caption": "다음 체크포인트는 CDMO 수요입니다.",
        "slides": [{"layout": "editorialBeat", "kicker": "승", "line": "HBM이 좋아집니다"}],
        "explainers": [{"term": "HBM", "body": "High Bandwidth Memory의 약자입니다."}],
    }
    errors = cp.validate_contract_readability("x", contract)
    assert any("체크리스트식 문구" in err for err in errors)
    assert any("구조 라벨 금지" in err for err in errors)
    assert any("어려운 약어 사용" in err and "CDMO" in err for err in errors)
    assert any("약자 설명형 문장" in err for err in errors)


def test_contract_plan_gate_finds_plan_by_slug(tmp_path: Path) -> None:
    blog = tmp_path / "blog"
    post = _write_post(blog, "01-999999-test", slides=_SEVEN_SLIDES)
    plan = _mark_passed(cp.build_company_post_plan(post, count=7))
    (post / cp.PLAN_FILE).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    contracts = {"999999-test": {"code": "999999", "slug": "999999-test", "slides": _valid_big_sentence_slides()}}
    errors, stats = cp.validate_contract_plan_gate(contracts, blog_dir=blog, issues_dir=tmp_path / "_issues")
    assert errors == []
    assert stats == {"contracts": 1, "plans": 1, "missing": 0, "passed": 1}


def test_contract_plan_gate_blocks_numeric_slide_without_visual(tmp_path: Path) -> None:
    blog = tmp_path / "blog"
    post = _write_post(blog, "01-999999-test", slides=_SEVEN_SLIDES)
    plan = _mark_passed(cp.build_company_post_plan(post, count=7))
    (post / cp.PLAN_FILE).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    slides = _valid_big_sentence_slides()
    slides[2].pop("visual")
    contracts = {"999999-test": {"code": "999999", "slug": "999999-test", "slides": slides}}
    errors, stats = cp.validate_contract_plan_gate(contracts, blog_dir=blog, issues_dir=tmp_path / "_issues")
    assert stats["passed"] == 0
    assert any("배경 image" in err for err in errors)


def test_contract_plan_gate_blocks_missing_emphasis_for_new_plans(tmp_path: Path) -> None:
    blog = tmp_path / "blog"
    post = _write_post(blog, "01-999999-test", slides=_SEVEN_SLIDES)
    plan = _mark_passed(cp.build_company_post_plan(post, count=7))
    (post / cp.PLAN_FILE).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    slides = _valid_big_sentence_slides()
    slides[0]["line"] = "계산대보다 먼저 회원권이 돈을 만듭니다"
    contracts = {"999999-test": {"code": "999999", "slug": "999999-test", "slides": slides}}
    errors, stats = cp.validate_contract_plan_gate(contracts, blog_dir=blog, issues_dir=tmp_path / "_issues")
    assert stats["passed"] == 0
    assert any("[[강조]]" in err for err in errors)


def test_contract_visual_gate_blocks_array_table_rows() -> None:
    errors = cp.validate_contract_visuals(
        "x",
        {
            "slides": [
                {
                    "layout": "editorialBeat",
                    "line": "표 행이 배열이면 렌더가 비어 버립니다",
                    "visual": {"kind": "table", "cols": ["회사", "값"], "data": [["A", "1"]]},
                }
            ]
        },
    )
    assert any("배열 행" in err for err in errors)


def test_contract_visual_gate_accepts_multi_visuals() -> None:
    dense = ["24Q1", "24Q2", "24Q3", "24Q4", "25Q1", "25Q2"]
    errors = cp.validate_contract_visuals(
        "x",
        {
            "slides": [
                {
                    "layout": "editorialStat",
                    "context": "이 숫자는 [[표와 그래프]]를 같이 봐야 말이 됩니다",
                    "visuals": [
                        {
                            "kind": "table",
                            "cols": ["구분", "값"],
                            "data": [{"구분": "매출", "값": "636억달러"}],
                        },
                        {
                            "kind": "finCard",
                            "periods": dense,
                            "series": [{"name": "매출", "type": "line", "data": [10, 11, 12, 13, 14, 15]}],
                        },
                    ],
                }
            ]
        },
    )
    assert errors == []


def test_contract_visual_gate_blocks_too_many_visuals() -> None:
    errors = cp.validate_contract_visuals(
        "x",
        {
            "slides": [
                {
                    "layout": "editorialBeat",
                    "line": "시각물이 너무 많으면 카드가 읽히지 않습니다",
                    "visuals": [
                        {"kind": "table", "cols": ["a"], "data": [{"a": "1"}]},
                        {"kind": "table", "cols": ["a"], "data": [{"a": "2"}]},
                        {"kind": "table", "cols": ["a"], "data": [{"a": "3"}]},
                        {"kind": "table", "cols": ["a"], "data": [{"a": "4"}]},
                        {"kind": "table", "cols": ["a"], "data": [{"a": "5"}]},
                    ],
                }
            ]
        },
    )
    assert any("최대 4개" in err for err in errors)


def test_contract_planned_visuals_require_multi_visual_alignment() -> None:
    dense = ["24Q1", "24Q2", "24Q3", "24Q4", "25Q1", "25Q2"]
    slides = [
        {"layout": "editorial", "line": "표지는 질문으로 엽니다"},
        {"layout": "editorialBeat", "line": "그래서 먼저 흐름을 설명합니다"},
        {
            "layout": "editorialStat",
            "context": "이 숫자는 [[표와 그래프]]를 같이 봐야 말이 됩니다",
            "bigNumber": "636",
            "unit": "억달러",
        },
        {"layout": "editorialBeat", "line": "결국 판단은 다음 장면으로 이어집니다"},
    ]
    slides[2]["visuals"] = [
        {"kind": "table", "cols": ["기간", "값"], "data": [{"기간": "25Q1", "값": "636억달러"}]},
        {
            "kind": "finCard",
            "periods": dense,
            "series": [{"name": "매출", "type": "line", "data": [10, 11, 12, 13, 14, 15]}],
        },
    ]
    plan = {
        "planning": {
            "bigSentenceContract": {"strip": cp.big_sentence_strip(slides)},
            "visualPlan": [
                {
                    "order": 3,
                    "visualRole": "dataEvidence",
                    "visualKind": "table",
                    "visualKinds": ["table", "finCard"],
                    "visualCount": 2,
                    "visuals": [
                        {
                            "visualIndex": 1,
                            "visualKind": "table",
                            "dataExplanation": "분기 매출의 기간과 단위를 표로 먼저 검산하게 한다.",
                            "evidenceRefs": ["2025Q1 매출 636억달러"],
                        },
                        {
                            "visualIndex": 2,
                            "visualKind": "finCard",
                            "dataExplanation": "같은 매출이 최근 여섯 분기에서 어떤 방향으로 움직였는지 보여준다.",
                            "evidenceRefs": ["2024Q1~2025Q2 매출 시계열"],
                        },
                    ],
                }
            ],
        }
    }
    assert cp.validate_contract_planned_visuals("x", {"slides": slides}, plan) == []
    plan["planning"]["visualPlan"][0]["visualCount"] = 1
    errors = cp.validate_contract_planned_visuals("x", {"slides": slides}, plan)
    assert any("visualCount" in err for err in errors)


def test_contract_plan_gate_can_require_all_plans(tmp_path: Path) -> None:
    contracts = {"999999-test": {"code": "999999", "slug": "999999-test", "slides": [{"layout": "editorial"}]}}
    errors, stats = cp.validate_contract_plan_gate(
        contracts,
        blog_dir=tmp_path / "blog",
        issues_dir=tmp_path / "_issues",
        require_plan=True,
    )
    assert stats["missing"] == 1
    assert any("cards.plan.json 없음" in err for err in errors)


def test_count_must_be_at_least_seven_without_hard_upper_bound(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    with pytest.raises(ValueError):
        cp.build_company_post_plan(post, count=6)
    plan = cp.build_company_post_plan(post, count=11)
    assert len(plan["imagePlan"]) == 11


def test_contract_big_sentence_flow_blocks_fragmented_labels() -> None:
    contract = {
        "slides": [
            {"layout": "editorial", "line": "회원권"},
            {"layout": "editorialBeat", "line": "매출"},
            {"layout": "editorialStat", "kicker": "마진", "bigNumber": "3", "unit": "%"},
            {"layout": "editorialBeat", "line": "가격"},
            {"layout": "editorialBeat", "line": "결론"},
            {"layout": "editorialBeat", "line": "다음"},
            {"layout": "editorialBeat", "line": "확인"},
        ]
    }
    errors = cp.validate_contract_big_sentence_flow("x", contract)
    assert any("큰문장이 너무 짧아" in err for err in errors)
    assert any("context 에 큰문장 서사" in err for err in errors)
    assert any("낱장 메모처럼" in err for err in errors)


def test_contract_big_sentence_flow_accepts_connected_story() -> None:
    errors = cp.validate_contract_big_sentence_flow("x", {"slides": _valid_big_sentence_slides()})
    assert errors == []


def test_contract_big_sentence_flow_accepts_short_cover_question() -> None:
    slides = _valid_big_sentence_slides()
    slides[0]["line"] = "회원권은 정말 돈일까?"
    errors = cp.validate_contract_big_sentence_flow("x", {"slides": slides})
    assert errors == []
