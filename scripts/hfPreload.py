"""HuggingFace Spaces Docker 빌드 시 샘플 데이터 프리로드.

삼성전자(005930)와 AAPL 데이터를 미리 다운로드하여
cold start 시간을 줄인다.
"""

from __future__ import annotations

import os
import sys

# Docker 빌드 환경에서는 dartlab이 이미 pip install된 상태
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

SAMPLES = ["005930", "AAPL"]


def main() -> None:
    from dartlab.core.dataLoader import download

    for code in SAMPLES:
        print(f"  preloading {code}...")
        try:
            download(code)
            print(f"  {code} done")
        except Exception as e:  # noqa: BLE001
            print(f"  {code} skipped: {e}")


if __name__ == "__main__":
    main()
