"""설치된 에이전트가 DartLab 표면에 실제로 닿는지 재는 운영자 트리거 측정기.

왜 필요한가. DartLab 은 모델 루프를 사용자 PC 의 agent CLI 에 넘긴 중개상이다. 그래서
품질의 질문이 바뀌었다. "우리 답이 좋은가" 가 아니라 "남의 에이전트가 우리 표면을 제대로
다 쓰는가" 다. 그런데 저장소에서 설치형 CLI 를 end to end 로 띄워 이걸 재는 자산은 없었다.
`tests/_evals/test_eval_live.py` 는 `runAgent(question)` 을 부르는데 그 함수는 `provider`
키워드가 필수라 TypeError 로 죽고, 반환도 dict 가 아니라 이터레이터다. 게다가 그 경로는
DartLab 이 모델을 통제하던 옛 구조여서 지금 제품이 아니다.

이 측정기는 게이트가 아니다. CI 에 붙이지 않는다. 결함을 찾는 발견 도구이며 결과는 JSON
리포트다. 통과 실패를 선언하는 대신 도달한 표면과 오사용 신호를 숫자로 남긴다.

실행:
    uv run python -X utf8 tests/ai/runners/brokerReachProbe.py --runtime claude
    uv run python -X utf8 tests/ai/runners/brokerReachProbe.py --runtime claude --case scanScreening
    uv run python -X utf8 tests/ai/runners/brokerReachProbe.py --list

케이스마다 실제 CLI 세션이 열리므로 1 건에 수 분이 걸린다. 구독 사용량을 쓴다.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

_CASES = Path(__file__).with_name("brokerReachCases.json")


def _loadCases() -> list[dict[str, Any]]:
    """케이스 파일에서 질문과 기대 표면을 읽는다."""
    payload = json.loads(_CASES.read_text(encoding="utf-8"))
    return list(payload.get("cases") or [])


def _argSignature(name: str, payload: Any) -> str:
    """같은 도구를 같은 인자로 다시 부르는 것을 알아보게 서명을 만든다."""
    try:
        return f"{name}:{json.dumps(payload, ensure_ascii=False, sort_keys=True)}"
    except (TypeError, ValueError):
        return f"{name}:{payload!r}"


# 예산 초과 케이스의 호출 순서를 남길 때 쓰는 상한. 그 이상은 원인 규명에 보태지 않는다.
_MAX_TRACE_CALLS = 40
_MAX_TRACE_ARG_CHARS = 160


def _traceArgs(payload: Any) -> str:
    """호출 인자를 한 줄로 줄인다. 무엇을 반복했는지 보이는 정도면 충분하다."""
    try:
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        text = repr(payload)
    return text[:_MAX_TRACE_ARG_CHARS]


def _apiRefOf(payload: Any) -> str:
    """EngineCall 인자에서 apiRef 를 꺼낸다. 없으면 빈 문자열이다."""
    if not isinstance(payload, dict):
        return ""
    raw = payload.get("apiRef") or payload.get("api_ref") or ""
    return str(raw).strip()


def _malformedArgs(name: str, payload: Any) -> str | None:
    """방어 shim 이 조용히 고쳐 주는 기형 인자를 그 전에 붙잡는다.

    engineCall 에는 apiRef 에 인자를 통째로 밀어 넣거나 args dict 를 빼먹는 호출을 되살리는
    보정 계층이 있다. 보정되면 결과가 정상이라 오사용이 계측에 잡히지 않는다. 여기서는
    보정 전 원본을 보므로 실제 사용 습관이 보인다.
    """
    if name != "EngineCall" or not isinstance(payload, dict):
        return None
    apiRef = _apiRefOf(payload)
    if apiRef and (" " in apiRef or "(" in apiRef):
        return f"apiRef 에 인자가 섞여 있다: {apiRef[:80]}"
    if "args" not in payload:
        return "args dict 가 없다"
    if not isinstance(payload.get("args"), dict):
        return f"args 가 dict 가 아니다: {type(payload.get('args')).__name__}"
    return None


_REF_ID = re.compile(r"\b(?:table|value|date|doc|web|execution|artifact|visual):[A-Za-z0-9._:{}\-,]+")
_NUMBER = re.compile(r"\d[\d,.]*\s*(?:%|조원|억원|조|억|원|배|bp|배수)")

# 캡슐이 이미 요구하는 것들이다. 요구와 실물의 간극이 곧 개선 지점이라 요구별로 센다.
_QUALITY_MARKERS: dict[str, tuple[str, ...]] = {
    "table": ("|---", "| ---"),
    "counterEvidence": ("반대", "반증", "다만", "그러나", "리스크", "약점", "부정적"),
    # 실측(2026-08-06): 목록이 좁아 오탐이 났다. 답변이 "이 판단이 틀리려면" 절과 반증 표
    # 두 개를 내놓았는데 "틀렸" 만 보느라 빠짐으로 셌다. 없는 결함을 보고하는 측정기는
    # 측정기가 아니다. 같은 뜻의 어미와 표현을 함께 본다.
    #
    # 주의. 같은 날 tool 결과에 "판단이 뒤집히는 지점" 이라는 제목을 싣기 시작했다. 모델이
    # 그 제목만 옮겨 적어도 "뒤집" 이 걸린다. 이 축의 True 는 그때부터 약한 신호이며,
    # 판정은 본문을 읽어서 한다. 재료에 심은 말로 재료의 효과를 재면 안 된다.
    "falsifier": (
        "바뀌",
        "틀렸",
        "틀리려",
        "틀린다",
        "뒤집",
        "무효",
        "성립하지 않",
        "가정이 깨",
        "무너진",
        "깨지는",
        "반증",
        "tripwire",
    ),
    "comparison": ("대비", "동종", "업종 평균", "경쟁", "peer", "상위", "하위", "백분위"),
    "nextCheck": ("다음", "확인할", "지켜볼", "모니터", "추가 확인", "후속"),
    "observationSplit": ("관측", "사실", "해석", "판단", "의미"),
    "asOf": ("기준", "FY", "분기", "asOf", "시점"),
    "uncertainty": ("불확실", "한계", "주의", "가정", "추정"),
}


def answerQualitySignals(text: str) -> dict[str, Any]:
    """답변 본문이 분석 계약을 실제로 지켰는지 기계로 센다.

    점수를 매기는 것이 목적이 아니다. 캡슐이 요구하는 항목 중 무엇이 실물에서 빠지는지
    찾아 개선 지점을 고르는 발견 도구다.
    """
    body = text or ""
    signals: dict[str, Any] = {
        "length": len(body),
        "refCitations": len(set(_REF_ID.findall(body))),
        "numbers": len(_NUMBER.findall(body)),
        "headings": body.count("\n#") + body.count("\n**"),
    }
    for name, markers in _QUALITY_MARKERS.items():
        signals[name] = any(marker in body for marker in markers)
    missing = [name for name in _QUALITY_MARKERS if not signals[name]]
    signals["missing"] = missing
    return signals


def runCase(case: dict[str, Any], *, runtimeId: str, timeoutSec: float) -> dict[str, Any]:
    """케이스 하나를 실제 중개 세션으로 돌리고 관측치를 모은다."""
    from dartlab.ai.agent import runRuntimeAgent

    toolCalls: list[dict[str, Any]] = []
    apiRefs: list[str] = []
    signatures: list[str] = []
    malformed: list[str] = []
    refIds: list[str] = []
    answerParts: list[str] = []
    meta: dict[str, Any] = {}
    failure: str | None = None

    started = time.monotonic()
    try:
        for event in runRuntimeAgent(case["question"], runtimeId=runtimeId):
            if time.monotonic() - started > timeoutSec:
                failure = f"측정기 상한 {timeoutSec:.0f} 초 초과"
                break
            kind = getattr(event, "kind", "")
            data = getattr(event, "data", {}) or {}
            if kind == "tool_start":
                name = str(data.get("canonicalName") or data.get("name") or "")
                payload = data.get("input")
                toolCalls.append({"name": name, "input": payload})
                signatures.append(_argSignature(name, payload))
                apiRef = _apiRefOf(payload)
                if apiRef:
                    apiRefs.append(apiRef)
                problem = _malformedArgs(name, payload)
                if problem:
                    malformed.append(f"{name}: {problem}")
            elif kind == "chunk":
                answerParts.append(str(data.get("text") or ""))
            elif kind == "done":
                meta = dict(data.get("responseMeta") or {})
                refIds = [str(ref.get("id") or "") for ref in (data.get("refs") or []) if isinstance(ref, dict)]
    except Exception as exc:  # noqa: BLE001 - 측정기는 어떤 실패도 케이스 결과로 기록한다
        failure = f"{type(exc).__name__}: {exc}"

    elapsed = time.monotonic() - started
    names = [call["name"] for call in toolCalls]
    expectedTools = list(case.get("expectTools") or [])
    expectedPrefixes = list(case.get("expectApiRefPrefix") or [])
    hitTools = sorted({name for name in names if name in expectedTools})
    hitRefs = sorted({ref for ref in apiRefs if any(ref.startswith(prefix) for prefix in expectedPrefixes)})
    duplicates = len(signatures) - len(set(signatures))
    maxCalls = int(case.get("maxToolCalls") or 0)

    return {
        "caseId": case["caseId"],
        "question": case["question"],
        "elapsedSec": round(elapsed, 1),
        "toolCallCount": len(toolCalls),
        "toolsCalled": sorted(set(names)),
        "apiRefsCalled": sorted(set(apiRefs)),
        "expectTools": expectedTools,
        "expectApiRefPrefix": expectedPrefixes,
        "reachedExpectedTool": bool(hitTools) if expectedTools else None,
        "reachedExpectedApiRef": bool(hitRefs) if expectedPrefixes else None,
        "duplicateCalls": duplicates,
        "overCallBudget": bool(maxCalls and len(toolCalls) > maxCalls),
        "malformedArgs": malformed,
        # 호출 이름 집합만 남기면 "29 회" 가 무엇이었는지 알 수 없다. 실측(2026-08-06):
        # macroTrend 가 예산 5 회에 29 회를 썼는데 리포트로는 원인을 짚지 못했다. 예산을
        # 넘긴 케이스만 호출 순서를 남긴다. 전건 저장은 리포트를 읽을 수 없게 만든다.
        "callTrace": [
            {"name": call["name"], "args": _traceArgs(call["input"])} for call in toolCalls[:_MAX_TRACE_CALLS]
        ]
        if maxCalls and len(toolCalls) > maxCalls
        else [],
        "answer": "".join(answerParts),
        "quality": answerQualitySignals("".join(answerParts)),
        "evidenceCount": meta.get("evidenceCount"),
        "responseStatus": meta.get("responseStatus"),
        "verificationStatus": meta.get("verificationStatus"),
        "failureReason": meta.get("failureReason") or failure,
        "refIdSample": refIds[:5],
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    """케이스 결과를 표면 도달률과 오사용 신호로 집계한다."""
    from dartlab.mcp.protocol import mcpAdvertisedToolNames

    advertised = set(mcpAdvertisedToolNames("agent"))
    reachedTools = {name for item in results for name in item["toolsCalled"]}
    expectedHits = [item for item in results if item["reachedExpectedTool"] is not None]
    refHits = [item for item in results if item["reachedExpectedApiRef"] is not None]
    completed = [item for item in results if item.get("responseStatus") == "ok"]
    return {
        "caseCount": len(results),
        "completedCount": len(completed),
        "advertisedToolCount": len(advertised),
        "toolsActuallyUsed": sorted(reachedTools & advertised),
        "toolsNeverUsed": sorted(advertised - reachedTools),
        "toolReachRate": f"{len(reachedTools & advertised)}/{len(advertised)}",
        "expectedToolHitRate": f"{sum(1 for i in expectedHits if i['reachedExpectedTool'])}/{len(expectedHits)}",
        "expectedApiRefHitRate": f"{sum(1 for i in refHits if i['reachedExpectedApiRef'])}/{len(refHits)}",
        "casesOverCallBudget": [i["caseId"] for i in results if i["overCallBudget"]],
        "casesWithDuplicateCalls": [i["caseId"] for i in results if i["duplicateCalls"]],
        "casesWithMalformedArgs": [i["caseId"] for i in results if i["malformedArgs"]],
        "casesWithoutEvidence": [i["caseId"] for i in results if not i.get("evidenceCount")],
        # 어떤 계약 항목이 실물에서 가장 자주 빠지는지. 개선 순위는 여기서 고른다.
        "qualityGapCounts": {
            marker: sum(1 for i in results if marker in (i.get("quality") or {}).get("missing", []))
            for marker in _QUALITY_MARKERS
        },
        "medianAnswerLength": sorted(int((i.get("quality") or {}).get("length") or 0) for i in results)[
            len(results) // 2
        ]
        if results
        else 0,
    }


def main() -> int:
    """케이스를 돌려 도달성 리포트를 만든다."""
    parser = argparse.ArgumentParser(description="설치된 에이전트의 DartLab 표면 도달성 측정")
    parser.add_argument("--runtime", default="claude", help="측정할 설치형 런타임 식별자")
    parser.add_argument("--case", action="append", help="특정 케이스만 실행 (반복 지정 가능)")
    parser.add_argument("--timeout", type=float, default=420.0, help="케이스당 상한 초")
    parser.add_argument("--out", default="", help="리포트 저장 경로")
    parser.add_argument("--list", action="store_true", help="케이스 목록만 출력")
    args = parser.parse_args()

    cases = _loadCases()
    if args.list:
        for case in cases:
            print(f"{case['caseId']:20s} {case['question'][:70]}")
        return 0
    if args.case:
        wanted = set(args.case)
        cases = [case for case in cases if case["caseId"] in wanted]
        if not cases:
            print(f"해당 케이스가 없습니다: {sorted(wanted)}")
            return 2

    results: list[dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['caseId']} 실행 중...", flush=True)
        item = runCase(case, runtimeId=args.runtime, timeoutSec=args.timeout)
        results.append(item)
        reached = item["reachedExpectedTool"] or item["reachedExpectedApiRef"]
        print(
            f"    {item['elapsedSec']}s | 도구 {item['toolCallCount']} 회 {item['toolsCalled']}"
            f" | 기대표면도달={reached} | 근거 {item['evidenceCount']} | {item['responseStatus']}"
            f"\n    답변 {item['quality']['length']}자 인용 {item['quality']['refCitations']}"
            f" 수치 {item['quality']['numbers']} | 빠진 항목: {item['quality']['missing'] or '없음'}",
            flush=True,
        )
        if item["malformedArgs"]:
            for problem in item["malformedArgs"]:
                print(f"    기형 인자: {problem}", flush=True)
        if item["failureReason"]:
            print(f"    실패 사유: {item['failureReason']}", flush=True)

    report = {"runtimeId": args.runtime, "summary": summarize(results), "cases": results}
    print("\n=== 집계 ===")
    for key, value in report["summary"].items():
        print(f"  {key}: {value}")
    if args.out:
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n리포트: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
