"""auditBlog publish gate tests.

실행: uv run python -X utf8 -m pytest blog/_scripts/test_audit_blog_gate.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import auditBlog as ab  # noqa: E402


def _brief(score: int = 94) -> dict:
    title = "스텔스는 왜 기체보다 병목이 먼저 보일까"
    return {
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
                "slot": "hero",
                "subject": "스텔스 격납고와 레이더 시험 장비",
                "query": "stealth aircraft hangar radar test maintenance",
                "keywords": ["stealth", "hangar", "radar"],
                "placement": "첫 화면 hero 이미지",
                "narrativeUse": "글 시작에서 스텔스를 전투 장면이 아니라 시험과 정비 기술로 보이게 한다.",
            },
            {
                "slot": "inline",
                "subject": "저피탐 코팅 정비 장면",
                "query": "aircraft stealth coating maintenance panel inspection",
                "keywords": ["coating", "maintenance", "panel"],
                "insertAfterAct": 2,
                "placement": "2막 코팅 정비 설명 뒤",
                "narrativeUse": "독자가 저피탐 성능이 출고 뒤 정비 품질에 계속 의존한다는 점을 본다.",
            },
            {
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
    (assets / "hero.webp").write_bytes(b"fake")
    thumb = root / "landing" / "static" / "thumbnails"
    thumb.mkdir(parents=True)
    (thumb / "tech-stealth-test.webp").write_bytes(b"fake")
    filler = "스텔스 공정 병목과 대표 회사가 왜 핵심인지 설명하는 문장입니다. " * 520
    body = f"""
![스텔스 격납고](./assets/hero.webp)

## 공정·회사·근거 지도

| 공정/층위 | 대표 회사 | 공시 근거 |
|---|---|---|
| 형상·체계통합 | LMT·KAI | EDGAR 10-K·DART 사업보고서 |

왜 이 회사가 이 공정 네트워크 칸의 핵심인지 보려면 병목, 대체 난도, 양산 인증, CAPEX를 함께 봐야 한다.
DART와 EDGAR 근거를 모두 연결하고, dartlab 실측으로 2025Q1~Q4 손익을 확인한다.

## 기술 성숙도와 출처

양산 단계와 실험 단계를 분리한다.

## 이렇게 오해하면 안 된다

RCS 숫자 하나로 모든 각도와 주파수를 설명하면 안 된다.

{filler}
"""
    (post / "index.md").write_text(
        f"""---
title: "스텔스는 왜 기체보다 병목이 먼저 보일까"
date: "2026-07-06"
category: tech-story
series: tech-story
topicSlug: "stealth-test"
ogImage: /thumbnails/tech-stealth-test.webp
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


def test_dartlab_story_title_gate_blocks_intro_title() -> None:
    assert not ab._validate_dartlab_story_title("DART 공시분석, 설치 없이", "title")
    errors = ab._validate_dartlab_story_title("dartlab이란 무엇인가", "title")
    assert any("소개형" in err for err in errors)
