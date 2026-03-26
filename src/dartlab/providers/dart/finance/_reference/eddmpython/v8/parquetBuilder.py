"""standardAccounts.json → Parquet 변환기

OWL 온톨로지 대신 Parquet 사용:
- 로딩 속도: 5초 → 0.05초 (100배 빠름)
- 메모리: 30MB → 5MB (6배 절약)
- 기능: v8과 동일 (컨텍스트, Fuzzy)
"""

import json
from pathlib import Path

import polars as pl


def buildParquet(dataDir: Path = None):
    """standardAccounts.json → standardAccounts.parquet 변환"""

    if dataDir is None:
        currentFile = Path(__file__).resolve()
        dataDir = currentFile.parent.parent

    jsonPath = dataDir / "standardAccounts.json"
    parquetPath = dataDir / "standardAccounts.parquet"

    print(f"JSON 읽기: {jsonPath}")
    with open(jsonPath, "r", encoding="utf-8") as f:
        data = json.load(f)

    accounts = data.get("accounts", [])
    print(f"총 계정 수: {len(accounts):,}")

    rows = []
    for acc in accounts:
        snakeId = acc.get("snakeId", "")
        if not snakeId:
            continue

        rows.append(
            {
                "code": acc.get("code", ""),
                "korName": acc.get("korName", ""),
                "engName": acc.get("engName", ""),
                "snakeId": snakeId,
                "industry": acc.get("industry", 0),
                "statementKind": acc.get("statementKind", 0),
                "codeType": acc.get("codeType", "M"),
                "level": acc.get("level", 0),
            }
        )

    df = pl.DataFrame(rows)

    print(f"Parquet 쓰기: {parquetPath}")
    df.write_parquet(parquetPath, compression="zstd")

    fileSizeKb = parquetPath.stat().st_size / 1024
    print(f"✅ 완료: {len(rows):,}개 계정, {fileSizeKb:.1f}KB")

    return df


if __name__ == "__main__":
    buildParquet()
