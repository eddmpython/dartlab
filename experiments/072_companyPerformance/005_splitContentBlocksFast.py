"""
실험 ID: 005
실험명: _splitContentBlocks 최적화

목적:
- _splitContentBlocks가 sections 빌드의 텍스트 파싱 부분 (약 0.74s)
- splitlines + line-by-line startswith("|") 반복
- 최적화: early return 개선 + 단순화

가설:
1. 대부분 content에 "|"가 없으면 early return → 이미 최적
2. "|" 포함 시에도 현재 로직이 단순해서 큰 개선 여지 적음
3. 가능하면 0.74s → 0.5s (30% 절감)

방법:
1. 삼성전자(005930) sections 빌드에서 _splitContentBlocks 호출 패턴 분석
2. 최적화 버전 구현 후 before/after 비교
3. 결과 동일성 assert

결과 (실험 후 작성):
- 호출 1,446회, 84.6%가 "|" 포함, 평균 46,913 chars/call
- before avg: 2.74s (전체 sections 빌드)
- after avg: 3.04s (0.9x — 오히려 느려짐)
- isTableFlags 배열 생성 오버헤드가 절감보다 큼

결론:
- **기각**. 현재 구현이 이미 최적. 추가 flag 배열 생성이 역효과
- _splitContentBlocks 자체보다 메인 루프의 dict 조립이 진짜 병목

실험일: 2026-03-19
"""

import sys
import time

sys.path.insert(0, "src")


def main():
    import dartlab
    from dartlab.engines.company.dart.docs.sections import pipeline

    original_fn = pipeline._splitContentBlocks

    # 호출 통계
    call_count = 0
    has_pipe_count = 0
    total_len = 0

    def counting_wrapper(content):
        nonlocal call_count, has_pipe_count, total_len
        call_count += 1
        total_len += len(content)
        if "|" in content:
            has_pipe_count += 1
        return original_fn(content)

    # --- 호출 통계 수집 ---
    pipeline._splitContentBlocks = counting_wrapper
    c1 = dartlab.Company("005930")
    _ = c1.docs.sections
    pipeline._splitContentBlocks = original_fn

    print(f"  호출 횟수: {call_count}")
    print(f"  '|' 포함: {has_pipe_count} ({has_pipe_count/call_count:.1%})")
    print(f"  총 텍스트 길이: {total_len:,} chars")
    print(f"  평균 길이: {total_len/call_count:.0f} chars")

    # --- before ---
    times_before = []
    for i in range(3):
        c = dartlab.Company("005930")
        t0 = time.perf_counter()
        _ = c.docs.sections
        t1 = time.perf_counter()
        times_before.append(t1 - t0)
        print(f"  before #{i+1}: {t1-t0:.4f}s")

    # --- after: 최적화 버전 ---
    def splitContentBlocksFast(content: str) -> list[tuple[str, str]]:
        """최적화 _splitContentBlocks."""
        strippedContent = content.strip()
        if not strippedContent:
            return []
        if "|" not in strippedContent:
            return [("text", strippedContent)]

        # 모든 줄이 테이블인지 빠르게 체크
        lines = strippedContent.splitlines()
        isTableFlags = [bool(line.strip()) and line.strip()[0] == "|" for line in lines]
        nonEmptyFlags = [bool(line.strip()) for line in lines]

        # 모두 테이블이면 early return
        nonEmptyTableCount = sum(1 for t, ne in zip(isTableFlags, nonEmptyFlags) if ne and t)
        nonEmptyCount = sum(nonEmptyFlags)
        if nonEmptyCount > 0 and nonEmptyTableCount == nonEmptyCount:
            return [("table", strippedContent)]

        # 혼합: 원본 로직과 동일
        rows = []
        buffer = []
        currentKind = None

        for raw in lines:
            stripped = raw.strip()
            if not stripped:
                if currentKind == "table":
                    if buffer:
                        text = "\n".join(buffer).strip()
                        if text:
                            rows.append((currentKind, text))
                        buffer = []
                    currentKind = None
                elif currentKind == "text" and buffer:
                    buffer.append("")
                continue

            nextKind = "table" if stripped[0] == "|" else "text"
            if currentKind is None:
                currentKind = nextKind
                buffer.append(stripped)
                continue

            if nextKind != currentKind:
                if buffer:
                    text = "\n".join(buffer).strip()
                    if text:
                        rows.append((currentKind, text))
                    buffer = []
                currentKind = nextKind
            buffer.append(stripped)

        if currentKind and buffer:
            text = "\n".join(buffer).strip()
            if text:
                rows.append((currentKind, text))
        return rows

    pipeline._splitContentBlocks = splitContentBlocksFast

    times_after = []
    for i in range(3):
        c = dartlab.Company("005930")
        t0 = time.perf_counter()
        _ = c.docs.sections
        t1 = time.perf_counter()
        times_after.append(t1 - t0)
        print(f"  after  #{i+1}: {t1-t0:.4f}s")

    pipeline._splitContentBlocks = original_fn

    speedup = (sum(times_before)/3) / (sum(times_after)/3) if sum(times_after) > 0 else float("inf")
    print(f"\n  avg: {sum(times_before)/3:.4f}s → {sum(times_after)/3:.4f}s ({speedup:.1f}x)")


if __name__ == "__main__":
    main()
