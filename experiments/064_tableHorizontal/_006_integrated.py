"""
실험 ID: 064-006
실험명: Layer 2+3 통합 — 전체 파이프라인 조립

목적:
- 개선된 cell parser(005) + block horizontalizer + show composer 통합
- text-table 교차 순서 + 테이블 항목×기간 매트릭스
- 10종목 전수 검증

가설:
1. 비교형 테이블(multi_year)은 항목×기간 매트릭스 정상 생성
2. 현황형 테이블(kv/matrix)은 기간별 값 수평화 정상
3. 목록형 테이블은 감지 + 원본 마크다운 유지
4. text-table 교차 순서 보장

방법:
1. show_integrated(topic) → DataFrame (blockOrder 순서 교차)
2. 10종목 × 핵심 topic 검증

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-17
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import re
from collections import defaultdict

import polars as pl

from dartlab.engines.company.dart.docs.sections.pipeline import sections
from dartlab.engines.company.dart.docs.sections.tableParser import splitSubtables

# 005에서 만든 개선 파서
sys.path.insert(0, str(Path(__file__).parent))
from _005_improvedParser import parseCellSubtablesV2


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


def _subtableItemSet(sub) -> set[str]:
    """서브테이블의 항목명 집합."""
    return {item for item, _ in sub.items}


def _clusterSubtables(
    periodSubs: dict[str, list],  # period → [ParsedSubtable, ...]
) -> list[dict[str, "ParsedSubtable"]]:
    """항목명 겹침 기반으로 서브테이블을 클러스터링.

    같은 클러스터 = 같은 논리적 테이블의 기간별 버전.
    """
    # tableType별로 분리 후 클러스터링
    byType: dict[str, list[tuple[str, object]]] = defaultdict(list)
    for p, subs in periodSubs.items():
        for sub in subs:
            byType[sub.tableType].append((p, sub))

    clusters: list[dict[str, object]] = []

    for tableType, pairs in byType.items():
        typeClusters: list[dict[str, object]] = []

        for p, sub in pairs:
            itemSet = _subtableItemSet(sub)
            if not itemSet:
                continue

            bestCluster = None
            bestScore = 0.0

            for ci, cluster in enumerate(typeClusters):
                clusterItems: set[str] = set()
                for csub in cluster.values():
                    clusterItems.update(_subtableItemSet(csub))

                intersection = len(itemSet & clusterItems)
                union = len(itemSet | clusterItems)
                if union > 0:
                    score = intersection / union
                    if score > bestScore:
                        bestScore = score
                        bestCluster = ci

            if bestCluster is not None and bestScore >= 0.3 and p not in typeClusters[bestCluster]:
                typeClusters[bestCluster][p] = sub
            else:
                typeClusters.append({p: sub})

        clusters.extend(typeClusters)

    return clusters


def horizontalizeTopic(
    topicFrame: pl.DataFrame,
    periodCols: list[str],
) -> list[pl.DataFrame]:
    """topic 전체의 table 행을 내용 기반 클러스터링 → 서브테이블별 항목×기간 DataFrame.

    blockOrder를 무시하고 모든 table 행의 마크다운을 기간별로 파싱,
    항목명 기반 클러스터링으로 같은 논리적 테이블을 매칭.
    """
    tableRows = topicFrame.filter(pl.col("blockType") == "table") if "blockType" in topicFrame.columns else topicFrame
    if tableRows.is_empty():
        return []

    # 모든 기간에서 모든 table blockOrder의 서브테이블 파싱
    periodSubsList: dict[str, list] = {}

    for p in periodCols:
        allSubs = []
        for row in tableRows.iter_rows(named=True):
            md = row.get(p)
            if md is None:
                continue
            pYear = int(re.match(r"\d{4}", p).group()) if re.match(r"\d{4}", p) else None
            if pYear is None:
                continue
            subs = parseCellSubtablesV2(str(md), pYear)
            allSubs.extend(subs)
        if allSubs:
            periodSubsList[p] = allSubs

    if not periodSubsList:
        return []

    # 항목명 기반 클러스터링 (blockOrder 무시, 내용으로 매칭)
    clusters = _clusterSubtables(periodSubsList)

    results = []
    for subIdx, cluster in enumerate(clusters):
        periodSubs = cluster
        if not periodSubs:
            continue

        # 서브테이블 타입 결정 (최다 타입)
        typeCounts = defaultdict(int)
        for sub in periodSubs.values():
            typeCounts[sub.tableType] += 1
        mainType = max(typeCounts, key=typeCounts.get)

        # 목록형 감지 — tableType별 다른 기준
        itemCounts = [len(sub.items) for sub in periodSubs.values() if len(sub.items) > 0]
        avgCount = sum(itemCounts) / len(itemCounts) if itemCounts else 0
        maxCount = max(itemCounts) if itemCounts else 0
        minCount = min(itemCounts) if itemCounts else 0

        if mainType == "multi_year":
            # multi_year: 항목 수만으로 판단 (50+ 이면 목록형)
            # 기간별 부재로 변동률이 높아지는 건 정상
            isListType = maxCount > 50
        else:
            # key_value/matrix: 변동률 + maxCount 복합
            varRate = (maxCount - minCount) / avgCount if avgCount > 0 else 0
            isListType = (varRate > 0.5 and maxCount > 15) or maxCount > 30

        if isListType:
            # 목록형: 스킵 (원본 마크다운 유지 — text 행처럼 기간별 원본)
            continue

        # 항목 수집 + 값 배치
        allItems: list[str] = []
        seenItems: set[str] = set()
        periodItemVal: dict[str, dict[str, str]] = {}

        if mainType == "multi_year":
            # multi_year: 당기 값만
            for p, sub in periodSubs.items():
                if sub.tableType != "multi_year":
                    continue
                for item, vals in sub.items:
                    if item not in seenItems:
                        allItems.append(item)
                        seenItems.add(item)
                    if item not in periodItemVal:
                        periodItemVal[item] = {}
                    if vals:
                        periodItemVal[item][p] = vals[0]
        else:
            # kv/matrix: 기간별 값
            for p, sub in periodSubs.items():
                if sub.tableType not in ("key_value", "matrix"):
                    continue
                for item, vals in sub.items:
                    if item not in seenItems:
                        allItems.append(item)
                        seenItems.add(item)
                    if item not in periodItemVal:
                        periodItemVal[item] = {}
                    val = " | ".join(vals) if vals else ""
                    if val:
                        periodItemVal[item][p] = val

        if not allItems:
            continue

        # 품질 필터: 숫자만 항목명 제거, 전체 null 항목 제거
        def _isJunkItem(item: str) -> bool:
            stripped = re.sub(r"[,.\-\s]", "", item)
            return stripped.isdigit() or not stripped

        cleanItems = [item for item in allItems if not _isJunkItem(item)]
        cleanItems = [item for item in cleanItems if periodItemVal.get(item)]
        if not cleanItems:
            continue
        allItems = cleanItems

        # 유효 항목만 유지
        allItems = [item for item in allItems if len(periodItemVal.get(item, {})) > 0]
        if not allItems:
            continue

        # DataFrame 구성
        usedPeriods = [p for p in periodCols if any(p in periodItemVal.get(item, {}) for item in allItems)]
        if not usedPeriods:
            continue

        # 서브테이블 전체에서 연간 기간에 유효 값 비율 체크
        annualAll = [p for p in usedPeriods if re.match(r"^\d{4}$", p)]
        if annualAll:
            annualHits = sum(
                1 for item in allItems
                if any(periodItemVal.get(item, {}).get(p) for p in annualAll)
            )
            if annualHits == 0:
                # 연간에 값이 하나도 없는 서브테이블 스킵
                continue

        schema: dict[str, pl.DataType] = {
            "blockType": pl.Utf8,
            "subtable": pl.Int64,
            "항목": pl.Utf8,
        }
        for p in usedPeriods:
            schema[p] = pl.Utf8

        # 연간 기간에 값이 하나라도 있는 항목만 유지 (분기만 있는 항목은 노이즈)
        annualPeriods = [p for p in usedPeriods if re.match(r"^\d{4}$", p)]
        rows = []
        for item in allItems:
            hasAnnualValue = any(periodItemVal.get(item, {}).get(p) for p in annualPeriods) if annualPeriods else False
            hasAnyValue = any(periodItemVal.get(item, {}).get(p) for p in usedPeriods)
            if not hasAnyValue:
                continue
            # 연간 기간이 있는데 연간에 값이 전혀 없으면 스킵
            if annualPeriods and not hasAnnualValue:
                continue
            row: dict = {
                "blockType": "table",
                "subtable": subIdx,
                "항목": item,
            }
            for p in usedPeriods:
                row[p] = periodItemVal.get(item, {}).get(p)
            rows.append(row)

        if not rows:
            continue
        results.append(pl.DataFrame(rows, schema=schema))

    return results


def showIntegrated(
    sec: pl.DataFrame,
    topic: str,
) -> pl.DataFrame | None:
    """통합 show — text/table 교차 순서 DataFrame."""
    topicFrame = sec.filter(pl.col("topic") == topic)
    if topicFrame.is_empty():
        return None

    periodCols = [c for c in sec.columns if _isPeriodCol(c)]
    blockOrders = sorted(topicFrame["blockOrder"].unique().to_list())

    frames: list[pl.DataFrame] = []

    # text 블록 수집
    for bo in blockOrders:
        boRows = topicFrame.filter(pl.col("blockOrder") == bo)
        bt = boRows["blockType"][0]
        if bt == "text":
            keepCols = ["blockOrder", "blockType"] + [c for c in periodCols if c in boRows.columns]
            textDf = boRows.select([c for c in keepCols if c in boRows.columns])
            dataCols = [c for c in textDf.columns if _isPeriodCol(c)]
            nonNullCols = [c for c in dataCols if textDf[c].null_count() < textDf.height]
            if nonNullCols:
                selectCols = ["blockOrder", "blockType"] + nonNullCols
                frames.append(textDf.select([c for c in selectCols if c in textDf.columns]))

    # table 블록: topic 전체를 한꺼번에 클러스터링 (blockOrder 무시)
    tableDfs = horizontalizeTopic(topicFrame, periodCols)
    if tableDfs:
        frames.extend(tableDfs)
    else:
        # 목록형만 있거나 파싱 실패 — table 행을 원본 마크다운으로 유지
        for bo in blockOrders:
            boRows = topicFrame.filter(pl.col("blockOrder") == bo)
            bt = boRows["blockType"][0]
            if bt == "table":
                keepCols = ["blockOrder", "blockType"] + [c for c in periodCols if c in boRows.columns]
                rawDf = boRows.select([c for c in keepCols if c in boRows.columns])
                dataCols = [c for c in rawDf.columns if _isPeriodCol(c)]
                nonNullCols = [c for c in dataCols if rawDf[c].null_count() < rawDf.height]
                if nonNullCols:
                    selectCols = ["blockOrder", "blockType"] + nonNullCols
                    frames.append(rawDf.select([c for c in selectCols if c in rawDf.columns]))

    if not frames:
        return None

    result = pl.concat(frames, how="diagonal_relaxed")
    # text는 blockOrder로 정렬, table은 subtable로 정렬, text가 먼저
    sortCols = [c for c in ["blockOrder", "subtable"] if c in result.columns]
    if sortCols:
        result = result.sort(sortCols, nulls_last=False)

    return result


if __name__ == "__main__":
    stocks = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035420", "네이버"),
        ("005380", "현대차"),
        ("068270", "셀트리온"),
        ("105560", "KB금융"),
        ("051910", "LG화학"),
        ("003550", "LG"),
        ("028260", "삼성물산"),
        ("034730", "SK"),
    ]

    topics = ["dividend", "companyOverview", "audit", "employee"]

    print("=" * 80)
    print("통합 검증: 10종목 × 4 topic")
    print("=" * 80)

    for code, name in stocks:
        try:
            sec = sections(code)
        except Exception as e:
            print(f"\n{name}: 로딩 실패 — {e}")
            continue
        if sec is None:
            print(f"\n{name}: sections None")
            continue

        print(f"\n{'─'*40}")
        print(f"  {name} ({code})")
        print(f"{'─'*40}")

        for topic in topics:
            try:
                result = showIntegrated(sec, topic)
            except Exception as e:
                print(f"  {topic}: ERROR — {e}")
                continue

            if result is None:
                print(f"  {topic}: None")
                continue

            # 블록 구성 분석
            textCount = result.filter(pl.col("blockType") == "text").height if "blockType" in result.columns else 0
            tableCount = result.filter(pl.col("blockType") == "table").height if "blockType" in result.columns else 0
            dataCols = [c for c in result.columns if _isPeriodCol(c)]
            hasItem = "항목" in result.columns
            itemCount = result.filter(pl.col("항목").is_not_null()).height if hasItem else 0

            print(f"  {topic}: {result.height}행 (text={textCount}, table={tableCount}, items={itemCount}) × {len(dataCols)}기간")

            # dividend는 상세 출력
            if topic == "dividend" and hasItem:
                tableRows = result.filter(pl.col("blockType") == "table")
                if not tableRows.is_empty():
                    recent = ["항목"] + [c for c in dataCols[-3:] if c in tableRows.columns]
                    preview = tableRows.select([c for c in recent if c in tableRows.columns]).head(5)
                    print(preview)

    # ── 삼성전자 companyOverview 상세 ──
    print("\n" + "=" * 80)
    print("삼성전자 companyOverview 상세 (text-table 교차)")
    print("=" * 80)

    sec = sections("005930")
    result = showIntegrated(sec, "companyOverview")
    if result is not None:
        for row in result.iter_rows(named=True):
            bo = row.get("blockOrder", "?")
            bt = row.get("blockType", "?")
            item = row.get("항목", "")
            sub = row.get("subtable", "")
            # 최근 기간 값 미리보기
            val = ""
            for c in reversed(result.columns):
                if _isPeriodCol(c) and row.get(c):
                    val = str(row[c])[:50]
                    break
            if item:
                print(f"  bo={bo} [{bt}] sub={sub} {item}: {val}")
            else:
                print(f"  bo={bo} [{bt}] {val}")
