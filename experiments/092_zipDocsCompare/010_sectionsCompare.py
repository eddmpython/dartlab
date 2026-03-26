"""실험 ID: 010
실험명: collector vs ZIP 전체 기간 sections 품질 최종 비교

목적:
- 009에서 수집한 collector_full / zip_full parquet으로 sections를 각각 생성
- topic, 기간축, 텍스트 품질, 블록 구조를 정량 비교
- ZIP이 sections 품질에서 collector 이상인지 최종 판정

가설:
1. 소분류 기준 sections는 ZIP이 collector와 95%+ 동등할 것이다
2. ZIP은 추가 섹션(대표이사확인 등)으로 topic 커버리지가 더 넓을 것이다

방법:
1. 두 parquet을 임시로 dataDir에 복사 → sections() 호출
2. 또는 sections 핵심 함수를 직접 호출하여 비교
3. topic × period 행 수, 텍스트 길이, 누락 기간 비교

결과 (실험 후 작성):
- (실행 후 채울 것)

결론:
- (실행 후 채울 것)

실험일: 2026-03-24
"""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

import polars as pl

TEMP_DIR = Path(__file__).parent / "temp"


def _buildSections(parquetPath: Path, label: str) -> pl.DataFrame:
    """parquet → sections (임시 dataDir로 우회)."""
    from dartlab import config
    from dartlab.core.dataConfig import DATA_RELEASES

    # 임시 디렉토리에 복사
    tmpDir = Path(tempfile.mkdtemp(prefix=f"dartlab_{label}_"))
    docsDir = tmpDir / DATA_RELEASES["docs"]["dir"]
    docsDir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(parquetPath, docsDir / "005930.parquet")

    # dataDir 임시 전환
    origDataDir = config.dataDir
    config.dataDir = str(tmpDir)

    try:
        from dartlab.providers.dart.docs.sections.pipeline import sections
        result = sections("005930")
        return result
    finally:
        config.dataDir = origDataDir
        shutil.rmtree(tmpDir, ignore_errors=True)


def main():
    collPath = TEMP_DIR / "collector_full.parquet"
    zipPath = TEMP_DIR / "zip_full.parquet"

    if not collPath.exists() or not zipPath.exists():
        print("temp/ 파일 없음. 009 먼저 실행")
        return

    print("=" * 100)
    print("collector vs ZIP — sections 최종 비교")
    print("=" * 100)

    # sections 생성
    print("\n[1] collector parquet → sections...")
    collSections = _buildSections(collPath, "coll")
    print(f"  완료: {collSections.height}행, {len(collSections.columns)}컬럼")

    print("\n[2] ZIP parquet → sections...")
    zipSections = _buildSections(zipPath, "zip")
    print(f"  완료: {zipSections.height}행, {len(zipSections.columns)}컬럼")

    # 저장
    collSections.write_parquet(TEMP_DIR / "sections_collector.parquet")
    zipSections.write_parquet(TEMP_DIR / "sections_zip.parquet")
    print(f"\n  sections_collector.parquet: {collSections.height}행")
    print(f"  sections_zip.parquet:      {zipSections.height}행")

    # ── 비교 ──

    # period 컬럼 추출 (숫자로 시작하는 컬럼들 = 기간 데이터)
    periodCols = [c for c in collSections.columns if re.match(r"^\d{4}", c)]
    zipPeriodCols = [c for c in zipSections.columns if re.match(r"^\d{4}", c)]

    print("\n" + "=" * 100)
    print("3. 기본 통계")
    print("=" * 100)
    print(f"  collector sections: {collSections.height}행, 기간 {len(periodCols)}개 {sorted(periodCols)[:5]}...{sorted(periodCols)[-3:]}")
    print(f"  ZIP sections:      {zipSections.height}행, 기간 {len(zipPeriodCols)}개 {sorted(zipPeriodCols)[:5]}...{sorted(zipPeriodCols)[-3:]}")

    # topic 비교
    collTopics = set(collSections["topic"].unique().to_list())
    zipTopics = set(zipSections["topic"].unique().to_list())
    commonTopics = collTopics & zipTopics

    print(f"\n  collector topic: {len(collTopics)}개")
    print(f"  ZIP topic:       {len(zipTopics)}개")
    print(f"  공통:            {len(commonTopics)}개")

    zipOnly = zipTopics - collTopics
    collOnly = collTopics - zipTopics
    if zipOnly:
        print(f"  ZIP에만: {sorted(zipOnly)}")
    if collOnly:
        print(f"  coll에만: {sorted(collOnly)}")

    # ── 4. topic별 행 수 비교 ──
    print("\n" + "=" * 100)
    print("4. topic별 행 수 비교 (공통 topic)")
    print("=" * 100)

    collByTopic = collSections.group_by("topic").len().rename({"len": "coll"}).sort("topic")
    zipByTopic = zipSections.group_by("topic").len().rename({"len": "zip"}).sort("topic")
    topicMerge = collByTopic.join(zipByTopic, on="topic", how="full", coalesce=True)
    topicMerge = topicMerge.with_columns([
        pl.col("coll").fill_null(0),
        pl.col("zip").fill_null(0),
    ]).sort("topic")

    print(f"{'topic':40s} | {'coll':>5s} | {'zip':>5s} | 차이")
    print("-" * 65)
    for row in topicMerge.iter_rows(named=True):
        diff = row["zip"] - row["coll"]
        diffStr = f"{diff:+d}" if diff != 0 else "="
        print(f"  {row['topic'][:40]:40s} | {row['coll']:5d} | {row['zip']:5d} | {diffStr}")

    # ── 5. 기간별 텍스트 존재율 비교 ──
    print("\n" + "=" * 100)
    print("5. 기간별 텍스트 존재율 (null이 아닌 비율)")
    print("=" * 100)

    commonPeriods = sorted(set(periodCols) & set(zipPeriodCols))
    print(f"{'기간':12s} | {'coll존재':>8s} {'coll총':>6s} {'coll%':>6s} | {'zip존재':>8s} {'zip총':>6s} {'zip%':>6s}")
    print("-" * 75)

    for period in commonPeriods[-12:]:  # 최근 12개 기간
        cNotNull = collSections[period].is_not_null().sum()
        cTotal = collSections.height
        zNotNull = zipSections[period].is_not_null().sum() if period in zipSections.columns else 0
        zTotal = zipSections.height

        cPct = cNotNull / cTotal * 100 if cTotal else 0
        zPct = zNotNull / zTotal * 100 if zTotal else 0

        print(f"  {period:12s} | {cNotNull:8d} {cTotal:6d} {cPct:5.1f}% | {zNotNull:8d} {zTotal:6d} {zPct:5.1f}%")

    # ── 6. 동일 topic×period 텍스트 유사도 샘플 ──
    print("\n" + "=" * 100)
    print("6. 동일 topic × period 텍스트 비교 (최근 연간, 샘플 10개)")
    print("=" * 100)

    from difflib import SequenceMatcher

    # 최근 연간 기간
    latestAnnual = [p for p in commonPeriods if not "Q" in p]
    if latestAnnual:
        targetPeriod = latestAnnual[-1]
    else:
        targetPeriod = commonPeriods[-1] if commonPeriods else None

    if targetPeriod and targetPeriod in collSections.columns and targetPeriod in zipSections.columns:
        print(f"  비교 기간: {targetPeriod}")

        # topic으로 조인
        collSub = collSections.select("topic", "blockType", "blockOrder", targetPeriod).rename({targetPeriod: "coll_text"})
        zipSub = zipSections.select("topic", "blockType", "blockOrder", targetPeriod).rename({targetPeriod: "zip_text"})

        joined = collSub.join(zipSub, on=["topic", "blockType", "blockOrder"], how="inner")
        # 둘 다 null 아닌 것만
        both = joined.filter(pl.col("coll_text").is_not_null() & pl.col("zip_text").is_not_null())

        print(f"  양쪽 모두 텍스트 있는 행: {both.height}개")

        sims = []
        for i, row in enumerate(both.iter_rows(named=True)):
            if i >= 10:
                break
            cText = row["coll_text"] or ""
            zText = row["zip_text"] or ""
            sim = SequenceMatcher(None, cText[:2000], zText[:2000]).ratio()
            sims.append(sim)
            print(f"    {row['topic'][:30]:30s} {row['blockType']:>6s} [{row['blockOrder']:2d}] | "
                  f"coll {len(cText):>7,}자 zip {len(zText):>7,}자 | 유사도 {sim:.1%}")

        if sims:
            print(f"\n  샘플 평균 유사도: {sum(sims)/len(sims):.1%}")

        # 전체 유사도 (빠른 근사)
        allSims = []
        for row in both.head(100).iter_rows(named=True):
            cText = row["coll_text"] or ""
            zText = row["zip_text"] or ""
            if len(cText) > 0 and len(zText) > 0:
                sim = SequenceMatcher(None, cText[:1000], zText[:1000]).ratio()
                allSims.append(sim)
        if allSims:
            print(f"  상위 100행 평균 유사도: {sum(allSims)/len(allSims):.1%}")

    # ── 최종 판정 ──
    print("\n" + "=" * 100)
    print("최종 판정")
    print("=" * 100)
    print(f"  sections 행 수: collector {collSections.height} vs ZIP {zipSections.height}")
    print(f"  topic 수: collector {len(collTopics)} vs ZIP {len(zipTopics)}")
    print(f"  기간 수: collector {len(periodCols)} vs ZIP {len(zipPeriodCols)}")
    if zipOnly:
        print(f"  ZIP 추가 topic: {sorted(zipOnly)}")
    if collOnly:
        print(f"  collector 추가 topic: {sorted(collOnly)}")


if __name__ == "__main__":
    main()
