"""FRED 산업별 지표 사전 수집 → Parquet 캐시.

PRODUCT_INDICATOR_MAP에 등록된 모든 FRED 시리즈를 수집하여
~/.dartlab/cache/macro/fred/ 에 Parquet으로 저장한다.

한 번 실행하면 calcMacroRegression이 캐시만 읽어서 산업 지표를 회귀 변수로 사용.

Usage:
    uv run python scripts/collectIndustryIndicators.py
"""

from __future__ import annotations

import os
import sys

# .env 로드
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())


def main():
    from dartlab.core.finance.productIndicators import PRODUCT_INDICATOR_MAP
    from dartlab.gather.fred import Fred
    from dartlab.gather.macro import enrichAndCache

    # 고유 FRED 시리즈 ID 추출
    fredIds: set[str] = set()
    for mapping in PRODUCT_INDICATOR_MAP.values():
        for sid in mapping.get("fred", []):
            fredIds.add(sid)

    print(f"[1/2] FRED 산업 지표 {len(fredIds)}개 수집 시작")

    fc = Fred()
    success = 0
    failed = 0

    for sid in sorted(fredIds):
        try:
            df = fc.series(sid, start="2000-01-01")
            if len(df) > 0:
                enriched = enrichAndCache(sid, df, source="fred")
                print(f"  OK  {sid:25s} {len(enriched):5d} rows ({enriched['date'][0]} ~ {enriched['date'][-1]})")
                success += 1
            else:
                print(f"  EMPTY {sid}")
                failed += 1
        except Exception as exc:
            print(f"  FAIL {sid}: {exc}")
            failed += 1

    fc.close()
    print(f"\n[2/2] 완료: {success} 성공, {failed} 실패")


if __name__ == "__main__":
    main()
