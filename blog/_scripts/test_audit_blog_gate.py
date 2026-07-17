"""auditBlog publish gate tests.

실행: uv run python -X utf8 -m pytest blog/_scripts/test_audit_blog_gate.py -v
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import auditBlog as ab  # noqa: E402


def _brief(score: int = 94) -> dict:
    title = "스텔스는 왜 기체보다 병목이 먼저 보일까"
    return {
        "contractVersion": 2,
        "title": title,
        "titleContract": {
            "workingTitle": title,
            "selectedTitle": title,
            "hookQuestion": "스텔스 뉴스에서 왜 전투기 사진보다 병목 회사가 먼저 보일까?",
            "readerGap": "독자는 기체가 주인공이라고 보지만 글은 공정과 공시의 병목을 보여준다.",
            "promise": "제목의 질문을 기술 지도와 DART·EDGAR 근거로 끝까지 갚는다.",
            "whySelected": "기체 사진이라는 상식을 뒤집고 공정 병목을 첫 문장부터 걸기 때문이다.",
            "candidates": [
                {"title": title, "hook": "기체와 병목의 충돌", "risk": "기술 설명을 충분히 갚아야 한다"},
                {"title": "스텔스의 진짜 주인공은 어디에 있을까", "hook": "주인공 전환", "risk": "다소 넓다"},
                {"title": "레이더보다 공시에서 보이는 스텔스", "hook": "기술과 공시 연결", "risk": "은유가 강하다"},
            ],
            "rejectedPatterns": ["정리", "분석", "돈을 못 번다"],
        },
        "description": "스텔스 기술을 공정 지도와 공시 근거로 읽는다.",
        "readerQuestion": "스텔스는 왜 전투기 한 대가 아니라 형상·센서·엔진·정비의 병목 지도로 읽어야 할까?",
        "insight": {
            "commonBelief": "스텔스는 안 보이는 전투기라서 완성기 회사만 보면 된다고 여긴다.",
            "twistFact": "스텔스의 경제적 힘은 기체 사진보다 형상, 센서, 엔진, 전자전, 정비 병목이 공시에 찍히는 시간표에서 보인다.",
            "whatToWatch": "다음 공시에서는 수주잔고, 개발비, 양산 전환, 정비 계약이 어느 회사에 붙는지 본다.",
            "freshnessArgument": "기술 원리와 DART·EDGAR 손익을 같은 지도에 놓아 기존 전투기 성능 서사와 다르게 읽는다.",
            "evidenceRefs": ["DART 2025Q1~Q4", "EDGAR FY2025 10-K"],
        },
        "watchScenarios": [
            {
                "condition": "만약 양산 전환과 정비 계약이 같은 분기에 늘어난다면",
                "mechanism": "생산 물량과 후속 정비 수요가 부품과 센서 회사로 함께 전달된다.",
                "outcome": "완성기보다 병목 부품 회사의 수주잔고가 먼저 늘어날 수 있다.",
                "watchMetric": "다음 DART 공시의 수주잔고와 양산 매출 비중을 확인한다.",
                "invalidatedBy": "양산 물량은 늘어도 부품 수주잔고와 정비 계약이 줄면 이 경로는 틀린다.",
                "evidenceRefs": ["DART 2025Q1~Q4"],
            },
            {
                "condition": "만약 개발 일정이 늦어지고 고정가 계약 원가가 오른다면",
                "mechanism": "재설계와 시험 비용이 계약 매출보다 먼저 손익에 반영된다.",
                "outcome": "기술 진척 뉴스와 달리 관련 회사의 이익률은 낮아질 수 있다.",
                "watchMetric": "EDGAR 공시의 프로그램 손실과 영업이익률을 확인한다.",
                "invalidatedBy": "일정 지연에도 프로그램 손실이 줄고 이익률이 오르면 가정이 깨진다.",
                "evidenceRefs": ["EDGAR FY2025 10-K"],
            },
        ],
        "acts": [
            {
                "order": i,
                "heading": f"{i}막 스텔스 병목을 여는 질문",
                "purpose": "메커니즘공개",
                "scene": "격납고에서 형상, 센서, 정비 문서가 함께 보이는 장면",
                "keyNumbers": ["2025 영업이익률", "수주잔고"],
                "causalBridge": "이 막의 기술 병목이 다음 막의 공시 숫자로 이어진다.",
            }
            for i in range(1, 7)
        ],
        "sections": [
            {
                "order": i,
                "heading": f"{i}막 스텔스 병목을 여는 질문",
                "subtitle": "기체 사진보다 먼저 공정 병목을 보게 만드는 한 줄 훅이다.",
                "visualAnchor": "공정 지도 표와 실제 수치 차트를 섹션 앞쪽에 배치한다.",
                "explanation": "스텔스 기술을 쉬운 말로 풀고 공시 숫자와 연결한다.",
                "example": "LMT, KAI, 한화시스템 같은 실제 회사와 FY2025 수치를 예로 든다.",
                "support": "기술 난도와 회사 전체 이익률을 바로 같게 보면 안 된다는 오해 방지를 넣는다.",
                "transition": "이 섹션의 병목이 다음 섹션의 공시 숫자와 연결된다.",
                "evaluation": "타이틀, 훅, 시각 앵커, 설명, 예시, 보완, 다음 연결이 모두 살아 있는지 평가한다.",
            }
            for i in range(1, 7)
        ],
        "visuals": [
            {
                "actOrder": 1,
                "kind": "table",
                "title": "스텔스 공정 회사 근거 지도",
                "proves": "기술 병목과 회사 배치가 한눈에 연결된다.",
                "seriesHint": "공정·회사·공시 근거",
                "placement": "1막 RCS 개념 설명 뒤 본문 중간",
                "insertAfter": "RCS가 탐지거리와 판단 시간을 바꾼다는 설명 뒤",
                "narrativeUse": "독자가 스텔스를 기체 사진이 아니라 공정 지도와 회사 배치로 보게 한다.",
            },
            {
                "actOrder": 3,
                "kind": "bar",
                "title": "미국 방산사 영업이익률 비교",
                "proves": "기술 난도가 곧바로 초고마진으로 이어지지 않는다.",
                "seriesHint": "FY2025 EDGAR",
                "placement": "3막 미국 방산사 계약 구조 설명 뒤",
                "insertAfter": "cost-plus와 고정가 계약이 손익을 제한한다는 문단 뒤",
                "narrativeUse": "독자가 기술 난도와 회계 이익률을 바로 동일시하지 않게 한다.",
            },
            {
                "actOrder": 5,
                "kind": "line",
                "title": "한국 KF-21 라인 시간표",
                "proves": "체계통합, 센서, 엔진의 이익 시차가 다르다.",
                "seriesHint": "DART 2021~2025",
                "placement": "5막 한국 KF-21 밸류체인 설명 뒤",
                "insertAfter": "KAI, 한화시스템, 한화에어로, LIG 역할 분해 뒤",
                "narrativeUse": "독자가 회사별 역할과 이익 시차를 같은 시간축으로 이해하게 한다.",
            },
        ],
        "imagePlan": [
            {
                "assetKey": "stealth-hangar",
                "sourcePolicy": "auto",
                "slot": "hero",
                "subject": "스텔스 격납고와 레이더 시험 장비",
                "query": "stealth aircraft hangar radar test maintenance",
                "keywords": ["stealth", "hangar", "radar"],
                "placement": "첫 화면 hero 이미지",
                "narrativeUse": "글 시작에서 스텔스를 전투 장면이 아니라 시험과 정비 기술로 보이게 한다.",
            },
            {
                "assetKey": "coating-maintenance",
                "sourcePolicy": "auto",
                "slot": "inline",
                "subject": "저피탐 코팅 정비 장면",
                "query": "aircraft stealth coating maintenance panel inspection",
                "keywords": ["coating", "maintenance", "panel"],
                "insertAfterAct": 2,
                "placement": "2막 코팅 정비 설명 뒤",
                "narrativeUse": "독자가 저피탐 성능이 출고 뒤 정비 품질에 계속 의존한다는 점을 본다.",
            },
            {
                "assetKey": "aesa-test-bench",
                "sourcePolicy": "auto",
                "slot": "inline",
                "subject": "AESA 레이더와 항공전자 시험 장면",
                "query": "aesa radar avionics test bench aircraft",
                "keywords": ["aesa", "radar", "avionics"],
                "insertAfterAct": 4,
                "placement": "4막 센서융합 설명 뒤",
                "narrativeUse": "독자가 스텔스를 덜 보이는 기체가 아니라 먼저 보는 센서 네트워크로 이해한다.",
            },
        ],
        "relatedPosts": {
            "searches": ["스텔스", "방산", "KF-21", "방산 수주잔고"],
            "placementRule": "기술 원리 설명 뒤에는 기술이야기, 회사 배치 설명 뒤에는 기업이야기를 연결한다.",
            "links": [
                {
                    "path": "/blog/hanwha-aerospace",
                    "title": "한화에어로스페이스 기업이야기",
                    "reason": "엔진과 방산 수주잔고를 회사 단위로 이어 본다.",
                    "placement": "KF-21 엔진과 방산 수주잔고 설명 뒤",
                },
                {
                    "path": "/blog/lig-nexone-cash-clock",
                    "title": "LIG넥스원 기업이야기",
                    "reason": "센서와 미사일 체계의 현금화 시차를 함께 본다.",
                    "placement": "센서융합과 방산 전자 장비 설명 뒤",
                },
            ],
        },
        "honestyGuards": [
            "EDGAR는 fiscal year와 quarter period를 원문으로 확인한다.",
            "DART는 연결과 별도, 분기와 누적 표시를 분리한다.",
            "기술 난도와 회사 전체 영업이익률을 바로 동일시하지 않는다.",
        ],
        "evidenceMap": [
            {
                "claim": "미국 방산사는 EDGAR FY2025 영업이익률을 쓴다.",
                "sourceType": "EDGAR",
                "period": "FY2025",
                "sourceRef": "10-K와 10-Q period",
                "howUsed": "미국 대표사 비교 표",
            },
            {
                "claim": "한국 KF-21 주변사는 DART 2025Q1~Q4를 쓴다.",
                "sourceType": "DART",
                "period": "2025Q1~Q4",
                "sourceRef": "사업보고서와 분기보고서",
                "howUsed": "한국 라인 비교 표",
            },
            {
                "claim": "계산은 dartlab Company.select로 재현한다.",
                "sourceType": "dartlab",
                "period": "2021~2025",
                "sourceRef": "Company().select('IS')",
                "howUsed": "검증표와 시계열",
            },
        ],
        "reviewGate": {
            "status": "passed",
            "loopEvidence": {
                "workflow": ab.BLOG_LOOP_WORKFLOW_NAME,
                "rounds": [
                    {
                        "round": 1,
                        "planner": "초안에서 기술 원리와 공시 지도를 함께 잡았다.",
                        "evaluator": "제목과 비주얼은 있으나 마지막 렌즈가 약해 재기획을 요구했다.",
                        "skeptic": "기체 사진 중심으로 흐를 위험과 일반 이미지 위험을 지적했다.",
                        "decision": "revise",
                        "evaluatorScore": 84,
                        "plannerRevision": "공정 병목과 DART·EDGAR 근거를 막마다 다시 배치했다.",
                    },
                    {
                        "round": 2,
                        "planner": "개선안에서 공정 지도, 비주얼, 이미지, 검증표를 제목 약속과 연결했다.",
                        "evaluator": "독자 질문과 비주얼 증거가 끝까지 살아 있고 다음 공시 렌즈가 남는다.",
                        "skeptic": "하드 kill 축이 남지 않았다.",
                        "decision": "passed",
                        "evaluatorScore": score,
                        "plannerRevision": "평가 피드백을 반영한 최종안이다.",
                    },
                ],
            },
        },
    }


def _write_tech_post(root: Path, *, brief_score: int = 94) -> Path:
    post = root / "blog" / "08-tech-story" / "01-stealth-test"
    assets = post / "assets"
    assets.mkdir(parents=True)
    for assetKey in ("stealth-hangar", "coating-maintenance", "aesa-test-bench"):
        (assets / f"{assetKey}.webp").write_bytes(b"fake")
    sha256 = hashlib.sha256(b"fake").hexdigest()
    objectPath = f"objects/sha256/{sha256[:2]}/{sha256}.webp"
    assetKeys = ("stealth-hangar", "coating-maintenance", "aesa-test-bench")
    files = {f"blog/08-tech-story/01-stealth-test/assets/{assetKey}.webp": sha256 for assetKey in assetKeys}
    files["landing/static/thumbnails/tech-stealth-test.webp"] = sha256
    media = {
        "version": 4,
        "repo": "eddmpython/dartlab-media",
        "objectPrefix": "objects/sha256",
        "collections": {},
        "manifests": {
            "carousels": "manifests/carousels.json",
            "companies": "manifests/companies.json",
        },
        "objects": {sha256: {"bytes": 4, "path": objectPath}},
        "files": files,
        "posts": {
            "08-tech-story/01-stealth-test": {
                "assets": {
                    assetKey: f"blog/08-tech-story/01-stealth-test/assets/{assetKey}.webp" for assetKey in assetKeys
                },
                "og": "landing/static/thumbnails/tech-stealth-test.webp",
                "staging": sorted(files),
            }
        },
    }
    catalogPath = root / "media" / "catalog.json"
    catalogPath.parent.mkdir(parents=True, exist_ok=True)
    catalogPath.write_text(json.dumps(media, ensure_ascii=False, indent=2), encoding="utf-8")
    (assets / "CREDITS.md").write_text(
        "\n".join(
            [
                "# 이미지 출처",
                "- stealth-hangar: image_gen 생성 이미지",
                "- coating-maintenance: 공식 보도자료 이미지",
                "- aesa-test-bench: CC0 실사",
            ]
        ),
        encoding="utf-8",
    )
    thumb = root / "landing" / "static" / "thumbnails"
    thumb.mkdir(parents=True)
    (thumb / "tech-stealth-test.webp").write_bytes(b"fake")
    filler = "스텔스 공정 병목과 대표 회사가 왜 핵심인지 설명하는 문장입니다. " * 520
    body = f"""
![스텔스 격납고](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/{objectPath})

## 공정·회사·근거 지도

| 공정/층위 | 대표 회사 | 공시 근거 |
|---|---|---|
| 형상·체계통합 | LMT·KAI | EDGAR 10-K·DART 사업보고서 |

왜 이 회사가 이 공정 네트워크 칸의 핵심인지 보려면 병목, 대체 난도, 양산 인증, CAPEX를 함께 봐야 한다.
DART와 EDGAR 근거를 모두 연결하고, dartlab 실측으로 2025Q1~Q4 손익을 확인한다.

## 기술 성숙도와 출처

양산 단계와 실험 단계를 분리한다.

![저피탐 코팅 정비](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/{objectPath})

## 이렇게 오해하면 안 된다

RCS 숫자 하나로 모든 각도와 주파수를 설명하면 안 된다.

![AESA 시험 장비](https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/{objectPath})

{filler}

## 만약 조건이 바뀐다면: 관전 시나리오

만약 양산 전환과 정비 계약이 같은 분기에 늘어난다면 부품 회사의 수주잔고가 먼저 늘어날 수 있다. 다음 DART 공시의 양산 매출 비중을 확인한다. 수주잔고가 줄면 이 시나리오는 틀린다.

만약 개발 일정이 늦고 고정가 계약 원가가 오른다면 기술 진척 뉴스와 달리 이익률은 낮아질 수 있다. EDGAR의 프로그램 손실을 추적한다. 손실이 줄고 이익률이 오르면 이 가정은 깨진다.
"""
    (post / "index.md").write_text(
        f"""---
title: "스텔스는 왜 기체보다 병목이 먼저 보일까"
date: "2026-07-06"
category: tech-story
series: tech-story
topicSlug: "stealth-test"
ogImage: https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main/{objectPath}
---
{body}
""",
        encoding="utf-8",
    )
    (post / "brief.json").write_text(json.dumps(_brief(brief_score), ensure_ascii=False, indent=2), encoding="utf-8")
    return post


def test_publish_gate_accepts_tech_story_with_92_loop(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path)
    assert ab.publish_gate(post) == []


def test_publish_gate_accepts_hf_catalog_without_local_raster_staging(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path)
    for raster in post.joinpath("assets").glob("*.webp"):
        raster.unlink()
    for raster in tmp_path.joinpath("landing", "static", "thumbnails").glob("*.webp"):
        raster.unlink()

    assert ab.publish_gate(post) == []


def test_publish_gate_keeps_legacy_plan_compatible(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path)
    brief = _brief()
    brief.pop("contractVersion")
    brief.pop("watchScenarios")
    for image in brief["imagePlan"]:
        image.pop("assetKey")
        image.pop("sourcePolicy")
    (post / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")

    assert ab.publish_gate(post) == []


def test_publish_gate_requires_v2_for_new_post(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path)
    brief = _brief()
    brief.pop("contractVersion")
    (post / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")

    errors = ab.publish_gate(post, requireContractV2=True)

    assert any("contractVersion 2" in error for error in errors)


def test_publish_gate_blocks_unknown_contract_version(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path)
    brief = _brief()
    brief["contractVersion"] = 3
    (post / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")

    errors = ab.publish_gate(post, requireContractV2=True)

    assert any("지원하지 않는 contractVersion 3" in error for error in errors)
    assert any("contractVersion 2" in error for error in errors)


def test_publish_gate_blocks_missing_watch_scenarios(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path)
    brief = _brief()
    brief["watchScenarios"] = []
    (post / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")

    errors = ab.publish_gate(post)

    assert any("watchScenarios" in error for error in errors)


def test_publish_gate_blocks_image_ssot_drift(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path)
    mediaPath = tmp_path / "media" / "catalog.json"
    media = json.loads(mediaPath.read_text(encoding="utf-8"))
    del media["posts"]["08-tech-story/01-stealth-test"]["assets"]["aesa-test-bench"]
    mediaPath.write_text(json.dumps(media, ensure_ascii=False, indent=2), encoding="utf-8")
    creditsPath = post / "assets" / "CREDITS.md"
    creditsPath.write_text(
        creditsPath.read_text(encoding="utf-8").replace("- aesa-test-bench: CC0 실사", ""),
        encoding="utf-8",
    )
    indexPath = post / "index.md"
    indexPath.write_text(
        indexPath.read_text(encoding="utf-8").replace("AESA 시험 장비", "계약에서 빠진 시험 장비"),
        encoding="utf-8",
    )

    errors = ab.publish_gate(post)

    assert any("media/catalog.json" in error and "누락" in error for error in errors)
    assert any("CREDITS.md" in error and "assetKey 누락" in error for error in errors)


def test_publish_gate_blocks_non_scenario_last_section(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path)
    indexPath = post / "index.md"
    indexPath.write_text(
        indexPath.read_text(encoding="utf-8") + "\n## 참고 문서\n\nDART와 EDGAR 원문 링크를 다시 확인한다.\n",
        encoding="utf-8",
    )

    errors = ab.publish_gate(post)

    assert any("마지막 H2" in error for error in errors)


def test_publish_gate_blocks_loop_score_below_92(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path, brief_score=91)
    errors = ab.publish_gate(post)
    assert any("< 92" in err for err in errors)


def test_publish_gate_blocks_missing_loop_evidence(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path)
    brief = _brief()
    brief["reviewGate"].pop("loopEvidence")
    (post / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    errors = ab.publish_gate(post)
    assert any("loopEvidence" in err for err in errors)


def test_publish_gate_blocks_visuals_without_inline_use(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path)
    brief = _brief()
    brief["visuals"][0].pop("placement")
    brief["imagePlan"][1].pop("narrativeUse")
    (post / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    errors = ab.publish_gate(post)
    assert any("visuals[1].placement" in err for err in errors)
    assert any("imagePlan[2].narrativeUse" in err for err in errors)


def test_publish_gate_blocks_missing_section_flow(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ab, "repo_root", lambda: tmp_path)
    post = _write_tech_post(tmp_path)
    brief = _brief()
    brief["sections"][0].pop("visualAnchor")
    (post / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    errors = ab.publish_gate(post)
    assert any("sections[1].visualAnchor" in err for err in errors)


def test_common_body_gate_blocks_abstract_expert_tone() -> None:
    body = """
## 시장을 읽는 프레임

이 구조는 시장의 흐름과 맥락을 관통하는 핵심 프레임이다.
이 메커니즘은 투자 판단의 시사점과 방향성을 제공한다.
서사의 레버리지와 모멘텀은 전체 내러티브의 의미를 만든다.
이 관점은 기업 체력과 퀄리티의 연결을 보여 준다.

OPM과 EBITDA는 밸류에이션 프레임워크의 핵심이다.
CAPEX와 FCF는 컨센서스와 멀티플에 영향을 준다.
ROE와 PER은 리레이팅을 설명하는 KPI다.
"""

    errors = ab._validate_common_body_plainness(body, "investment-stories")

    assert any("추상 문장" in err for err in errors)
    assert any("전문가 말투" in err for err in errors)


def test_common_body_gate_applies_to_every_blog_category() -> None:
    body = """
## 설명

이 구조는 시장의 흐름과 맥락을 관통하는 핵심 프레임이다.
이 메커니즘은 판단의 시사점과 방향성을 제공한다.
서사의 모멘텀과 레버리지는 전체 내러티브의 의미를 만든다.
이 관점은 기업 체력과 퀄리티의 연결을 보여 준다.
전체 스토리의 관통선과 함의는 추상적인 방향성과 감각을 강화한다.
이 서사는 핵심 관점과 맥락의 연결을 통해 새로운 의미를 제시한다.
OPM과 EBITDA는 밸류에이션 프레임워크의 핵심이다.
CAPEX와 FCF는 컨센서스와 멀티플에 영향을 준다.
ROE와 PER은 리레이팅을 설명하는 KPI다.
"""

    for category in ab.BLOG_CATEGORIES:
        errors = ab._validate_common_body_plainness(body, category)

        assert any("추상 문장" in err for err in errors), category
        assert any("전문가 말투" in err for err in errors), category


def test_short_category_publish_gate_requires_reader_narrative(tmp_path: Path) -> None:
    postDir = tmp_path / "blog" / "02-dartlab-news" / "01-update"
    postDir.mkdir(parents=True)
    body = "\n\n".join(
        [
            "새 기능과 변경 내용을 안내합니다. 기능 목록과 제공 범위를 차례로 적습니다."
            " 화면 구성과 처리 항목을 설명하고 지원 대상을 소개합니다."
        ]
        * 10
    )
    (postDir / "index.md").write_text(
        f"---\ncategory: dartlab-news\n---\n\n{body}\n",
        encoding="utf-8",
    )

    errors = ab.publish_gate(postDir)

    assert any("왜 이 글을 읽어야" in err for err in errors)
    assert any("오해·한계·주의" in err for err in errors)
    assert any("다음에 볼 기준" in err for err in errors)


def test_short_category_common_gate_allows_easy_connected_story() -> None:
    body = """
왜 이번 변경을 알아야 할까요? 처음 온 독자에게는 메뉴 이름보다 무엇을 할 수 있는지가 먼저입니다.
실제 화면에서 회사 코드를 넣고 결과 표를 확인하면 첫 번째 값이 바로 보입니다. 표의 날짜와 금액을 함께 읽으면 어떤 자료인지도 알 수 있습니다.
여기서 바로 결론을 내리면 안 됩니다. 같은 값처럼 보여도 기간이 다르면 결과가 달라지므로 날짜 열을 다시 확인해야 합니다.
예를 들어 연간 값과 분기 값을 나란히 두면 합계와 한 시점 숫자를 섞는 오해를 피할 수 있습니다. 빈칸도 0으로 바꾸지 않고 원문을 다시 봅니다.
첫 결과 표에서는 회사 이름, 날짜, 금액을 한 줄씩 읽습니다. 같은 회사라도 날짜가 바뀌면 금액이 달라질 수 있으므로 어느 기간의 값인지 먼저 확인합니다.
두 번째 표에서는 앞에서 본 값과 새 값을 비교합니다. 차이가 생긴 칸을 찾고 공시 문장을 함께 읽으면 숫자가 바뀐 이유를 쉬운 말로 설명할 수 있습니다.
주의할 점도 있습니다. 화면에 값이 없다고 회사에 실적이 없다는 뜻은 아닙니다. 원문에 항목이 없는지, 기간이 다른지, 아직 공시되지 않았는지 차례로 확인합니다.
그래서 기능 이름을 외우는 대신 입력, 결과, 주의할 점을 한 번에 연결해 봅니다. 독자가 직접 같은 화면을 열어 값이 어디에서 달라지는지 확인할 수 있습니다.
다음에는 다른 회사를 넣고 같은 날짜 기준이 유지되는지 확인하면 됩니다. 결과가 다르면 원문과 기간을 다시 보는 것이 다음 질문입니다.
"""

    assert ab.prose_char_count(body) >= 500
    assert ab._validate_common_body_plainness(body, "dartlab-news") == []


def test_common_plan_gate_blocks_missing_reader_arc() -> None:
    brief = _brief()
    brief["readerQuestion"] = "시장 프레임을 설명한다."
    brief["insight"]["whatToWatch"] = "좋은 기준을 기억한다."
    for act in brief["acts"]:
        act["heading"] = "시장 프레임"
        act["scene"] = "프레임과 구조를 설명하는 장면"
        act["causalBridge"] = "관련 흐름을 설명한다."
    for section in brief["sections"]:
        section["subtitle"] = "시장 프레임을 설명한다."
        section["visualAnchor"] = "개념 도식"
        section["explanation"] = "구조와 흐름과 맥락을 설명한다."
        section["example"] = "시사점과 방향성을 예시로 든다."
        section["support"] = "보완 설명을 붙인다."
        section["transition"] = "관련 흐름을 설명한다."

    errors = ab._validate_common_plan(brief, brief, label="brief.json", category="investment-stories")

    assert any("전환 지점" in err for err in errors)
    assert any("실제 숫자·회사·공시·사례" in err for err in errors)


def test_dartlab_story_title_gate_blocks_intro_title() -> None:
    assert not ab._validate_dartlab_story_title("DART 공시분석, 설치 없이", "title")
    errors = ab._validate_dartlab_story_title("dartlab이란 무엇인가", "title")
    assert any("소개형" in err for err in errors)


def test_dartlab_story_gate_blocks_internal_count_terms() -> None:
    brief_path = (
        Path(__file__).resolve().parents[1] / "03-dartlab-stories" / "02-call-financial-statements" / "brief.json"
    )
    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    brief["sections"][0]["explanation"] = "axis count 13/13 인증을 보여 주는 내부 점검 설명이다."

    errors = ab._validate_common_plan(brief, brief, label="brief.json", category="dartlab-stories")

    assert any("내부 기능 개수" in err for err in errors)


def test_dartlab_story_gate_blocks_abstract_section_plan() -> None:
    brief_path = (
        Path(__file__).resolve().parents[1] / "03-dartlab-stories" / "02-call-financial-statements" / "brief.json"
    )
    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    brief["sections"][0]["explanation"] = "구조와 흐름과 표면의 의미를 설명한다."
    brief["sections"][0]["example"] = "중요한 기준과 맥락을 예시로 든다."

    errors = ab._validate_common_plan(brief, brief, label="brief.json", category="dartlab-stories")

    assert any("직접 할 행동" in err for err in errors)
    assert any("실제 예시로 잡아야 함" in err for err in errors)


def test_dartlab_story_body_gate_blocks_abstract_only_sentences() -> None:
    body = """
## 허공에 도는 설명

이 구조는 전체 흐름과 기준을 이해하게 한다. 표면의 맥락과 역할이 중요하다.
이런 연결 감각이 핵심이다. 그래서 좋은 분석이 된다.
독자는 이 설명을 통해 구조와 흐름의 의미를 자연스럽게 파악한다.
결국 맥락과 기준이 서로 연결된다는 점이 이 섹션의 역할이다.
"""

    errors = ab._validate_dartlab_body_plainness(body)

    assert any("추상 문장" in err for err in errors)


def test_dartlab_story_gate_blocks_missing_beginner_arc() -> None:
    brief_path = (
        Path(__file__).resolve().parents[1] / "03-dartlab-stories" / "02-call-financial-statements" / "brief.json"
    )
    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    brief["readerQuestion"] = "재무제표 파이썬 실행 결과를 읽는다."
    for act in brief["acts"]:
        act["heading"] = "재무제표 값 화면"
        act["scene"] = "코드 출력 표에서 005930 매출액 값을 확인하는 장면"
        act["causalBridge"] = "관련 값을 계속 확인한다."
    for section in brief["sections"]:
        section["subtitle"] = "코드 출력 표에서 005930 매출액 값을 본다."
        section["visualAnchor"] = "코드 출력 표와 005930 매출액 값을 섹션 앞쪽에 둔다."
        section["explanation"] = "코드에서 005930 매출액 값을 확인한다."
        section["example"] = "005930 2026Q1 매출액 133.873조원 값을 예시로 든다."
        section["support"] = "주의: 빈칸은 0으로 읽지 않는다."
        section["transition"] = "다음 섹션으로 이어진다."

    errors = ab._validate_common_plan(brief, brief, label="brief.json", category="dartlab-stories")

    assert any("첫 단계" in err for err in errors)


def test_dartlab_story_body_gate_blocks_expert_jargon() -> None:
    body = """
## 코드를 먼저 본다

```python
from dartlab import Company
Company("005930").panel("IS").head()
```

파사드와 스키마는 런타임 계약의 정본을 구성한다.
프로바이더와 컨텍스트는 아키텍처의 핵심 계층을 이룬다.
엔진과 어댑터의 추상화가 인터페이스 경계를 담당한다.
"""

    errors = ab._validate_dartlab_body_plainness(body)

    assert any("전문가 말투" in err for err in errors)
