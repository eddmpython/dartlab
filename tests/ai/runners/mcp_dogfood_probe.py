"""dartlab MCP 도그푸드 probe: 외부 클라이언트의 advertise/실행 경계 검증.

실행 ::
    uv run python -X utf8 tests/ai/runners/mcp_dogfood_probe.py

목적: pytest 가 dispatch / 거부 경로 위주로 커버할 때, 실제 호출 흐름의 happy path 마찰을
잡는 *수동 verification asset*. 도그푸드 자체가 강화 사이클의 일부 — 단위 테스트만으로는
LookAheadGuard 의 Company(market=...) 같은 외부 의존 회귀를 못 잡는다는 발견 (2026-05-09).

검증 항목 (11):
  1. ReadSkill — 분석 의도 매칭
  2. ReadCapability — API 카탈로그 검색
  3. RunPython sanity
  4. RunPython 실제 dartlab.Company.panel 호출
  5. S2 sandbox os.system 차단
  6. 비광고 GroundingCheck 실행 차단
  7. 비광고 LookAheadGuard 실행 차단
  7b. 비광고 호출은 인자와 무관하게 동일 차단
  8. 비광고 RequestUserInput elicit 전 차단
  9. S1 progress notification (1 s 임계 + 0.5 s 간격)
  10. prompts/list

판정: 각 항목 OK / MEH / FAIL. 마지막에 카운트 + 상세 출력.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys


def _proactor():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def _short(text, n=180):
    s = json.dumps(text, ensure_ascii=False, default=str) if not isinstance(text, str) else text
    s = s.replace("\n", " ")
    return s[:n] + ("..." if len(s) > n else "")


async def main():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    env["DARTLAB_PROGRESS_THRESHOLD_SEC"] = "1.0"
    env["DARTLAB_PROGRESS_INTERVAL_SEC"] = "0.5"
    server = StdioServerParameters(command="dartlab", args=["mcp"], env=env)

    findings = []  # (verdict, msg)

    def note(verdict, msg):
        findings.append((verdict, msg))
        print(f"  [{verdict}] {msg}")

    print("=" * 72)
    print("dartlab MCP 도그푸드 — 11 도구 실사용")
    print("=" * 72)

    async with stdio_client(server) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()

            # ── 1. ReadSkill — 분석 시작 ───────────────────────────────
            print("\n## 1. ReadSkill('quant 예측')")
            res = await s.call_tool("ReadSkill", {"query": "quant 예측", "limit": 3})
            sc = res.structuredContent or {}
            refs = sc.get("refs") or []
            print(f"  refs={len(refs)}, summary={_short(sc.get('summary'))}")
            if refs:
                top = refs[0]
                print(f"  top: id={top.get('id')}, title={_short(top.get('title'), 80)}")
                if top.get("id") in {"skill:engines.quant", "skill:engines.quant.forecast"}:
                    note("OK", "ReadSkill 이 quant 예측 의도를 정확히 매칭")
                else:
                    note("MEH", f"top match가 quant 가 아님: {top.get('id')}")
            else:
                note("FAIL", "ReadSkill refs 0 — 검색 실패")

            # ── 2. ReadCapability — 같은 의도 다른 채널 ─────────────────
            print("\n## 2. ReadCapability('quant')")
            res = await s.call_tool("ReadCapability", {"query": "quant", "limit": 3})
            sc = res.structuredContent or {}
            refs = sc.get("refs") or []
            print(f"  refs={len(refs)}")
            for ref in refs[:2]:
                print(f"    - {ref.get('payload', {}).get('apiRef')} (score={ref.get('payload', {}).get('score'):.2f})")
            if any("quant" in (ref.get("payload", {}).get("apiRef") or "") for ref in refs):
                note("OK", "ReadCapability 가 quant API 발견")

            # ── 3. RunPython — 실제 분석 (sanity) ────────────────────────
            print("\n## 3. RunPython sanity")
            res = await s.call_tool(
                "RunPython",
                {"code": "emit_result(values={'mode': 'dogfood', 'pid_alive': True})"},
            )
            sc = res.structuredContent or {}
            note(
                "OK" if sc.get("ok") else "FAIL",
                f"RunPython sanity ok={sc.get('ok')}, refs={len(sc.get('refs') or [])}",
            )

            # ── 4. RunPython — 실제 dartlab 호출 (cold path 포함) ──────
            print("\n## 4. RunPython — dartlab.Company('005930').show('BS')")
            try:
                res = await s.call_tool(
                    "RunPython",
                    {
                        "code": (
                            "import dartlab\n"
                            "c = dartlab.Company('005930')\n"
                            "df = c.panel('BS')\n"
                            "emit_result(values={'rows': df.height if df is not None else 0, 'columns': len(df.columns) if df is not None else 0})"
                        )
                    },
                )
                sc = res.structuredContent or {}
                if sc.get("ok"):
                    rows = next(
                        (r.get("payload", {}).get("value") for r in (sc.get("refs") or []) if r.get("title") == "rows"),
                        None,
                    )
                    note("OK", f"실제 dartlab API 통한 BS 로드 성공 — rows={rows}")
                else:
                    note("FAIL", f"dartlab.Company.panel 실패: {_short(sc.get('summary'))}")
            except Exception as e:
                note("FAIL", f"RunPython exception: {e}")

            # ── 5. S2 sandbox 차단 ────────────────────────────────────
            print("\n## 5. S2 sandbox — os.system 차단 검증")
            res = await s.call_tool(
                "RunPython", {"code": "import os\nos.system('echo blocked')\nemit_result(values={'leak': True})"}
            )
            sc = res.structuredContent or {}
            stderr = ""
            for ref in sc.get("refs") or []:
                stderr = ref.get("payload", {}).get("stderr", "") or stderr
            if not sc.get("ok") and "PermissionError" in stderr and "os.system" in stderr:
                note("OK", "차단 메시지 + 대안 안내 PermissionError 로 정확히 거부")
            else:
                note("FAIL", f"sandbox 차단 안 됨: ok={sc.get('ok')}")

            # 6. 내부 GroundingCheck: advertise 밖 실행 차단
            print("\n## 6. GroundingCheck: 비광고 실행 차단")
            sample = "삼성전자 ROE 는 12.3% 다. 3 분기 연속 OPM > 15% 유지."
            res = await s.call_tool("GroundingCheck", {"answer": sample, "refs": []})
            sc = res.structuredContent or {}
            if sc.get("error") == "tool_not_advertised":
                note("OK", "tools/list 밖 GroundingCheck 직접 호출 차단")
            else:
                note("FAIL", f"비광고 도구가 실행됨: {_short(sc)}")

            # 7. 내부 LookAheadGuard: advertise 밖 실행 차단
            print("\n## 7. LookAheadGuard: 비광고 실행 차단")
            try:
                res = await s.call_tool(
                    "LookAheadGuard",
                    {"stockCode": "005930", "asOf": "2024Q4", "topic": "BS"},
                )
                sc = res.structuredContent or {}
                if sc.get("error") == "tool_not_advertised":
                    note("OK", "tools/list 밖 LookAheadGuard 직접 호출 차단")
                else:
                    note("FAIL", f"비광고 도구가 실행됨: {_short(sc)}")
            except Exception as e:
                note("FAIL", f"LookAheadGuard exception: {e}")

            print("\n## 7b. LookAheadGuard: 인자와 무관한 동일 경계")
            res = await s.call_tool("LookAheadGuard", {"stockCode": "005930", "asOf": ""})
            sc = res.structuredContent or {}
            if not sc.get("ok") and sc.get("error") == "tool_not_advertised":
                note("OK", "비광고 호출은 asOf 검증 전에 동일하게 차단")

            # 8. 내부 RequestUserInput: elicit 전 실행 차단
            print("\n## 8. RequestUserInput: 비광고 실행 차단")
            res = await s.call_tool(
                "RequestUserInput",
                {
                    "message": "분석할 회사를 선택하세요",
                    "fields": [{"name": "company", "enum": ["005930", "AAPL"]}],
                },
            )
            sc = res.structuredContent or {}
            err = sc.get("error")
            if err == "tool_not_advertised":
                note("OK", "tools/list 밖 RequestUserInput은 elicit 전에 차단")
            else:
                note("FAIL", f"비광고 도구가 실행됨: {err}")

            # ── 10. S1 progress — 2 s sleep RunPython ────────────────────
            print("\n## 9. S1 progress — 2 s sleep RunPython")
            events = []

            async def on_progress(p, total, msg):
                events.append((p, msg))

            res = await s.call_tool(
                "RunPython",
                {"code": "import time\nfor _ in range(4): time.sleep(0.5)\nemit_result(values={'done': True})"},
                progress_callback=on_progress,
            )
            sc = res.structuredContent or {}
            note(
                "OK" if (sc.get("ok") and len(events) >= 1) else "FAIL",
                f"slow RunPython ok={sc.get('ok')}, progress events={len(events)}",
            )
            if events:
                print(f"  first event: progress={events[0][0]}, msg={_short(events[0][1], 80)}")

            # ── 11. prompts/list — 49 recipe ───────────────────────────
            print("\n## 10. prompts/list")
            prompts = await s.list_prompts()
            recipe_count = sum(1 for p in prompts.prompts if "recipes." in p.name)
            note("OK" if recipe_count >= 30 else "MEH", f"recipe prompt {recipe_count} (전체 {len(prompts.prompts)})")

    # ── 결과 정리 ────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("판정")
    print("=" * 72)
    ok = sum(1 for v, _ in findings if v == "OK")
    meh = sum(1 for v, _ in findings if v == "MEH")
    fail = sum(1 for v, _ in findings if v == "FAIL")
    print(f"  OK={ok}, MEH={meh}, FAIL={fail}")
    print()
    for v, msg in findings:
        print(f"  [{v}] {msg}")


if __name__ == "__main__":
    _proactor()
    asyncio.run(main())
