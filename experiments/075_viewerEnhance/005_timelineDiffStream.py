"""
실험 ID: 005
실험명: 다기간 텍스트 스트림 비교

목적:
- 동일 topic 텍스트를 4기간+ segment 매칭으로 타임라인 정렬 가능한지 검증
- segment(문단) 수준에서 "언제 추가/삭제/변경"되었는지 추적

가설:
1. 인접 기간 segment 매칭률 50% 이상
2. segment × period 매트릭스가 50행 × 10기간 이내 (렌더링 가능 크기)
3. 변화 패턴에서 의미 있는 시점 식별 가능 (대량 추가/삭제 시점)

방법:
1. 삼성전자/현대차/LG에너지솔루션 businessOverview 전 기간 텍스트 추출
2. 각 기간 텍스트를 \\n\\n 기준 segment로 분할
3. difflib.SequenceMatcher로 인접 기간 segment 매칭 (ratio > 0.6)
4. segment × period 매트릭스 구축

결과 (v2 — non-period 필터 정규식 수정 후):
- 삼성전자: 258행 × 40기간, 평균 매칭률 93.9%
- 현대차: 390행 × 33기간, 매칭률 89.8%
- LG에너지솔루션: 93행 × 20기간, 매칭률 97.8%
- 기간 정규식 `^\d{4}(Q[1-4])?$`로 메타 컬럼 오염 완전 제거
- LG에너지솔루션: 인접 기간 매칭 100% 다수 (구조 안정)
- 현대차: 2022Q1→2022 31.8%, 2021Q2→2021Q1 62.0% (구조 변경 시점)
- 삼성전자: 최소 84.4%(2019→2018Q3), 최대 100%(2016Q2→2016Q1)
- 1기간 slot: 삼성 111/258, 현대 119/390, LG 9/93
  → 여전히 \n\n 분할 과도, 핵심 slot 필터 필요
- 매트릭스 크기: 렌더 불가 (필터 필요)

결론:
- 가설 1 채택: 인접 기간 segment 매칭률 89.8~97.8% (50% 이상 대폭 초과)
- 가설 2 기각: segment 수 93~390행 (50행 이내 불가). 핵심 slot 필터 시 가능성
- 가설 3 채택: 현대차 2022Q1→2022 31.8% 급락 = 보고서 구조 대개편 시점
  → "구조 변경 시점 자동 감지" 기능으로 활용 가능
- non-period 버그 완전 해결 → 매칭률 83~87% → 89.8~97.8%로 상승
- 흡수 조건: 핵심 slot 필터(10기간+ 출현) + 렌더 크기 제한 추가 후 흡수 가능

실험일: 2026-03-20
"""

import difflib

import polars as pl

import dartlab


def split_segments(text: str) -> list[str]:
    """텍스트를 문단 단위 segment로 분할."""
    if not text or not isinstance(text, str):
        return []
    # 빈 줄 2개 이상으로 분할, 짧은 세그먼트 제거
    raw = text.split("\n\n")
    segments = []
    for s in raw:
        s = s.strip()
        if len(s) >= 20:  # 20자 미만은 제목/구분선 등 → 무시
            segments.append(s)
    return segments


def match_segments(segs_from: list[str], segs_to: list[str], threshold: float = 0.6) -> list[tuple]:
    """두 기간 segment 매칭. [(from_idx, to_idx, ratio)] 반환."""
    matches = []
    used_to = set()

    for i, sf in enumerate(segs_from):
        best_j = -1
        best_ratio = 0
        for j, st in enumerate(segs_to):
            if j in used_to:
                continue
            ratio = difflib.SequenceMatcher(None, sf, st).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_j = j

        if best_ratio >= threshold:
            matches.append((i, best_j, best_ratio))
            used_to.add(best_j)

    return matches


def build_segment_timeline(sections_df: pl.DataFrame, topic: str) -> dict:
    """topic의 전 기간 텍스트 → segment × period 매트릭스."""
    # 기간 컬럼 추출
    import re as _re
    periods = sorted([c for c in sections_df.columns if _re.match(r"^\d{4}(Q[1-4])?$", c)], reverse=True)

    # topic 텍스트 추출
    topic_rows = sections_df.filter(
        (pl.col("topic") == topic) &
        (pl.col("blockType") == "text")
    )
    if len(topic_rows) == 0:
        return {"error": "topic not found"}

    # 기간별 텍스트 합치기 + segment 분할
    period_segments = {}
    for p in periods:
        if p not in topic_rows.columns:
            continue
        texts = topic_rows[p].drop_nulls().to_list()
        full_text = "\n\n".join(str(t) for t in texts if t)
        segs = split_segments(full_text)
        if segs:
            period_segments[p] = segs

    valid_periods = sorted(period_segments.keys(), reverse=True)
    if len(valid_periods) < 2:
        return {"error": "too few periods", "periods": len(valid_periods)}

    # 인접 기간 매칭
    # 최신부터 과거로: 최신 segment가 기준
    all_slots = []  # [{period: segment_text, ...}]
    match_stats = []

    # 초기: 최신 기간 segment로 시작
    latest = valid_periods[0]
    for seg in period_segments[latest]:
        all_slots.append({latest: seg})

    for i in range(1, len(valid_periods)):
        curr_period = valid_periods[i]
        prev_period = valid_periods[i - 1]

        curr_segs = period_segments[curr_period]
        prev_segs = period_segments[prev_period]

        matches = match_segments(prev_segs, curr_segs)
        matched_prev = {m[0] for m in matches}
        matched_curr = {m[1] for m in matches}
        match_ratio = len(matches) / max(len(prev_segs), 1)
        match_stats.append({
            "from": prev_period,
            "to": curr_period,
            "prev_segs": len(prev_segs),
            "curr_segs": len(curr_segs),
            "matched": len(matches),
            "ratio": match_ratio,
        })

        # 매칭된 segment → 기존 slot에 추가
        prev_to_slot = {}
        for slot_idx, slot in enumerate(all_slots):
            if prev_period in slot:
                for m in matches:
                    if period_segments[prev_period][m[0]] == slot[prev_period]:
                        prev_to_slot[m[0]] = slot_idx
                        break

        # 실제 매칭 적용
        for from_idx, to_idx, ratio in matches:
            slot_idx = prev_to_slot.get(from_idx)
            if slot_idx is not None:
                all_slots[slot_idx][curr_period] = curr_segs[to_idx]

        # 매칭 안 된 curr segment → 새 slot
        for j, seg in enumerate(curr_segs):
            if j not in matched_curr:
                all_slots.append({curr_period: seg})

    return {
        "topic": topic,
        "periods": valid_periods,
        "slot_count": len(all_slots),
        "match_stats": match_stats,
        "slots": all_slots,
    }


if __name__ == "__main__":
    test_cases = [
        ("005930", "삼성전자", "businessOverview"),
        ("005380", "현대차", "businessOverview"),
        ("373220", "LG에너지솔루션", "businessOverview"),
    ]

    all_results = {}

    for code, name, topic in test_cases:
        print(f"\n{'='*60}")
        print(f"{name} ({code}) — {topic}")
        print(f"{'='*60}")

        c = dartlab.Company(code)
        sections = c.docs.sections.raw

        result = build_segment_timeline(sections, topic)

        if "error" in result:
            print(f"  오류: {result['error']}")
            all_results[name] = {"error": result["error"]}
            continue

        print(f"  유효 기간: {len(result['periods'])}개")
        print(f"  기간 목록: {result['periods'][:8]}...")
        print(f"  총 slot(행) 수: {result['slot_count']}")

        # 매칭 통계
        print(f"\n  [기간별 매칭률]")
        avg_ratio = 0
        for ms in result["match_stats"]:
            print(f"    {ms['from']} → {ms['to']}: "
                  f"{ms['matched']}/{ms['prev_segs']}개 매칭 ({ms['ratio']:.1%})")
            avg_ratio += ms["ratio"]
        avg_ratio /= max(len(result["match_stats"]), 1)
        print(f"  평균 매칭률: {avg_ratio:.1%}")

        # slot 커버리지
        coverage = {}
        for slot in result["slots"]:
            n_periods = len(slot)
            coverage[n_periods] = coverage.get(n_periods, 0) + 1

        print(f"\n  [slot 기간 분포]")
        for n, cnt in sorted(coverage.items(), reverse=True):
            print(f"    {n}기간 출현: {cnt}개 slot")

        # 매트릭스 크기
        rows = result["slot_count"]
        cols = len(result["periods"])
        print(f"\n  매트릭스 크기: {rows} × {cols}")
        print(f"  렌더링 가능: {'예' if rows <= 50 and cols <= 10 else '아니오 (필터 필요)'}")

        all_results[name] = {
            "periods": len(result["periods"]),
            "slots": result["slot_count"],
            "avg_match_ratio": round(avg_ratio, 3),
            "matrix_size": f"{rows}×{cols}",
            "renderable": rows <= 50 and cols <= 10,
        }

    # 종합
    print(f"\n{'='*60}")
    print("종합")
    print(f"{'='*60}")
    for name, r in all_results.items():
        if "error" in r:
            print(f"  {name}: {r['error']}")
        else:
            print(f"  {name}: {r['slots']}행 × {r['periods']}기간, 매칭률 {r['avg_match_ratio']:.1%}, 렌더 {'가능' if r['renderable'] else '불가'}")
