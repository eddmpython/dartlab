"""팟캐스트 기획 저작기: podcast_plan_loop 산출(plan JSON) -> 에피소드 폴더 스캐폴드.

podcast_plan_loop.workflow.js 가 통과시킨 plan(완결 산문 소스 문서 구조체)을 받아
blog/_podcasts/episodes/P0N-{lane}-{slug}/ 아래에:
  - script.md      : NotebookLM 에 넣을 완결 산문 소스 문서 (운영자가 이걸 NotebookLM 에 제공)
  - episode.yaml   : 메타데이터 스캐폴드 (status: draft, 오디오 나오면 ready 로)
  - brief.json     : 기획 요지 (insight + oneLineMessage + whereToLook)
를 만든다. episodeNo 는 기존 최대+1 자동 배정.

사용:
    uv run python -X utf8 blog/_podcasts/_lib/plan_episode.py \
        --plan /path/to/plan.json --lane company --slug samyang-foods \
        --stock-code 003230 --corp-name 삼양식품 \
        [--card-slug 003230-samyang-foods] [--blog-slug 003230-samyang-foods]

플로우: 이 스캐폴드 -> 운영자가 script.md 검토 -> NotebookLM 에 제공 -> 오디오 m4a 수령
        -> episode.yaml status=ready -> publish_podcast.py 로 발행.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
PODCAST_DIR = LIB_DIR.parent
EPISODES_DIR = PODCAST_DIR / "episodes"

VALID_LANES = ("dartlab", "company", "economy", "disclosure", "quant")


def next_episode_no() -> int:
    """기존 에피소드 폴더에서 최대 episodeNo+1 반환."""
    mx = 0
    for d in EPISODES_DIR.glob("P*-*"):
        m = re.match(r"P(\d+)-", d.name)
        if m:
            mx = max(mx, int(m.group(1)))
    return mx + 1


def render_script_md(plan: dict) -> str:
    """plan(소스 문서 구조체) -> NotebookLM 용 완결 산문 마크다운."""
    out: list[str] = []
    out.append(f"# {plan['title']}")
    out.append("")
    out.append(plan.get("oneLineMessage", "").strip())
    out.append("")
    for sec in sorted(plan.get("sections", []), key=lambda s: s["order"]):
        out.append(f"## {sec['heading']}")
        out.append("")
        out.append(sec["body"].strip())
        out.append("")
    refs = plan.get("insight", {}).get("evidenceRefs", [])
    if refs:
        out.append("## 근거 메모 (진행자용, 낭독 아님)")
        out.append("")
        for r in refs:
            out.append(f"- {r}")
        out.append("")
    forbidden = plan.get("forbiddenAngles", [])
    if forbidden:
        out.append("## 이 에피소드에서 하지 않는 말")
        out.append("")
        out.append("- " + ", ".join(forbidden) + " 로 흐르지 않는다. 투자 권유가 아니다.")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_episode_yaml(
    plan: dict,
    *,
    episode_id: str,
    episode_no: int,
    lane: str,
    slug: str,
    stock_code: str,
    corp_name: str,
    card_slug: str,
    blog_slug: str,
    terminal_code: str,
) -> str:
    """episode.yaml 스캐폴드 문자열(사람이 이어서 손보는 SSOT)."""
    insight = plan.get("insight", {})
    summary = insight.get("twistFact", plan.get("oneLineMessage", "")).strip()
    where = plan.get("closingWhereToLook", [])
    forbidden = plan.get("forbiddenAngles", [])
    card_type = "meta" if lane == "dartlab" else ("company" if lane == "company" else lane)

    def _yaml_list(items: list[str], indent: str) -> str:
        if not items:
            return " []"
        return "\n" + "\n".join(f"{indent}- {json.dumps(x, ensure_ascii=False)}" for x in items)

    lines = [
        "# 에피소드 메타데이터 (사람이 작성하는 SSOT).",
        "# 발행 시 guid/오디오크기/길이/발행일은 published.json 에 기록된다(여기 아님).",
        "episode:",
        "  version: 1",
        f"  episodeId: {episode_id}",
        f"  episodeNo: {episode_no}",
        f"  slug: {slug}",
        f"  title: {json.dumps(plan['title'], ensure_ascii=False)}",
        f"  lane: {lane}",
        "  language: ko",
        "  status: draft                          # 오디오 수령 후 ready 로 바꾸면 발행 대상",
        "",
        "  audio:",
        "    generator: notebooklm",
        '    sourceHint: ""                       # NotebookLM m4a 경로(발행 시 --audio 로 지정)',
        "    sourceDoc: script.md",
        "",
        "  image:",
        '    source: ""                           # 에피소드 폴더 기준 커버 소스. 예: cover.png',
        f"    key: episodes/{slug}/cover-3000.jpg",
        "  staticImage:",
        '    source: ""                           # 16:9 정적 영상 이미지 소스. 예: static-video.jpg',
        f"    key: episodes/{slug}/static-video.jpg",
        "  thumbnail:",
        '    source: ""                           # staticImage 와 같으면 같은 파일 지정',
        f"    key: episodes/{slug}/static-video.jpg",
        "  sourceAssets: []                       # HF media repo 에 보관할 재사용 원본 이미지",
        "  visual:",
        '    source: ""                           # 예: assets/source-gray.webp',
        f'    kicker: "EP.{episode_no:02d} · DartLab Podcast"',
        "    titleLines: []                       # 카드뉴스형 줄바꿈 제목",
        '    subtitle: ""',
        '    footer: ""',
        "  caption:",
        '    hook: ""',
        '    body: ""',
        '    cta: ""',
        "    hashtags: []",
        "",
        f"  audienceQuestion: {json.dumps(insight.get('commonBelief', ''), ensure_ascii=False)}",
        f"  oneLineMessage: {json.dumps(plan.get('oneLineMessage', ''), ensure_ascii=False)}",
        f"  summary: {json.dumps(' '.join(summary.split()), ensure_ascii=False)}",
        "  whereToLook:" + _yaml_list(where, "    "),
        "  forbiddenAngles:" + _yaml_list(forbidden, "    "),
        "",
        f"  stockCode: {json.dumps(stock_code, ensure_ascii=False)}",
        f"  corpName: {json.dumps(corp_name, ensure_ascii=False)}",
        # topicSlug = 주제축 조인 키 SSOT. 주제글은 블로그 URL slug 와 동일해야 세 서피스가 조인된다
        # (operation.content 조인 키 계약). 블로그 링크가 있으면 그 slug 를 쓰고, 없으면 에피소드 slug 폴백.
        f"  topicSlug: {'dartlab' if lane == 'dartlab' else (blog_slug or slug)}",
        f"  cardType: {card_type}",
        "  links:",
        f"    blogSlug: {json.dumps(blog_slug, ensure_ascii=False)}",
        f"    cardSlug: {json.dumps(card_slug, ensure_ascii=False)}",
        f"    terminalCode: {json.dumps(terminal_code, ensure_ascii=False)}",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="팟캐스트 기획 저작 (plan JSON -> 에피소드 폴더)")
    parser.add_argument("--plan", required=True, help="podcast_plan_loop 산출 plan JSON 경로")
    parser.add_argument("--lane", required=True, choices=VALID_LANES)
    parser.add_argument("--slug", required=True, help="에피소드 slug (kebab)")
    parser.add_argument("--stock-code", default="", help="회사 lane 이면 6자리")
    parser.add_argument("--corp-name", default="")
    parser.add_argument("--card-slug", default="")
    parser.add_argument("--blog-slug", default="")
    parser.add_argument("--terminal-code", default="")
    parser.add_argument("--force", action="store_true", help="기존 폴더 덮어쓰기")
    args = parser.parse_args(argv)

    raw = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    plan = raw.get("plan", raw)  # 워크플로 산출 {plan,...} 또는 plan 자체 허용
    if args.lane == "company" and not args.stock_code:
        raise SystemExit("[plan] company lane 은 --stock-code 6자리 필수")

    episode_no = next_episode_no()
    episode_id = f"P{episode_no:02d}-{args.lane}-{args.slug}"
    ep_dir = EPISODES_DIR / episode_id
    if ep_dir.exists() and not args.force:
        raise SystemExit(f"[plan] 이미 존재: {ep_dir} (덮어쓰려면 --force)")
    ep_dir.mkdir(parents=True, exist_ok=True)

    (ep_dir / "script.md").write_text(render_script_md(plan), encoding="utf-8")
    (ep_dir / "episode.yaml").write_text(
        render_episode_yaml(
            plan,
            episode_id=episode_id,
            episode_no=episode_no,
            lane=args.lane,
            slug=args.slug,
            stock_code=args.stock_code,
            corp_name=args.corp_name,
            card_slug=args.card_slug,
            blog_slug=args.blog_slug,
            terminal_code=args.terminal_code,
        ),
        encoding="utf-8",
    )
    (ep_dir / "brief.json").write_text(
        json.dumps(
            {
                "title": plan["title"],
                "oneLineMessage": plan.get("oneLineMessage", ""),
                "insight": plan.get("insight", {}),
                "closingWhereToLook": plan.get("closingWhereToLook", []),
                "forbiddenAngles": plan.get("forbiddenAngles", []),
                "loopLog": raw.get("loopLog", []),
                "passed": raw.get("passed"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"[plan] 스캐폴드 완료: {ep_dir}")
    print("  - script.md   (NotebookLM 에 제공할 완결 산문 소스 문서)")
    print("  - episode.yaml (status=draft, 오디오 수령 후 ready 로)")
    print("  - brief.json  (기획 요지 + 루프 로그)")
    print("\n다음: script.md 검토 -> NotebookLM 에 제공 -> m4a 수령 -> episode.yaml status=ready ->")
    print(f"  uv run python -X utf8 blog/_podcasts/_lib/publish_podcast.py --episode {episode_id} --audio <m4a>")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
