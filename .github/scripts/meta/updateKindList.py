"""KRX KIND 상장법인 목록 → Parquet 발행 (gather SSOT 위임).

GitHub Actions(``kindlist.yml``)에서 실행되는 발행 래퍼. 수집·HTML 파싱·SPAC/리츠
필터·재시도 로직은 **중복 구현하지 않고** gather 엔진 SSOT(``getKindList``)를 그대로
호출한다 — 별도빌드 금지, 공동작업대(gather) 경유. 본 스크립트의 책임은 sink 플러밍
(parquet 쓰기 + 변경 해시 + 업로드 SKIP 신호)뿐이다. 런타임(Company/Search/Scan)과
CI 가 같은 한 줄기 수집·견고성을 공유한다.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from dartlab.gather.krx.listing import getKindList

OUTPUT_DIR = Path("dist")
OUTPUT_FILE = OUTPUT_DIR / "corpList.parquet"


def fileHash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    print("KRX KIND 상장법인 목록 — gather SSOT(getKindList) 호출")
    # 수집·파싱·필터·재시도 = gather 단일 경로(별도 크롤 없음). 이 스크립트가 HF 미러를 만드는 쪽이라
    # KIND 가 비었을 때 미러로 채우지 않는다(mirrorFallback=False). 채우면 옛 미러를 새 목록처럼 다시 올린다.
    df = getKindList(forceRefresh=True, mirrorFallback=False)
    if df.height == 0:
        print("KIND 수집 실패 — 빈 결과(재시도 소진)")
        sys.exit(1)
    print(f"{df.height}개 종목 수집 완료")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(str(OUTPUT_FILE))

    newHash = fileHash(OUTPUT_FILE)
    print(f"파일 생성 완료: {OUTPUT_FILE} (hash: {newHash[:12]})")

    existingHashFile = Path("dist/previous.sha256")
    if existingHashFile.exists():
        oldHash = existingHashFile.read_text().strip()
        if oldHash == newHash:
            print("변경 없음 — 업로드 스킵")
            Path("dist/SKIP").touch()
        else:
            print("변경 감지 — 업로드 진행")
    else:
        print("이전 해시 없음 — 업로드 진행")

    existingHashFile.write_text(newHash)
