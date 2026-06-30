"""발행 러너 회귀 — detect(실 index.md·_issues cards.plan.json) · payload url/tag · nonce 결정성 · sanitize.

slug 가 라이브 +page.ts normalizePath 와 동형(\\d+- 뒤 그룹)이고 title+body 가 비지 않음을 검증.
실행: uv run python -X utf8 -m pytest .github/scripts/notify/
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))  # 플랫 import(러너 디렉터리)

import send  # noqa: E402
from authHeaders import nonce_for, serialize_body  # noqa: E402
from payload import PublishEvent, build_payload  # noqa: E402
from sanitize import sanitize, with_source_label  # noqa: E402


# ── 경로 regex / slug 동형 ──────────────────────────────────────────
def test_blog_re_slug_matches_normalizePath():
    m = send._BLOG_RE.match("blog/company/03-everything-about-dart/index.md")
    assert m and m.group(1) == "everything-about-dart"  # 카테고리·번호 미포함(+page.ts 동형)


def test_issue_re_slug():
    m = send._ISSUE_RE.match("blog/_issues/sk-hynix-hbm/cards.plan.json")
    assert m and m.group(1) == "sk-hynix-hbm"


def test_blog_re_rejects_non_index():
    assert send._BLOG_RE.match("blog/company/03-foo/cover.png") is None


# ── detect (git diff monkeypatch + 실 파일) ─────────────────────────
def test_detect_blog(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "blog" / "company" / "03-foo-bar"
    d.mkdir(parents=True)
    (d / "index.md").write_text(
        "---\ntitle: 삼성전자 분석\ndescription: 반도체 사이클 정리\n---\n본문", encoding="utf-8"
    )
    monkeypatch.setattr(send, "_git", lambda *a: "blog/company/03-foo-bar/index.md\n")
    evs = send.detect("a", "b")
    assert len(evs) == 1
    assert evs[0].topic == "blogPublish"
    assert evs[0].slug == "foo-bar"
    assert evs[0].title == "삼성전자 분석"
    assert evs[0].summary == "반도체 사이클 정리"


def test_detect_blog_with_carousel_emits_card(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "blog" / "company" / "07-hbm-story"
    d.mkdir(parents=True)
    (d / "index.md").write_text(
        "---\ntitle: HBM 이야기\ndescription: 메모리 슈퍼사이클\ncarousel:\n  slides: 8\n---\n본문",
        encoding="utf-8",
    )
    monkeypatch.setattr(send, "_git", lambda *a: "blog/company/07-hbm-story/index.md\n")
    evs = send.detect("a", "b")
    assert [e.topic for e in evs] == ["blogPublish", "cardPublish"]
    assert all(e.slug == "hbm-story" for e in evs)


def test_detect_issue_card(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "blog" / "_issues" / "samsung-q3"
    d.mkdir(parents=True)
    (d / "cards.plan.json").write_text(
        '{"target":{"title":"삼성 3분기","slug":"samsung-q3"},"planning":{"cardThesis":"실적 서프라이즈 요약"}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(send, "_git", lambda *a: "blog/_issues/samsung-q3/cards.plan.json\n")
    evs = send.detect("a", "b")
    assert len(evs) == 1
    assert evs[0].topic == "cardPublish"
    assert evs[0].slug == "samsung-q3"
    assert evs[0].title == "삼성 3분기"
    assert evs[0].summary == "실적 서프라이즈 요약"


def test_detect_skips_deleted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # 파일 미생성 = 삭제분
    monkeypatch.setattr(send, "_git", lambda *a: "blog/company/03-gone/index.md\n")
    assert send.detect("a", "b") == []


# ── payload url/tag/title ───────────────────────────────────────────
def test_build_payload_blog():
    p = build_payload(PublishEvent("blogPublish", "foo-bar", "제목", "요약문"))
    n = p["notification"]
    assert p["topic"] == "blogPublish"
    assert n["url"] == "/blog/foo-bar"  # app-path(base 없음) — SW 가 BASE 접두
    assert n["tag"] == "blog:foo-bar"
    assert n["title"].startswith("[새 글] ")
    assert n["body"] == "요약문"


def test_build_payload_card_route():
    p = build_payload(PublishEvent("cardPublish", "samsung-q3", "제목", "요약"))
    n = p["notification"]
    assert n["url"] == "/cards?post=samsung-q3"  # 라이브 = /cards?post= (share.ts 동형)
    assert n["tag"] == "card:samsung-q3"
    assert n["title"].startswith("[새 카드] ")


# ── nonce 결정성 (멱등) ─────────────────────────────────────────────
def test_nonce_deterministic_and_topic_separated():
    assert nonce_for("blogPublish", "foo") == nonce_for("blogPublish", "foo")  # 같은 발행 = 같은 nonce(멱등)
    assert nonce_for("blogPublish", "foo") != nonce_for("cardPublish", "foo")  # blog vs card 분리(둘 다 발송)
    assert nonce_for("blogPublish", "foo") != nonce_for("blogPublish", "bar")


def test_serialize_body_compact_bytes():
    raw = serialize_body({"a": 1, "b": "한글"})
    assert isinstance(raw, bytes)
    assert b", " not in raw and b": " not in raw  # separators=(",",":") 콤팩트


# ── sanitize ────────────────────────────────────────────────────────
def test_sanitize_strips_control_and_caps():
    assert sanitize("a" + chr(0x07) + "b") == "ab"
    assert sanitize("x" + chr(0x200B) + chr(0x202E) + "y") == "xy"  # zero-width + RTL override
    out = sanitize("가" * 200, max_len=120)
    assert len(out) == 120 and out.endswith("…")
    assert sanitize("a\t\nb") == "a b"  # 공백 제어문자는 단일 공백


def test_with_source_label():
    assert with_source_label("신규 수주 1조원", "DART 공시").startswith("[DART 공시] ")
