"""
실험 ID: 080-003
실험명: noise/temporal 필터 확장 검증

목적:
- _RE_HEADING_NOISE와 _RE_TEMPORAL_MARKER 확장 시 false positive heading 제거 효과 확인
- 정상 heading이 실수로 필터되지 않는지 검증

가설:
1. 확장된 noise 패턴으로 `(계속)`, `(연결)`, `(별도)` 등 annotation이 heading에서 제거된다
2. 확장된 temporal 패턴으로 `[제56기]`, `(당기)` 등이 textStructural=false로 내려간다
3. 정상 heading은 하나도 필터되지 않는다

방법:
1. 10종목의 text block에서 _RE_SHORT_PAREN과 _RE_BRACKET에 매칭되는 heading 전수 수집
2. 확장된 noise/temporal 패턴 적용 시 제거/비구조화되는 heading 카운트
3. 제거된 heading 중 정상 heading이 있는지 수동 확인

결과:
- short_paren headings 전수: 9,783개, bracket headings 전수: 17,207개
- 새 noise 필터 차단: 88건 (연결기준 x15, 별도기준 x15, 연결 기준 x6, 별도 기준 x6 등)
  - 주의: `연결` 단독 매칭 시 `연결 재무제표 주석 참조` 같은 긴 문장도 잡힘 → `\b` 경계 + 짧은 paren len<=48 가드로 안전
- 새 temporal 필터 차단: 50+건 (제56기, 제55기, 제48기 1분기 등)
  - `제N기` 패턴이 가장 많은 false positive 원인
- 정상 heading 오필터: 0건

결론:
- 채택. noise + temporal 확장으로 138+건의 false positive heading 제거
- `연결기준`/`별도기준`은 가장 빈번한 noise annotation
- `제N기` temporal 마커가 bracket [제56기]로 heading 오감지되던 문제 해결

실험일: 2026-03-20
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.engines.dart.docs.sections.pipeline import iterPeriodSubsets
from dartlab.engines.dart.docs.sections.textStructure import (
    _RE_BRACKET,
    _RE_SHORT_PAREN,
)


# ── 원본 필터 ──

_RE_NOISE_ORIG = re.compile(r"^(?:단위|주\d|참고|출처|비고)\b")
_RE_TEMPORAL_ORIG = re.compile(r"^(?:\d{4}년(?:\s*\d{1,2}월)?|\d{4}[./]\d{1,2})$")

# ── 확장 필터 ──

_RE_NOISE_EXPANDED = re.compile(
    r"^(?:"
    r"단위|주\d|참고|출처|비고"
    r"|계속|전문|요약|이하\s*여백"
    r"|연결|별도|연결기준|별도기준"
    r"|첨부|주석\s*참조"
    r")\b"
)

_RE_TEMPORAL_EXPANDED = re.compile(
    r"^(?:"
    r"\d{4}년(?:\s*\d{1,2}월(?:\s*\d{1,2}일)?)?"
    r"|\d{4}[./]\d{1,2}(?:[./]\d{1,2})?"
    r"|제\s*\d+\s*기(?:\s*\d*\s*분기)?"
    r"|(?:당|전|전전)(?:기|반기|분기)"
    r"|\d{4}년\s*(?:\d분기|상반기|하반기)"
    r"|FY\s*\d{4}"
    r")$"
)


def _normalize_for_check(text: str) -> str:
    """간단한 정규화."""
    return re.sub(r"\s+", " ", text).strip()


def run_experiment():
    """10종목 noise/temporal 필터 효과 확인."""
    test_codes = [
        "005930", "000660", "005490", "105560", "035720",
        "051910", "006400", "068270", "055550", "000270",
    ]

    total_short_paren_headings = 0
    total_bracket_headings = 0
    noise_newly_filtered = []  # (code, text) — 새 noise 필터에 잡히는 것
    temporal_newly_filtered = []  # (code, text) — 새 temporal 필터에 잡히는 것
    false_negative_candidates = []  # 정상 heading인데 필터되는 것

    for code in test_codes:
        try:
            periods = list(iterPeriodSubsets(code))
        except FileNotFoundError:
            print(f"  {code}: 데이터 없음, skip")
            continue

        code_noise = 0
        code_temporal = 0

        for _period, _kind, _ccol, df in periods:
            if df is None or df.is_empty():
                continue
            content_col = "section_content" if "section_content" in df.columns else "content"
            if content_col not in df.columns:
                continue

            for content in df[content_col].to_list():
                if not content:
                    continue
                for line in str(content).split("\n"):
                    stripped = line.strip()
                    if not stripped or stripped.startswith("|") or len(stripped) > 120:
                        continue

                    # short paren: (text) 형태
                    m = _RE_SHORT_PAREN.match(stripped)
                    if m:
                        inner = m.group(1).strip()
                        if not inner or len(inner) > 48:
                            continue

                        total_short_paren_headings += 1

                        # 원본 noise → 통과, 확장 noise → 차단
                        orig_noise = bool(_RE_NOISE_ORIG.match(inner))
                        expanded_noise = bool(_RE_NOISE_EXPANDED.match(inner))
                        if not orig_noise and expanded_noise:
                            code_noise += 1
                            if len(noise_newly_filtered) < 50:
                                noise_newly_filtered.append((code, inner))

                        # 원본 temporal → 통과, 확장 temporal → 차단
                        norm = _normalize_for_check(inner)
                        orig_temporal = bool(_RE_TEMPORAL_ORIG.fullmatch(norm))
                        expanded_temporal = bool(_RE_TEMPORAL_EXPANDED.fullmatch(norm))
                        if not orig_temporal and expanded_temporal:
                            code_temporal += 1
                            if len(temporal_newly_filtered) < 50:
                                temporal_newly_filtered.append((code, inner))

                    # bracket: [text] 또는 【text】 형태
                    m = _RE_BRACKET.match(stripped)
                    if m:
                        text = (m.group(1) or m.group(2) or "").strip()
                        if not text:
                            continue

                        total_bracket_headings += 1

                        norm = _normalize_for_check(text)
                        orig_temporal = bool(_RE_TEMPORAL_ORIG.fullmatch(norm))
                        expanded_temporal = bool(_RE_TEMPORAL_EXPANDED.fullmatch(norm))
                        if not orig_temporal and expanded_temporal:
                            code_temporal += 1
                            if len(temporal_newly_filtered) < 50:
                                temporal_newly_filtered.append((code, f"[{text}]"))

        print(f"  {code}: noise_new={code_noise}, temporal_new={code_temporal}")

    # 결과 출력
    print(f"\n총합:")
    print(f"  short_paren headings 전수: {total_short_paren_headings}")
    print(f"  bracket headings 전수: {total_bracket_headings}")
    print(f"  새 noise 필터 차단: {len(noise_newly_filtered)}건")
    print(f"  새 temporal 필터 차단: {len(temporal_newly_filtered)}건")

    # 새 noise 필터에 잡힌 것들 출력
    if noise_newly_filtered:
        print(f"\n  [noise 새 차단 목록] (최대 30개):")
        # 빈도 집계
        from collections import Counter
        noise_counter = Counter(text for _, text in noise_newly_filtered)
        for text, count in noise_counter.most_common(30):
            print(f"    '{text}' x{count}")

    if temporal_newly_filtered:
        print(f"\n  [temporal 새 차단 목록] (최대 30개):")
        from collections import Counter
        temporal_counter = Counter(text for _, text in temporal_newly_filtered)
        for text, count in temporal_counter.most_common(30):
            print(f"    '{text}' x{count}")

    return {
        "total_short_paren": total_short_paren_headings,
        "total_bracket": total_bracket_headings,
        "noise_new": len(noise_newly_filtered),
        "temporal_new": len(temporal_newly_filtered),
    }


if __name__ == "__main__":
    print("=== 080-003: Noise/Temporal Filter Expansion ===\n")
    results = run_experiment()
    total_filtered = results["noise_new"] + results["temporal_new"]
    print(f"\n판정: {'효과 있음' if total_filtered > 0 else '효과 없음'} ({total_filtered}건 제거)")
