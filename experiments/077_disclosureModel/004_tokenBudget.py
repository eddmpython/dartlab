"""
실험 ID: 004
실험명: 정확한 토큰 카운트 (tokenizer 기반)

목적:
- tiktoken으로 정확한 토큰 수 측정
- 파인튜닝 예상 시간/비용 산출 근거 확보
- 목표: 10M+ 토큰이면 7B 파인튜닝 가능

가설:
1. 총 코퍼스 50M+ 토큰 (문자 수의 ~1/4 기준)
2. 한국어 토큰 효율이 영어보다 낮음 (같은 의미를 더 많은 토큰으로)
3. 텍스트 토큰이 전체의 70%+ (테이블은 구조 오버헤드가 큼)

방법:
1. tiktoken cl100k_base 토크나이저 사용 (GPT-4 호환, 근사치)
2. 30개사 샘플에서 문자당 토큰 비율(chars_per_token) 측정
3. 001의 총 문자 수 × 비율로 전체 토큰 추정
4. text/table별 토큰 효율 비교

결과 (실행 후 작성):

결론 (실행 후 작성):

실험일: 2026-03-20
"""

import sys
import re
import random
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
            from dartlab.engines.dart.docs.sections.pipeline import sections
        else:
            from dartlab.engines.edgar.docs.sections.pipeline import sections
        return sections(code)
    except Exception:
        return None


def main():
    try:
        import tiktoken
    except ImportError:
        print("tiktoken not installed. Run: uv pip install tiktoken")
        print("Falling back to character-based estimation (÷4 for English, ÷2 for Korean)")
        _use_tiktoken = False
        enc = None
    else:
        _use_tiktoken = True
        enc = tiktoken.get_encoding("cl100k_base")

    data = Path(dataDir)
    random.seed(42)

    dart_files = sorted((data / "dart" / "docs").glob("*.parquet"))
    edgar_files = sorted((data / "edgar" / "docs").glob("*.parquet"))
    dart_sample = random.sample(dart_files, min(15, len(dart_files)))
    edgar_sample = random.sample(edgar_files, min(15, len(edgar_files)))

    stats = {
        "DART": {"text_chars": 0, "text_tokens": 0, "table_chars": 0, "table_tokens": 0},
        "EDGAR": {"text_chars": 0, "text_tokens": 0, "table_chars": 0, "table_tokens": 0},
    }

    for market, samples in [("DART", dart_sample), ("EDGAR", edgar_sample)]:
        print(f"\n--- {market} ({len(samples)} samples) ---")
        for f in samples:
            df = _load_sections(f.stem, market)
            if df is None:
                continue

            periods = _period_cols(df)
            for block_type in ["text", "table"]:
                sub = df.filter(pl.col("blockType") == block_type)
                chars_key = f"{block_type}_chars"
                tokens_key = f"{block_type}_tokens"

                for p in periods:
                    if p not in sub.columns:
                        continue
                    vals = sub[p].drop_nulls().to_list()
                    for v in vals:
                        if not v:
                            continue
                        stats[market][chars_key] += len(v)
                        if _use_tiktoken:
                            stats[market][tokens_key] += len(enc.encode(v))
                        else:
                            # 한국어 근사: ÷2, 영어: ÷4
                            kr = sum(1 for c in v if "\uac00" <= c <= "\ud7a3")
                            ratio = kr / max(len(v), 1)
                            factor = 2 if ratio > 0.3 else 4
                            stats[market][tokens_key] += len(v) // factor

            total_chars = stats[market]["text_chars"] + stats[market]["table_chars"]
            total_tokens = stats[market]["text_tokens"] + stats[market]["table_tokens"]
            cpt = total_chars / total_tokens if total_tokens else 0
            print(f"  {f.stem}: {total_chars:,} chars, {total_tokens:,} tokens (cpt={cpt:.2f})")

    # 결과
    print(f"\n{'='*60}")
    for market in ["DART", "EDGAR"]:
        s = stats[market]
        total_chars = s["text_chars"] + s["table_chars"]
        total_tokens = s["text_tokens"] + s["table_tokens"]
        cpt = total_chars / total_tokens if total_tokens else 0
        text_cpt = s["text_chars"] / s["text_tokens"] if s["text_tokens"] else 0
        table_cpt = s["table_chars"] / s["table_tokens"] if s["table_tokens"] else 0

        print(f"\n{market} (sample):")
        print(f"  총 문자: {total_chars:,}")
        print(f"  총 토큰: {total_tokens:,}")
        print(f"  chars/token: {cpt:.2f}")
        print(f"  text chars/token: {text_cpt:.2f}")
        print(f"  table chars/token: {table_cpt:.2f}")
        print(f"  text 토큰 비율: {s['text_tokens']/total_tokens*100:.1f}%" if total_tokens else "")

    # 전체 추정 (001 결과 기반)
    # 001에서 총 문자 수를 모르므로, 샘플 chars/token 비율로 추정
    dart_s = stats["DART"]
    edgar_s = stats["EDGAR"]
    dart_total = dart_s["text_chars"] + dart_s["table_chars"]
    edgar_total = edgar_s["text_chars"] + edgar_s["table_chars"]
    dart_tokens = dart_s["text_tokens"] + dart_s["table_tokens"]
    edgar_tokens = edgar_s["text_tokens"] + edgar_s["table_tokens"]

    dart_cpt = dart_total / dart_tokens if dart_tokens else 2
    edgar_cpt = edgar_total / edgar_tokens if edgar_tokens else 4

    # 319 DART 중 15 샘플, 974 EDGAR 중 15 샘플 → 스케일 추정
    dart_scale = 319 / min(15, len(dart_files))
    edgar_scale = 974 / min(15, len(edgar_files))

    estimated_dart_tokens = int(dart_tokens * dart_scale)
    estimated_edgar_tokens = int(edgar_tokens * edgar_scale)
    estimated_total = estimated_dart_tokens + estimated_edgar_tokens

    print(f"\n--- 전체 추정 ---")
    print(f"DART ({319}개사): ~{estimated_dart_tokens:,} tokens")
    print(f"EDGAR ({974}개사): ~{estimated_edgar_tokens:,} tokens")
    print(f"합계: ~{estimated_total:,} tokens ({estimated_total/1_000_000:.1f}M)")
    print(f"파인튜닝 가능 기준 10M: {'충분' if estimated_total > 10_000_000 else '부족'}")


if __name__ == "__main__":
    main()
