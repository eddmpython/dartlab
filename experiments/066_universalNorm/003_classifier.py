"""
실험 ID: 066-003
실험명: 테이블 수평화 가능/불가능 자동 분류기

목적:
- 현재 규칙 기반 필터(Jaccard < 0.3, 항목 > 50, fillRate < 0.5)를 ML 분류기로 대체
- 수평화 성공/실패 블록에서 특성을 추출하여 분류기 학습
- 현재 규칙 대비 precision/recall 개선 여부 측정

가설:
1. 테이블의 구조적 특성(컬럼 수, 행 수, 숫자 비율, 겹침률 등)으로 수평화 가능 여부를 90%+ 정확도로 예측 가능
2. Decision Tree가 현재 규칙 기반보다 F1 스코어 5%p 이상 개선

방법:
1. 50종목에서 모든 table 블록의 성공/실패 레이블 수집
2. 각 블록에서 8개 특성 추출 (컬럼 수, 행 수, 숫자 비율 등)
3. Decision Tree / Random Forest 학습 (80/20 split)
4. 현재 규칙 기반 분류기와 비교

결과 (실험 후 작성):
- 데이터: 50종목 23,333 블록 (성공 15,415 / 실패 7,918)
- 특성 분포: 실패 블록은 maxRowCount(19.4 vs 10.7), numSubtables(16.7 vs 8.7),
  maxColCount(8.3 vs 5.5), numPeriods(12.7 vs 7.8) 모두 높음
- 테스트셋 정확도:
  | 모델         | 정확도 | 실패-F1 | 성공-F1 |
  | 규칙 기반     | 0.61  | 0.40   | 0.71   |
  | Decision Tree | 0.75  | 0.58   | 0.82   |
  | Random Forest | 0.78  | 0.58   | 0.85   |
- 핵심 특성 (RF 중요도): maxRowCount(.16), numSubtables(.13),
  maxColCount(.10), jaccardOverlap(.09), avgColCount(.08)
- 단순 규칙 (DT depth=3): maxRowCount>15 + numSubtables>17 → 실패,
  maxColCount>8 + textOnly → 실패, avgDateRatio>0.28 → 실패
- 오분류 1040/4667 (22%) — 주로 실패를 성공으로 예측 (861건)

결론:
- **가설 1 기각**: 정확도 78%로 90% 목표 미달. 특성만으로 수평화 가능 여부를
  정확히 예측하기 어렵다. 수평화 실패의 원인이 구조적 특성보다는
  파서 구현의 한계(기수 매핑 실패, 비정형 헤더 등)에 있기 때문.
- **가설 2 채택**: DT/RF 모두 규칙 기반(61%) 대비 14~17%p 개선.
  단, 실패 recall이 46~52%로 낮아 실패 블록의 절반은 여전히 놓침.
- **실용적 결론**: 분류기 도입보다 파서 자체 개선이 더 효과적.
  maxRowCount>15, numSubtables>17, avgDateRatio>0.28 세 조건을
  기존 규칙에 추가하면 규칙 기반만으로도 상당 부분 개선 가능.

실험일: 2026-03-18
"""

import re
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import polars as pl

from dartlab.core.dataLoader import _dataDir
from dartlab.providers.dart.docs.sections.pipeline import sections
from dartlab.providers.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _isJunk,
    _normalizeHeader,
    splitSubtables,
)

# ── 특성 추출 ──


_MULTI_YEAR_KW = {"당기", "전기", "전전기", "당반기", "전반기", "당분기", "전분기"}
_NUM_RE = re.compile(r"^[\-\d,\.]+$")
_DATE_RE = re.compile(r"\d{4}[\.\-/]\d{1,2}[\.\-/]\d{1,2}")
_PERIOD_COL_RE = re.compile(r"^\d{4}(Q[1-4])?$")


def _extractFeatures(
    mdTexts: dict[str, str],
) -> dict[str, float] | None:
    """기간별 markdown 테이블에서 특성 추출.

    mdTexts: {period: markdown_text}
    """
    if not mdTexts:
        return None

    # 모든 기간의 서브테이블에서 통계 수집
    allColCounts = []
    allRowCounts = []
    allNumRatios = []
    allTextRatios = []
    allDateRatios = []
    allUniqueFirstColRatios = []
    headerHasPeriodKw = 0
    structTypes = []
    periodItemSets: dict[str, set[str]] = {}

    for period, md in mdTexts.items():
        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            if _isJunk(hc):
                continue
            dr = _dataRows(sub)
            if not dr:
                continue

            colCount = len(hc)
            rowCount = len(dr)
            allColCounts.append(colCount)
            allRowCounts.append(rowCount)

            # 구조 분류
            st = _classifyStructure(hc)
            structTypes.append(st)

            # 헤더에 기간 키워드 유무
            joined = " ".join(hc)
            if any(kw in joined for kw in _MULTI_YEAR_KW):
                headerHasPeriodKw += 1

            # 셀 통계
            numCells = 0
            textCells = 0
            dateCells = 0
            totalCells = 0
            firstColValues = []

            for row in dr:
                for ci, cell in enumerate(row):
                    cell = cell.strip()
                    if not cell or cell == "-":
                        continue
                    totalCells += 1
                    if ci == 0:
                        firstColValues.append(cell)
                    if _NUM_RE.match(cell):
                        numCells += 1
                    elif _DATE_RE.search(cell):
                        dateCells += 1
                    else:
                        textCells += 1

            if totalCells > 0:
                allNumRatios.append(numCells / totalCells)
                allTextRatios.append(textCells / totalCells)
                allDateRatios.append(dateCells / totalCells)

            if firstColValues:
                allUniqueFirstColRatios.append(
                    len(set(firstColValues)) / len(firstColValues)
                )

            # 기간별 첫 컬럼 항목 수집 (겹침률 계산용)
            items = set()
            for row in dr:
                if row and row[0].strip():
                    items.add(row[0].strip())
            if items:
                periodItemSets[period] = items

    if not allColCounts:
        return None

    # 기간 간 겹침률 (Jaccard)
    jaccardOverlap = 0.0
    if len(periodItemSets) >= 2:
        sets = list(periodItemSets.values())
        totalOv = 0
        totalPairs = 0
        for i in range(len(sets)):
            for j in range(i + 1, min(i + 4, len(sets))):
                union = len(sets[i] | sets[j])
                inter = len(sets[i] & sets[j])
                if union > 0:
                    totalOv += inter / union
                    totalPairs += 1
        jaccardOverlap = totalOv / totalPairs if totalPairs else 0.0

    # 구조 타입 분포
    multiYearRatio = structTypes.count("multi_year") / len(structTypes) if structTypes else 0
    kvRatio = structTypes.count("key_value") / len(structTypes) if structTypes else 0
    matrixRatio = structTypes.count("matrix") / len(structTypes) if structTypes else 0

    features = {
        "avgColCount": sum(allColCounts) / len(allColCounts),
        "maxColCount": max(allColCounts),
        "avgRowCount": sum(allRowCounts) / len(allRowCounts),
        "maxRowCount": max(allRowCounts),
        "avgNumRatio": sum(allNumRatios) / len(allNumRatios) if allNumRatios else 0,
        "avgTextRatio": sum(allTextRatios) / len(allTextRatios) if allTextRatios else 0,
        "avgDateRatio": sum(allDateRatios) / len(allDateRatios) if allDateRatios else 0,
        "avgUniqueFirstColRatio": (
            sum(allUniqueFirstColRatios) / len(allUniqueFirstColRatios)
            if allUniqueFirstColRatios
            else 1.0
        ),
        "jaccardOverlap": jaccardOverlap,
        "headerHasPeriodKw": 1.0 if headerHasPeriodKw > 0 else 0.0,
        "multiYearRatio": multiYearRatio,
        "kvRatio": kvRatio,
        "matrixRatio": matrixRatio,
        "numPeriods": len(mdTexts),
        "numSubtables": len(allColCounts),
    }
    return features


# ── 현재 규칙 기반 분류기 재현 ──


def _ruleBasedPredict(feat: dict[str, float]) -> int:
    """현재 company.py의 규칙 기반 필터를 재현.

    Returns: 1 = 수평화 가능(통과), 0 = 수평화 불가(스킵)
    """
    # 이력형: Jaccard < 0.3 and items > 5
    if feat["jaccardOverlap"] < 0.3 and feat["avgRowCount"] > 5:
        return 0
    # 목록형: items > 50
    if feat["maxRowCount"] > 50:
        return 0
    # sparse 감지는 fillRate 기반이지만 여기서는 정확히 재현 어려움
    # 근사: 기간 3개+ 이고 항목 15개+ 이면 Jaccard 기반으로 추정
    return 1


# ── 실제 수평화 시도로 레이블 수집 ──


def _collectSamples(stockCodes: list[str]) -> tuple[list[dict], list[int]]:
    """종목별로 모든 table 블록의 특성과 레이블(성공=1, 실패=0) 수집."""
    from dartlab.providers.dart.company import Company

    allFeatures: list[dict] = []
    allLabels: list[int] = []
    meta: list[dict] = []

    for si, code in enumerate(stockCodes):
        try:
            c = Company(code)
        except Exception:
            print(f"  [{si+1}/{len(stockCodes)}] {code}: 로딩 실패")
            continue

        sec = c.docs.sections
        if sec is None or sec.is_empty():
            print(f"  [{si+1}/{len(stockCodes)}] {code}: sections 없음")
            continue

        periodCols = [col for col in sec.columns if _PERIOD_COL_RE.match(col)]
        if not periodCols:
            continue

        # topic + blockOrder별로 수평화 시도
        topics = sec.filter(pl.col("blockType") == "table")["topic"].unique().to_list()
        successCount = 0
        failCount = 0

        for topic in topics:
            topicFrame = sec.filter(pl.col("topic") == topic)
            tableRows = topicFrame.filter(pl.col("blockType") == "table")
            blockOrders = tableRows["blockOrder"].unique().to_list()

            for bo in blockOrders:
                boRow = topicFrame.filter(
                    (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
                )
                if boRow.is_empty():
                    continue

                # 기간별 markdown 수집
                mdTexts = {}
                for p in periodCols:
                    if p in boRow.columns:
                        val = boRow[p][0]
                        if val is not None:
                            mdTexts[p] = str(val)

                if not mdTexts:
                    continue

                # 특성 추출
                feat = _extractFeatures(mdTexts)
                if feat is None:
                    continue

                # 실제 수평화 시도
                result = c._horizontalizeTableBlock(topicFrame, bo, periodCols)
                label = 1 if result is not None else 0

                allFeatures.append(feat)
                allLabels.append(label)
                meta.append({"code": code, "topic": topic, "blockOrder": bo})

                if label == 1:
                    successCount += 1
                else:
                    failCount += 1

        print(
            f"  [{si+1}/{len(stockCodes)}] {code} ({c.corpName}): "
            f"성공={successCount}, 실패={failCount}"
        )

    return allFeatures, allLabels


def _printDistribution(featureNames: list[str], X, y, label0Name: str, label1Name: str):
    """레이블별 특성 분포 출력."""
    import numpy as np

    print(f"\n{'특성':<30} {'실패(mean)':>12} {'성공(mean)':>12} {'차이':>10}")
    print("-" * 70)
    for i, name in enumerate(featureNames):
        vals0 = X[y == 0, i]
        vals1 = X[y == 1, i]
        m0 = np.mean(vals0) if len(vals0) > 0 else 0
        m1 = np.mean(vals1) if len(vals1) > 0 else 0
        diff = m1 - m0
        print(f"{name:<30} {m0:>12.4f} {m1:>12.4f} {diff:>+10.4f}")


if __name__ == "__main__":
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
    )
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier

    pl.Config.set_tbl_cols(8)
    pl.Config.set_fmt_str_lengths(40)

    # ── 1. 종목 50개 선택 (다양한 업종 포함) ──
    dataDir = _dataDir("docs")
    import os
    allCodes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(dataDir)
        if f.endswith(".parquet")
    )

    # 50개 균등 샘플링
    step = max(1, len(allCodes) // 50)
    sampleCodes = allCodes[::step][:50]
    print(f"=== 종목 {len(sampleCodes)}개에서 특성 추출 시작 ===")
    print(f"샘플: {sampleCodes[:5]} ... {sampleCodes[-3:]}")

    t0 = time.time()
    features, labels = _collectSamples(sampleCodes)
    elapsed = time.time() - t0
    print(f"\n추출 완료: {len(features)}개 블록 ({elapsed:.1f}초)")
    print(f"  성공(수평화): {sum(labels)}")
    print(f"  실패(fallback): {len(labels) - sum(labels)}")

    if len(features) < 20:
        print("데이터 부족 — 종료")
        sys.exit(1)

    # ── 2. 특성 분포 비교 ──
    featureNames = list(features[0].keys())
    X = np.array([[f[k] for k in featureNames] for f in features])
    y = np.array(labels)

    _printDistribution(featureNames, X, y, "실패", "성공")

    # ── 3. 학습/평가 ──
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\n학습: {len(X_train)}개, 평가: {len(X_test)}개")

    # 3-a. Decision Tree
    dt = DecisionTreeClassifier(max_depth=5, random_state=42, min_samples_leaf=10)
    dt.fit(X_train, y_train)
    dt_pred = dt.predict(X_test)

    print("\n" + "=" * 60)
    print("=== Decision Tree (max_depth=5) ===")
    print(classification_report(y_test, dt_pred, target_names=["실패", "성공"]))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, dt_pred))

    # 특성 중요도
    importances = dt.feature_importances_
    sortedIdx = np.argsort(importances)[::-1]
    print("\n특성 중요도:")
    for i in sortedIdx:
        if importances[i] > 0.01:
            print(f"  {featureNames[i]:<30} {importances[i]:.4f}")

    # Decision Tree 규칙 출력
    from sklearn.tree import export_text
    treeRules = export_text(dt, feature_names=featureNames, max_depth=3)
    print("\nDecision Tree 규칙 (depth 3):")
    print(treeRules)

    # 3-b. Random Forest
    rf = RandomForestClassifier(
        n_estimators=100, max_depth=7, random_state=42, min_samples_leaf=5
    )
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)

    print("=" * 60)
    print("=== Random Forest (n=100, max_depth=7) ===")
    print(classification_report(y_test, rf_pred, target_names=["실패", "성공"]))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, rf_pred))

    # RF 특성 중요도
    rfImportances = rf.feature_importances_
    rfSortedIdx = np.argsort(rfImportances)[::-1]
    print("RF 특성 중요도:")
    for i in rfSortedIdx:
        if rfImportances[i] > 0.01:
            print(f"  {featureNames[i]:<30} {rfImportances[i]:.4f}")

    # ── 4. 현재 규칙 기반과 비교 ──
    print("\n" + "=" * 60)
    print("=== 현재 규칙 기반 vs ML 비교 ===")

    rulePred = np.array([_ruleBasedPredict(f) for f in features])

    # 전체 데이터에서 비교
    print("\n[전체 데이터]")
    print(f"  규칙 기반 정확도: {accuracy_score(y, rulePred):.4f}")
    print(f"  DT 정확도:       {accuracy_score(y, dt.predict(X)):.4f}")
    print(f"  RF 정확도:       {accuracy_score(y, rf.predict(X)):.4f}")

    # 테스트셋에서 비교
    ruleTestPred = np.array(
        [
            _ruleBasedPredict(features[i])
            for i in range(len(features))
            if i in set(
                np.where(np.isin(np.arange(len(features)),
                         train_test_split(
                             np.arange(len(features)),
                             test_size=0.2,
                             random_state=42,
                             stratify=y,
                         )[1]))[0]
            )
        ]
    )
    # 간단히: 테스트 인덱스 추출
    _, testIdx = train_test_split(
        np.arange(len(features)), test_size=0.2, random_state=42, stratify=y
    )
    ruleTestPred = np.array([_ruleBasedPredict(features[i]) for i in testIdx])

    print("\n[테스트셋]")
    print(f"  규칙 기반:")
    print(
        classification_report(
            y_test, ruleTestPred, target_names=["실패", "성공"], zero_division=0
        )
    )
    print("  DT:")
    print(
        classification_report(
            y_test, dt_pred, target_names=["실패", "성공"], zero_division=0
        )
    )
    print("  RF:")
    print(
        classification_report(
            y_test, rf_pred, target_names=["실패", "성공"], zero_division=0
        )
    )

    # ── 5. 오분류 분석 ──
    print("\n" + "=" * 60)
    print("=== 오분류 분석 (RF 기준, 테스트셋) ===")

    misclassified = np.where(rf_pred != y_test)[0]
    print(f"오분류: {len(misclassified)}/{len(y_test)}개")

    if len(misclassified) > 0:
        print(f"\n  {'예측':>6} {'실제':>6} {'topic':<30} {'Jaccard':>8} {'rows':>6} {'cols':>6}")
        print("  " + "-" * 80)
        for idx in misclassified[:20]:
            globalIdx = testIdx[idx]
            f = features[globalIdx]
            print(
                f"  {'성공' if rf_pred[idx] else '실패':>6} "
                f"{'성공' if y_test[idx] else '실패':>6} "
                f"{'':.<30} "
                f"{f['jaccardOverlap']:>8.3f} "
                f"{f['avgRowCount']:>6.1f} "
                f"{f['avgColCount']:>6.1f}"
            )

    # ── 6. 최적 규칙 추출 (DT depth=3) ──
    print("\n" + "=" * 60)
    print("=== 단순 규칙 추출 (DT depth=3) ===")
    simpleDt = DecisionTreeClassifier(max_depth=3, random_state=42, min_samples_leaf=10)
    simpleDt.fit(X, y)
    simplePred = simpleDt.predict(X)
    print(f"전체 정확도: {accuracy_score(y, simplePred):.4f}")
    print("\n규칙:")
    print(export_text(simpleDt, feature_names=featureNames))
