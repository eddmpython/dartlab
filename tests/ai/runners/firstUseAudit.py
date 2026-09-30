"""새 세션의 첫 데이터 도달과 원문 답변을 비교한다. 결과 품질은 원문을 읽고 판단한다.

UV_NO_SYNC=1 uv run python -X utf8 tests/ai/runners/firstUseAudit.py
    --output <공유 실행 폴더> [--native] [--cases size,revenue] [--runtime codex]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--native", action="store_true")
    parser.add_argument("--cases", default="")
    parser.add_argument("--runtime", default="codex")
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[3]
    with (root / "tests/_evals/firstUseCases.csv").open(encoding="utf-8", newline="") as source:
        cases = list(csv.DictReader(source))
    if args.cases:
        selected = set(args.cases.split(","))
        cases = [case for case in cases if case["id"] in selected]

    # 같은 프로세스의 baseline은 실행 시작 시점의 함수와 catalog를 사용한다.
    from dartlab.ai.runtime.analysisCapsule import buildAnalysisCapsule
    from dartlab.ai.runtime.sessionTools import sessionToolSpecs
    from dartlab.ai.tools.readSkill import readSkill
    from dartlab.skills import listSkills

    for module in ("dartlab.ai.tools.registry", "dartlab.ai.tools.engineCall"):
        importlib.import_module(module)
    listSkills(includeUser=False)
    capsule = buildAnalysisCapsule(cwd=root, mcpConnected=True, toolTransport="native")
    metadata = {
        "capsuleChars": len(capsule),
        "toolSchemaChars": len(json.dumps(sessionToolSpecs(), ensure_ascii=False)),
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "sourceHash": hashlib.sha256(
            b"".join(path.read_bytes() for path in sorted((root / "src/dartlab/ai").rglob("*.py")))
        ).hexdigest(),
        "runtime": args.runtime,
    }
    (args.output / "environment.json").write_text(json.dumps(metadata), encoding="utf-8")
    rows = []
    for case in cases:
        started = time.monotonic()
        result = readSkill(case["question"], includeUser=False).toDict()
        skills = result.get("data", {}).get("skills", [])
        row = {
            **case,
            "discoverySeconds": round(time.monotonic() - started, 3),
            "discoveryChars": len(json.dumps(result, ensure_ascii=False)),
            "topSkill": skills[0]["id"] if skills else "",
            "operationalSkills": sum(s["id"].startswith(("operation.", "start.", "runtime.")) for s in skills),
        }
        (args.output / f"{case['id']}.discovery.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if args.native:
            row.update(runNative(case, args.output, args.runtime, args.timeout))
        rows.append(row)
        with (args.output / "metrics.csv").open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(json.dumps(row, ensure_ascii=False), flush=True)


def runNative(case: dict, output: Path, runtime: str, timeout: float) -> dict:
    from dartlab.ai.runtime.engine import AgentRuntimeEngine
    from dartlab.ai.runtime.sessionStore import SessionStore

    engine = AgentRuntimeEngine(sessionStore=SessionStore(output / "sessions.sqlite3"))
    started = time.monotonic()
    firstData = None
    errors = 0
    calls = 0
    refs = set()
    chunks = []
    completed = False
    timedOut = threading.Event()
    timer = None
    try:
        session = engine.openSession(runtimeId=runtime, cwd=output)

        def cancelTurn() -> None:
            timedOut.set()
            engine.cancel(session.sessionId)

        timer = threading.Timer(timeout, cancelTurn)
        timer.daemon = True
        timer.start()
        with (output / f"{case['id']}.events.jsonl").open("w", encoding="utf-8") as trace:
            for event in engine.streamTurn(session.sessionId, case["question"]):
                payload = event.payload
                if event.kind != "native":
                    trace.write(json.dumps(event.toDict(), ensure_ascii=False, default=str) + "\n")
                    trace.flush()
                if event.kind == "toolCompleted":
                    calls += 1
                    item = payload.get("item") or {}
                    result = item.get("result") or {}
                    errors += int(result.get("ok") is False)
                    dataRefs = [r for r in result.get("refs", []) if r.get("kind") not in {"skillRef", "capabilityRef"}]
                    refs.update(r["id"] for r in dataRefs if r.get("id"))
                    if dataRefs and result.get("ok") and isDataCall(case["id"], item) and firstData is None:
                        firstData = round(time.monotonic() - started, 3)
                if event.kind == "messageDelta":
                    chunks.append(str(payload.get("text") or payload.get("delta") or ""))
                if event.kind == "turnCompleted":
                    completed = True
    except Exception as exc:
        chunks.append(f"\n실행 실패: {type(exc).__name__}: {exc}")
        errors += 1
    finally:
        if timer:
            timer.cancel()
        engine.close()
    answer = "".join(chunks)
    (output / f"{case['id']}.answer.md").write_text(answer, encoding="utf-8")
    return {
        "firstDataSeconds": firstData,
        "elapsedSeconds": round(time.monotonic() - started, 3),
        "toolCalls": calls,
        "toolErrors": errors,
        "evidenceRefs": len(refs),
        "answerChars": len(answer),
        "completed": completed,
        "timedOut": timedOut.is_set(),
    }


def isDataCall(caseId: str, item: dict) -> bool:
    """스킬/API/필드 발견과 실제 답변 자료 도달을 구분한다."""
    if item.get("tool") in {
        "ReadSkill",
        "GetSkillBody",
        "ReadCapability",
        "ReadSkillMarket",
        "Read",
        "ExternalReachDoctor",
        "SearchPastSessions",
    }:
        return False
    arguments = item.get("arguments") or {}
    apiRef = arguments.get("apiRef", "")
    if apiRef == "dataHub.catalog":
        return caseId == "catalog"
    if apiRef in {"capabilities", "help", "scan.fields"}:
        return False
    args = arguments.get("args") or {}
    return not (apiRef == "scan" and isinstance(args, dict) and (args.get("axis") or args.get("target")) == "fields")


def recordedDataTime(caseId: str, events: list[dict], originalSeconds: float | None) -> float | None:
    """초기 runner의 발견 표 포함 시간을 trace timestamp로 보정한다."""
    oldFirst = None
    actualFirst = None
    for event in events:
        if event.get("kind") != "toolCompleted":
            continue
        item = event.get("payload", {}).get("item", {})
        result = item.get("result") or {}
        refs = [ref for ref in result.get("refs", []) if ref.get("kind") not in {"skillRef", "capabilityRef"}]
        if not result.get("ok") or not refs:
            continue
        when = datetime.fromisoformat(event["timestamp"])
        oldFirst = oldFirst or when
        if isDataCall(caseId, item):
            actualFirst = when
            break
    if oldFirst is None or actualFirst is None or originalSeconds is None:
        return None
    return round(originalSeconds + (actualFirst - oldFirst).total_seconds(), 3)


if __name__ == "__main__":
    main()
