"""Evidence forensics incubator recipe guard tests."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]
FORENSICS_DIR = REPO_ROOT / "src" / "dartlab" / "skills" / "specs" / "recipes" / "fundamental" / "quality" / "forensics"

FORENSICS_IDS = {
    "recipes.fundamental.quality.forensics.index",
    "recipes.fundamental.quality.forensics.dataCoverageAudit",
    "recipes.fundamental.quality.forensics.accountTraceLedger",
    "recipes.fundamental.quality.forensics.revenueToCashBridge",
    "recipes.fundamental.quality.forensics.workingCapitalPressureMap",
    "recipes.fundamental.quality.forensics.noteSignalExtractor",
    "recipes.fundamental.quality.forensics.eventToStatementMatcher",
    "recipes.fundamental.quality.forensics.crossSectionAnomalyRank",
    "recipes.fundamental.quality.forensics.falsifierLedger",
    "recipes.fundamental.quality.forensics.engineCandidateMemo",
    "recipes.fundamental.quality.forensics.deepDive",
}

BANNED_L2_CALLS = (
    "c.analysis",
    "c.quant",
    "c.credit",
    "c.macro",
    "c.industry",
    "c.story",
    "dartlab.analysis",
    "dartlab.quant",
    "dartlab.credit",
    "dartlab.macro",
    "dartlab.industry",
    "dartlab.story",
)


def _publicCallSection(text: str) -> str:
    marker = "## 공개 호출 방식"
    start = text.find(marker)
    assert start >= 0, "missing public call section"
    section = text[start + len(marker) :]
    next_h2 = section.find("\n## ")
    return section if next_h2 < 0 else section[:next_h2]


def _pythonBlocks(text: str) -> list[str]:
    return re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)


def testForensicsRecipeSpecsLoadAsObservedRecipes() -> None:
    from dartlab.skills import listSkills
    from dartlab.skills import registry as _registry

    _registry._LIST_SKILLS_CACHE.clear()
    specs = {spec.id: spec for spec in listSkills(includeUser=False)}

    assert FORENSICS_IDS <= set(specs)
    for skill_id in FORENSICS_IDS:
        spec = specs[skill_id]
        assert spec.kind == "recipe"
        assert spec.category == "recipes"
        assert spec.status in {"observed", "tested", "curated"}, f"{skill_id}: status={spec.status}"
        assert spec.graphTier == "L1.5"
        assert spec.requiredEvidence
        assert spec.expectedOutputs
        # capabilityRefs 는 lint 가 빈 리스트를 허용 (registry.py::_validateCapabilityRefs).
        # 선언된 경우만 L1.5 셋과 교집합 필수. scan.{quality,audit,disclosureRisk} 는
        # registry 에 없는 axis 이므로 빈 상태가 합법적.
        if spec.capabilityRefs:
            assert set(spec.capabilityRefs) & {
                "Company.panel",
                "Company.disclosure",
                "Company.trace",
                "scan.quality",
                "scan.audit",
                "scan.disclosureRisk",
            }


def testForensicsSkillsAreExposedThroughAiEntryPoints() -> None:
    from dartlab.ai.tools.readSkill import getSkillBody, readSkill

    entry = readSkill("포렌식 팩 L1.5 회계 검증 analysis 없이", limit=8, includeUser=False)
    deep = readSkill("삼성전자 포렌식 deep dive 원표 공시", limit=8, includeUser=False)
    bridge = readSkill("revenue to cash bridge 매출 현금 괴리", limit=8, includeUser=False)

    assert entry.ok
    assert entry.data["skills"][0]["id"] == "recipes.fundamental.quality.forensics.index"
    assert deep.ok
    assert deep.data["skills"][0]["id"] == "recipes.fundamental.quality.forensics.deepDive"
    assert bridge.ok
    assert bridge.data["skills"][0]["id"] == "recipes.fundamental.quality.forensics.revenueToCashBridge"

    body = getSkillBody("recipes.fundamental.quality.forensics.deepDive", includeUser=False)
    assert body.ok
    raw = body.data["body"]
    assert "buildEvidenceForensicsMemo" in raw
    assert "recipes.fundamental.quality.forensics.engineCandidateMemo" in raw


def testForensicsSkillsAreInPublicSkillArtifacts() -> None:
    artifact_dir = REPO_ROOT / "src" / "dartlab" / "skills"

    for name in ("catalog.json", "agent.json", "web.json", "mcp.json", "pyodide.json"):
        payload = json.loads((artifact_dir / name).read_text(encoding="utf-8"))
        rows = payload.get("skills", [])
        by_id = {row["id"]: row for row in rows}

        assert FORENSICS_IDS <= set(by_id), f"{name} missing forensics skill rows"
        if name != "pyodide.json":
            assert payload["meta"]["skillCount"] == len(rows)
            recipe_meta = [row for row in payload["meta"]["categories"] if row["id"] == "recipes"]
            assert recipe_meta and recipe_meta[0]["count"] == sum(row.get("category") == "recipes" for row in rows)
        if name in {"catalog.json", "agent.json", "mcp.json"}:
            assert by_id["recipes.fundamental.quality.forensics.index"]["bodyPreview"]
        if name in {"catalog.json", "agent.json", "web.json"}:
            assert by_id["recipes.fundamental.quality.forensics.deepDive"]["expectedOutputs"]
        if name == "web.json":
            assert by_id["recipes.fundamental.quality.forensics.index"]["bodyHuman"]

    graph = json.loads((artifact_dir / "graph.json").read_text(encoding="utf-8"))
    graph_ids = {node["id"] for node in graph.get("nodes", [])}
    assert FORENSICS_IDS <= graph_ids


def testForensicsPublicCallBlocksStayBelowL2() -> None:
    failures: list[str] = []
    for path in sorted(FORENSICS_DIR.glob("*.md")):
        section = _publicCallSection(path.read_text(encoding="utf-8"))
        for token in BANNED_L2_CALLS:
            if token in section:
                failures.append(f"{path.name}: banned L2 call {token}")

    assert not failures, "Forensics recipes must not call L2 engines\n" + "\n".join(failures)


def testForensicsPublicCallBlocksParseAsPython() -> None:
    failures: list[str] = []
    for path in sorted(FORENSICS_DIR.glob("*.md")):
        section = _publicCallSection(path.read_text(encoding="utf-8"))
        blocks = _pythonBlocks(section)
        if not blocks:
            failures.append(f"{path.name}: no python block")
            continue
        for idx, code in enumerate(blocks):
            try:
                ast.parse(code)
            except SyntaxError as exc:
                failures.append(f"{path.name} block {idx}: {exc.msg} line {exc.lineno}")

    assert not failures, "Forensics recipe code blocks must be AST-parseable\n" + "\n".join(failures)


def testForensicsPublicCallBlocksUseL15MemoBuilder() -> None:
    failures: list[str] = []
    for path in sorted(FORENSICS_DIR.glob("*.md")):
        section = _publicCallSection(path.read_text(encoding="utf-8"))
        if 'target = "005930"' not in section:
            failures.append(f"{path.name}: missing default target placeholder")
        if "buildEvidenceForensicsMemo" not in section:
            failures.append(f"{path.name}: missing L1.5 memo builder")
        if 'sources=memo["sources"]' not in section:
            failures.append(f"{path.name}: missing sourceRef payload")

    assert not failures, "Forensics recipes must execute the L1.5 helper\n" + "\n".join(failures)


def _sampleStatements() -> dict[str, pl.DataFrame]:
    years = ["2025", "2024", "2023", "2022"]
    revenue = [1300.0, 1000.0, 920.0, 850.0]
    cost = [830.0, 660.0, 610.0, 570.0]
    operating_profit = [210.0, 190.0, 170.0, 150.0]
    net_income = [170.0, 150.0, 135.0, 120.0]
    receivables = [420.0, 180.0, 155.0, 140.0]
    inventory = [380.0, 210.0, 190.0, 175.0]
    payables = [130.0, 110.0, 100.0, 95.0]
    assets = [2200.0, 1900.0, 1750.0, 1600.0]
    liabilities = [900.0, 760.0, 700.0, 640.0]
    equity = [1300.0, 1140.0, 1050.0, 960.0]
    short_debt = [120.0, 80.0, 72.0, 68.0]
    long_debt = [420.0, 310.0, 285.0, 260.0]
    cfo = [70.0, 160.0, 150.0, 135.0]
    capex = [-180.0, -145.0, -120.0, -110.0]

    def row(snake: str, values: list[float]) -> dict[str, float | str]:
        return {"snakeId": snake, "항목": snake, **dict(zip(years, values, strict=True))}

    return {
        "IS": pl.DataFrame(
            [
                row("sales", revenue),
                row("cost_of_sales", cost),
                row("operating_profit", operating_profit),
                row("net_income", net_income),
            ]
        ),
        "BS": pl.DataFrame(
            [
                row("total_assets", assets),
                row("total_liabilities", liabilities),
                row("total_stockholders_equity", equity),
                row("short_term_debt", short_debt),
                row("long_term_debt", long_debt),
                row("trade_and_other_receivables", receivables),
                row("inventories", inventory),
                row("trade_and_other_payables", payables),
            ]
        ),
        "CF": pl.DataFrame(
            [
                row("operating_cashflow", cfo),
                row("purchase_of_property_plant_and_equipment", capex),
            ]
        ),
    }


def testForensicsSynthBuildsDeepMemoFromL15Inputs() -> None:
    from dartlab.synth.evidenceForensics import buildEvidenceForensicsMemo

    memo = buildEvidenceForensicsMemo(
        target="SAMPLE",
        market="KR",
        companyName="Sample Manufacturing",
        statements=_sampleStatements(),
        sectionTexts={
            "notes": "대손충당금 손상 allowance impairment. 정정 restatement disclosure.",
            "risk": "재고평가손 write-down risk and related party transaction.",
        },
        events=[
            {"rcept_dt": "20260501", "report_nm": "사업보고서 정정 공시"},
            {"rcept_dt": "20260415", "report_nm": "전환사채 발행 결정"},
        ],
        scanRows=[
            {"stockCode": "SAMPLE", "corpName": "Sample Manufacturing", "axis": "audit", "score": 2.5},
            {"stockCode": "PEER1", "corpName": "Peer One", "axis": "quality", "score": 1.2},
        ],
    )

    assert memo["decisionStatus"] == "usable"
    assert memo["headline"]["riskScore"] >= 4
    assert memo["headline"]["candidateCount"] == 5
    assert {
        "dataCoverageAudit",
        "accountTraceLedger",
        "revenueToCashBridge",
        "workingCapitalPressureMap",
        "noteSignalExtractor",
        "eventToStatementMatcher",
        "crossSectionAnomalyRank",
        "falsifierLedger",
        "engineCandidateMemo",
        "deepDive",
    } <= set(memo["tables"])
    assert len(memo["tables"]["deepDive"]) == 10
    assert memo["tables"]["deepDive"][-1]["step"] == "finalDecision"
    assert memo["tables"]["revenueToCashBridge"][0]["status"] == "risk"
    assert memo["tables"]["workingCapitalPressureMap"][0]["status"] in {"watch", "risk"}
    assert any(
        row["signal"] == "restatement" and row["status"] == "risk" for row in memo["tables"]["noteSignalExtractor"]
    )
    assert any(row["matchedSignal"] == "restatement" for row in memo["tables"]["eventToStatementMatcher"])
    assert any(row["status"] == "open" for row in memo["tables"]["falsifierLedger"])
    assert any(row["signalId"] == "revenueCashDivergence" for row in memo["tables"]["engineCandidateMemo"])
    assert any(source["id"] == "l15EvidenceForensics" for source in memo["sources"])


def testForensicsAskWorkbenchRunsL15Memo(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.ai.kernel import ask
    from dartlab.ai.runtime.eventProjection import EventProjector

    class PassingQuality:
        passed = True
        issues: tuple[str, ...] = ()
        score = 100
        requiredClaimCells = 0
        coveredClaimCells = 0

        def toDict(self) -> dict[str, object]:
            return {
                "passed": True,
                "issues": [],
                "score": 100,
                "requiredClaimCells": 0,
                "coveredClaimCells": 0,
            }

    class FakeRuntimeEngine:
        calls: list[dict] = []

        def stream(self, question: str, **kwargs):
            self.calls.append({"question": question, **kwargs})
            projector = EventProjector("codex", "session-forensics")
            turn_id = "turn-forensics"
            yield projector.event("sessionStarted", turnId=turn_id)
            yield projector.event("turnStarted", turnId=turn_id)
            yield projector.event(
                "toolStarted",
                turnId=turn_id,
                payload={"canonicalName": "ReadSkill", "toolCallId": "read-forensics"},
            )
            yield projector.event(
                "toolCompleted",
                turnId=turn_id,
                payload={
                    "canonicalName": "ReadSkill",
                    "toolCallId": "read-forensics",
                    "refDetails": [
                        {
                            "id": "skill:recipes.fundamental.quality.forensics.deepDive",
                            "kind": "skillRef",
                            "title": "포렌식 deep dive",
                            "source": "ReadSkill",
                        }
                    ],
                },
            )
            answer = (
                "L1.5 포렌식 deep dive입니다. L2 분석엔진 없이 원표와 공시를 검토합니다.\n"
                "왜 이렇게 봤나: 근거 연결 상태를 확인했습니다.\n"
                "비어있는 근거: 추가 원문 확인이 필요합니다.\n"
                "반증 우선순위: 현금흐름과 정정 공시를 먼저 확인합니다.\n"
                "엔진 환류 후보: 검증된 신호만 후보로 남깁니다.\n"
                "다음 확인: tableRef, valueRef, dateRef, sourceRef를 순서대로 점검합니다."
            )
            yield projector.event("messageDelta", turnId=turn_id, payload={"text": answer})
            yield projector.event(
                "turnCompleted",
                turnId=turn_id,
                payload={
                    "status": "completed",
                    "outcomeId": "outcome-forensics",
                    "runtimeCoverage": {"readSkillCalls": 1},
                },
            )

    engine = FakeRuntimeEngine()
    monkeypatch.setattr("dartlab.ai.runtime.getRuntimeEngine", lambda: engine)
    monkeypatch.setattr("dartlab.ai.agent._runtimeAnswerQuality", lambda *args, **kwargs: PassingQuality())

    answer = ask(
        "Sample Manufacturing 포렌식 deep dive를 analysis 없이 L1.5 원표와 공시만으로 검증",
        stockCode="SAMPLE",
        stream=False,
        mode="workbench",
        provider="heuristic",
    )

    assert "L1.5 포렌식 deep dive입니다" in answer
    assert "L2 분석엔진 없이" in answer
    assert "왜 이렇게 봤나" in answer
    assert "비어있는 근거" in answer
    assert "반증 우선순위" in answer
    assert "엔진 환류 후보" in answer
    assert "다음 확인" in answer
    assert "tableRef, valueRef, dateRef, sourceRef" in answer
    assert "stream_provider failed" not in answer
    assert "analysis." not in answer
    assert "revenueCashDivergence" not in answer
    assert "open falsifier" not in answer
    assert "Deep Dive 단계" not in answer
    assert engine.calls[0]["context"]["stockCode"] == "SAMPLE"
    for token in BANNED_L2_CALLS:
        assert token not in answer
