"""
실험 ID: 015
실험명: 자동 검증 테스트 — 그룹 분류 품질 게이트

목적:
- classify_balanced() 결과에 대한 자동 검증 테스트 구축
- 패키지 이관 시 regression test로 전환 가능
- 수치 기반 PASS/FAIL 판정

가설:
1. 20개+ 검증 시나리오를 자동으로 실행 가능
2. 현재 012/013 결과가 모든 시나리오 PASS
3. 검증 시간 < 1초 (파이프라인 실행 후 dict만 검사)

방법:
1. 013 파이프라인 실행 → code_to_group dict
2. 시나리오별 assert 검증:
   - 그룹 크기 범위 (삼성 15~25, 현대차 15~25 등)
   - 그룹 소속 필수 멤버 (삼성전자∈삼성, 기아∈현대차 등)
   - 그룹 소속 금지 멤버 (원익∉삼성, 현대해상∉독립 등)
   - 독립 비율 범위 (40~60%)
   - 순환출자 최소 개수
   - 교차 그룹 오분류 검사
3. 전체 PASS/FAIL 판정

결과 (실험 후 작성):
- 40개 검증 시나리오 전부 PASS
- 카테고리별:
  - 그룹 크기 범위: 10/10 (삼성~HD현대 모두 범위 내)
  - 필수 소속: 18/18 (삼성전자∈삼성, 현대해상∈현대차 등)
  - 금지 소속: 5/5 (원익IPS∉삼성, 현대해상≠독립 등)
  - 독립 비율: 1/1 (53%, 40~60% 범위 내)
  - 그룹 수: 1/1 (185, 150~250 범위 내)
  - 순환출자: 2/2 (85개 ≥ 50, 현대차 내부 순환 존재)
  - 데이터 무결성: 3/3
- 검증 시간: <1초 (파이프라인 23초 + 검증 <1초)

결론:
- 가설 1 채택: 40개 시나리오 자동 실행
- 가설 2 채택: 013 결과가 40/40 PASS
- 가설 3 채택: 검증 자체 <1초
- 패키지 이관 시 이 시나리오를 tests/test_affiliate.py로 전환 가능
- 핵심 gate: 삼성 ≤ 25 (공급체인 차단), 현대해상 ∈ 현대차 (독립 방지)

실험일: 2026-03-19
"""

import time
from pathlib import Path
from collections import Counter

import importlib.util
_parent = Path(__file__).resolve().parent
_sp = importlib.util.spec_from_file_location("_m13", str(_parent / "013_consolidatedPipeline.py"))
_m13 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(_m13)


def _group_of(code: str, ctg: dict[str, str]) -> str:
    return ctg.get(code, "?")


def _is_independent(code: str, ctg: dict[str, str], code_to_name: dict[str, str]) -> bool:
    """code가 독립(그룹명 == 회사명)인지."""
    return ctg.get(code) == code_to_name.get(code, code)


def run_validation(
    code_to_group: dict[str, str],
    code_to_name: dict[str, str],
    all_node_ids: set[str],
    cycles: list[list[str]],
) -> tuple[int, int, list[str]]:
    """검증 테스트 실행.

    Returns:
        (pass_count, fail_count, fail_messages)
    """
    gc = Counter(code_to_group[n] for n in all_node_ids)
    passed = 0
    failed = 0
    fails: list[str] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  ✓ {name}")
        else:
            failed += 1
            msg = f"  ✗ {name}" + (f" — {detail}" if detail else "")
            print(msg)
            fails.append(msg)

    # ── 그룹 크기 범위 ──────────────────────────────────────
    print("\n[그룹 크기 범위]")
    check("삼성 15~25", 15 <= gc.get("삼성", 0) <= 25, f"actual={gc.get('삼성', 0)}")
    check("현대차 15~25", 15 <= gc.get("현대차", 0) <= 25, f"actual={gc.get('현대차', 0)}")
    check("SK 15~25", 15 <= gc.get("SK", 0) <= 25, f"actual={gc.get('SK', 0)}")
    check("LG 8~15", 8 <= gc.get("LG", 0) <= 15, f"actual={gc.get('LG', 0)}")
    check("한화 10~15", 10 <= gc.get("한화", 0) <= 15, f"actual={gc.get('한화', 0)}")
    check("롯데 8~15", 8 <= gc.get("롯데", 0) <= 15, f"actual={gc.get('롯데', 0)}")
    check("현대백화점 10~15", 10 <= gc.get("현대백화점", 0) <= 15, f"actual={gc.get('현대백화점', 0)}")
    check("KT 5~15", 5 <= gc.get("KT", 0) <= 15, f"actual={gc.get('KT', 0)}")
    check("효성 8~15", 8 <= gc.get("효성", 0) <= 15, f"actual={gc.get('효성', 0)}")
    check("HD현대 5~10", 5 <= gc.get("HD현대", 0) <= 10, f"actual={gc.get('HD현대', 0)}")

    # ── 필수 소속 ─────────────────────────────────────────
    print("\n[필수 소속]")
    must_belong = [
        ("005930", "삼성전자", "삼성"),
        ("006400", "삼성SDI", "삼성"),
        ("032830", "삼성생명", "삼성"),
        ("207940", "삼성바이오로직스", "삼성"),
        ("005380", "현대자동차", "현대차"),
        ("000270", "기아", "현대차"),
        ("012330", "현대모비스", "현대차"),
        ("001450", "현대해상", "현대차"),
        ("034730", "SK", "SK"),
        ("000660", "SK하이닉스", "SK"),
        ("003550", "LG", "LG"),
        ("066570", "LG전자", "LG"),
        ("000880", "한화에어로스페이스", "한화"),
        ("088350", "한화생명", "한화"),
        ("023530", "롯데지주", "롯데"),
        ("004800", "효성", "효성"),
        ("329180", "HD현대", "HD현대"),
        ("035720", "카카오", "카카오"),
    ]
    for code, name, expected_group in must_belong:
        actual = _group_of(code, code_to_group)
        check(f"{name}∈{expected_group}", actual == expected_group, f"actual={actual}")

    # ── 금지 소속 ─────────────────────────────────────────
    print("\n[금지 소속 — 오분류 검사]")
    must_not_belong = [
        ("240810", "원익IPS", "삼성"),      # 공급체인, 삼성 아님
        ("222800", "심텍", "삼성"),          # 공급체인
        ("002390", "한독", "삼성"),          # 무관
        ("010060", "OCI홀딩스", "삼성"),      # 무관
        ("001450", "현대해상", None),         # 독립이면 안됨 (독립 = 회사명 그룹)
    ]
    for code, name, forbidden_group in must_not_belong:
        if forbidden_group is None:
            # 독립이면 안됨
            check(f"{name}≠독립", not _is_independent(code, code_to_group, code_to_name),
                  f"actual={_group_of(code, code_to_group)}")
        else:
            actual = _group_of(code, code_to_group)
            check(f"{name}∉{forbidden_group}", actual != forbidden_group, f"actual={actual}")

    # ── 독립 비율 ─────────────────────────────────────────
    print("\n[독립 비율]")
    indep = sum(1 for c in gc.values() if c == 1)
    ratio = indep / len(all_node_ids)
    check("독립 40~60%", 0.40 <= ratio <= 0.60, f"actual={ratio:.1%}")

    # ── 그룹 수 ───────────────────────────────────────────
    print("\n[그룹 수]")
    multi = sum(1 for c in gc.values() if c >= 2)
    check("2명+ 그룹 150~250", 150 <= multi <= 250, f"actual={multi}")

    # ── 순환출자 ──────────────────────────────────────────
    print("\n[순환출자]")
    check("순환출자 50+", len(cycles) >= 50, f"actual={len(cycles)}")
    # 현대차 내부 순환 존재
    hyundai_cycle = any(
        "005380" in c or "000270" in c for c in cycles
    )
    check("현대차 내부 순환 존재", hyundai_cycle)

    # ── JSON 무결성 ──────────────────────────────────────
    print("\n[데이터 무결성]")
    check("모든 노드에 그룹 할당", all(n in code_to_group for n in all_node_ids))
    check("그룹명 빈 문자열 없음", all(code_to_group.get(n, "") != "" for n in all_node_ids))
    check("노드 수 1500+", len(all_node_ids) >= 1500, f"actual={len(all_node_ids)}")

    return passed, failed, fails


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("파이프라인 실행...")
    data = _m13.build_graph()

    print("\n" + "=" * 60)
    print("검증 테스트 실행")
    print("=" * 60)

    passed, failed, fails = run_validation(
        data["code_to_group"],
        data["code_to_name"],
        data["all_node_ids"],
        data["cycles"],
    )

    print(f"\n{'=' * 60}")
    print(f"결과: {passed} PASS / {failed} FAIL")
    print("=" * 60)

    if failed > 0:
        print("\n실패 항목:")
        for f in fails:
            print(f)

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
