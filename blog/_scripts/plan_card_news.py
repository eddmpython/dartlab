"""Create or check a unified blog + landing /cards image_gen plan.

Examples:
  uv run python -X utf8 blog/_scripts/plan_card_news.py --post blog/05-company-reports/30-005930-samsung --write
  uv run python -X utf8 blog/_scripts/plan_card_news.py --issue 2026-06-korea-macro --write --count 6
  uv run python -X utf8 blog/_scripts/plan_card_news.py --check --allow-planned
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cards_plan import (
    ISSUES_DIR,
    PLAN_FILE,
    ROOT,
    build_company_post_plan,
    build_issue_plan,
    rel,
    validate_plan_file,
)


def plan_path_for_post(post: Path) -> Path:
    post_dir = post if post.is_dir() else post.parent
    return post_dir / PLAN_FILE


def plan_path_for_issue(slug: str) -> Path:
    return ISSUES_DIR / slug / PLAN_FILE


def collect_plan_files(root: Path = ROOT) -> list[Path]:
    return sorted(root.glob(f"blog/**/{PLAN_FILE}"))


def print_plan(plan: dict) -> None:
    print(json.dumps(plan, ensure_ascii=False, indent=2))


def write_plan(plan: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {rel(path)}")
    print(f"imagePlan={len(plan.get('imagePlan', []))} reviewGate={plan.get('reviewGate', {}).get('status')}")
    print("먼저 planning.narrativeContract 기준으로 슬라이드가 한 문장처럼 이어지는지 닫는다.")
    print("새 계획은 큰문장만 이어 읽어도 이해되는 7장 이상 서사를 발행 게이트에서 다시 검사한다.")
    print("다음: imagePlan[].prompt 를 image_gen 으로 한 장씩 생성하고, imagegen.extractCommand 로 저장한다.")


def check_plans(paths: list[Path], *, require_passed: bool, require_assets: bool) -> int:
    failed = 0
    if not paths:
        print("cards.plan.json 없음")
        return 0
    for path in paths:
        errors = validate_plan_file(path, require_passed=require_passed, require_assets=require_assets)
        if errors:
            failed += 1
            print(f"FAIL {rel(path)}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"PASS {rel(path)}")
    print(f"checked={len(paths)} failed={failed}")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--post", type=Path, help="blog post directory or index.md")
    target.add_argument("--issue", help="blog/_issues/<slug>")
    target.add_argument("--check", action="store_true", help="check existing cards.plan.json files")
    parser.add_argument(
        "--count", type=int, help="image count, at least 7 for new narrative plans. Default derives from slide count"
    )
    parser.add_argument("--write", action="store_true", help="write cards.plan.json instead of printing JSON")
    parser.add_argument(
        "--allow-planned", action="store_true", help="check structure without requiring reviewGate.status=passed"
    )
    parser.add_argument("--require-assets", action="store_true", help="check that every planned .webp exists")
    args = parser.parse_args()

    if args.check:
        return check_plans(
            collect_plan_files(),
            require_passed=not args.allow_planned,
            require_assets=args.require_assets,
        )

    if args.post:
        post_dir = args.post if args.post.is_dir() else args.post.parent
        plan = build_company_post_plan(post_dir, count=args.count)
        out = plan_path_for_post(post_dir)
    elif args.issue:
        issue_dir = ISSUES_DIR / args.issue
        plan = build_issue_plan(issue_dir, count=args.count)
        out = plan_path_for_issue(args.issue)
    else:
        parser.error("one of --post, --issue, or --check is required")

    if args.write:
        write_plan(plan, out)
    else:
        print_plan(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
