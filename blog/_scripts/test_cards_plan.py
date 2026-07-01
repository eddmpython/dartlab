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
title: "테스트 글"
description: "블로그 산문과 카드 흐름을 같이 검토하는 테스트"
date: 2026-01-02
stockCode: "999999"
corpName: "테스트회사"
carousel:
  title: "테스트 카드"
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


def _mark_passed(plan: dict) -> dict:
    plan = json.loads(json.dumps(plan, ensure_ascii=False))
    plan["reviewGate"]["status"] = "passed"
    for row in plan["reviewGate"]["requiredRounds"]:
        row["status"] = "passed"
    # 발행 준비된 plan 은 insightContract(통념·반전·렌즈·근거)도 채워져 있어야 한다(v4+ 발행 게이트).
    ic = plan.setdefault("planning", {}).setdefault("insightContract", {})
    ic["commonBelief"] = "회원제 창고형 매장은 싸게 파니까 이익이 얇을 것이라고 여긴다."
    ic["twistFact"] = (
        "실제 이익의 중심은 상품 마진이 아니라 회비다. 낮은 상품 가격으로 재방문을 만들고 그 회비가 이익을 떠받친다."
    )
    ic["whatToWatch"] = "분기 상품 마진이 아니라 회비 매출과 재방문이 같이 늘어나는지를 본다."
    ic["evidenceRefs"] = ["분기 회비 매출 12억달러, 상품 매출 636억달러 대비 비중"]
    return plan


def _valid_big_sentence_slides() -> list[dict]:
    return [
        {"layout": "editorial", "line": "계산대보다 먼저 회원권이 돈을 만듭니다"},
        {"layout": "editorialBeat", "line": "이 구조는 낮은 가격을 약속할 때 작동합니다"},
        {
            "layout": "editorialStat",
            "kicker": "분기 매출",
            "bigNumber": "636",
            "unit": "억달러",
            "context": "이 숫자는 사람이 계속 매장으로 돌아왔다는 뜻입니다",
        },
        {"layout": "editorialBeat", "line": "그 돈은 낮은 마진을 버틸 시간을 만듭니다"},
        {
            "layout": "editorialStat",
            "kicker": "회비",
            "bigNumber": "12",
            "unit": "억달러",
            "context": "그 결과 회비가 이익의 중심을 더 선명하게 보여줍니다",
        },
        {"layout": "editorialBeat", "line": "하지만 회원이 줄면 낮은 가격 전략도 힘을 잃습니다"},
        {"layout": "editorialBeat", "line": "결국 힘은 회비와 재방문이 같이 늘어나는지로 봐야 합니다"},
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
    assert "큰문장" in " ".join(plan["planning"]["bigSentenceContract"]["rules"])
    assert "전문용어" in " ".join(plan["planning"]["plainLanguageContract"]["rules"])
    assert plan["planning"]["plainLanguageContract"]["preferredRewrites"]["ARR"] == "연간 반복 매출"
    assert "AI" not in plan["planning"]["plainLanguageContract"]["preferredRewrites"]
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
    post = _write_post(blog, "01-999999-test", slides=_TWO_SLIDES)
    plan = _mark_passed(cp.build_company_post_plan(post, count=7))
    (post / cp.PLAN_FILE).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    contracts = {"999999-test": {"code": "999999", "slug": "999999-test", "slides": _valid_big_sentence_slides()}}
    errors, stats = cp.validate_contract_plan_gate(contracts, blog_dir=blog, issues_dir=tmp_path / "_issues")
    assert errors == []
    assert stats == {"contracts": 1, "plans": 1, "missing": 0, "passed": 1}


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
