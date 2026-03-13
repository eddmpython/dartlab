"""
실험 ID: 058-006
실험명: EDGAR Company 4-namespace 전종목 검증

목적:
- 패키지에 반영된 EDGAR Company의 docs/finance namespace가 전종목에서 동작하는지 검증한다.

가설:
1. docs.sections는 docs parquet가 있는 모든 ticker에서 동작한다.
2. finance.BS/IS/CF는 companyfacts가 있는 모든 ticker에서 동작한다.
3. show()는 에러 없이 동작한다.

방법:
1. data/edgar/docs/*.parquet 전체 ticker에서 Company 생성
2. docs.sections, finance.BS, show 동작 확인
3. 에러/None/성공 분류

결과 (실험 후 작성):

결론:

실험일: 2026-03-13
"""

from __future__ import annotations

import traceback
from pathlib import Path

from dartlab import config


def main() -> None:
    docsDir = Path(config.dataDir) / "edgar" / "docs"
    files = sorted(docsDir.glob("*.parquet"))
    tickers = [f.stem for f in files]

    print(f"=== 058-006 EDGAR Company 전종목 검증 ===")
    print(f"tickers with docs: {len(tickers)}\n")

    from dartlab.engines.edgar.company import Company

    success = 0
    noFinance = 0
    errors: list[tuple[str, str]] = []

    for i, ticker in enumerate(tickers):
        try:
            c = Company(ticker)
            sec = c.docs.sections
            bs = c.finance.BS
            text = c.show("10-K::item1Business") if sec is not None else None

            secShape = f"{sec.height}x{len(sec.columns)-1}" if sec is not None else "None"
            bsShape = f"{bs.height}x{len(bs.columns)-1}" if bs is not None else "None"
            textLen = len(text) if text else 0

            success += 1
            if (i + 1) % 50 == 0 or i == 0:
                print(f"  [{i+1}/{len(tickers)}] {ticker} sec={secShape} bs={bsShape} business={textLen}")

        except ValueError as e:
            if "재무 데이터 없음" in str(e) or "CIK를 찾을 수 없음" in str(e):
                noFinance += 1
                if (i + 1) % 100 == 0:
                    print(f"  [{i+1}/{len(tickers)}] {ticker} → {e}")
            else:
                errors.append((ticker, str(e)))
                print(f"  [{i+1}/{len(tickers)}] {ticker} → ERROR: {e}")
        except Exception as e:
            errors.append((ticker, traceback.format_exc()))
            print(f"  [{i+1}/{len(tickers)}] {ticker} → ERROR: {e}")

    print(f"\n=== RESULT ===")
    print(f"success: {success}")
    print(f"no finance/CIK: {noFinance}")
    print(f"errors: {len(errors)}")

    if errors:
        print(f"\n--- ERRORS (first 5) ---")
        for ticker, tb in errors[:5]:
            print(f"\n{ticker}: {tb[-300:]}")


if __name__ == "__main__":
    main()
