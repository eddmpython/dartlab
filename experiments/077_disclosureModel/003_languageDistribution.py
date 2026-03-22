"""
실험 ID: 003
실험명: 한/영 비율 측정

목적:
- 코퍼스의 한국어/영어 비율을 정확히 측정
- bilingual 학습 전략의 비율 결정 근거 확보
- 혼합 언어 텍스트 존재 여부 확인

가설:
1. DART = 99%+ 한국어, EDGAR = 99%+ 영어
2. 혼합 언어(한영 섞인 텍스트)는 5% 미만
3. 전체 코퍼스 기준 영어 60-70% (EDGAR 회사 수가 3배)

방법:
1. 30개사 샘플 (DART 15 + EDGAR 15)에서 텍스트 블록 추출
2. 각 텍스트의 한글 문자 비율로 언어 판정
   - 한글 50%+ → 한국어
   - 한글 5% 미만 → 영어
   - 나머지 → 혼합
3. 문자 수 기준 비율 산출

결과 (실행 후 작성):

결론 (실행 후 작성):

실험일: 2026-03-20
"""

import random
import re
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from dartlab.config import dataDir


def _period_cols(df: pl.DataFrame) -> list[str]:
    return [c for c in df.columns if re.match(r"^\d{4}(Q[1-4])?$", c)]


def _load_sections(code: str, market: str) -> pl.DataFrame | None:
    try:
        if market == "DART":
            from dartlab.engines.company.dart.docs.sections.pipeline import sections
        else:
            from dartlab.engines.company.edgar.docs.sections.pipeline import sections
        return sections(code)
    except Exception:
        return None


def _classify_language(text: str) -> str:
    """텍스트의 한글 비율로 언어 판정."""
    if not text or len(text.strip()) < 10:
        return "empty"
    # 한글 유니코드 범위
    korean_chars = sum(1 for c in text if "\uac00" <= c <= "\ud7a3" or "\u3131" <= c <= "\u318e")
    alpha_chars = sum(1 for c in text if c.isalpha())
    if alpha_chars == 0:
        return "numeric"
    ratio = korean_chars / alpha_chars
    if ratio >= 0.5:
        return "korean"
    elif ratio < 0.05:
        return "english"
    else:
        return "mixed"


def main():
    data = Path(dataDir)
    random.seed(42)

    # 샘플 선택
    dart_files = sorted((data / "dart" / "docs").glob("*.parquet"))
    edgar_files = sorted((data / "edgar" / "docs").glob("*.parquet"))

    dart_sample = random.sample(dart_files, min(15, len(dart_files)))
    edgar_sample = random.sample(edgar_files, min(15, len(edgar_files)))

    total_stats = {"korean": 0, "english": 0, "mixed": 0, "empty": 0, "numeric": 0}
    market_stats = {
        "DART": {"korean": 0, "english": 0, "mixed": 0, "total_chars": 0, "korean_chars": 0},
        "EDGAR": {"korean": 0, "english": 0, "mixed": 0, "total_chars": 0, "korean_chars": 0},
    }

    for market, samples in [("DART", dart_sample), ("EDGAR", edgar_sample)]:
        print(f"\n--- {market} ({len(samples)} samples) ---")
        for f in samples:
            df = _load_sections(f.stem, market)
            if df is None:
                print(f"  {f.stem}: skip (no data)")
                continue

            periods = _period_cols(df)
            text_df = df.filter(pl.col("blockType") == "text")
            counts = {"korean": 0, "english": 0, "mixed": 0, "empty": 0, "numeric": 0}

            for p in periods:
                if p not in text_df.columns:
                    continue
                vals = text_df[p].drop_nulls().to_list()
                for v in vals:
                    if not v:
                        continue
                    lang = _classify_language(v)
                    counts[lang] += 1
                    total_stats[lang] += 1

                    # 문자 수 집계
                    char_count = len(v)
                    korean_count = sum(1 for c in v if "\uac00" <= c <= "\ud7a3")
                    market_stats[market]["total_chars"] += char_count
                    market_stats[market]["korean_chars"] += korean_count

            market_stats[market]["korean"] += counts["korean"]
            market_stats[market]["english"] += counts["english"]
            market_stats[market]["mixed"] += counts["mixed"]

            total = sum(counts.values())
            if total > 0:
                print(
                    f"  {f.stem}: {total} blocks — "
                    f"kr:{counts['korean']} en:{counts['english']} "
                    f"mix:{counts['mixed']} empty:{counts['empty']}"
                )

    # 전체 결과
    print(f"\n{'='*60}")
    meaningful = total_stats["korean"] + total_stats["english"] + total_stats["mixed"]
    if meaningful > 0:
        print(f"전체 텍스트 블록: {meaningful}")
        print(f"  한국어: {total_stats['korean']} ({total_stats['korean']/meaningful*100:.1f}%)")
        print(f"  영어: {total_stats['english']} ({total_stats['english']/meaningful*100:.1f}%)")
        print(f"  혼합: {total_stats['mixed']} ({total_stats['mixed']/meaningful*100:.1f}%)")

    for market in ["DART", "EDGAR"]:
        ms = market_stats[market]
        blocks = ms["korean"] + ms["english"] + ms["mixed"]
        if blocks > 0:
            print(f"\n{market}:")
            print(f"  블록: kr:{ms['korean']} en:{ms['english']} mix:{ms['mixed']}")
            print(f"  총 문자: {ms['total_chars']:,}")
            print(f"  한글 문자: {ms['korean_chars']:,}")
            if ms["total_chars"] > 0:
                print(f"  한글 비율: {ms['korean_chars']/ms['total_chars']*100:.1f}%")


if __name__ == "__main__":
    main()
