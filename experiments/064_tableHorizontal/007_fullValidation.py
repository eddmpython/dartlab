"""
실험 ID: 064-007
실험명: 283종목 전수 검증

목적:
- 전 종목에서 showIntegrated 에러율 확인
- topic별 품질 통계 수집
- 에러/이상 패턴 분류

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-17
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import polars as pl
from _006_integrated import _isPeriodCol, showIntegrated

from dartlab.engines.company.dart.docs.sections.pipeline import sections


def validateStock(code: str) -> dict:
    """한 종목의 전체 topic 검증."""
    result = {
        "code": code,
        "error": None,
        "topicCount": 0,
        "successCount": 0,
        "failCount": 0,
        "failures": [],
        "stats": {},
    }

    try:
        sec = sections(code)
    except Exception as e:
        result["error"] = f"sections 로딩 실패: {e}"
        return result

    if sec is None:
        result["error"] = "sections None"
        return result

    topics = sec["topic"].unique().to_list()
    result["topicCount"] = len(topics)

    for topic in topics:
        try:
            df = showIntegrated(sec, topic)
            if df is not None:
                dataCols = [c for c in df.columns if _isPeriodCol(c)]
                textCount = df.filter(pl.col("blockType") == "text").height if "blockType" in df.columns else 0
                tableCount = df.filter(pl.col("blockType") == "table").height if "blockType" in df.columns else 0
                itemCount = df.filter(pl.col("항목").is_not_null()).height if "항목" in df.columns else 0
                result["stats"][topic] = {
                    "rows": df.height,
                    "text": textCount,
                    "table": tableCount,
                    "items": itemCount,
                    "periods": len(dataCols),
                }
            else:
                result["stats"][topic] = {"rows": 0}
            result["successCount"] += 1
        except Exception as e:
            result["failCount"] += 1
            result["failures"].append({
                "topic": topic,
                "error": str(e),
                "traceback": traceback.format_exc().split("\n")[-3],
            })

    return result


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    print(f"전수 검증: {len(codes)}종목")
    print("=" * 70)

    totalErrors = 0
    totalTopics = 0
    totalSuccess = 0
    errorStocks = []
    failureDetails = []

    for i, code in enumerate(codes):
        result = validateStock(code)

        if result["error"]:
            print(f"  [{i+1}/{len(codes)}] {code}: ERROR — {result['error']}")
            totalErrors += 1
            errorStocks.append(code)
            continue

        totalTopics += result["topicCount"]
        totalSuccess += result["successCount"]

        if result["failCount"] > 0:
            print(f"  [{i+1}/{len(codes)}] {code}: {result['successCount']}/{result['topicCount']} topics OK, {result['failCount']} FAIL")
            for f in result["failures"]:
                print(f"    FAIL {f['topic']}: {f['error']}")
                failureDetails.append({"code": code, **f})
            errorStocks.append(code)
        else:
            # 성공 — 진행 표시만
            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{len(codes)}] ... {code} OK")

    print("\n" + "=" * 70)
    print(f"결과: {len(codes)}종목, {totalTopics} topics")
    print(f"  성공: {totalSuccess} topics")
    print(f"  에러 종목: {len(errorStocks)}")

    if failureDetails:
        print(f"\n실패 상세 ({len(failureDetails)}건):")
        # 에러 유형별 분류
        errorTypes = {}
        for f in failureDetails:
            key = f["traceback"].strip()
            if key not in errorTypes:
                errorTypes[key] = []
            errorTypes[key].append(f"{f['code']}:{f['topic']}")

        for errType, cases in sorted(errorTypes.items(), key=lambda x: -len(x[1])):
            print(f"\n  [{len(cases)}건] {errType}")
            for case in cases[:5]:
                print(f"    {case}")
            if len(cases) > 5:
                print(f"    ... +{len(cases)-5}건")
