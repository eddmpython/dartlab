"""
실험 ID: 003
실험명: 텍스트-재무 숫자 교차 참조

목적:
- sections 텍스트에 언급된 금액(매출액 xxx억, 영업이익 xxx억 등)이
  finance DataFrame의 실제 숫자와 자동 매칭 가능한지 검증
- 매칭되면 뷰어에서 텍스트 내 숫자를 finance 블록에 연결할 수 있음

가설:
1. 정규식으로 텍스트 금액 추출 가능 (매출 xxx억, xxx원 등)
2. 주요 topic(businessOverview, salesOrder)에서 매칭률 30% 이상
3. 매칭된 숫자의 오차율 5% 이내

방법:
1. 삼성전자 businessOverview 텍스트에서 금액 패턴 정규식 추출
2. finance IS/BS/CF 주요 계정 숫자 추출 (같은 기간)
3. 텍스트 숫자 ↔ finance 숫자 매칭 (+-5% 오차 허용)
4. 10개사 반복

결과 (v2 — non-period 정규식 수정 + finance 접근 수정):
- 10사 전체: 추출 631개, 매칭 342개, 전체 매칭률 54.2%, 평균 오차 1.89%
- 삼성전자: 67개 추출, 31개 매칭 (46.3%) — 매출액 0.07%, 유형자산 0.0%
- 현대차: 45개 추출, 29개 매칭 (64.4%) — 차입부채 0.02%, 영업이익 0.48%
- LG: 170개 추출, 113개 매칭 (66.5%) — 최다 추출/매칭 (지주사 특성)
- 셀트리온: 26개 추출, 10개 매칭 (38.5%) — 매출액 0.0%, 영업이익 0.0% (정확 매칭)
- 수정 사항:
  1. 기간 정규식 `^\d{4}(Q[1-4])?$`로 메타 컬럼 오염 제거
  2. finance 컬럼명 `계정명`으로 수정 (기존 `account`/`항목` 잘못됨)
  3. 연간 기간 `2024` → `2024Q4` 자동 변환 추가

결론:
- 가설 1 채택: 정규식으로 텍스트 금액 추출 가능 (631개)
- 가설 2 채택: 주요 topic 매칭률 38.5~66.5% (30% 이상 충족)
- 가설 3 채택: 매칭 오차율 평균 1.89% (5% 이내 대폭 충족)
- 흡수: 텍스트 금액 → finance 계정 자동 연결 기능으로 활용
  → 뷰어에서 "매출액 86조 1,229억" 클릭 시 finance IS 해당 행 하이라이트
- 매칭 안 된 45.8%는 주로: 시가총액/주가(finance 미포함), 성장률/비율, 단위 불일치

실험일: 2026-03-20
"""

import re

import polars as pl

import dartlab


# 금액 추출 패턴
# "약 300조 5,230억원", "매출액 2,587,849백만원", "3조 1,200억" 등
AMOUNT_PATTERNS = [
    # 조+억 패턴: "300조 5,230억"
    re.compile(r"([\d,]+)\s*조\s*([\d,]*)\s*억"),
    # 단독 조: "300조원"
    re.compile(r"([\d,]+)\s*조(?:\s*원)?(?![억])"),
    # 단독 억: "5,230억"
    re.compile(r"([\d,]+)\s*억(?:\s*원)?"),
    # 백만원: "2,587,849백만원"
    re.compile(r"([\d,]+)\s*백만\s*원"),
    # 천원: "2,587,849천원"
    re.compile(r"([\d,]+)\s*천\s*원"),
]


def parse_number(s: str) -> float:
    """쉼표 제거 후 float 변환."""
    if not s:
        return 0
    cleaned = s.replace(",", "").strip()
    if not cleaned:
        return 0
    try:
        return float(cleaned)
    except ValueError:
        return 0


def extract_amounts_from_text(text: str) -> list[dict]:
    """텍스트에서 금액 추출 → [{value_억: float, raw: str, unit: str}]."""
    if not text or not isinstance(text, str):
        return []

    results = []
    seen_positions = set()

    # 조+억 패턴
    for m in AMOUNT_PATTERNS[0].finditer(text):
        if m.start() in seen_positions:
            continue
        seen_positions.add(m.start())
        jo = parse_number(m.group(1))
        eok = parse_number(m.group(2)) if m.group(2) else 0
        value_억 = jo * 10000 + eok
        results.append({"value_억": value_억, "raw": m.group(0), "unit": "조억"})

    # 단독 조
    for m in AMOUNT_PATTERNS[1].finditer(text):
        if m.start() in seen_positions:
            continue
        seen_positions.add(m.start())
        value_억 = parse_number(m.group(1)) * 10000
        results.append({"value_억": value_억, "raw": m.group(0), "unit": "조"})

    # 단독 억
    for m in AMOUNT_PATTERNS[2].finditer(text):
        if m.start() in seen_positions:
            continue
        seen_positions.add(m.start())
        value_억 = parse_number(m.group(1))
        results.append({"value_억": value_억, "raw": m.group(0), "unit": "억"})

    # 백만원
    for m in AMOUNT_PATTERNS[3].finditer(text):
        if m.start() in seen_positions:
            continue
        seen_positions.add(m.start())
        value_억 = parse_number(m.group(1)) / 100  # 백만원 → 억
        results.append({"value_억": value_억, "raw": m.group(0), "unit": "백만원"})

    # 천원
    for m in AMOUNT_PATTERNS[4].finditer(text):
        if m.start() in seen_positions:
            continue
        seen_positions.add(m.start())
        value_억 = parse_number(m.group(1)) / 100000  # 천원 → 억
        results.append({"value_억": value_억, "raw": m.group(0), "unit": "천원"})

    return results


def get_finance_amounts(company, period: str) -> dict:
    """finance에서 주요 계정 → {account: value_억}.

    sections 기간이 '2024'(연간)이면 finance에서 '2024Q4'를 찾고,
    '2024Q3'(분기)이면 그대로 찾는다.
    """
    result = {}

    # 연간 기간이면 Q4로 변환 시도
    candidates = [period]
    if re.match(r"^\d{4}$", period):
        candidates.append(f"{period}Q4")

    for stmt_name in ["IS", "BS", "CF"]:
        try:
            stmt = getattr(company.finance, stmt_name)
            if stmt is None:
                continue

            # 매칭되는 기간 컬럼 찾기
            target_period = None
            for cand in candidates:
                if cand in stmt.columns:
                    target_period = cand
                    break
            if target_period is None:
                continue

            for row in stmt.iter_rows(named=True):
                account = row.get("계정명") or row.get("account") or row.get("항목")
                val = row.get(target_period)
                if account and val is not None:
                    try:
                        val_f = float(val)
                        # finance 값은 원 단위 → 억 변환
                        result[account] = val_f / 100_000_000
                    except (ValueError, TypeError):
                        pass
        except Exception:
            pass

    return result


def match_amounts(text_amounts: list[dict], finance_amounts: dict, tolerance: float = 0.05) -> list[dict]:
    """텍스트 금액 ↔ finance 금액 매칭."""
    matches = []
    for ta in text_amounts:
        tv = ta["value_억"]
        if tv == 0:
            continue
        best_match = None
        best_error = float("inf")
        for account, fv in finance_amounts.items():
            if fv == 0:
                continue
            error = abs(tv - fv) / abs(fv)
            if error <= tolerance and error < best_error:
                best_error = error
                best_match = {
                    "text_raw": ta["raw"],
                    "text_value_억": tv,
                    "finance_account": account,
                    "finance_value_억": round(fv, 1),
                    "error": round(error * 100, 2),
                }
        if best_match:
            matches.append(best_match)
    return matches


if __name__ == "__main__":
    test_codes = [
        ("005930", "삼성전자"),
        ("005380", "현대차"),
        ("035720", "카카오"),
        ("000660", "SK하이닉스"),
        ("051910", "LG화학"),
        ("006400", "삼성SDI"),
        ("003550", "LG"),
        ("105560", "KB금융"),
        ("055550", "신한지주"),
        ("068270", "셀트리온"),
    ]

    all_results = {}

    for code, name in test_codes:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        c = dartlab.Company(code)

        # sections에서 businessOverview 텍스트 추출
        sections = c.docs.sections.raw
        topics = sections["topic"].unique().to_list()

        # businessOverview 찾기
        target_topics = ["businessOverview", "companyOverview", "salesOrder"]
        found_topics = [t for t in target_topics if t in topics]

        if not found_topics:
            print("  대상 topic 없음")
            all_results[name] = {"extracted": 0, "matched": 0, "rate": 0}
            continue

        # 기간 컬럼 추출
        periods = sorted([c_ for c_ in sections.columns if re.match(r"^\d{4}(Q[1-4])?$", c_)], reverse=True)

        # 최신 기간
        latest_period = periods[0] if periods else None
        if not latest_period:
            print("  기간 없음")
            all_results[name] = {"extracted": 0, "matched": 0, "rate": 0}
            continue

        print(f"  최신 기간: {latest_period}")
        print(f"  대상 topic: {found_topics}")

        total_extracted = 0
        total_matched = 0
        all_matches = []

        for topic in found_topics:
            topic_rows = sections.filter(
                (pl.col("topic") == topic) &
                (pl.col("blockType") == "text")
            )
            if len(topic_rows) == 0:
                continue

            # 텍스트 합치기
            texts = topic_rows[latest_period].drop_nulls().to_list()
            full_text = "\n".join(str(t) for t in texts if t)

            # 금액 추출
            amounts = extract_amounts_from_text(full_text)
            print(f"\n  [{topic}] 추출된 금액: {len(amounts)}개")
            for a in amounts[:5]:
                print(f"    · {a['raw']} → {a['value_억']:,.0f}억")
            if len(amounts) > 5:
                print(f"    ... 외 {len(amounts)-5}개")

            # finance 매칭
            finance_vals = get_finance_amounts(c, latest_period)
            print(f"  finance 계정 수: {len(finance_vals)}개")

            matches = match_amounts(amounts, finance_vals)
            print(f"  매칭된 금액: {len(matches)}개 / {len(amounts)}개 ({len(matches)/max(len(amounts),1)*100:.1f}%)")
            for m in matches[:5]:
                print(f"    ✓ '{m['text_raw']}' ({m['text_value_억']:,.0f}억) → {m['finance_account']} ({m['finance_value_억']:,.0f}억) 오차 {m['error']}%")

            total_extracted += len(amounts)
            total_matched += len(matches)
            all_matches.extend(matches)

        rate = total_matched / max(total_extracted, 1) * 100
        print(f"\n  [종합] 추출 {total_extracted}개, 매칭 {total_matched}개, 매칭률 {rate:.1f}%")

        all_results[name] = {
            "extracted": total_extracted,
            "matched": total_matched,
            "rate": round(rate, 1),
            "topics": found_topics,
            "matches": all_matches,
        }

    # 종합
    print(f"\n{'='*60}")
    print("종합 결과")
    print(f"{'='*60}")
    total_ext = sum(r["extracted"] for r in all_results.values())
    total_mat = sum(r["matched"] for r in all_results.values())
    overall_rate = total_mat / max(total_ext, 1) * 100

    for name, r in all_results.items():
        print(f"  {name}: 추출 {r['extracted']}개, 매칭 {r['matched']}개 ({r['rate']}%)")

    print(f"\n  전체: 추출 {total_ext}개, 매칭 {total_mat}개, 전체 매칭률 {overall_rate:.1f}%")

    if total_mat > 0:
        avg_error = sum(m["error"] for r in all_results.values() for m in r.get("matches", [])) / total_mat
        print(f"  평균 오차: {avg_error:.2f}%")
