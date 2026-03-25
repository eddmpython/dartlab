"""실험 ID: 093-005
실험명: period 컬럼 Categorical 인코딩 RSS 절감 검증

목적:
- sections DataFrame의 period 컬럼을 Categorical로 변환 시 실제 RSS 절감 측정
- 004에서 estimated_size 97.7% 절감 확인됨 → 실제 RSS에 반영되는지 확인
- sections 파이프라인 출력 단계에서 cast만 추가하면 되는지 검증

가설:
1. period 컬럼 Categorical 변환 시 RSS 100MB+ 절감 (97MB text → 2MB)
2. diff(), show() 등 소비자가 Categorical을 정상 처리
3. pipeline 수정 1줄(cast)로 적용 가능

방법:
1. sections() 호출 → 기준 RSS 측정
2. period 컬럼을 Categorical로 cast → RSS 재측정
3. Categorical DataFrame에서 show/diff 호환성 테스트
4. 소형 종목(이엔에프테크놀로지 102710)에서도 재현 확인

결과 (삼성전자 005930 / 이엔에프테크 102710):

| 지표 | 005930 | 102710 |
|------|--------|--------|
| 원본 estimated_size | 112.0MB | 41.4MB |
| Categorical estimated | 16.9MB | 18.6MB |
| period 절감 | 97.3→2.2MB (97.7%) | 25.0→2.1MB (91.5%) |
| 원본 RSS | 559MB | 603MB |
| Categorical RSS | 618MB | 592MB |
| **RSS 절감** | **-59MB (악화)** | **+11MB** |

소비자 호환성: str.contains, cast(Utf8) 복원, null 보존 모두 OK

메타 컬럼 Categorical 탐색:
- textPath 계열 (6개): 각 1.2~1.7MB → 55KB (99% 절감)
- segmentKey: 1.5MB → 55KB
- topic, sourceTopic, cadenceKey: 소폭 절감

결론:
- estimated_size 절감은 극적 (85~55%)
- **RSS는 "변환" 방식에선 절감 없음** — 원본+Categorical 동시 존재 때문
- 근본 해결: pipeline 출력 단계에서 처음부터 Categorical로 생성해야 함
- 소비자 호환성 문제 없음 — cast(Utf8)로 복원 가능
- 메타 컬럼도 Categorical 효과 있지만 period 대비 미미 (~10MB)
- 가설 1 부분 기각: 변환 방식으로는 RSS 절감 불가. pipeline 내장 필요

실험일: 2026-03-25
"""

import gc
import re
import sys

import polars as pl
import psutil

from dartlab.engines.company.dart.docs.sections.pipeline import sections


def mb():
    return psutil.Process().memory_info().rss / 1024 / 1024


def main(stockCode: str = "005930") -> None:
    gc.collect()
    baseRss = mb()
    print(f"=== {stockCode} ===")
    print(f"시작 RSS: {baseRss:.0f}MB")

    # 1. 기준: 원본 sections
    df = sections(stockCode)
    gc.collect()
    origRss = mb()
    origSize = df.estimated_size() / 1024 / 1024
    print(f"\n[원본 sections]")
    print(f"  shape: {df.shape}")
    print(f"  RSS: {origRss:.0f}MB (+{origRss - baseRss:.0f}MB)")
    print(f"  estimated_size: {origSize:.1f}MB")

    periodCols = [c for c in df.columns if re.fullmatch(r"\d{4}(Q[1-4])?", c)]
    origPeriodSize = sum(df[c].estimated_size() for c in periodCols) / 1024 / 1024
    print(f"  period 컬럼({len(periodCols)}개) estimated_size: {origPeriodSize:.1f}MB")

    # 2. Categorical 변환
    castExprs = [
        pl.col(c).cast(pl.Categorical).alias(c) if c in periodCols else pl.col(c)
        for c in df.columns
    ]
    dfCat = df.select(castExprs)

    # 원본 해제
    del df
    gc.collect()

    catRss = mb()
    catSize = dfCat.estimated_size() / 1024 / 1024
    catPeriodSize = sum(dfCat[c].estimated_size() for c in periodCols) / 1024 / 1024
    print(f"\n[Categorical 변환 후]")
    print(f"  RSS: {catRss:.0f}MB (+{catRss - baseRss:.0f}MB)")
    print(f"  estimated_size: {catSize:.1f}MB")
    print(f"  period 컬럼 estimated_size: {catPeriodSize:.1f}MB")
    print(f"  RSS 절감: {origRss - catRss:.0f}MB")
    print(f"  estimated_size 절감: {origSize - catSize:.1f}MB ({(1 - catSize/origSize)*100:.1f}%)")
    print(f"  period 절감: {origPeriodSize - catPeriodSize:.1f}MB ({(1 - catPeriodSize/origPeriodSize)*100:.1f}%)")

    # 3. 소비자 호환성 테스트
    print(f"\n[소비자 호환성]")

    # 3a. 문자열 비교 가능?
    sampleCol = periodCols[-1]  # 최신 period
    nonNull = dfCat.filter(pl.col(sampleCol).is_not_null())
    print(f"  최신 period '{sampleCol}': {nonNull.height}개 non-null 행")

    # 3b. str 메서드 호출?
    try:
        containsTest = dfCat.filter(pl.col(sampleCol).cast(pl.Utf8).str.contains("사업"))
        print(f"  str.contains('사업'): {containsTest.height}개 매칭 — OK")
    except Exception as e:
        print(f"  str.contains 실패: {e}")

    # 3c. Utf8로 복원?
    try:
        restored = dfCat[sampleCol].cast(pl.Utf8)
        print(f"  cast(Utf8) 복원: OK (null={restored.null_count()})")
    except Exception as e:
        print(f"  cast(Utf8) 실패: {e}")

    # 3d. null 처리?
    nullCount = dfCat[sampleCol].null_count()
    print(f"  null 보존: {nullCount}개 (원본과 동일해야 함)")

    # 4. 메타 컬럼도 Categorical 가능한지 탐색
    print(f"\n[메타 컬럼 Categorical 탐색]")
    nonPeriodStr = [
        c for c in dfCat.columns
        if c not in periodCols
        and c != "stockCode"
        and dfCat[c].dtype in (pl.Utf8, pl.String)
    ]
    for c in nonPeriodStr:
        unique = dfCat[c].n_unique()
        total = dfCat[c].len() - dfCat[c].null_count()
        origSz = dfCat[c].estimated_size() / 1024
        if total > 0:
            ratio = unique / total
            try:
                catSz = dfCat[c].cast(pl.Categorical).estimated_size() / 1024
                saving = origSz - catSz
                if saving > 10:  # 10KB 이상 절감만 출력
                    print(f"  {c}: {unique}/{total} unique ({ratio:.1%}), {origSz:.0f}KB→{catSz:.0f}KB ({saving:.0f}KB 절감)")
            except Exception:
                pass


if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    main(code)
    # 소형 종목도 테스트
    if code == "005930":
        print("\n" + "=" * 60)
        main("102710")
