"""
실험 ID: 062
실험명: docs sections 매퍼 커버리지 전수점검

목적:
- 전체 docs parquet에서 고유 section_title을 수집
- 현재 매퍼의 매핑률을 정확히 측정
- 미매핑 항목의 빈도와 성격을 분석

가설:
1. 매핑률 95%+ 달성 가능
2. 미매핑 항목 대부분은 appendix/detail 또는 저빈도 회사 특화 섹션

방법:
1. eddmpython/data/dartData/docsData + dartlab/data/dart/docs 모든 parquet 로드
2. section_title 고유 목록 추출
3. mapSectionTitle 적용하여 매핑/미매핑 분류
4. 빈도 카운트로 중요도 정렬

결과 (실험 후 작성):

결론:

실험일: 2026-03-14
"""
import sys

sys.stdout.reconfigure(encoding='utf-8')

from collections import Counter
from pathlib import Path

import polars as pl

from dartlab.providers.dart.docs.sections.mapper import mapSectionTitle, normalizeSectionTitle

# docs parquet 디렉토리 (두 곳 합산)
DATA_DIRS = [
    Path(r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"),
    Path(r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\data\dart\docs"),
]

docs_files = []
seen = set()
for d in DATA_DIRS:
    if d.exists():
        for f in sorted(d.glob("*.parquet")):
            if f.name not in seen:
                docs_files.append(f)
                seen.add(f.name)

print(f"docs parquet 파일 수: {len(docs_files)} (중복 제거)")
print(f"  eddmpython: {sum(1 for f in docs_files if 'eddmpython' in str(f))}")
print(f"  dartlab:    {sum(1 for f in docs_files if 'dartlab' in str(f))}")

# 모든 파일에서 section_title 수집
all_titles = set()
title_counts = Counter()  # normalized title -> 출현 행 수
file_title_counts = Counter()  # normalized title -> 출현 파일 수
sample_count = 0
error_count = 0

for f in docs_files:
    try:
        df = pl.read_parquet(f, columns=["section_title"])
        titles = df.get_column("section_title").to_list()
        all_titles.update(titles)

        # 빈도 카운트
        file_seen = set()
        for t in titles:
            n = normalizeSectionTitle(t)
            title_counts[n] += 1
            if n not in file_seen:
                file_title_counts[n] += 1
                file_seen.add(n)

        sample_count += 1
    except Exception as e:
        error_count += 1
        print(f"  에러: {f.name} - {e}")

print(f"\n처리된 파일: {sample_count}, 에러: {error_count}")
print(f"고유 원본 section_title 수: {len(all_titles)}")

# 정규화 후 고유 수
normalized_titles = set()
for t in all_titles:
    normalized_titles.add(normalizeSectionTitle(t))
print(f"고유 정규화 section_title 수: {len(normalized_titles)}")

# 매핑 결과 분석
mapped = {}
unmapped = {}
for title in sorted(all_titles):
    norm = normalizeSectionTitle(title)
    result = mapSectionTitle(title)
    if result != norm:  # 매핑됨
        mapped[norm] = result
    else:
        if norm not in unmapped:
            unmapped[norm] = title  # 원본 예시 보관

# 행 수 기준 매핑률
total_rows = sum(title_counts.values())
mapped_rows = sum(title_counts[n] for n in title_counts if n in mapped)
unmapped_rows = total_rows - mapped_rows

# 파일 수 기준도 계산
total_unique = len(normalized_titles)
mapped_count = len(mapped)
unmapped_count = len(unmapped)
rate = mapped_count / total_unique * 100 if total_unique > 0 else 0

print(f"\n{'='*60}")
print(f"=== 매핑률 (고유 정규화 타이틀 기준) ===")
print(f"{'='*60}")
print(f"전체 고유 타이틀: {total_unique}")
print(f"매핑됨:          {mapped_count} ({rate:.1f}%)")
print(f"미매핑:          {unmapped_count} ({100-rate:.1f}%)")

row_rate = mapped_rows / total_rows * 100 if total_rows > 0 else 0
print(f"\n=== 매핑률 (행 수 기준) ===")
print(f"전체 행:    {total_rows:,}")
print(f"매핑됨:     {mapped_rows:,} ({row_rate:.1f}%)")
print(f"미매핑:     {unmapped_rows:,} ({100-row_rate:.1f}%)")

# 미매핑 항목 출력 (빈도순)
if unmapped:
    print(f"\n{'='*60}")
    print(f"=== 미매핑 항목 ({len(unmapped)}개, 출현 파일수 기준 정렬) ===")
    print(f"{'='*60}")

    unmapped_by_freq = sorted(
        [(n, file_title_counts[n], title_counts[n], unmapped[n]) for n in unmapped],
        key=lambda x: (-x[1], -x[2])
    )

    for i, (norm, file_count, row_count, original) in enumerate(unmapped_by_freq):
        print(f"  {i+1:3d}. [{file_count:3d}사/{row_count:5d}행] {norm}")
        if norm != original:
            print(f"       원본예: {original}")

# 매핑된 topic별 통계
if mapped:
    print(f"\n{'='*60}")
    print(f"=== 매핑된 topic 분포 (상위 30) ===")
    print(f"{'='*60}")

    topic_stats = Counter()
    topic_file_stats = Counter()
    for norm, topic in mapped.items():
        topic_stats[topic] += title_counts[norm]
        topic_file_stats[topic] += file_title_counts[norm]

    for topic, count in topic_stats.most_common(30):
        file_c = topic_file_stats[topic]
        print(f"  {topic:40s}  {file_c:4d}사  {count:6d}행")

if __name__ == '__main__':
    pass
