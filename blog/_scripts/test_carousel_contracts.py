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

import json
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
    # 첫 슬라이드 image는 중앙 콘텐츠 주소 객체 경로다.
    img = c["slides"][0]["image"]
    assert img.startswith("objects/sha256/") and img.endswith(".webp")
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
    assert c["slides"][0]["image"].startswith("objects/sha256/")
    assert len(ops) == 1


def test_issue_image_skip_when_already_uploaded(tmp_path: Path) -> None:
    """이미 같은 해시가 repo 에 있으면 재업로드 안 함(op 0). 계약 경로는 그대로."""
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
    assert mig._inject(idx, block) is False  # 멱등. 두 번째 주입 안 함
    assert idx.read_text(encoding="utf-8") == first  # 본문/frontmatter 불변


def test_name_equals_code_blocks_publish() -> None:
    """표시 이름이 종목코드와 같으면(corpName 누락 + kindList 미해석) 발행 가드가 잡는다.
    '058610 · 058610' 헤더 회귀 차단. code 가 비면(순수 이슈) 면제."""
    bad = {"058610-x": {"code": "058610", "name": "058610", "slides": []}}
    v = bcc.validate_contracts(bad)
    assert v and "종목코드와 동일" in v[0]
    # 회사명이 채워지면 통과.
    good = {"058610-x": {"code": "058610", "name": "에스피지", "slides": []}}
    assert bcc.validate_contracts(good) == []
    # code 없는 이슈(economy)는 name 이 슬러그여도 면제.
    issue = {"macro-x": {"code": "", "name": "macro-x", "slides": []}}
    assert bcc.validate_contracts(issue) == []


def test_corp_name_resolver_fallback(monkeypatch) -> None:
    """corpName·carousel.name 이 비면 kindList(gather SSOT)로 회사명을 해석해 코드 폴백을 막는다."""
    bcc._KIND_NAME_CACHE = {"058610": "에스피지"}  # getKindList 우회(네트워크 0)
    try:
        assert bcc._corp_name_from_code("058610") == "에스피지"
        assert bcc._corp_name_from_code("999999") == ""  # 미상장 → 빈 문자열(가드가 이어서 차단)
    finally:
        bcc._KIND_NAME_CACHE = None


def test_series_strips_stock_identity(tmp_path: Path) -> None:
    """series 트랙은 종목 정체성을 안 붙인다. stockCode 가 있어도 code=''·배지=편별 주제 라벨(carousel.name).
    규소 밸류체인 글에 SK하이닉스 badge 재발 방지(테마/설명 글을 종목 하나로 오분류 차단)."""
    blog = tmp_path / "blog"
    sy = "  name: 반도체 공정\n" + _SLIDES_A  # 편별 주제 라벨
    _write_post(blog, "01-000660-sand", code="000660", date="2026-01-01", with_carousel=True, slides_yaml=sy)
    c = bcc.build_contracts(blog, series=True)["000660-sand"]
    assert c["code"] == ""  # 종목코드 badge 없음
    assert c["name"] == "반도체 공정"  # 배지 = 편별 주제(회사명·코드 아님)
    assert c["cardType"] == "tech-story"
    assert bcc.validate_contracts({"000660-sand": c}) == []  # code 빈 문자열이라 name==code 가드 무관
    # series 인데 주제 라벨(carousel.name) 없으면 skip(주제 badge 필수).
    _write_post(blog, "02-000660-x", code="000660", date="2026-01-01", with_carousel=True, slides_yaml=_SLIDES_A)
    assert "000660-x" not in bcc.build_contracts(blog, series=True)
    # series 아니면 기존 회사카드 그대로(회귀 없음).
    c2 = bcc.build_contracts(blog)["000660-sand"]
    assert c2["code"] == "000660" and c2["cardType"] == "company"


def test_series_image_upload_ops_dedupes_reused_asset(tmp_path: Path) -> None:
    """기술이야기에서 같은 이미지가 여러 슬라이드에 쓰여도 업로드 op 는 1개만 만든다."""
    blog = tmp_path / "blog"
    slides = """  name: 스텔스 기술
  slides:
    - layout: editorial
      line: "스텔스는 정말 안 보일까?"
      image: hero
    - layout: editorialBeat
      line: "첫 단계는 레이더 전파가 돌아오는 길을 줄이는 일입니다."
      image: hero
"""
    _write_post(blog, "01-000000-stealth", code="000000", date="2026-01-01", with_carousel=True, slides_yaml=slides)
    assets = blog / "01-000000-stealth" / "assets"
    assets.mkdir(parents=True)
    (assets / "hero.webp").write_bytes(b"\x00fakewebp")
    image_ops: list = []
    contracts = bcc.build_contracts(blog, series=True, existing_files=set(), image_ops=image_ops)
    images = [slide["image"] for slide in contracts["000000-stealth"]["slides"]]
    assert images[0] == images[1]
    assert images[0].startswith("objects/sha256/")
    assert len(image_ops) == 1
    assert image_ops[0].path_in_repo == images[0]


def test_series_image_reuses_blog_media_catalog(tmp_path: Path) -> None:
    """기술이야기 카드는 Git 바이너리 없이 중앙 HF 객체를 그대로 재사용한다."""
    blog = tmp_path / "blog" / "08-tech-story"
    slides = """  name: 스텔스 기술
  slides:
    - layout: editorial
      line: "스텔스는 정말 안 보일까?"
      image: hero
"""
    _write_post(blog, "01-000000-stealth", code="000000", date="2026-01-01", with_carousel=True, slides_yaml=slides)
    assets = blog / "01-000000-stealth" / "assets"
    assets.mkdir(parents=True)
    sha256 = "0" * 64
    remote = f"objects/sha256/00/{sha256}.webp"
    source = "blog/08-tech-story/01-000000-stealth/assets/hero.webp"
    catalogPath = tmp_path / "media" / "catalog.json"
    catalogPath.parent.mkdir(parents=True, exist_ok=True)
    catalogPath.write_text(
        json.dumps(
            {
                "version": 4,
                "repo": "eddmpython/dartlab-media",
                "objectPrefix": "objects/sha256",
                "collections": {},
                "manifests": {
                    "carousels": "manifests/carousels.json",
                    "companies": "manifests/companies.json",
                },
                "objects": {sha256: {"bytes": 8, "path": remote}},
                "files": {source: sha256},
                "posts": {
                    "08-tech-story/01-000000-stealth": {
                        "assets": {"hero": source},
                        "og": source,
                        "staging": [source],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    imageOps: list = []

    contracts = bcc.build_contracts(blog, series=True, existing_files=set(), image_ops=imageOps)

    assert contracts["000000-stealth"]["slides"][0]["image"] == remote
    assert imageOps == []


def test_company_semantic_images_resolve_to_catalog_objects() -> None:
    """회사 의미 키는 발행 직전에 중앙 컬렉션의 객체 경로로 확정된다."""
    sha256 = "a" * 64
    objectPath = f"objects/sha256/aa/{sha256}.webp"
    contracts = {
        "005930-samsung": {
            "code": "005930",
            "cardType": "company",
            "slides": [{"layout": "editorial", "image": "semiconductor-fab"}],
        }
    }
    catalog = {
        "collections": {"companies": {"005930": {"assets": {"semiconductor-fab": sha256}}}},
        "objects": {sha256: {"path": objectPath}},
    }

    assert bcc.resolveCompanySlideImages(contracts, catalog) == []
    assert contracts["005930-samsung"]["slides"][0]["image"] == objectPath
    assert bcc.validateObjectPaths(contracts) == []


def test_non_object_slide_path_is_rejected() -> None:
    """레거시 HF 폴더와 해석되지 않은 의미 키는 런타임 manifest에 들어갈 수 없다."""
    contracts = {
        "x": {
            "code": "",
            "slides": [
                {"layout": "editorial", "image": "issues/x/cover.webp"},
                {"layout": "editorialBeat", "image": "semantic-key"},
            ],
        }
    }
    assert len(bcc.validateObjectPaths(contracts)) == 2


def test_tech_story_requires_plan(tmp_path: Path) -> None:
    """기술이야기(설명) 카드는 plan 을 08-tech-story 에서 찾고, plan 없이는 발행 못 한다(기획 강제).
    회사카드 틀에 얹어 기획을 건너뛴 회귀 봉쇄. 회사(company) 카드는 기존대로 plan 선택."""
    tech = tmp_path / "tech"
    (tech / "01-sand-to-semiconductor").mkdir(parents=True)
    tc = {"code": "", "slug": "sand-to-semiconductor", "cardType": "tech-story", "name": "반도체 공정", "slides": []}
    # plan 경로 라우팅: tech-story → tech_dir 검색(회사리포트 폴더 아님)
    p = cp.plan_path_for_contract("sand-to-semiconductor", tc, tech_dir=tech)
    assert p is not None and p.parent.name == "01-sand-to-semiconductor" and p.name == "cards.plan.json"
    # 강제: plan 파일 없으면 기획 게이트가 발행 차단(require_plan=False 여도)
    errs, _ = cp.validate_contract_plan_gate(
        {"sand-to-semiconductor": tc}, blog_dir=tmp_path / "b", issues_dir=tmp_path / "i", tech_dir=tech
    )
    assert any("기획 필수" in e for e in errs)
    # 회사 카드는 plan 없어도 통과(회귀 없음)
    comp = {"code": "005930", "slug": "x", "cardType": "company", "name": "삼성전자", "slides": []}
    errs2, _ = cp.validate_contract_plan_gate(
        {"x": comp}, blog_dir=tmp_path / "b", issues_dir=tmp_path / "i", tech_dir=tech
    )
    assert not any("없음" in e for e in errs2)


def test_visual_contract_gate() -> None:
    """하이브리드 visual 렌더링 계약 게이트 + 확장 루프. 렌더러 구현분만 통과, 나머지는 '추가하라'로 막는다."""

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
