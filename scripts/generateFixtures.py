"""벤치마크 종목의 테스트 fixture parquet 생성.

로컬에 있는 finance/docs/report 데이터를 tests/fixtures/로 복사한다.
이미 존재하는 fixture는 건너뛴다 (--force로 덮어쓰기).

사용법:
  uv run python -X utf8 scripts/generateFixtures.py
  uv run python -X utf8 scripts/generateFixtures.py --force
  uv run python -X utf8 scripts/generateFixtures.py --stocks 005930 005380
"""

import argparse
import shutil
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

BENCHMARK_STOCKS = [
    "005930",  # 삼성전자
    "005380",  # 현대자동차
    "055550",  # 신한지주
    "035720",  # 카카오
    "000660",  # SK하이닉스
    "006400",  # 삼성SDI
    "207940",  # 삼성바이오로직스
    "003550",  # LG
    "017670",  # SK텔레콤
    "034730",  # SK
]

CATEGORIES = ["finance", "docs", "report"]


def main():
    parser = argparse.ArgumentParser(description="테스트 fixture parquet 생성")
    parser.add_argument("--force", action="store_true", help="기존 fixture 덮어쓰기")
    parser.add_argument("--stocks", nargs="+", default=None, help="특정 종목만 생성")
    parser.add_argument("--categories", nargs="+", default=None, help="특정 카테고리만")
    args = parser.parse_args()

    from dartlab.core.dataLoader import _dataDir

    stocks = args.stocks or BENCHMARK_STOCKS
    categories = args.categories or CATEGORIES

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    missing = 0

    for code in stocks:
        for cat in categories:
            src = _dataDir(cat) / f"{code}.parquet"
            dst = FIXTURE_DIR / f"{code}.{cat}.parquet"

            if not src.exists():
                missing += 1
                continue

            if dst.exists() and not args.force:
                skipped += 1
                continue

            shutil.copy2(src, dst)
            sizeMb = dst.stat().st_size / 1024 / 1024
            print(f"  {dst.name} ({sizeMb:.2f} MB)")
            created += 1

    print(f"\n{created} created, {skipped} skipped, {missing} source missing")


if __name__ == "__main__":
    main()
