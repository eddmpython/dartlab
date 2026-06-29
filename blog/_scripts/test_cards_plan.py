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
    return plan


def test_build_company_plan_clamps_to_min_five_images(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    plan = cp.build_company_post_plan(post)
    assert plan["target"]["slug"] == "999999-test"
    assert plan["target"]["assetRoot"] == "sns/assets/999999"
    assert plan["planning"]["narrativeContract"]["spine"] == "훅 -> 왜 지금 중요한가 -> 근거 -> 전환 -> 판단 질문"
    assert "체크리스트" in " ".join(plan["planning"]["narrativeContract"]["rules"])
    assert len(plan["imagePlan"]) == 5
    assert all("/cards" in row["prompt"] for row in plan["imagePlan"])
    assert all("Asset key:" in row["prompt"] for row in plan["imagePlan"])
    assert all("Story specificity:" in row["prompt"] for row in plan["imagePlan"])
    assert all("avoid generic stock-finance imagery" in row["prompt"] for row in plan["imagePlan"])


def test_plan_validation_requires_passed_review(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = cp.build_company_post_plan(post, count=6)
    assert cp.validate_plan(planned, require_passed=False) == []
    errors = cp.validate_plan(planned, require_passed=True)
    assert any("reviewGate.status" in err for err in errors)
    assert cp.validate_plan(_mark_passed(planned), require_passed=True) == []


def test_plan_validation_requires_narrative_contract(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    planned = cp.build_company_post_plan(post, count=6)
    planned["planning"].pop("narrativeContract")
    errors = cp.validate_plan(planned, require_passed=False)
    assert any("planning.narrativeContract" in err for err in errors)


def test_contract_plan_gate_finds_plan_by_slug(tmp_path: Path) -> None:
    blog = tmp_path / "blog"
    post = _write_post(blog, "01-999999-test", slides=_TWO_SLIDES)
    plan = _mark_passed(cp.build_company_post_plan(post, count=5))
    (post / cp.PLAN_FILE).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    contracts = {"999999-test": {"code": "999999", "slug": "999999-test", "slides": [{"layout": "editorial"}]}}
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


def test_count_must_be_between_five_and_ten(tmp_path: Path) -> None:
    post = _write_post(tmp_path / "blog", "01-999999-test", slides=_TWO_SLIDES)
    with pytest.raises(ValueError):
        cp.build_company_post_plan(post, count=4)
    with pytest.raises(ValueError):
        cp.build_company_post_plan(post, count=11)
