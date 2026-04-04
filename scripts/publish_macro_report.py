"""매크로 경제분석 보고서 자동 발간.

GitHub Actions에서 매월 실행. 결과를 docs/macro-reports/{YYYY-MM}.md로 저장.
실패 시 GitHub Issue를 생성하는 것은 Actions workflow에서 처리.

실행: uv run python -X utf8 scripts/publish_macro_report.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main():
    from dotenv import load_dotenv

    load_dotenv()

    today = date.today()
    year_month = today.strftime("%Y-%m")

    print(f"=== dartlab macro 보고서 발간: {year_month} ===")
    print()

    # ── US 보고서 ──
    us_report = None
    us_error = None
    try:
        from dartlab.macro.report import macroReport

        us_report = macroReport(market="US", fmt="markdown")
        print(f"US 보고서: {len(us_report)}자")
    except Exception as e:
        us_error = str(e)
        print(f"US 보고서 실패: {e}")

    # ── KR 보고서 ──
    kr_report = None
    kr_error = None
    try:
        from dartlab.macro.report import macroReport

        kr_report = macroReport(market="KR", fmt="markdown")
        print(f"KR 보고서: {len(kr_report)}자")
    except Exception as e:
        kr_error = str(e)
        print(f"KR 보고서 실패: {e}")

    # ── 스냅샷 JSON ──
    snapshot = None
    try:
        from dartlab.macro.summary import analyze_summary

        snapshot = analyze_summary(market="US")
        # 직렬화 불가능한 항목 제거
        for key in list(snapshot.keys()):
            try:
                json.dumps(snapshot[key])
            except (TypeError, ValueError):
                snapshot[key] = str(snapshot[key])[:200]
    except Exception as e:
        print(f"스냅샷 실패: {e}")

    # ── 파일 저장 (docs + blog 양쪽) ──
    report_dir = os.path.join("docs", "macro-reports")
    os.makedirs(report_dir, exist_ok=True)

    # blog 카테고리 폴더
    blog_dir = os.path.join("blog", "06-macro-reports")
    os.makedirs(blog_dir, exist_ok=True)

    for market_code, report_text in [("US", us_report), ("KR", kr_report)]:
        if not report_text:
            continue

        frontmatter = (
            f"---\n"
            f"title: {market_code} 경제분석 보고서 {year_month}\n"
            f"date: {today}\n"
            f"description: dartlab macro 엔진 자동 발간. 11축 분석 + 3막 서사.\n"
            f"category: macro-reports\n"
            f"thumbnail: /avatar-macro.png\n"
            f"---\n\n"
        )

        # docs 저장
        docs_path = os.path.join(report_dir, f"{year_month}-{market_code}.md")
        with open(docs_path, "w", encoding="utf-8") as f:
            f.write(frontmatter + report_text)
        print(f"저장: {docs_path}")

        # blog 저장 (slug 기반)
        slug = f"{year_month}-{market_code.lower()}"
        blog_post_dir = os.path.join(blog_dir, slug)
        os.makedirs(blog_post_dir, exist_ok=True)
        blog_path = os.path.join(blog_post_dir, "index.md")
        with open(blog_path, "w", encoding="utf-8") as f:
            f.write(frontmatter + report_text)
        print(f"블로그: {blog_path}")

    if snapshot:
        snapshot_dir = os.path.join("docs", "macro-reports", "snapshots")
        os.makedirs(snapshot_dir, exist_ok=True)
        path = os.path.join(snapshot_dir, f"{year_month}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)
        print(f"스냅샷: {path}")

    # ── 전월 대비 diff ──
    prev_month = today.replace(day=1)
    prev_month = (prev_month - __import__("datetime").timedelta(days=1)).replace(day=1)
    prev_ym = prev_month.strftime("%Y-%m")
    prev_snapshot_path = os.path.join("docs", "macro-reports", "snapshots", f"{prev_ym}.json")

    if os.path.exists(prev_snapshot_path) and snapshot:
        try:
            with open(prev_snapshot_path, encoding="utf-8") as f:
                prev = json.load(f)
            changes = []
            # 국면 변화
            curr_phase = (snapshot.get("cycle") or {}).get("phase", "")
            prev_phase = (prev.get("cycle") or {}).get("phase", "")
            if curr_phase != prev_phase:
                changes.append(f"국면 전환: {prev_phase} → {curr_phase}")
            # 종합 점수 변화
            curr_score = snapshot.get("score", 0)
            prev_score = prev.get("score", 0)
            if isinstance(curr_score, (int, float)) and isinstance(prev_score, (int, float)):
                diff = curr_score - prev_score
                if abs(diff) > 0.5:
                    changes.append(f"종합 점수: {prev_score:+.1f} → {curr_score:+.1f} (변화 {diff:+.1f})")
            if changes:
                print(f"\n전월 대비 변화 감지:")
                for c in changes:
                    print(f"  ⚠ {c}")
        except Exception as e:
            print(f"diff 실패: {e}")

    # ── 결과 요약 (Actions output) ──
    success = us_report is not None or kr_report is not None
    errors = []
    if us_error:
        errors.append(f"US: {us_error}")
    if kr_error:
        errors.append(f"KR: {kr_error}")

    # GitHub Actions output
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"success={'true' if success else 'false'}\n")
            f.write(f"errors={'; '.join(errors) if errors else 'none'}\n")
            f.write(f"year_month={year_month}\n")

    if not success:
        print("\n보고서 생성 전부 실패!")
        sys.exit(1)

    print(f"\n=== {year_month} 보고서 발간 완료 ===")


if __name__ == "__main__":
    main()
