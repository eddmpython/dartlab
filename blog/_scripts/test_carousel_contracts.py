"""build_carousel_contracts + migrate_carousels_to_blog 단위 테스트(운영자 로컬·CI 무관).

핵심 회귀 가드:
  - 같은 코드 다글(slug A·B) → 계약 2개·index posts 2엔트리(덮어쓰기 0) = 1:N.
  - index posts date 내림차순.
  - carousel: 없는 글 = 계약 없음. 슬라이드 0 = skip.
  - _normalize_slide layout enum.
  - migration _inject 멱등(2회 = 동일).

실행: uv run python -X utf8 -m pytest blog/_scripts/test_carousel_contracts.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_carousel_contracts as bcc  # noqa: E402
import cards_plan as cp  # noqa: E402
import migrate_carousels_to_blog as mig  # noqa: E402


def _write_post(
    blog_dir: Path, folder: str, *, code: str, date: str, with_carousel: bool, slides_yaml: str = ""
) -> None:
    """fixture 블로그 글 index.md 작성(frontmatter + 본문)."""
    d = blog_dir / folder
    d.mkdir(parents=True, exist_ok=True)
    carousel = ""
    if with_carousel:
        carousel = f"""carousel:
  title: "포스트 {folder}"
  caption: |
    캡션 문단1.

    캡션 문단2.
  keyMetrics:
    - label: "매출"
      value: "10억"
  pinnedComment: "근거·면책"
{slides_yaml}"""
    (d / "index.md").write_text(
        f"""---
title: "글 {folder}"
date: {date}
stockCode: "{code}"
corpName: "테스트{code}"
{carousel}---
본문 산문. 숫자 21 과 7배.
""",
        encoding="utf-8",
    )


_SLIDES_A = """  slides:
    - layout: editorial
      line: "커버 라인 A"
      image: hero-a
    - layout: editorialStat
      kicker: "마진"
      bigNumber: "21%"
"""
_SLIDES_B = """  slides:
    - layout: editorialBeat
      line: "비트 라인 B"
"""


def test_one_to_n_same_code_two_slugs(tmp_path: Path) -> None:
    """같은 코드(999999) 다른 슬러그 2글 → 계약 2개(덮어쓰기 0) = 1:N."""
    blog = tmp_path / "blog"
    _write_post(blog, "01-999999-aaa", code="999999", date="2026-01-02", with_carousel=True, slides_yaml=_SLIDES_A)
    _write_post(blog, "02-999999-bbb", code="999999", date="2026-01-01", with_carousel=True, slides_yaml=_SLIDES_B)
    contracts = bcc.build_contracts(blog)
    assert set(contracts.keys()) == {"999999-aaa", "999999-bbb"}
    assert contracts["999999-aaa"]["code"] == "999999"
    assert contracts["999999-bbb"]["code"] == "999999"
    assert len(contracts["999999-aaa"]["slides"]) == 2
    assert len(contracts["999999-bbb"]["slides"]) == 1
    assert contracts["999999-aaa"]["keyMetrics"] == [{"label": "매출", "value": "10억"}]


def test_index_date_desc(tmp_path: Path) -> None:
    """index posts = date 내림차순(인스타식 최신순)."""
    blog = tmp_path / "blog"
    _write_post(blog, "01-999999-aaa", code="999999", date="2026-01-02", with_carousel=True, slides_yaml=_SLIDES_A)
    _write_post(blog, "02-888888-bbb", code="888888", date="2026-03-09", with_carousel=True, slides_yaml=_SLIDES_B)
    posts = bcc.build_index(bcc.build_contracts(blog))
    assert [p["slug"] for p in posts] == ["888888-bbb", "999999-aaa"]
    assert posts[0]["date"] == "2026-03-09"


def test_no_carousel_excluded(tmp_path: Path) -> None:
    """carousel: 없는 글 = 계약 없음(자동 덱만, 피드 비노출)."""
    blog = tmp_path / "blog"
    _write_post(blog, "01-777777-ccc", code="777777", date="2026-01-01", with_carousel=False)
    assert bcc.build_contracts(blog) == {}


def test_carousel_without_slides_skipped(tmp_path: Path) -> None:
    """carousel: 있어도 editorial 슬라이드 0이면 skip."""
    blog = tmp_path / "blog"
    _write_post(
        blog, "01-666666-ddd", code="666666", date="2026-01-01", with_carousel=True, slides_yaml="  slides: []\n"
    )
    assert bcc.build_contracts(blog) == {}


def test_spec_overlay_carried(tmp_path: Path) -> None:
    """hero/order/notes 오버레이가 계약 spec 에 실린다(blog 번들 비의존)."""
    blog = tmp_path / "blog"
    sy = _SLIDES_A + "  hero: cover-x\n  order:\n    - segment\n  notes:\n    segment: 손글 한줄\n"
    _write_post(blog, "01-555555-eee", code="555555", date="2026-01-01", with_carousel=True, slides_yaml=sy)
    c = bcc.build_contracts(blog)["555555-eee"]
    assert c["spec"]["hero"] == "cover-x"
    assert c["spec"]["order"] == ["segment"]
    assert c["spec"]["notes"] == {"segment": "손글 한줄"}


@pytest.mark.parametrize(
    "raw,expect",
    [
        ({"layout": "editorial", "line": "x", "image": "y"}, {"layout": "editorial", "line": "x", "image": "y"}),
        ({"layout": "editorialStat", "bigNumber": "21%"}, {"layout": "editorialStat", "bigNumber": "21%"}),
        ({"layout": "bottomLeft", "line": "x"}, None),  # editorial 3종 아님 → None
        ({"line": "x"}, None),  # layout 없음
        ("notadict", None),
    ],
)
def test_normalize_slide(raw, expect) -> None:
    assert bcc._normalize_slide(raw) == expect


def test_issue_contract_standalone(tmp_path: Path) -> None:
    """blog/_issues/<slug>/carousel.yaml → code 없는 standalone 이슈 계약 + 이미지 hfMedia 경로/업로드 op."""
    issues = tmp_path / "_issues"
    slug = "2026-06-korea-macro"
    d = issues / slug
    (d / "assets").mkdir(parents=True, exist_ok=True)
    (d / "assets" / "cover.webp").write_bytes(b"\x00fakewebp")  # 콘텐츠해시용 더미
    (d / "carousel.yaml").write_text(
        """name: "2026 한국 경제"
title: "반도체가 끌고, 환율이 누른다"
date: 2026-06-25
sector: macro
caption: |
  설명 문단.
pinnedComment: "출처·면책"
slides:
  - layout: editorial
    line: "커버 [[강조]]"
    image: cover
  - layout: editorialStat
    kicker: "성장률"
    bigNumber: "2.5"
    unit: "%"
""",
        encoding="utf-8",
    )
    contracts, ops = bcc.build_issue_contracts(issues, existing_files=set())
    assert set(contracts.keys()) == {slug}
    c = contracts[slug]
    assert c["code"] == ""  # 종목코드 없음
    assert c["standalone"] is True
    assert c["name"] == "2026 한국 경제"
    assert c["sector"] == "macro"
    assert len(c["slides"]) == 2
    # 첫 슬라이드 image → hfMedia 상대경로(issues/<slug>/cover.<hash8>.webp)
    img = c["slides"][0]["image"]
    assert img.startswith(f"issues/{slug}/cover.") and img.endswith(".webp")
    assert len(ops) == 1 and ops[0].path_in_repo == img  # 새 해시 → 업로드 1건


def test_issue_contract_with_stock_code_attaches_company_deck(tmp_path: Path) -> None:
    """stockCode 있는 이슈 카드는 블로그 CTA 는 숨기되 회사 report 덱을 붙일 수 있게 code 를 싣는다."""
    issues = tmp_path / "_issues"
    slug = "samsung-biologics-rockville-rampup"
    d = issues / slug
    (d / "assets").mkdir(parents=True, exist_ok=True)
    (d / "assets" / "cover.webp").write_bytes(b"\x00fakewebp")
    (d / "carousel.yaml").write_text(
        """name: "삼성바이오로직스"
stockCode: "207940"
corpName: "삼성바이오로직스"
title: "공장 가동을 봅니다"
date: 2026-06-28
keyMetrics:
  - label: "매출"
    value: "10억"
explainers:
  - term: "록빌"
    body: "미국 생산 거점"
relatedNews:
  - title: "관련 뉴스"
    source: "naver.example"
    date: 2026-06-15
    url: "https://example.com/news"
    track: "naver"
    description: "보관 뉴스 링크"
slides:
  - layout: editorial
    line: "좋은 숫자보다 [[공장]]"
    image: cover
""",
        encoding="utf-8",
    )
    contracts, ops = bcc.build_issue_contracts(issues, existing_files=set())
    c = contracts[slug]
    assert c["code"] == "207940"
    assert c["name"] == "삼성바이오로직스"
    assert c["standalone"] is True  # 블로그 글은 없어서 CTA 숨김. 차트 첨부 여부는 code 가 결정.
    assert c["keyMetrics"] == [{"label": "매출", "value": "10억"}]
    assert c["explainers"] == [{"term": "록빌", "body": "미국 생산 거점"}]
    assert c["relatedNews"] == [
        {
            "title": "관련 뉴스",
            "url": "https://example.com/news",
            "source": "naver.example",
            "date": "2026-06-15",
            "description": "보관 뉴스 링크",
            "track": "naver",
        }
    ]
    assert c["slides"][0]["image"].startswith(f"issues/{slug}/cover.")
    assert len(ops) == 1


def test_issue_image_skip_when_already_uploaded(tmp_path: Path) -> None:
    """이미 같은 해시가 repo 에 있으면 재업로드 안 함(op 0) — 계약 경로는 그대로."""
    issues = tmp_path / "_issues"
    d = issues / "x"
    (d / "assets").mkdir(parents=True, exist_ok=True)
    (d / "assets" / "cover.webp").write_bytes(b"\x00fakewebp")
    (d / "carousel.yaml").write_text(
        'name: "X"\nslides:\n  - layout: editorial\n    line: "L"\n    image: cover\n', encoding="utf-8"
    )
    first, ops1 = bcc.build_issue_contracts(issues, existing_files=set())
    remote = first["x"]["slides"][0]["image"]
    _, ops2 = bcc.build_issue_contracts(issues, existing_files={remote})
    assert len(ops1) == 1 and ops2 == []  # 두 번째는 스킵


def test_migration_idempotent(tmp_path: Path) -> None:
    """_inject 2회 = 동일(이미 carousel: 있으면 두 번째는 False)."""
    blog = tmp_path / "blog"
    _write_post(blog, "01-444444-fff", code="444444", date="2026-01-01", with_carousel=False)
    idx = blog / "01-444444-fff" / "index.md"
    block = {"title": "T", "slides": [{"layout": "editorial", "line": "L"}]}
    assert mig._inject(idx, block) is True
    first = idx.read_text(encoding="utf-8")
    assert mig._has_carousel(idx) is True
    assert mig._inject(idx, block) is False  # 멱등 — 두 번째 주입 안 함
    assert idx.read_text(encoding="utf-8") == first  # 본문/frontmatter 불변


def test_visual_contract_gate() -> None:
    """하이브리드 visual 렌더링 계약 게이트 + 확장 루프 — 렌더러 구현분만 통과, 나머지는 '추가하라'로 막는다."""

    def contract(visual: dict) -> dict:
        return {"slides": [{"layout": "editorialBeat", "line": "큰문장입니다", "visual": visual}]}

    # 렌더러 구현분(finCard/table). 밀도 충족(분기 6점 이상) + 필드 유효하면 통과
    dense = ["24Q1", "24Q2", "24Q3", "24Q4", "25Q1", "25Q2"]
    assert (
        cp.validate_contract_visuals(
            "s", contract({"kind": "finCard", "periods": dense, "series": [{"name": "x", "data": [1, 2, 3, 4, 5, 6]}]})
        )
        == []
    )
    assert (
        cp.validate_contract_visuals(
            "s", contract({"kind": "table", "cols": ["기간", "값"], "data": [{"기간": "24", "값": "1"}]})
        )
        == []
    )
    # 등록됐으나 렌더러 미구현(finChart). 확장 루프(렌더러 추가) 안내로 막힘
    errs = cp.validate_contract_visuals("s", contract({"kind": "finChart", "stockCode": "005930"}))
    assert errs and "렌더러 미구현" in errs[0]
    # 미등록 계약(sankey). 레지스트리 추가(확장 루프) 안내로 막힘
    errs2 = cp.validate_contract_visuals("s", contract({"kind": "sankey"}))
    assert errs2 and "미등록" in errs2[0]
    # 듬성 시계열(periods<6). 막힘(그래프는 항상 밀도 있게)
    sparse = cp.validate_contract_visuals(
        "s", contract({"kind": "finCard", "periods": ["23", "24", "25"], "series": [{"name": "x", "data": [1, 2, 3]}]})
    )
    assert sparse and any("밀도" in e for e in sparse)
    # 구멍(빈 값) 있는 시리즈. 막힘(연도·분기 건너뛰지 않는다)
    holed = cp.validate_contract_visuals(
        "s",
        contract({"kind": "finCard", "periods": dense, "series": [{"name": "x", "data": [1, 2, None, 4, 5, 6]}]}),
    )
    assert holed and any("구멍" in e for e in holed)
    # visual 없는 슬라이드(기존 카드). 무회귀(통과)
    assert cp.validate_contract_visuals("s", {"slides": [{"layout": "editorialBeat", "line": "x"}]}) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
