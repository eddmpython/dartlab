"""DART 엔진 내부 Company 본체.

사용법::

    from dartlab.engines.dart.company import Company

    c = Company("005930")       # 한국 (DART)
    c = Company("삼성전자")      # 한국 (회사명)
    c.BS                        # 재무상태표 DataFrame
    c.ratios                    # 재무비율
    c.insights                  # 인사이트 등급
"""

from __future__ import annotations

import difflib
import hashlib
import logging
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, NamedTuple

import polars as pl

pl.Config.set_fmt_str_lengths(80)
pl.Config.set_tbl_width_chars(200)

from dartlab.core.dataLoader import (
    DART_VIEWER,
    _dataDir,
    buildIndex,
    extractCorpName,
    loadData,
)
from dartlab.core.kindList import (
    codeToName,
    getKindList,
    nameToCode,
    searchName,
)

# ── 모듈 레지스트리 (core/registry.py에서 자동 생성) ──
# (모듈 import 경로, 함수명, 한글 라벨, primary DataFrame 추출)
# fsSummary/statements는 내부 디스패치 전용 (BS/IS/CF property가 statements를 호출)
from dartlab.core.registry import getEntry as _getEntry
from dartlab.core.registry import getModuleEntries as _getModuleEntries
from dartlab.engines.dart.docs.notes import Notes

_MODULE_REGISTRY: list[tuple[str, str, str, Any]] = [
    ("dartlab.engines.dart.docs.finance.summary", "fsSummary", "요약재무정보", None),
    ("dartlab.engines.dart.docs.finance.statements", "statements", "재무제표", None),
] + [
    (e.modulePath, e.funcName, e.label, e.extractor)
    for e in _getModuleEntries()
]

# 모듈명 → 레지스트리 인덱스
_MODULE_INDEX: dict[str, int] = {entry[1]: i for i, entry in enumerate(_MODULE_REGISTRY)}

# all()에서 사용할 순서 (fsSummary, statements 제외 — BS/IS/CF로 대체)
_ALL_PROPERTIES: list[tuple[str, str]] = [
    ("BS", "재무상태표"),
    ("IS", "손익계산서"),
    ("CF", "현금흐름표"),
]
for entry in _MODULE_REGISTRY:
    name = entry[1]
    if name in ("fsSummary", "statements", "companyOverview"):
        continue
    _ALL_PROPERTIES.append((name, entry[2]))

_CHAPTER_TITLES: OrderedDict[str, str] = OrderedDict([
    ("I", "I. 회사의 개요"),
    ("II", "II. 사업의 내용"),
    ("III", "III. 재무에 관한 사항"),
    ("IV", "IV. 이사의 경영진단 및 분석의견"),
    ("V", "V. 감사인의 감사의견등"),
    ("VI", "VI. 이사회등회사의기관및계열회사에관한사항"),
    ("VII", "VII. 주주에 관한 사항"),
    ("VIII", "VIII. 임원 및 직원 등에 관한 사항"),
    ("IX", "IX. 이해관계자와의 거래내용"),
    ("X", "X. 그 밖에 투자자 보호를 위하여 필요한 사항"),
    ("XI", "XI. 재무제표등"),
    ("XII", "XII. 상세표 및 부속명세서"),
])

_CHAPTER_ORDER: dict[str, int] = {chapter: idx for idx, chapter in enumerate(_CHAPTER_TITLES, start=1)}
_PERIOD_COLUMN_RE = re.compile(r"^\d{4}(Q[1-4])?$")
_REPORT_TOPIC_TO_API_TYPE: dict[str, str] = {
    "audit": "auditOpinion",
}
# OpenDART 개발가이드 공식 한글 컬럼 매핑 (https://opendart.fss.or.kr/guide/)
_REPORT_COL_KR: dict[str, str] = {
    # 증자(감자) 현황 — apiId=2019004
    "isu_dcrs_de": "주식발행(감소)일자", "isu_dcrs_stle": "발행(감소)형태",
    "isu_dcrs_stock_knd": "발행(감소)주식종류", "isu_dcrs_qy": "발행(감소)수량",
    "isu_dcrs_mstvdv_fval_amount": "주당액면가액", "isu_dcrs_mstvdv_amount": "주당가액",
    # 자기주식 취득/처분 — apiId=2019006
    "stock_knd": "주식종류", "acqs_mth1": "취득방법(대)",
    "acqs_mth2": "취득방법(중)", "acqs_mth3": "취득방법(소)",
    "bsis_qy": "기초수량", "change_qy_acqs": "변동수량(취득)",
    "change_qy_dsps": "변동수량(처분)", "change_qy_incnr": "변동수량(소각)",
    "trmend_qy": "기말수량",
    # 주식총수 현황 — apiId=2020002
    "se": "구분", "isu_stock_totqy": "발행할주식총수",
    "now_to_isu_stock_totqy": "현재까지발행주식총수",
    "now_to_dcrs_stock_totqy": "현재까지감소주식총수",
    "redc": "감자", "profit_incnr": "이익소각", "rdmstk_repy": "상환주식상환",
    "etc": "기타", "istc_totqy": "발행주식총수",
    "tesstk_co": "자기주식수", "distb_stock_co": "유통주식수",
    # 타법인 출자 현황 — apiId=2019015
    "inv_prm": "법인명", "frst_acqs_de": "최초취득일자", "invstmnt_purps": "출자목적",
    "frst_acqs_amount": "최초취득금액", "bsis_blce_qy": "기초잔액(수량)",
    "bsis_blce_qota_rt": "기초잔액(지분율)", "bsis_blce_acntbk_amount": "기초잔액(장부가액)",
    "incrs_dcrs_acqs_dsps_qy": "증감(취득처분)(수량)",
    "incrs_dcrs_acqs_dsps_amount": "증감(취득처분)(금액)",
    "incrs_dcrs_evl_lstmn": "증감(평가손액)",
    "trmend_blce_qy": "기말잔액(수량)", "trmend_blce_qota_rt": "기말잔액(지분율)",
    "trmend_blce_acntbk_amount": "기말잔액(장부가액)",
    "recent_bsns_year_fnnr_sttus_tot_assets": "최근사업연도재무현황(총자산)",
    "recent_bsns_year_fnnr_sttus_thstrm_ntpf": "최근사업연도재무현황(당기순이익)",
    # 최대주주 변동현황 — apiId=2019008
    "change_on": "변동일", "mxmm_shrholdr_nm": "최대주주명",
    "posesn_stock_co": "소유주식수", "qota_rt": "지분율", "change_cause": "변동원인",
    # 소액주주 현황 — apiId=2019009
    "shrholdr_co": "주주수", "shrholdr_tot_co": "전체주주수", "shrholdr_rate": "주주비율",
    "hold_stock_co": "보유주식수", "stock_tot_co": "총발행주식수", "hold_stock_rate": "보유주식비율",
    # 사외이사 현황 — apiId=2020012
    "drctr_co": "이사의수", "otcmp_drctr_co": "사외이사수",
    "apnt": "사외이사변동(선임)", "rlsofc": "사외이사변동(해임)",
    "mdstrm_resig": "사외이사변동(중도퇴임)",
    # 공모자금 사용내역 — apiId=2020016
    "se_nm": "구분", "tm": "회차", "pay_de": "납입일", "pay_amount": "납입금액",
    "on_dclrt_cptal_use_plan": "신고서상자금사용계획",
    "real_cptal_use_sttus": "실제자금사용현황",
    "rs_cptal_use_plan_useprps": "증권신고서자금사용계획(용도)",
    "rs_cptal_use_plan_prcure_amount": "증권신고서자금사용계획(조달금액)",
    "real_cptal_use_dtls_cn": "실제자금사용내역(내용)",
    "real_cptal_use_dtls_amount": "실제자금사용내역(금액)",
    "dffrnc_occrrnc_resn": "차이발생사유",
    # 사모자금 사용내역 — apiId=2020017
    "cptal_use_plan": "자금사용계획",
    "mtrpt_cptal_use_plan_useprps": "주요사항보고서자금사용계획(용도)",
    "mtrpt_cptal_use_plan_prcure_amount": "주요사항보고서자금사용계획(조달금액)",
    # 회사채 미상환 잔액 — apiId=2020006
    "sm": "합계", "remndr_exprtn1": "잔여만기(대분류)", "remndr_exprtn2": "잔여만기(소분류)",
    "yy1_below": "1년이하", "yy1_excess_yy2_below": "1년초과2년이하",
    "yy2_excess_yy3_below": "2년초과3년이하", "yy3_excess_yy4_below": "3년초과4년이하",
    "yy4_excess_yy5_below": "4년초과5년이하", "yy5_excess_yy10_below": "5년초과10년이하",
    "yy10_excess": "10년초과",
    # 단기사채 미상환 잔액 — apiId=2020005
    "de10_below": "10일이하", "de10_excess_de30_below": "10일초과30일이하",
    "de30_excess_de90_below": "30일초과90일이하", "de90_excess_de180_below": "90일초과180일이하",
    "de180_excess_yy1_below": "180일초과1년이하", "isu_lmt": "발행한도", "remndr_lmt": "잔여한도",
    # 감사용역 체결현황 — apiId=2020010
    "bsns_year": "사업연도", "adtor": "감사인", "cn": "내용", "mendng": "보수",
    "tot_reqre_time": "총소요시간", "adt_cntrct_dtls_mendng": "감사계약내역(보수)",
    "adt_cntrct_dtls_time": "감사계약내역(시간)",
    "real_exc_dtls_mendng": "실제수행내역(보수)", "real_exc_dtls_time": "실제수행내역(시간)",
    # 비감사 용역 계약현황 — apiId=2020011
    "cntrct_cncls_de": "계약체결일", "servc_cn": "용역내용",
    "servc_exc_pd": "용역수행기간", "servc_mendng": "용역보수",
    # 이사·감사 보수현황 — apiId=2019013
    "nmpr": "인원수", "mendng_totamt": "보수총액",
    "jan_avrg_mendng_am": "1인평균보수액",
    # 개인별 보수현황 — apiId=2019012, 2019014
    "nm": "이름", "ofcps": "직위",
    "mendng_totamt_ct_incls_mendng": "보수총액비포함보수",
    # 미등기임원 보수현황 — apiId=2020013
    "fyer_salary_totamt": "연간급여총액", "jan_salary_am": "1인평균급여액",
    # 공통
    "rm": "비고",
}
_DOCS_TOPIC_HINTS: dict[str, tuple[str, ...]] = {
    "costByNature": ("비용의 성격별 분류", "비용의성격별분류", "제조원가", "감가상각비"),
    "tangibleAsset": ("유형자산", "감가상각비"),
}
_DOCS_TITLE_HINTS: dict[str, tuple[str, ...]] = {
    "costByNature": ("비용의 성격별 분류", "비용의성격별분류", "제조원가명세서"),
    "tangibleAsset": ("유형자산",),
}

_TOPIC_LABELS: dict[str, str] = {
    "businessOverview": "사업의 개요",
    "businessStatus": "사업현황",
    "consolidatedNotes": "연결재무제표 주석",
    "consolidatedStatements": "연결재무제표",
    "financialNotes": "재무제표 주석",
    "financialStatements": "재무제표",
    "financialSoundnessOtherReference": "재무건전성 기타참고",
    "governanceOverview": "지배구조 개요",
    "majorContractsAndRnd": "주요계약 및 R&D",
    "mdna": "경영진단 및 분석의견",
    "segmentFinancialSummary": "부문별 재무요약",
    "investmentInOtherDetail": "타법인출자 상세",
    "stockAdministration": "주식사무",
    "stockPriceTrend": "주가 추이",
    "appendixSchedule": "상세표",
    "investorProtection": "투자자보호",
    "disclosureChanges": "공시내용 변경",
    "subsequentEvents": "후발사건",
    "expertConfirmation": "전문가확인",
    "subsidiaryDetail": "종속회사 상세",
    "affiliateGroupDetail": "계열회사 상세",
    "rndDetail": "연구개발 상세",
    "otherReference": "기타참고사항",
    "otherReferences": "기타참고사항",
    "operatingFacilities": "생산설비",
}


def listExportModules() -> list[tuple[str, str]]:
    """Excel/export용 DART 공개 모듈 목록."""
    return list(_ALL_PROPERTIES)


def _isPeriodColumn(name: str) -> bool:
    return bool(_PERIOD_COLUMN_RE.fullmatch(name))


def _normalizeTextCell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return re.sub(r"\s+", " ", text)


def _stableFingerprint(*parts: Any) -> str:
    raw = "||".join(_normalizeTextCell(part) for part in parts if part is not None)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


def _tableMetrics(text: str) -> tuple[int, int, str, str]:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return 0, 0, "", ""

    parsed: list[list[str]] = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        parsed.append(cells)

    header = parsed[0] if parsed else []
    body = parsed[2:] if len(parsed) > 2 else []
    rowLabels = [row[0] for row in body if row]
    return len(body), max((len(row) for row in parsed), default=0), "/".join(header), "/".join(rowLabels[:12])


def _textSimilarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, _normalizeTextCell(left), _normalizeTextCell(right)).ratio()


def _canonicalBlockRecord(record: dict[str, Any]) -> dict[str, Any]:
    rawText = str(record.get("blockText") or "")
    blockType = str(record.get("blockType") or "")
    if blockType == "table":
        normalizedText = "\n".join(line.strip() for line in rawText.splitlines() if line.strip())
    else:
        normalizedText = _normalizeTextCell(rawText)
    blockLabel = _normalizeTextCell(record.get("blockLabel"))
    semanticTopic = _normalizeTextCell(record.get("semanticTopic"))
    detailTopic = _normalizeTextCell(record.get("detailTopic"))
    tableRows, tableCols, tableHeader, tableLabels = (0, 0, "", "")
    if blockType == "table":
        tableRows, tableCols, tableHeader, tableLabels = _tableMetrics(normalizedText)
    tableShape = (
        f"rows={tableRows}|cols={tableCols}|header={tableHeader}|labels={tableLabels}"
        if blockType == "table"
        else None
    )
    anchorKey = "|".join([
        blockType,
        detailTopic,
        semanticTopic,
        blockLabel,
    ])
    structureKey = "|".join([
        anchorKey,
        tableShape or "",
    ])
    textHash = _stableFingerprint(normalizedText)
    blockKey = _stableFingerprint(structureKey, normalizedText)
    evidenceRef = f"{record.get('cellKey')}#{int(record.get('blockIdx', 0))}"
    return {
        "topic": str(record.get("topic") or ""),
        "period": str(record.get("period") or ""),
        "periodOrder": int(record.get("periodOrder") or 0),
        "sectionOrder": int(record.get("sectionOrder") or 0),
        "blockIdx": int(record.get("blockIdx") or 0),
        "blockType": blockType,
        "blockLabel": blockLabel,
        "semanticTopic": semanticTopic or None,
        "detailTopic": detailTopic or None,
        "isPlaceholder": bool(record.get("isPlaceholder")),
        "cellKey": str(record.get("cellKey") or ""),
        "evidenceRef": evidenceRef,
        "blockText": rawText,
        "normalizedText": normalizedText,
        "textHash": textHash,
        "tableShape": tableShape,
        "tableRows": tableRows,
        "tableCols": tableCols,
        "anchorKey": anchorKey,
        "structureKey": structureKey,
        "blockKey": blockKey,
    }


def _matchTopicBlocks(
    previousBlocks: list[dict[str, Any]] | None,
    currentBlocks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    previousBlocks = previousBlocks or []
    previousByStructure: dict[str, list[dict[str, Any]]] = {}
    previousByAnchor: dict[str, list[dict[str, Any]]] = {}
    previousByText: dict[str, list[dict[str, Any]]] = {}
    for block in previousBlocks:
        previousByStructure.setdefault(block["structureKey"], []).append(block)
        previousByAnchor.setdefault(block["anchorKey"], []).append(block)
        previousByText.setdefault(block["textHash"], []).append(block)

    matches: list[dict[str, Any]] = []
    counts = {
        "kept": 0,
        "added": 0,
        "removed": 0,
        "edited": 0,
        "moved": 0,
        "restated": 0,
        "placeholder": 0,
    }

    for current in currentBlocks:
        if current["isPlaceholder"]:
            anchorCandidates = previousByAnchor.get(current["anchorKey"], [])
            if anchorCandidates:
                previous = anchorCandidates.pop(0)
                previousByStructure[previous["structureKey"]].remove(previous)
                previousByText[previous["textHash"]].remove(previous)
            else:
                previous = None
            counts["placeholder"] += 1
            matches.append({"changeType": "placeholder", "current": current, "previous": previous})
            continue

        structureCandidates = previousByStructure.get(current["structureKey"], [])
        exactIdx = next(
            (idx for idx, block in enumerate(structureCandidates) if block["blockKey"] == current["blockKey"]),
            None,
        )
        if exactIdx is not None:
            previous = structureCandidates.pop(exactIdx)
            previousByText[previous["textHash"]].remove(previous)
            previousByAnchor[previous["anchorKey"]].remove(previous)
            counts["kept"] += 1
            matches.append({"changeType": "unchanged", "current": current, "previous": previous})
            continue

        if structureCandidates:
            previous = structureCandidates.pop(0)
            previousByText[previous["textHash"]].remove(previous)
            previousByAnchor[previous["anchorKey"]].remove(previous)
            similarity = _textSimilarity(previous["normalizedText"], current["normalizedText"])
            if similarity >= 0.95:
                counts["restated"] += 1
                matches.append({"changeType": "restated", "current": current, "previous": previous})
            else:
                counts["edited"] += 1
                matches.append({"changeType": "edited", "current": current, "previous": previous})
            continue

        anchorCandidates = previousByAnchor.get(current["anchorKey"], [])
        if anchorCandidates:
            previous = anchorCandidates.pop(0)
            previousByStructure[previous["structureKey"]].remove(previous)
            previousByText[previous["textHash"]].remove(previous)
            if current["blockType"] == "table":
                if current["tableRows"] > previous["tableRows"] or current["tableCols"] > previous["tableCols"]:
                    counts["added"] += 1
                    matches.append({"changeType": "added", "current": current, "previous": previous})
                elif current["tableRows"] < previous["tableRows"] or current["tableCols"] < previous["tableCols"]:
                    counts["removed"] += 1
                    matches.append({"changeType": "removed", "current": current, "previous": previous})
                else:
                    counts["edited"] += 1
                    matches.append({"changeType": "edited", "current": current, "previous": previous})
            else:
                similarity = _textSimilarity(previous["normalizedText"], current["normalizedText"])
                if similarity >= 0.95:
                    counts["restated"] += 1
                    matches.append({"changeType": "restated", "current": current, "previous": previous})
                else:
                    counts["edited"] += 1
                    matches.append({"changeType": "edited", "current": current, "previous": previous})
            continue

        textCandidates = previousByText.get(current["textHash"], [])
        if textCandidates:
            previous = textCandidates.pop(0)
            previousByStructure[previous["structureKey"]].remove(previous)
            previousByAnchor[previous["anchorKey"]].remove(previous)
            counts["moved"] += 1
            matches.append({"changeType": "moved", "current": current, "previous": previous})
            continue

        counts["added"] += 1
        matches.append({"changeType": "added", "current": current, "previous": None})

    for remaining in previousByStructure.values():
        for previous in remaining:
            counts["removed"] += 1
            matches.append({"changeType": "removed", "current": None, "previous": previous})

    return matches, counts


def _summarizeTopicChange(matches: list[dict[str, Any]], counts: dict[str, int]) -> tuple[str, str]:
    nonPlaceholder = sum(
        counts[key] for key in ("added", "removed", "edited", "moved", "restated")
    )
    if nonPlaceholder == 0 and counts["placeholder"] > 0:
        changeType = "placeholder"
    elif counts["moved"] > 0 and counts["added"] == counts["removed"] == counts["edited"] == counts["restated"] == 0:
        changeType = "moved"
    elif counts["restated"] > 0 and counts["added"] == counts["removed"] == counts["edited"] == counts["moved"] == 0:
        changeType = "restated"
    elif counts["added"] > 0 and counts["removed"] == counts["edited"] == counts["moved"] == counts["restated"] == 0:
        changeType = "added"
    elif counts["removed"] > 0 and counts["added"] == counts["edited"] == counts["moved"] == counts["restated"] == 0:
        changeType = "removed"
    elif counts["edited"] > 0 or counts["restated"] > 0 or counts["moved"] > 0 or (counts["added"] > 0 and counts["removed"] > 0):
        changeType = "edited"
    else:
        changeType = "unchanged"

    labels: list[str] = []
    for match in matches:
        block = match.get("current") or match.get("previous")
        if block is None:
            continue
        label = block.get("detailTopic") or block.get("semanticTopic") or block.get("blockLabel") or block.get("blockType")
        if label and label not in labels:
            labels.append(str(label))
        if len(labels) >= 3:
            break

    parts: list[str] = []
    for key, label in (
        ("added", "추가"),
        ("removed", "삭제"),
        ("edited", "수정"),
        ("moved", "이동"),
        ("restated", "재기재"),
        ("placeholder", "placeholder"),
    ):
        if counts[key] > 0:
            parts.append(f"{label} {counts[key]}")
    if not parts:
        parts.append("변경 없음")
    if labels:
        parts.append(", ".join(labels))
    return changeType, " · ".join(parts)


def _buildTopicChangeLedger(topicBlocks: pl.DataFrame | None) -> pl.DataFrame:
    schema = {
        "topic": pl.Utf8,
        "period": pl.Utf8,
        "previousPeriod": pl.Utf8,
        "changeType": pl.Utf8,
        "change": pl.Utf8,
        "summary": pl.Utf8,
        "evidenceRef": pl.Utf8,
        "text": pl.Utf8,
        "addedBlocks": pl.Int64,
        "removedBlocks": pl.Int64,
        "editedBlocks": pl.Int64,
        "movedBlocks": pl.Int64,
        "restatedBlocks": pl.Int64,
        "placeholderBlocks": pl.Int64,
    }
    if topicBlocks is None or topicBlocks.is_empty():
        return pl.DataFrame(schema=schema)

    from dartlab.engines.dart.docs.sections import sortPeriods

    canonicalBlocks = [_canonicalBlockRecord(record) for record in topicBlocks.to_dicts()]
    periods = sortPeriods(sorted({block["period"] for block in canonicalBlocks}), descending=False)
    statesByPeriod: dict[str, list[dict[str, Any]]] = {
        period: sorted(
            [block for block in canonicalBlocks if block["period"] == period],
            key=lambda row: (row["sectionOrder"], row["blockIdx"]),
        )
        for period in periods
    }

    rows: list[dict[str, Any]] = []
    previousState: list[dict[str, Any]] | None = None
    previousPeriod: str | None = None
    previousFingerprint: str | None = None

    for period in periods:
        currentState = statesByPeriod[period]
        currentFingerprint = _stableFingerprint(*(block["blockKey"] for block in currentState))
        if previousFingerprint is not None and currentFingerprint == previousFingerprint:
            continue

        if previousState is None:
            changeType = "initial"
            summary = "초기 기준점"
            evidenceRef = f"{currentState[0]['cellKey']}#period" if currentState else f"{period}"
            text = "\n\n".join(block["blockText"] for block in currentState if block["blockText"]).strip()
            rows.append({
                "topic": currentState[0]["topic"] if currentState else None,
                "period": period,
                "previousPeriod": None,
                "changeType": changeType,
                "change": changeType,
                "summary": summary,
                "evidenceRef": evidenceRef,
                "text": text,
                "addedBlocks": len(currentState),
                "removedBlocks": 0,
                "editedBlocks": 0,
                "movedBlocks": 0,
                "restatedBlocks": 0,
                "placeholderBlocks": sum(1 for block in currentState if block["isPlaceholder"]),
            })
        else:
            matches, counts = _matchTopicBlocks(previousState, currentState)
            if counts["kept"] == len(currentState) and counts["removed"] == 0 and counts["placeholder"] == 0:
                previousFingerprint = currentFingerprint
                previousState = currentState
                previousPeriod = period
                continue

            changeType, summary = _summarizeTopicChange(matches, counts)
            evidenceRef = f"{currentState[0]['cellKey']}#period" if currentState else f"{previousState[0]['cellKey']}#removed"
            text = "\n\n".join(block["blockText"] for block in currentState if block["blockText"]).strip()
            rows.append({
                "topic": currentState[0]["topic"] if currentState else previousState[0]["topic"],
                "period": period,
                "previousPeriod": previousPeriod,
                "changeType": changeType,
                "change": changeType,
                "summary": summary,
                "evidenceRef": evidenceRef,
                "text": text,
                "addedBlocks": counts["added"],
                "removedBlocks": counts["removed"],
                "editedBlocks": counts["edited"],
                "movedBlocks": counts["moved"],
                "restatedBlocks": counts["restated"],
                "placeholderBlocks": counts["placeholder"],
            })

        previousFingerprint = currentFingerprint
        previousState = currentState
        previousPeriod = period

    result = pl.DataFrame(rows, schema=schema, strict=False)
    if result.is_empty():
        return result
    from dartlab.engines.dart.docs.sections import sortPeriods
    ordered = sortPeriods(result.get_column("period").to_list())
    orderMap = {period: idx for idx, period in enumerate(ordered)}
    return (
        result
        .with_columns(pl.col("period").replace(orderMap).alias("_order"))
        .sort("_order")
        .drop("_order")
    )


def _buildTopicEvidence(topicBlocks: pl.DataFrame | None, period: str) -> pl.DataFrame:
    schema = {
        "topic": pl.Utf8,
        "period": pl.Utf8,
        "previousPeriod": pl.Utf8,
        "changeType": pl.Utf8,
        "evidenceRef": pl.Utf8,
        "blockType": pl.Utf8,
        "blockLabel": pl.Utf8,
        "semanticTopic": pl.Utf8,
        "detailTopic": pl.Utf8,
        "currentText": pl.Utf8,
        "previousText": pl.Utf8,
        "tableShape": pl.Utf8,
        "previousTableShape": pl.Utf8,
    }
    if topicBlocks is None or topicBlocks.is_empty():
        return pl.DataFrame(schema=schema)

    from dartlab.engines.dart.docs.sections import sortPeriods

    canonicalBlocks = [_canonicalBlockRecord(record) for record in topicBlocks.to_dicts()]
    periods = sortPeriods(sorted({block["period"] for block in canonicalBlocks}), descending=False)
    if period not in periods:
        return pl.DataFrame(schema=schema)

    periodIndex = periods.index(period)
    previousPeriod = periods[periodIndex - 1] if periodIndex > 0 else None
    currentState = sorted(
        [block for block in canonicalBlocks if block["period"] == period],
        key=lambda row: (row["sectionOrder"], row["blockIdx"]),
    )
    previousState = None
    if previousPeriod is not None:
        previousState = sorted(
            [block for block in canonicalBlocks if block["period"] == previousPeriod],
            key=lambda row: (row["sectionOrder"], row["blockIdx"]),
        )

    matches, _ = _matchTopicBlocks(previousState, currentState)
    rows: list[dict[str, Any]] = []
    for match in matches:
        current = match.get("current")
        previous = match.get("previous")
        block = current or previous
        if block is None:
            continue
        rows.append({
            "topic": block["topic"],
            "period": period,
            "previousPeriod": previousPeriod,
            "changeType": match["changeType"],
            "evidenceRef": (current or previous)["evidenceRef"],
            "blockType": block["blockType"],
            "blockLabel": block["blockLabel"],
            "semanticTopic": block.get("semanticTopic"),
            "detailTopic": block.get("detailTopic"),
            "currentText": None if current is None else current["blockText"],
            "previousText": None if previous is None else previous["blockText"],
            "tableShape": None if current is None else current.get("tableShape"),
            "previousTableShape": None if previous is None else previous.get("tableShape"),
        })

    if not rows and currentState:
        for current in currentState:
            rows.append({
                "topic": current["topic"],
                "period": period,
                "previousPeriod": previousPeriod,
                "changeType": "initial",
                "evidenceRef": current["evidenceRef"],
                "blockType": current["blockType"],
                "blockLabel": current["blockLabel"],
                "semanticTopic": current.get("semanticTopic"),
                "detailTopic": current.get("detailTopic"),
                "currentText": current["blockText"],
                "previousText": None,
                "tableShape": current.get("tableShape"),
                "previousTableShape": None,
            })

    return pl.DataFrame(rows, schema=schema, strict=False)


def _shapeString(df: pl.DataFrame | None) -> str:
    if df is None:
        return "-"
    return f"{df.height}x{df.width}"


def _noticeFrame(topic: str, message: str) -> pl.DataFrame:
    return pl.DataFrame({
        "topic": [topic],
        "message": [message],
    })


def _import_and_call(modulePath: str, funcName: str, stockCode: str, **kwargs) -> Any:
    """모듈을 lazy import하고 함수 호출."""
    import importlib
    mod = importlib.import_module(modulePath)
    func = getattr(mod, funcName)
    return func(stockCode, **kwargs)


def _financeToDataFrame(
    series: dict[str, dict[str, list]], years: list[str], sjDiv: str,
) -> pl.DataFrame | None:
    """finance 연도별 시계열 → 한글 계정명 × 연도 컬럼 DataFrame.

    Args:
        series: {"BS": {"snakeId": [v1, v2, ...]}, ...}
        years: ["2016", "2017", ...]
        sjDiv: "BS", "IS", "CF"

    Returns:
        계정명 | 2016 | 2017 | ... 형태의 DataFrame.
    """
    stmtData = series.get(sjDiv)
    if not stmtData:
        return None

    from dartlab.engines.dart.finance.mapper import AccountMapper
    mapper = AccountMapper.get()
    labels = mapper.labelMap()
    order = mapper.sortOrder(sjDiv)
    levels = mapper.levelMap(sjDiv)

    rows = []
    for snakeId, values in stmtData.items():
        label = labels.get(snakeId, snakeId)
        level = levels.get(snakeId, 2)
        sortKey = order.get(snakeId, 9999)
        row = {"계정명": label, "_snakeId": snakeId, "_level": level, "_sort": sortKey}
        for i, y in enumerate(years):
            row[y] = values[i] if i < len(values) else None
        rows.append(row)

    if not rows:
        return None

    rows.sort(key=lambda r: r["_sort"])
    df = pl.DataFrame(rows)
    df = df.drop(["_snakeId", "_level", "_sort"])
    return df


_RATIO_CATEGORY_LABELS: dict[str, str] = {
    "profitability": "수익성",
    "stability": "안정성",
    "growth": "성장성",
    "efficiency": "효율성",
    "cashflow": "현금흐름",
    "absolute": "절대규모",
}

_RATIO_FIELD_LABELS: dict[str, str] = {
    "roe": "ROE (%)",
    "roa": "ROA (%)",
    "operatingMargin": "영업이익률 (%)",
    "netMargin": "순이익률 (%)",
    "grossMargin": "매출총이익률 (%)",
    "ebitdaMargin": "EBITDA마진 (%)",
    "costOfSalesRatio": "매출원가율 (%)",
    "sgaRatio": "판관비율 (%)",
    "debtRatio": "부채비율 (%)",
    "currentRatio": "유동비율 (%)",
    "quickRatio": "당좌비율 (%)",
    "equityRatio": "자기자본비율 (%)",
    "interestCoverage": "이자보상배율 (x)",
    "netDebtRatio": "순차입금비율 (%)",
    "noncurrentRatio": "비유동비율 (%)",
    "revenueGrowth": "매출 YoY (%)",
    "operatingProfitGrowth": "영업이익 YoY (%)",
    "netProfitGrowth": "순이익 YoY (%)",
    "assetGrowth": "자산 YoY (%)",
    "equityGrowthRate": "자본 YoY (%)",
    "totalAssetTurnover": "총자산회전율 (x)",
    "inventoryTurnover": "재고자산회전율 (x)",
    "receivablesTurnover": "매출채권회전율 (x)",
    "payablesTurnover": "매입채무회전율 (x)",
    "fcf": "FCF",
    "operatingCfMargin": "영업CF마진 (%)",
    "operatingCfToNetIncome": "영업CF/순이익 (%)",
    "capexRatio": "CAPEX비율 (%)",
    "dividendPayoutRatio": "배당성향 (%)",
    "revenue": "매출",
    "operatingProfit": "영업이익",
    "netProfit": "순이익",
    "totalAssets": "총자산",
    "totalEquity": "자본(지배)",
    "operatingCashflow": "영업현금흐름",
}


_RATIO_TEMPLATE_FIELDS: dict[str, tuple[str, ...]] = {
    "bank": (
        "roe", "roa", "equityRatio",
        "operatingProfitGrowth", "netProfitGrowth", "assetGrowth", "equityGrowthRate",
        "dividendPayoutRatio",
        "operatingProfit", "netProfit", "totalAssets", "totalEquity", "operatingCashflow",
    ),
    "insurance": (
        "roe", "roa", "equityRatio",
        "operatingProfitGrowth", "netProfitGrowth", "assetGrowth", "equityGrowthRate",
        "dividendPayoutRatio",
        "operatingProfit", "netProfit", "totalAssets", "totalEquity", "operatingCashflow",
    ),
    "diversified_financials": (
        "roe", "roa", "operatingMargin", "netMargin", "ebitdaMargin",
        "equityRatio",
        "revenueGrowth", "operatingProfitGrowth", "netProfitGrowth", "assetGrowth", "equityGrowthRate",
        "totalAssetTurnover",
        "dividendPayoutRatio",
        "revenue", "operatingProfit", "netProfit", "totalAssets", "totalEquity", "operatingCashflow",
    ),
}


def _ratioTemplateKeyForIndustryGroup(industryGroup: Any) -> str | None:
    if industryGroup is None:
        return None

    try:
        from dartlab.engines.sector.types import IndustryGroup
    except ImportError:
        return None

    mapping = {
        IndustryGroup.BANK: "bank",
        IndustryGroup.INSURANCE: "insurance",
        IndustryGroup.DIVERSIFIED_FINANCIALS: "diversified_financials",
    }
    return mapping.get(industryGroup)


def _ratioArchetypeOverrideForIndustryGroup(industryGroup: Any) -> str | None:
    if industryGroup is None:
        return None

    try:
        from dartlab.engines.sector.types import IndustryGroup
    except ImportError:
        return None

    mapping = {
        IndustryGroup.BANK: "bank",
        IndustryGroup.INSURANCE: "insurance",
        IndustryGroup.DIVERSIFIED_FINANCIALS: "securities",
    }
    return mapping.get(industryGroup)


def _ratioResultHasHeadlineSignal(result: Any) -> bool:
    if result is None:
        return False

    headlineFields = (
        "roe",
        "roa",
        "operatingMargin",
        "netMargin",
        "debtRatio",
        "currentRatio",
        "equityRatio",
        "revenueTTM",
        "netIncomeTTM",
    )
    return any(getattr(result, fieldName, None) is not None for fieldName in headlineFields)


def _shouldFallbackToAnnualRatios(result: Any, archetypeOverride: str | None) -> bool:
    if result is None:
        return True

    if archetypeOverride in {"bank", "insurance", "securities"}:
        profitabilityFields = ("roe", "roa", "operatingMargin", "netMargin")
        return not any(getattr(result, fieldName, None) is not None for fieldName in profitabilityFields)

    return not _ratioResultHasHeadlineSignal(result)


def _ratioSeriesToDataFrame(
    series: dict[str, dict[str, list[Any | None]]], years: list[str], fieldNames: tuple[str, ...] | None = None,
) -> pl.DataFrame | None:
    """재무비율 연도별 시계열 → 분류/항목 × 연도 컬럼 DataFrame."""
    ratioData = series.get("RATIO")
    if not ratioData:
        return None

    from dartlab.engines.common.finance.ratios import RATIO_CATEGORIES

    fieldFilter = set(fieldNames) if fieldNames is not None else None
    rows: list[dict[str, Any]] = []
    for category, fields in RATIO_CATEGORIES:
        for fieldName in fields:
            if fieldFilter is not None and fieldName not in fieldFilter:
                continue
            values = ratioData.get(fieldName)
            if not values or not any(v is not None for v in values):
                continue
            row = {
                "분류": _RATIO_CATEGORY_LABELS.get(category, category),
                "항목": _RATIO_FIELD_LABELS.get(fieldName, fieldName),
                "_field": fieldName,
            }
            for idx, year in enumerate(years):
                row[str(year)] = values[idx] if idx < len(values) else None
            rows.append(row)

    if not rows:
        return None

    df = pl.DataFrame(rows)
    return df.drop("_field")


def _sceToDataFrame(
    series: dict[str, dict[str, list]], years: list[str],
) -> pl.DataFrame | None:
    """SCE 연도별 시계열 → 항목 × 연도 컬럼 DataFrame."""
    from dartlab.engines.dart.finance.sceMapper import CAUSE_LABELS, DETAIL_LABELS

    stmtData = series.get("SCE")
    if not stmtData:
        return None

    rows = []
    for item, values in stmtData.items():
        cause, _, detail = item.partition("__")
        causeKr = CAUSE_LABELS.get(cause)
        if causeKr is None:
            # other_파생금융상품평가손익 → 기타(파생금융상품평가손익)
            baseCause, _, suffix = cause.partition("_")
            baseKr = CAUSE_LABELS.get(baseCause, baseCause)
            suffixKr = suffix.replace("_", " ") if suffix else ""
            causeKr = f"{baseKr}({suffixKr})" if suffixKr else baseKr
        detailKr = DETAIL_LABELS.get(detail, detail) if detail else ""
        label = f"{causeKr} / {detailKr}" if detailKr else causeKr
        row = {
            "계정명": label,
            "_cause": cause,
            "_detail": detail,
            "_sort": item,
        }
        for i, y in enumerate(years):
            row[y] = values[i] if i < len(values) else None
        rows.append(row)

    if not rows:
        return None

    rows.sort(key=lambda r: (r["_cause"], r["_detail"], r["_sort"]))
    df = pl.DataFrame(rows)
    return df.drop(["_cause", "_detail", "_sort"])


def _financeCisAnnual(stockCode: str, fsDivPref: str = "CFS") -> tuple[dict[str, dict[str, list]], list[str]] | None:
    """finance 원본에서 CIS 연도별 시계열 생성.

    기본 buildAnnual()은 CIS를 IS로 병합하므로, 공개 Company 계층에서는
    포괄손익계산서(CIS)를 별도 canonical row로 보여주기 위해 raw normalized
    finance parquet를 다시 집계한다.
    """
    from dartlab.engines.common.finance.period import extractYear, formatPeriod
    from dartlab.engines.dart.finance.mapper import AccountMapper
    from dartlab.engines.dart.finance.pivot import _loadAndNormalize

    result = _loadAndNormalize(stockCode, fsDivPref)
    if result is None:
        return None

    df, periods = result
    df = df.filter(pl.col("sj_div") == "CIS")
    if df.is_empty():
        return None

    periodIdx = {p: i for i, p in enumerate(periods)}
    mapper = AccountMapper.get()
    qSeries: dict[str, list[Any | None]] = {}

    for row in df.iter_rows(named=True):
        accountId = row.get("account_id", "") or ""
        accountNm = row.get("account_nm", "") or ""
        snakeId = mapper.map(accountId, accountNm)
        if snakeId is None:
            continue

        pKey = formatPeriod(row.get("bsns_year", ""), {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}.get(row.get("reprt_nm", ""), 0))
        idx = periodIdx.get(pKey)
        if idx is None:
            continue

        if snakeId not in qSeries:
            qSeries[snakeId] = [None] * len(periods)
        if qSeries[snakeId][idx] is None:
            qSeries[snakeId][idx] = row.get("_normalized_amount")

    yearSet: dict[str, list[int]] = {}
    for i, p in enumerate(periods):
        yearSet.setdefault(extractYear(p), []).append(i)

    years = sorted(yearSet.keys())
    annualSeries: dict[str, list[Any | None]] = {}
    for snakeId, vals in qSeries.items():
        annualVals: list[Any | None] = [None] * len(years)
        for yIdx, year in enumerate(years):
            qVals = [vals[qi] for qi in yearSet[year] if qi < len(vals) and vals[qi] is not None]
            annualVals[yIdx] = sum(qVals) if qVals else None
        annualSeries[snakeId] = annualVals

    return {"CIS": annualSeries}, years


def _financeCisQuarterly(stockCode: str, fsDivPref: str = "CFS") -> tuple[dict[str, dict[str, list]], list[str]] | None:
    """finance 원본에서 CIS 분기별 시계열 생성 (연간 합산 없이)."""
    from dartlab.engines.common.finance.period import formatPeriod
    from dartlab.engines.dart.finance.mapper import AccountMapper
    from dartlab.engines.dart.finance.pivot import _loadAndNormalize

    result = _loadAndNormalize(stockCode, fsDivPref)
    if result is None:
        return None

    df, periods = result
    df = df.filter(pl.col("sj_div") == "CIS")
    if df.is_empty():
        return None

    periodIdx = {p: i for i, p in enumerate(periods)}
    mapper = AccountMapper.get()
    qSeries: dict[str, list[Any | None]] = {}

    for row in df.iter_rows(named=True):
        accountId = row.get("account_id", "") or ""
        accountNm = row.get("account_nm", "") or ""
        snakeId = mapper.map(accountId, accountNm)
        if snakeId is None:
            continue

        pKey = formatPeriod(row.get("bsns_year", ""), {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}.get(row.get("reprt_nm", ""), 0))
        idx = periodIdx.get(pKey)
        if idx is None:
            continue

        if snakeId not in qSeries:
            qSeries[snakeId] = [None] * len(periods)
        if qSeries[snakeId][idx] is None:
            qSeries[snakeId][idx] = row.get("_normalized_amount")

    return {"CIS": qSeries}, periods


def _ensureData(stockCode: str, category: str) -> bool:
    """로컬에 parquet이 있으면 True, 없으면 다운로드 시도 후 결과 반환."""
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.core.dataLoader import _dataDir, _download
    dest = _dataDir(category) / f"{stockCode}.parquet"
    if dest.exists():
        return True
    try:
        _download(stockCode, dest, category)
        label = DATA_RELEASES[category]["label"]
        print(f"[dartlab] {stockCode} ({label}) 다운로드 완료")
        return True
    except (OSError, RuntimeError):
        return False


class _ReportAccessor:
    """DART Company.report 네임스페이스 — 28개 apiType 체계 접근.

    pivot 함수가 있는 5개(dividend, employee, majorHolder, executive, audit)는
    전용 Result 반환. 나머지는 extractAnnual 기준 DataFrame 반환.

    Example::

        c.report.dividend         # DividendResult (pivot)
        c.report.treasuryStock    # DataFrame (extractAnnual)
        c.report.extract("dividend")  # DataFrame (정제 원본)
        c.report.apiTypes         # 사용 가능한 apiType 목록
    """

    _PIVOT_NAMES = frozenset({"dividend", "employee", "majorHolder", "executive", "audit"})

    def __init__(self, company: "Company"):
        self._company = company
        self._cache: dict[str, Any] = {}

    def _pivot(self, name: str) -> Any:
        if name in self._cache:
            return self._cache[name]
        from dartlab.engines.dart.report import (
            pivotAudit,
            pivotDividend,
            pivotEmployee,
            pivotExecutive,
            pivotMajorHolder,
        )
        funcs = {
            "dividend": pivotDividend,
            "employee": pivotEmployee,
            "majorHolder": pivotMajorHolder,
            "executive": pivotExecutive,
            "audit": pivotAudit,
        }
        func = funcs.get(name)
        if func is None:
            return None
        result = func(self._company.stockCode)
        self._cache[name] = result
        return result

    def extract(self, apiType: str) -> pl.DataFrame | None:
        """apiType별 정제된 DataFrame 반환."""
        cacheKey = f"_extract_{apiType}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.report import extractClean
        try:
            result = extractClean(self._company.stockCode, apiType)
        except Exception:  # noqa: BLE001
            result = None
        self._cache[cacheKey] = result
        return result

    def extractAnnual(self, apiType: str, quarterNum: int | None = None) -> pl.DataFrame | None:
        """apiType별 연간 DataFrame 반환."""
        cacheKey = f"_annual_{apiType}_{quarterNum}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.report import extractAnnual as _extractAnnual
        try:
            result = _extractAnnual(self._company.stockCode, apiType, quarterNum)
        except Exception:  # noqa: BLE001
            result = None
        self._cache[cacheKey] = result
        return result

    def result(self, apiType: str, quarterNum: int | None = None) -> Any | None:
        """apiType별 통일된 Result 반환.

        pivot 전용 5개는 기존 Result 객체를 그대로 돌려주고,
        나머지는 ReportResult를 반환한다.
        """
        cacheKey = f"_result_{apiType}_{quarterNum}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        if apiType in self._PIVOT_NAMES:
            result = getattr(self, apiType)
            self._cache[cacheKey] = result
            return result

        from dartlab.engines.dart.report import extractResult
        try:
            result = extractResult(self._company.stockCode, apiType, quarterNum)
        except Exception:  # noqa: BLE001
            result = None
        self._cache[cacheKey] = result
        return result

    def status(self, apiType: str | None = None) -> pl.DataFrame | dict[str, bool]:
        """apiType availability 확인."""
        from dartlab.engines.dart.report.types import API_TYPE_LABELS, API_TYPES, PREFERRED_QUARTER
        if apiType is not None:
            return {apiType: self.extract(apiType) is not None}

        rows = []
        for name in API_TYPES:
            rows.append({
                "apiType": name,
                "label": API_TYPE_LABELS.get(name, name),
                "preferredQuarter": PREFERRED_QUARTER.get(name),
                "isPivot": name in self._PIVOT_NAMES,
                "available": self.extract(name) is not None,
            })
        return pl.DataFrame(rows)

    @property
    def dividend(self):
        """배당 시계열 (DividendResult)."""
        return self._pivot("dividend")

    @property
    def employee(self):
        """직원현황 시계열 (EmployeeResult)."""
        return self._pivot("employee")

    @property
    def majorHolder(self):
        """최대주주현황 시계열 (MajorHolderResult)."""
        return self._pivot("majorHolder")

    @property
    def executive(self):
        """임원현황 (ExecutiveResult)."""
        return self._pivot("executive")

    @property
    def audit(self):
        """감사의견 시계열 (AuditResult)."""
        return self._pivot("audit")

    def __getattr__(self, name: str) -> Any:
        """미등록 apiType은 extractAnnual 자동 호출."""
        if name.startswith("_"):
            raise AttributeError(name)
        from dartlab.engines.dart.report.types import API_TYPES
        if name in API_TYPES and name not in self._PIVOT_NAMES:
            return self.extractAnnual(name)
        raise AttributeError(f"ReportAccessor에 '{name}' 항목이 없습니다. apiTypes: {API_TYPES}")

    @property
    def apiTypes(self) -> list[str]:
        """사용 가능한 apiType 목록."""
        from dartlab.engines.dart.report.types import API_TYPES
        return list(API_TYPES)

    @property
    def labels(self) -> dict[str, str]:
        """apiType → 한글명 매핑."""
        from dartlab.engines.dart.report.types import API_TYPE_LABELS
        return dict(API_TYPE_LABELS)

    @property
    def availableApiTypes(self) -> list[str]:
        """현재 parquet에 실제 존재하는 apiType 목록."""
        from dartlab.engines.dart.report.types import API_TYPES
        return [name for name in API_TYPES if self.extract(name) is not None]

    def __repr__(self):
        from dartlab.engines.dart.report.types import API_TYPES
        return f"ReportAccessor({len(API_TYPES)} apiTypes, {len(self._PIVOT_NAMES)} pivots)"


class _DocsAccessor:
    """docs source namespace."""

    def __init__(self, company: "Company"):
        self._company = company

    @property
    def raw(self) -> pl.DataFrame | None:
        return self._company.rawDocs

    def filings(self) -> pl.DataFrame:
        return self._company._filings()

    @property
    def sections(self) -> pl.DataFrame | None:
        return self._company._get_primary("sections")

    @property
    def retrievalBlocks(self) -> pl.DataFrame | None:
        return self._company._retrievalBlocks()

    @property
    def contextSlices(self) -> pl.DataFrame | None:
        return self._company._contextSlices()

    @property
    def notes(self):
        return self._company._notesAccessor

    @property
    def business(self):
        return self._company._get_primary("business")

    @property
    def mdna(self):
        return self._company._get_primary("mdna")

    @property
    def rawMaterial(self):
        return self._company._sectionsSubtopicWide("rawMaterial") or self._company._rawMaterialLegacy()

    def subtables(self, topic: str, *, raw: bool = False) -> pl.DataFrame | None:
        return self._company._sectionsSubtopicLong(topic) if raw else self._company._sectionsSubtopicWide(topic)


class _FinanceAccessor:
    """finance authoritative namespace."""

    def __init__(self, company: "Company"):
        self._company = company

    @property
    def raw(self) -> pl.DataFrame | None:
        return self._company.rawFinance

    @property
    def BS(self) -> pl.DataFrame | None:
        return self._company._financeOrDocsStatement("BS")

    @property
    def IS(self) -> pl.DataFrame | None:
        return self._company._financeOrDocsStatement("IS")

    @property
    def CIS(self) -> pl.DataFrame | None:
        return self._company._financeOrDocsStatement("CIS")

    @property
    def CF(self) -> pl.DataFrame | None:
        return self._company._financeOrDocsStatement("CF")

    @property
    def timeseries(self):
        return self._company._getFinanceBuild("q", "CFS")

    @property
    def annual(self):
        return self._company._getFinanceBuild("y", "CFS")

    @property
    def cumulative(self):
        return self._company._getFinanceBuild("cum", "CFS")

    @property
    def ratios(self):
        return self._company.getRatios("CFS")

    @property
    def ratioSeries(self):
        return self._company._ratioSeries()

    @property
    def sce(self):
        return self._company._sce()

    @property
    def SCE(self):
        return self._company._sce()

    @property
    def sceMatrix(self):
        return self._company._sceMatrix()


class _ProfileAccessor:
    """docs spine + finance/report authoritative merge."""

    _CANONICAL_TOPIC_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

    _PREFERRED_TOPIC_ORDER = [
        "BS",
        "IS",
        "CIS",
        "CF",
        "SCE",
        "ratios",
        "dividend",
        "employee",
        "majorHolder",
        "executive",
        "audit",
        "capitalChange",
        "treasuryStock",
        "stockTotal",
        "investedCompany",
        "majorHolderChange",
        "minorityHolder",
        "outsideDirector",
        "publicOfferingUsage",
        "privateOfferingUsage",
        "corporateBond",
        "shortTermBond",
        "auditContract",
        "nonAuditContract",
    ]

    _REPORT_AUTHORITATIVE_TOPICS = {
        "dividend",
        "employee",
        "majorHolder",
        "executive",
        "audit",
        "capitalChange",
        "treasuryStock",
        "stockTotal",
        "investedCompany",
        "majorHolderChange",
        "minorityHolder",
        "outsideDirector",
        "publicOfferingUsage",
        "privateOfferingUsage",
        "corporateBond",
        "shortTermBond",
        "auditContract",
        "nonAuditContract",
        "executivePayAllTotal",
        "executivePayIndividual",
        "unregisteredExecutivePay",
        "topPay",
        "debtSecurities",
        "commercialPaper",
        "hybridSecurities",
        "contingentCapital",
        "executivePayTotal",
        "executivePayByType",
    }

    def __init__(self, company: "Company"):
        self._company = company

    @classmethod
    def _isProfileTopic(cls, topic: Any) -> bool:
        if not isinstance(topic, str) or not topic:
            return False
        return bool(cls._CANONICAL_TOPIC_RE.fullmatch(topic))

    @property
    def sections(self) -> pl.DataFrame | None:
        cacheKey = "_profileSections"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]

        docsSections = self._company.docs.sections
        facts = self.facts

        if docsSections is None and facts is None:
            return None

        periodCols: list[str] = []
        if docsSections is not None:
            periodCols.extend([c for c in docsSections.columns if _isPeriodColumn(c)])
        if facts is not None and not facts.is_empty():
            factPeriods = facts["period"].drop_nulls().unique().to_list()
            periodCols.extend(str(p) for p in factPeriods if p is not None)

        if not periodCols:
            return docsSections

        from dartlab.engines.dart.docs.sections import sortPeriods
        periodCols = sortPeriods(sorted(set(periodCols)))

        rowMap: dict[str, dict[str, Any]] = {}
        docsTopicOrder: list[str] = []
        if docsSections is not None:
            for row in docsSections.iter_rows(named=True):
                topic = row["topic"]
                if not self._isProfileTopic(topic):
                    continue
                docsTopicOrder.append(topic)
                rowMap[topic] = {"topic": topic}
                for period in periodCols:
                    rowMap[topic][period] = row.get(period)

        if facts is not None and not facts.is_empty():
            primaryFacts = (
                facts
                .sort(["priority", "source"], descending=[True, False])
                .group_by(["topic", "period"])
                .agg([
                    pl.col("source").first().alias("primarySource"),
                    pl.col("summary").first().alias("summary"),
                ])
            )

            for row in primaryFacts.iter_rows(named=True):
                topic = row["topic"]
                if not self._isProfileTopic(topic):
                    continue
                period = row["period"]
                summary = row["summary"]
                source = row["primarySource"]
                if topic not in rowMap:
                    rowMap[topic] = {"topic": topic}
                    for col in periodCols:
                        rowMap[topic][col] = None
                if rowMap[topic].get(period) is None and summary:
                    rowMap[topic][period] = summary

        orderedTopics: list[str] = []
        seen: set[str] = set()

        for topic in docsTopicOrder:
            if topic in rowMap and topic not in seen:
                orderedTopics.append(topic)
                seen.add(topic)

        remaining = [t for t in rowMap if t not in seen]
        prefOrder = {topic: idx for idx, topic in enumerate(self._PREFERRED_TOPIC_ORDER)}
        remaining.sort(key=lambda t: (prefOrder.get(t, 9999), t))
        orderedTopics.extend(remaining)

        records = [rowMap[t] for t in orderedTopics]
        result = pl.from_dicts(records, infer_schema_length=len(records)).select(["topic", *periodCols])
        castCols = [pl.col("topic").cast(pl.Utf8)]
        castCols.extend(pl.col(col).cast(pl.Utf8, strict=False) for col in periodCols)
        result = result.with_columns(castCols)
        self._company._cache[cacheKey] = result
        return result

    @property
    def facts(self) -> pl.DataFrame | None:
        cacheKey = "_profileFacts"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]

        frames: list[pl.DataFrame] = []

        annual = self._company.finance.annual
        if annual is not None:
            series, years = annual
            for sj in ("BS", "IS", "CF"):
                stmt = series.get(sj, {})
                if not stmt:
                    continue
                rows = []
                for item, values in stmt.items():
                    for idx, year in enumerate(years):
                        value = values[idx] if idx < len(values) else None
                        if value is None:
                            continue
                        rows.append({
                            "topic": sj,
                            "period": str(year),
                            "source": "finance",
                            "valueType": "number",
                            "valueKey": item,
                            "value": value,
                            "payloadRef": f"finance:{sj}:{item}",
                            "priority": 300,
                            "summary": f"{item}={value}",
                        })
                if rows:
                    frames.append(pl.DataFrame(rows))

        cisAnnual = self._company._financeCisAnnual()
        if cisAnnual is not None:
            cisSeries, years = cisAnnual
            rows = []
            for item, values in cisSeries.get("CIS", {}).items():
                for idx, year in enumerate(years):
                    value = values[idx] if idx < len(values) else None
                    if value is None:
                        continue
                    rows.append({
                        "topic": "CIS",
                        "period": str(year),
                        "source": "finance",
                        "valueType": "number",
                        "valueKey": item,
                        "value": value,
                        "payloadRef": f"finance:CIS:{item}",
                        "priority": 300,
                        "summary": f"{item}={value}",
                    })
            if rows:
                frames.append(pl.DataFrame(rows))

        sce = self._company._sceSeriesAnnual()
        if sce is not None:
            sceSeries, years = sce
            for item, values in sceSeries.get("SCE", {}).items():
                rows = []
                for idx, year in enumerate(years):
                    value = values[idx] if idx < len(values) else None
                    if value is None:
                        continue
                    rows.append({
                        "topic": "SCE",
                        "period": str(year),
                        "source": "finance",
                        "valueType": "number",
                        "valueKey": item,
                        "value": value,
                        "payloadRef": f"finance:SCE:{item}",
                        "priority": 300,
                        "summary": f"{item}={value}",
                    })
                if rows:
                    frames.append(pl.DataFrame(rows))

        if self._company.report is not None:
            for apiType in self._company.report.apiTypes:
                df = self._company.report.extractAnnual(apiType)
                if df is None or df.is_empty():
                    continue
                rows = []
                for row in df.iter_rows(named=True):
                    year = row.get("year")
                    quarter = row.get("quarter")
                    summaryParts = []
                    for key, value in row.items():
                        if key in {"stockCode", "year", "quarter", "quarterNum", "apiType", "stlm_dt"}:
                            continue
                        if value is None:
                            continue
                        summaryParts.append(f"{key}={value}")
                        rows.append({
                            "topic": self._canonicalReportTopic(apiType),
                            "period": str(year),
                            "source": "report",
                            "valueType": "field",
                            "valueKey": key,
                            "value": str(value),
                            "payloadRef": f"report:{apiType}:{quarter}",
                            "priority": 200,
                            "summary": None,
                        })
                    if rows and summaryParts:
                        summary = "; ".join(summaryParts[:6])
                        for item in rows[-len(summaryParts):]:
                            item["summary"] = summary
                if rows:
                    frames.append(pl.DataFrame(rows))

        docsBlocks = self._company.docs.retrievalBlocks
        if docsBlocks is not None and not docsBlocks.is_empty():
            docsRows = []
            for row in docsBlocks.iter_rows(named=True):
                period = row.get("period")
                blockText = row.get("blockText")
                if period is None or not blockText:
                    continue
                topic = row.get("detailTopic") or row.get("semanticTopic") or row.get("topic")
                if topic is None:
                    continue
                docsRows.append({
                    "topic": str(topic),
                    "period": str(period),
                    "source": "docs",
                    "valueType": row.get("blockType") or "text",
                    "valueKey": row.get("blockLabel") or row.get("rawTitle") or str(topic),
                    "value": str(blockText),
                    "payloadRef": row.get("cellKey") or f"docs:{topic}:{period}",
                    "priority": 100,
                    "summary": str(blockText)[:400],
                })
            if docsRows:
                frames.append(pl.DataFrame(docsRows))

        result = pl.concat(frames, how="vertical_relaxed") if frames else None
        self._company._cache[cacheKey] = result
        return result

    @property
    def availableTopics(self) -> list[str]:
        topics = set()
        if self.sections is not None and "topic" in self.sections.columns:
            topics.update(self.sections["topic"].to_list())
        facts = self.facts
        if facts is not None and "topic" in facts.columns:
            topics.update(facts["topic"].unique().to_list())
        return sorted(str(t) for t in topics if t is not None)

    def get(self, topic: str) -> Any:
        if topic in {"BS", "IS", "CF", "CIS"}:
            return getattr(self._company.finance, topic)
        if topic == "SCE":
            return self._company.finance.sce
        if topic in self._REPORT_AUTHORITATIVE_TOPICS and self._company.report is not None:
            if topic == "audit":
                return self._company.report.audit
            return getattr(self._company.report, topic, None)
        sections = self.sections
        if sections is None:
            return None
        return sections.filter(pl.col("topic") == topic)

    def trace(self, topic: str, period: str | None = None) -> pl.DataFrame | dict[str, Any] | None:
        facts = self.facts
        docsSections = self._company.docs.sections

        sources: list[dict[str, Any]] = []

        if facts is not None:
            traced = facts.filter(pl.col("topic") == topic)
            if period is not None:
                traced = traced.filter(pl.col("period") == period)
            if not traced.is_empty():
                grouped = traced.group_by("source").agg([
                    pl.len().alias("rows"),
                    pl.col("payloadRef").first().alias("payloadRef"),
                    pl.col("summary").first().alias("summary"),
                    pl.col("priority").max().alias("priority"),
                ])
                sources.extend(grouped.iter_rows(named=True))

        if docsSections is not None and topic in docsSections["topic"].to_list():
            row = docsSections.filter(pl.col("topic") == topic)
            if not row.is_empty():
                periodCols = [c for c in docsSections.columns if _isPeriodColumn(c)]
                if period is not None and period in periodCols:
                    value = row.item(0, period)
                    if value is not None:
                        sources.append({
                            "source": "docs",
                            "rows": 1,
                            "payloadRef": f"docs-sections:{topic}:{period}",
                            "summary": str(value)[:400],
                            "priority": 100,
                        })

        if not sources:
            return None

        sources.sort(key=lambda r: (r.get("priority", 0), r.get("source", "")), reverse=True)
        primary = sources[0]
        return {
            "topic": topic,
            "period": period,
            "primarySource": primary.get("source"),
            "fallbackSources": [r.get("source") for r in sources[1:]],
            "selectedPayloadRef": primary.get("payloadRef"),
            "availableSources": sources,
            "whySelected": f"{self._sourcePriority(topic)} authoritative priority",
        }

    def _canonicalReportTopic(self, apiType: str) -> str:
        if apiType == "auditOpinion":
            return "audit"
        return apiType

    def _sourcePriority(self, topic: str) -> str:
        if topic in {"BS", "IS", "CIS", "CF", "SCE"}:
            return "finance"
        if topic in self._REPORT_AUTHORITATIVE_TOPICS:
            return "report"
        return "docs"


class _BoardView(OrderedDict):
    """사용자용 회사 프로파일 뷰."""

    def __init__(self, company: "Company", payload: OrderedDict[str, OrderedDict[str, pl.DataFrame]], *, raw: bool):
        super().__init__(payload)
        self._company = company
        self._raw = raw

    @property
    def sections(self) -> pl.DataFrame | None:
        return self._company._profileAccessor.sections

    @property
    def facts(self) -> pl.DataFrame | None:
        return self._company._profileAccessor.facts

    @property
    def topics(self) -> list[str]:
        return self._company.topics

    @property
    def availableTopics(self) -> list[str]:
        return self._company.topics

    def get(self, topic: str, default: Any = None) -> Any:
        payload = self._company.show(topic, raw=self._raw)
        if payload is None:
            return default
        return payload

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
        return self._company.trace(topic, period=period)

    def show(self, topic: str, *, period: str | None = None, raw: bool | None = None) -> Any:
        effectiveRaw = self._raw if raw is None else raw
        return self._company.show(topic, period=period, raw=effectiveRaw)

    @property
    def ledger(self) -> pl.DataFrame:
        cacheKey = "_profileLedgerRaw" if self._raw else "_profileLedger"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]

        rows: list[pl.DataFrame] = []
        for chapter, topics in self.items():
            for topic in topics:
                ledger = self._company._topicChangeLedger(topic)
                if ledger is None or ledger.is_empty():
                    continue
                rows.append(
                    ledger.with_columns(
                        pl.lit(chapter).alias("chapter"),
                        pl.lit(self._company._topicLabel(topic)).alias("label"),
                    ).select([
                        "chapter",
                        "topic",
                        "label",
                        "period",
                        "previousPeriod",
                        "changeType",
                        "summary",
                        "evidenceRef",
                        "text",
                        "addedBlocks",
                        "removedBlocks",
                        "editedBlocks",
                        "movedBlocks",
                        "restatedBlocks",
                        "placeholderBlocks",
                    ])
                )

        result = pl.concat(rows, how="vertical_relaxed") if rows else pl.DataFrame(
            schema={
                "chapter": pl.Utf8,
                "topic": pl.Utf8,
                "label": pl.Utf8,
                "period": pl.Utf8,
                "previousPeriod": pl.Utf8,
                "changeType": pl.Utf8,
                "summary": pl.Utf8,
                "evidenceRef": pl.Utf8,
                "text": pl.Utf8,
                "addedBlocks": pl.Int64,
                "removedBlocks": pl.Int64,
                "editedBlocks": pl.Int64,
                "movedBlocks": pl.Int64,
                "restatedBlocks": pl.Int64,
                "placeholderBlocks": pl.Int64,
            }
        )
        self._company._cache[cacheKey] = result
        return result

    def evidence(self, topic: str, period: str) -> pl.DataFrame:
        return self._company._topicEvidence(topic, period)

    @property
    def index(self) -> pl.DataFrame:
        cacheKey = "_profileIndexRaw" if self._raw else "_profileIndex"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]

        rows: list[dict[str, Any]] = []
        if not self._company._hasDocs:
            rows.append({
                "chapter": "안내",
                "topic": "docsStatus",
                "label": "사업보고서",
                "kind": "notice",
                "source": "docs",
                "periods": "-",
                "shape": "missing",
                "preview": "현재 사업보고서 부재",
            })
        for chapter, topics in self.items():
            for topic, payload in topics.items():
                traced = self._company.trace(topic)
                rows.append({
                    "chapter": chapter,
                    "topic": topic,
                    "label": self._company._topicLabel(topic),
                    "kind": self._kindForPayload(payload),
                    "source": traced["primarySource"] if traced is not None else None,
                    "periods": self._periodsForPayload(payload),
                    "shape": _shapeString(payload) if isinstance(payload, pl.DataFrame) else type(payload).__name__,
                    "preview": self._previewForPayload(payload),
                })

        df = pl.DataFrame(rows) if rows else pl.DataFrame(schema={
            "chapter": pl.Utf8,
            "topic": pl.Utf8,
            "label": pl.Utf8,
            "kind": pl.Utf8,
            "source": pl.Utf8,
            "periods": pl.Utf8,
            "shape": pl.Utf8,
            "preview": pl.Utf8,
        })
        self._company._cache[cacheKey] = df
        return df

    def _kindForPayload(self, payload: Any) -> str:
        if not isinstance(payload, pl.DataFrame):
            return type(payload).__name__
        cols = set(payload.columns)
        if {"topic", "period", "changeType", "summary", "evidenceRef"}.issubset(cols):
            return "ledger"
        if {"topic", "period", "change", "text"}.issubset(cols):
            return "text"
        if "period" in cols:
            return "timeseries"
        if any(_isPeriodColumn(col) for col in payload.columns if col != "topic"):
            return "wide"
        return "dataframe"

    def _periodsForPayload(self, payload: Any) -> str:
        if not isinstance(payload, pl.DataFrame) or payload.is_empty():
            return "-"
        if "period" in payload.columns:
            periods = [str(v) for v in payload["period"].drop_nulls().to_list()]
            if not periods:
                return "-"
            return f"{periods[-1]}..{periods[0]}" if len(periods) > 1 else periods[0]
        periodCols = [col for col in payload.columns if _isPeriodColumn(col)]
        if not periodCols:
            return "-"
        return f"{periodCols[-1]}..{periodCols[0]}" if len(periodCols) > 1 else periodCols[0]

    def _previewForPayload(self, payload: Any) -> str:
        if not isinstance(payload, pl.DataFrame) or payload.is_empty():
            return "-"
        cols = set(payload.columns)
        if {"topic", "period", "changeType", "summary", "evidenceRef"}.issubset(cols):
            summary = payload.item(0, "summary")
            return _normalizeTextCell(summary)[:120]
        if {"topic", "period", "change", "text"}.issubset(cols):
            text = payload.item(0, "text")
            return _normalizeTextCell(text)[:120]
        periodCols = [col for col in payload.columns if _isPeriodColumn(col)]
        if periodCols:
            for period in periodCols:
                value = payload.item(0, period)
                text = _normalizeTextCell(value)
                if text:
                    return f"{period}: {text[:100]}"
        return ", ".join(payload.columns[:4])

    def __repr__(self) -> str:
        chapterCount = len(self)
        topicCount = sum(len(topics) for topics in self.values())
        kind = "profile" if not self._raw else "profile(raw)"
        ledger = self.ledger
        if ledger.is_empty():
            return f"{kind}({chapterCount} chapters, {topicCount} topics)\n{self.index}"
        return f"{kind}({chapterCount} chapters, {topicCount} topics)\n{ledger}"

    __str__ = __repr__

    def _repr_html_(self) -> str:
        ledger = self.ledger
        if hasattr(ledger, "_repr_html_"):
            return ledger._repr_html_()
        return f"<pre>{self}</pre>"


class ShowResult(NamedTuple):
    """show() 반환 — text와 table을 분리."""

    text: pl.DataFrame | None
    table: pl.DataFrame | None


class Company:
    """DART 기반 한국 상장기업 분석.

    기본 사용 모델은 index / show / trace다.

    - ``index``: sections 뼈대 위에 finance/report가 채워진 수평화 보드
    - ``show(topic)``: 특정 topic의 실제 payload(DataFrame)
    - ``trace(topic, period)``: 선택 source와 provenance

    3개 데이터 소스를 강점 기반으로 선별하여 제공:

    - **finance** (XBRL 정규화): BS/IS/CIS/CF/SCE, timeseries, annual, ratios
    - **report** (DART API 정형): 28개 apiType 체계, 현재 가용 항목 중심 structured disclosure
    - **docs** (HTML 파싱): 서술형(business, mdna), K-IFRS 주석(notes), 거버넌스, 리스크 등

    소스 우선순위:
    - docs sections 수평화가 구조의 spine
    - finance가 숫자 재무 authoritative source
    - report가 정형 공시 authoritative source
    - Company는 이 세 source를 merged board로 제공한다

    Example::

        c = Company("005930")           # 삼성전자
        c.index                          # 전체 수평화 보드
        c.show("BS")                     # 재무상태표
        c.show("salesOrder")             # sections 기반 subtopic DataFrame
        c.show("costByNature")           # sections/detailTopic 우선 + legacy fallback
        c.trace("dividend")              # source provenance
        c.finance.CIS                    # 포괄손익계산서
        c.finance.SCE                    # 자본변동표
        c.report.treasuryStock           # 정형 공시
        c.docs.sections                  # pure docs source view
    """

    def __init__(self, codeOrName: str):
        normalized = codeOrName.strip()
        if re.match(r"^[0-9A-Za-z]{6}$", normalized):
            self.stockCode = normalized.upper()
        else:
            code = nameToCode(normalized)
            if code is None:
                raise ValueError(f"'{normalized}'에 해당하는 종목을 찾을 수 없음")
            self.stockCode = code
        self._cache: dict[str, Any] = {}

        self._hasDocs = _ensureData(self.stockCode, "docs")
        self._hasFinance = _ensureData(self.stockCode, "finance")
        self._hasReport = _ensureData(self.stockCode, "report")

        if self._hasDocs:
            df = loadData(self.stockCode, category="docs")
            self.corpName = extractCorpName(df)
        else:
            self.corpName = codeToName(self.stockCode)

        if self._hasFinance:
            from dartlab.engines.dart.finance.pivot import buildTimeseries
            ts = buildTimeseries(self.stockCode)
            if ts is not None:
                self._cache["_finance_q_CFS"] = ts
            else:
                self._hasFinance = False

        if not self._hasDocs and not self._hasFinance and not self._hasReport:
            raise ValueError(f"'{self.stockCode}' 데이터 없음 (docs/finance/report 모두 없음)")

        self._notesAccessor = Notes(self) if self._hasDocs else None
        self.docs = _DocsAccessor(self)
        self.finance = _FinanceAccessor(self)
        self.report = _ReportAccessor(self)
        self._profileAccessor = _ProfileAccessor(self)

    def __repr__(self):
        from dartlab import config
        if config.verbose:
            from dartlab.display import printRepr
            from dartlab.engines.dart.docs.notes import _REGISTRY as notesRegistry
            nProps = len([p for p in _ALL_PROPERTIES if p[0] not in ("BS", "IS", "CF")])
            nNotes = len(notesRegistry) if self._hasDocs else 0
            printRepr(self.corpName, self.stockCode, nProps, nNotes)
            return ""
        return f"Company({self.stockCode}, {self.corpName})"

    def guide(self):
        """전체 사용 가이드 출력."""
        from dartlab.display import printGuide
        from dartlab.engines.dart.docs.notes import _REGISTRY as notesRegistry
        props = [p[0] for p in _ALL_PROPERTIES if p[0] not in ("BS", "IS", "CF")]
        if self._hasDocs:
            noteKeys = list(notesRegistry.keys())
            noteKeysKr = [v[1] for v in notesRegistry.values()]
        else:
            noteKeys = []
            noteKeysKr = []
        printGuide(self.corpName, self.stockCode, props, noteKeys, noteKeysKr)

    # ── 내부 호출 ──

    def _call_module(self, name: str, **kwargs) -> Any:
        """모듈 호출 + 캐싱. Notes에서도 사용."""
        if not self._hasDocs:
            return None
        cacheKey = f"{name}:{kwargs}" if kwargs else name
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        idx = _MODULE_INDEX[name]
        entry = _MODULE_REGISTRY[idx]
        result = _import_and_call(entry[0], entry[1], self.stockCode, **kwargs)
        self._cache[cacheKey] = result
        return result

    def _call_notesDetail(self, keyword: str) -> Any:
        """notesDetail 호출 (키워드별 캐싱)."""
        if not self._hasDocs:
            return None
        cacheKey = f"notesDetail:{keyword}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        result = _import_and_call(
            "dartlab.engines.dart.docs.finance.notesDetail", "notesDetail",
            self.stockCode, keyword=keyword,
        )
        self._cache[cacheKey] = result
        return result

    def _get_primary(self, name: str, **kwargs) -> Any:
        """모듈 호출 후 primary DataFrame 추출."""
        from dartlab import config
        cacheKey = f"{name}:{kwargs}" if kwargs else name
        idx = _MODULE_INDEX[name]
        entry = _MODULE_REGISTRY[idx]
        label = entry[2]

        if config.verbose and cacheKey not in self._cache:
            print(f"  ▶ {self.corpName} · {label}")

        result = self._call_module(name, **kwargs)
        extractor = entry[3]
        if result is None:
            return None
        if extractor is None:
            return result
        return extractor(result)

    # ── 인덱스·메타 ──

    @staticmethod
    def listing(*, forceRefresh: bool = False) -> pl.DataFrame:
        """KRX 전체 상장법인 목록 (KIND 기준)."""
        return getKindList(forceRefresh=forceRefresh)

    @staticmethod
    def search(keyword: str) -> pl.DataFrame:
        """회사명 부분 검색 (KIND 목록 기준)."""
        return searchName(keyword)

    @staticmethod
    def resolve(codeOrName: str) -> str | None:
        """종목코드 또는 회사명 → 종목코드 변환."""
        normalized = codeOrName.strip()
        if re.match(r"^[0-9A-Za-z]{6}$", normalized):
            return normalized.upper()
        return nameToCode(normalized)

    @staticmethod
    def codeName(stockCode: str) -> str | None:
        """종목코드 → 회사명 변환."""
        return codeToName(stockCode)

    @staticmethod
    def status() -> pl.DataFrame:
        """로컬에 보유한 전체 종목 인덱스."""
        return buildIndex()

    def _filings(self) -> pl.DataFrame:
        """이 종목의 공시 문서 목록 + DART 뷰어 링크."""
        if not self._hasDocs:
            return pl.DataFrame(schema={"year": pl.Utf8, "rceptDate": pl.Utf8, "rceptNo": pl.Utf8, "reportType": pl.Utf8, "dartUrl": pl.Utf8})
        df = loadData(self.stockCode)
        docs = (
            df.select("year", "rcept_date", "rcept_no", "report_type")
            .unique(subset=["rcept_no"])
            .with_columns(
                pl.lit(DART_VIEWER).add(pl.col("rcept_no")).alias("dartUrl"),
            )
            .rename({
                "report_type": "reportType",
                "rcept_date": "rceptDate",
                "rcept_no": "rceptNo",
            })
            .sort("year", "rceptDate", descending=[True, True])
        )
        return docs

    def filings(self) -> pl.DataFrame:
        """공시 문서 목록 + DART 뷰어 링크."""
        return self._filings()

    # ── 원본 데이터 (property) ──

    @property
    def rawDocs(self) -> pl.DataFrame | None:
        """공시 문서 원본 parquet 전체 (가공 전)."""
        if not self._hasDocs:
            return None
        cacheKey = "_rawDocs"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="docs")
        self._cache[cacheKey] = df
        return df

    @property
    def rawFinance(self) -> pl.DataFrame | None:
        """재무제표 원본 parquet 전체 (가공 전)."""
        if not self._hasFinance:
            return None
        cacheKey = "_rawFinance"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="finance")
        self._cache[cacheKey] = df
        return df

    @property
    def rawReport(self) -> pl.DataFrame | None:
        """정기보고서 원본 parquet 전체 (가공 전)."""
        if not self._hasReport:
            return None
        cacheKey = "_rawReport"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="report")
        self._cache[cacheKey] = df
        return df

    @property
    def notes(self):
        """K-IFRS notes accessor (compat)."""
        return self._notesAccessor

    def _retrievalBlocks(self) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        cacheKey = "retrievalBlocks"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.docs.sections import retrievalBlocks
        result = retrievalBlocks(self.stockCode)
        self._cache[cacheKey] = result
        return result

    def _contextSlices(self) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        cacheKey = "contextSlices"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.docs.sections import contextSlices
        result = contextSlices(self.stockCode)
        self._cache[cacheKey] = result
        return result

    def _rawMaterial(self) -> Any:
        from dartlab import config
        if config.verbose:
            print(f"  ▶ {self.corpName} · 원재료설비")
        return self._call_module("rawMaterial")

    def _rawMaterialLegacy(self) -> Any:
        try:
            return self._rawMaterial()
        except Exception:  # noqa: BLE001
            return None

    def _topicSubtables(self, topic: str):
        cacheKey = f"_topicSubtables:{topic}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        blocks = self._retrievalBlocks()
        if blocks is None or blocks.is_empty():
            self._cache[cacheKey] = None
            return None
        from dartlab.engines.dart.docs.sections import topicSubtables
        result = topicSubtables(blocks, topic)
        self._cache[cacheKey] = result
        return result

    def _sectionsSubtopicWide(self, topic: str) -> pl.DataFrame | None:
        result = self._topicSubtables(topic)
        return None if result is None else result.wide

    def _sectionsSubtopicLong(self, topic: str) -> pl.DataFrame | None:
        result = self._topicSubtables(topic)
        return None if result is None else result.long

    # subtopic 자동 수평화를 건너뛰는 topic (이미 다른 경로에서 처리되거나 subtopic 과다)
    _AUTO_SUBTOPIC_SKIP: frozenset[str] = frozenset({
        # 이미 명시적 subtopic 경로
        "salesOrder", "riskDerivative", "segments", "rawMaterial", "costByNature",
        # 재무제표 — finance 엔진이 authoritative
        "BS", "IS", "CIS", "CF", "SCE", "ratios",
        # fsSummary — subtopic 800+ (과다)
        "fsSummary",
        # 주석 — 너무 방대하여 subtopic 세분화 비효율
        "consolidatedNotes", "financialNotes",
    })

    _AUTO_SUBTOPIC_MAX = 100  # subtopic이 이 수를 넘으면 text fallback

    def _autoSubtopicWide(self, topic: str, *, raw: bool = False) -> pl.DataFrame | None:
        """table-heavy docs topic을 자동으로 subtopic wide 수평화."""
        if topic in self._AUTO_SUBTOPIC_SKIP:
            return None
        result = self._topicSubtables(topic)
        if result is None:
            return None
        if result.wide.height > self._AUTO_SUBTOPIC_MAX:
            return None
        return result.long if raw else result.wide

    def _safePrimary(self, name: str) -> pl.DataFrame | None:
        try:
            payload = self._get_primary(name)
        except Exception:  # noqa: BLE001
            return None
        return payload if isinstance(payload, pl.DataFrame) else None

    def _hasDocsTopicHint(self, topic: str) -> bool:
        cacheKey = f"_hasDocsTopicHint:{topic}"
        if cacheKey in self._cache:
            return bool(self._cache[cacheKey])
        keywords = _DOCS_TOPIC_HINTS.get(topic)
        if not self._hasDocs or not keywords:
            self._cache[cacheKey] = False
            return False
        raw = self.rawDocs
        if raw is None or raw.is_empty():
            self._cache[cacheKey] = False
            return False
        matched = False
        for keyword in keywords:
            subset = raw.filter(
                pl.col("section_title").str.contains(keyword, literal=True, strict=False)
                | pl.col("section_content").str.contains(keyword, literal=True, strict=False)
            )
            if not subset.is_empty():
                matched = True
                break
        self._cache[cacheKey] = matched
        return matched

    def _hasSectionTitleHint(self, topic: str) -> bool:
        cacheKey = f"_hasSectionTitleHint:{topic}"
        if cacheKey in self._cache:
            return bool(self._cache[cacheKey])
        keywords = _DOCS_TITLE_HINTS.get(topic)
        if not self._hasDocs or not keywords:
            self._cache[cacheKey] = False
            return False
        path = Path(_dataDir("docs")) / f"{self.stockCode}.parquet"
        if not path.exists():
            self._cache[cacheKey] = False
            return False
        matched = False
        for keyword in keywords:
            subset = (
                pl.scan_parquet(path)
                .select("section_title")
                .filter(pl.col("section_title").str.contains(keyword, literal=True, strict=False))
                .limit(1)
                .collect()
            )
            if subset.height > 0:
                matched = True
                break
        self._cache[cacheKey] = matched
        return matched

    def _sceMatrix(self):
        if not self._hasFinance:
            return None
        cacheKey = "_sceMatrix_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.finance.pivot import buildSceMatrix
        result = buildSceMatrix(self.stockCode)
        self._cache[cacheKey] = result
        return result

    def _sceSeriesAnnual(self):
        if not self._hasFinance:
            return None
        cacheKey = "_sceAnnual_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.finance.pivot import buildSceAnnual
        result = buildSceAnnual(self.stockCode)
        self._cache[cacheKey] = result
        return result

    def _sce(self) -> pl.DataFrame | None:
        cacheKey = "_sceDataFrame_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        result = self._sceSeriesAnnual()
        if result is None:
            self._cache[cacheKey] = None
            return None
        series, years = result
        df = _sceToDataFrame(series, years)
        self._cache[cacheKey] = df
        return df

    def _financeCisAnnual(self):
        if not self._hasFinance:
            return None
        cacheKey = "_financeCISAnnual_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        result = _financeCisAnnual(self.stockCode, "CFS")
        self._cache[cacheKey] = result
        return result

    def _financeCisQuarterly(self):
        """CIS 분기별 시계열 (연간 합산 없이)."""
        if not self._hasFinance:
            return None
        cacheKey = "_financeCISQuarterly_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        result = _financeCisQuarterly(self.stockCode, "CFS")
        self._cache[cacheKey] = result
        return result

    def _ratioSeries(self):
        if not self._hasFinance:
            return None
        cacheKey = "_ratioSeries_Q_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        qResult = self.finance.timeseries
        if qResult is None:
            return None
        qSeries, periods = qResult
        # 2016-Q1 → 2016Q1 포맷 통일
        normalizedPeriods = [p.replace("-", "") for p in periods]
        from dartlab.engines.common.finance.ratios import calcRatioSeries, toSeriesDict
        archetypeOverride = _ratioArchetypeOverrideForIndustryGroup(getattr(self.sector, "industryGroup", None))
        rs = calcRatioSeries(qSeries, normalizedPeriods, archetypeOverride=archetypeOverride, yoyLag=4)
        result = toSeriesDict(rs)
        self._cache[cacheKey] = result
        return result

    def _financeOrDocsStatement(self, sjDiv: str) -> pl.DataFrame | None:
        if sjDiv == "CIS":
            cisQ = self._financeCisQuarterly() if self._hasFinance else None
            if cisQ is not None:
                series, periods = cisQ
                normalizedPeriods = [p.replace("-", "") for p in periods]
                df = _financeToDataFrame(series, normalizedPeriods, "CIS")
                if df is not None:
                    return df
        df = self._financeStmt(sjDiv) if self._hasFinance else None
        if df is not None:
            return df
        r = self._call_module("statements")
        return getattr(r, sjDiv, None) if r else None

    # ── 재무제표 (property) ──
    # finance(XBRL) 우선 → docs fallback

    def _financeStmt(self, sjDiv: str) -> pl.DataFrame | None:
        """finance 분기별 시계열에서 sjDiv DataFrame 생성 (캐싱)."""
        cacheKey = f"_financeStmt_{sjDiv}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        qResult = self.timeseries
        if qResult is None:
            return None
        series, periods = qResult
        # 2016-Q1 → 2016Q1 포맷 통일
        normalizedPeriods = [p.replace("-", "") for p in periods]
        df = _financeToDataFrame(series, normalizedPeriods, sjDiv)
        self._cache[cacheKey] = df
        return df

    @property
    def BS(self) -> pl.DataFrame | None:
        """재무상태표 DataFrame (finance XBRL 우선, docs fallback)."""
        return self.finance.BS

    @property
    def IS(self) -> pl.DataFrame | None:
        """손익계산서 DataFrame (finance XBRL 우선, docs fallback)."""
        return self.finance.IS

    @property
    def CIS(self) -> pl.DataFrame | None:
        """포괄손익계산서 DataFrame (finance raw CIS 우선, docs fallback)."""
        return self.finance.CIS

    @property
    def CF(self) -> pl.DataFrame | None:
        """현금흐름표 DataFrame (finance XBRL 우선, docs fallback)."""
        return self.finance.CF

    # ── 정기보고서 (property) ──
    # report(DART API) 우선 → docs fallback

    @property
    def dividend(self) -> pl.DataFrame | None:
        """배당 시계열 DataFrame (report API 우선, docs fallback)."""
        if self._hasReport and self.report is not None:
            r = self.report.dividend
            if r is not None:
                return r.df
        return self._get_primary("dividend")

    @property
    def majorHolder(self) -> pl.DataFrame | None:
        """최대주주 시계열 DataFrame (report API 우선, docs fallback)."""
        if self._hasReport and self.report is not None:
            r = self.report.majorHolder
            if r is not None:
                return r.df
        return self._get_primary("majorHolder")

    @property
    def employee(self) -> pl.DataFrame | None:
        """직원 현황 시계열 DataFrame (report API 우선, docs fallback)."""
        if self._hasReport and self.report is not None:
            r = self.report.employee
            if r is not None:
                return r.df
        return self._get_primary("employee")

    @property
    def subsidiary(self) -> pl.DataFrame | None:
        """자회사 투자 시계열 DataFrame."""
        return self._get_primary("subsidiary")

    @property
    def bond(self) -> pl.DataFrame | None:
        """채무증권 발행 시계열 DataFrame."""
        return self._get_primary("bond")

    @property
    def shareCapital(self) -> pl.DataFrame | None:
        """주식 현황 시계열 DataFrame."""
        return self._get_primary("shareCapital")

    @property
    def executive(self) -> pl.DataFrame | None:
        """등기임원 집계 시계열 DataFrame (report API 우선, docs fallback)."""
        if self._hasReport and self.report is not None:
            r = self.report.executive
            if r is not None:
                return r.df
        return self._get_primary("executive")

    @property
    def executivePay(self) -> pl.DataFrame | None:
        """임원 보수 시계열 DataFrame."""
        return self._get_primary("executivePay")

    @property
    def audit(self) -> pl.DataFrame | None:
        """감사의견 시계열 DataFrame (report API 우선, docs fallback)."""
        if self._hasReport and self.report is not None:
            r = self.report.audit
            if r is not None:
                return r.df
        return self._get_primary("audit")

    @property
    def boardOfDirectors(self) -> pl.DataFrame | None:
        """이사회 시계열 DataFrame."""
        return self._get_primary("boardOfDirectors")

    @property
    def capitalChange(self) -> pl.DataFrame | None:
        """자본금 변동 시계열 DataFrame."""
        return self._get_primary("capitalChange")

    @property
    def contingentLiability(self) -> pl.DataFrame | None:
        """우발부채 시계열 DataFrame."""
        return self._get_primary("contingentLiability")

    @property
    def internalControl(self) -> pl.DataFrame | None:
        """내부통제 시계열 DataFrame."""
        return self._get_primary("internalControl")

    @property
    def relatedPartyTx(self) -> pl.DataFrame | None:
        """관계자거래 시계열 DataFrame."""
        return self._get_primary("relatedPartyTx")

    @property
    def rnd(self) -> pl.DataFrame | None:
        """R&D 비용 시계열 DataFrame."""
        return self._get_primary("rnd")

    @property
    def sanction(self) -> pl.DataFrame | None:
        """제재 현황 DataFrame."""
        return self._get_primary("sanction")

    @property
    def affiliateGroup(self) -> pl.DataFrame | None:
        """계열사 목록 DataFrame."""
        return self._get_primary("affiliateGroup")

    @property
    def affiliate(self) -> pl.DataFrame | None:
        """관계기업 투자 변동 시계열 DataFrame."""
        return self._get_primary("affiliate")

    @property
    def fundraising(self) -> pl.DataFrame | None:
        """증자/감자 이력 DataFrame."""
        return self._get_primary("fundraising")

    @property
    def productService(self) -> pl.DataFrame | None:
        """주요 제품/서비스 DataFrame."""
        return self._get_primary("productService")

    @property
    def salesOrder(self) -> pl.DataFrame | None:
        """매출/수주 DataFrame."""
        return self._sectionsSubtopicWide("salesOrder") or self._safePrimary("salesOrder")

    @property
    def riskDerivative(self) -> pl.DataFrame | None:
        """위험관리/파생거래 DataFrame."""
        return self._sectionsSubtopicWide("riskDerivative") or self._safePrimary("riskDerivative")

    @property
    def articlesOfIncorporation(self) -> pl.DataFrame | None:
        """정관 변경이력 DataFrame."""
        return self._get_primary("articlesOfIncorporation")

    @property
    def otherFinance(self) -> pl.DataFrame | None:
        """기타 재무 DataFrame."""
        return self._get_primary("otherFinance")

    @property
    def companyHistory(self) -> pl.DataFrame | None:
        """회사 연혁 DataFrame."""
        return self._get_primary("companyHistory")

    @property
    def shareholderMeeting(self) -> pl.DataFrame | None:
        """주주총회 안건 DataFrame."""
        return self._get_primary("shareholderMeeting")

    @property
    def auditSystem(self) -> pl.DataFrame | None:
        """감사제도 DataFrame."""
        return self._get_primary("auditSystem")

    @property
    def investmentInOther(self) -> pl.DataFrame | None:
        """타법인출자 현황 DataFrame."""
        return self._get_primary("investmentInOther")

    @property
    def companyOverviewDetail(self) -> dict | None:
        """회사 개요 상세 (설립일, 상장일, 대표이사 등)."""
        return self._get_primary("companyOverviewDetail")

    # ── 부문정보 / K-IFRS 주석 (property) ──

    @property
    def segments(self) -> pl.DataFrame | None:
        """부문별 매출 시계열 DataFrame."""
        return self._sectionsSubtopicWide("segments") or self._safePrimary("segments")

    @property
    def tangibleAsset(self) -> pl.DataFrame | None:
        """유형자산 변동표 DataFrame."""
        if not self._hasDocsTopicHint("tangibleAsset"):
            return None
        return self._get_primary("tangibleAsset")

    @property
    def costByNature(self) -> pl.DataFrame | None:
        """비용 성격별 분류 시계열 DataFrame.

        sections/detailTopic 기반 table extractor를 우선 사용하고,
        기존 parser 결과는 archive/fallback으로만 사용한다.
        """
        if not self._hasSectionTitleHint("costByNature"):
            return None
        sections_df = self._sectionsSubtopicWide("costByNature")
        if sections_df is not None:
            return sections_df
        if not self._hasDocsTopicHint("costByNature"):
            return None
        return self._safePrimary("costByNature")

    # ── 공시 서술 (property) ──

    @property
    def business(self) -> list | None:
        """사업의 내용 섹션 목록."""
        return self._get_primary("business")

    @property
    def overview(self) -> Any:
        """회사 개요 정량 데이터."""
        from dartlab import config
        if config.verbose:
            print(f"  ▶ {self.corpName} · 회사개요정량")
        return self._call_module("companyOverview")

    @property
    def mdna(self) -> str | None:
        """MD&A 개요 텍스트."""
        return self._get_primary("mdna")

    @property
    def rawMaterial(self) -> Any:
        """원재료/설비/시설투자 수평화 DataFrame."""
        return self._sectionsSubtopicWide("rawMaterial") or self._rawMaterialLegacy()

    @property
    def sections(self) -> pl.DataFrame | None:
        """merged company sections — topic(행) × period(열) DataFrame."""
        return self._profileAccessor.sections

    def _profileTable(self) -> pl.DataFrame | None:
        cacheKey = "_sectionProfileTable"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.docs.sections.artifacts import loadSectionProfileTable
        table = loadSectionProfileTable()
        self._cache[cacheKey] = table
        return table

    def _chapterMap(self) -> dict[str, str]:
        cacheKey = "_chapterMap"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        mapping: dict[str, str] = {
            "BS": "III",
            "IS": "III",
            "CIS": "III",
            "CF": "III",
            "SCE": "III",
            "ratios": "III",
            "audit": "V",
            "auditContract": "V",
            "nonAuditContract": "V",
            "majorHolder": "VII",
            "majorHolderChange": "VII",
            "minorityHolder": "VII",
            "treasuryStock": "VII",
            "stockTotal": "VII",
            "capitalChange": "VII",
            "shareholderMeeting": "VII",
            "employee": "VIII",
            "executive": "VIII",
            "topPay": "VIII",
            "unregisteredExecutivePay": "VIII",
            "executivePayAllTotal": "VIII",
            "executivePayIndividual": "VIII",
            "investedCompany": "IX",
            "relatedPartyTx": "IX",
            "publicOfferingUsage": "X",
            "privateOfferingUsage": "X",
            "corporateBond": "X",
            "shortTermBond": "X",
            "auditOpinion": "V",
            "outsideDirector": "VI",
            "executivePayByType": "VIII",
            "executivePayTotal": "VIII",
        }

        table = self._profileTable()
        if table is not None and not table.is_empty():
            canonicalCol = "canonicalTopic" if "canonicalTopic" in table.columns else "topic"
            grouped = (
                table
                .filter(pl.col(canonicalCol).is_not_null(), pl.col("chapter").is_not_null())
                .group_by([canonicalCol, "chapter"])
                .agg(pl.len().alias("count"))
                .sort(["count", canonicalCol], descending=[True, False])
            )
            for row in grouped.iter_rows(named=True):
                topic = row.get(canonicalCol)
                chapter = row.get("chapter")
                if isinstance(topic, str) and isinstance(chapter, str) and topic not in mapping:
                    mapping[topic] = chapter

        self._cache[cacheKey] = mapping
        return mapping

    def _chapterForTopic(self, topic: str) -> str:
        if topic in self._chapterMap():
            return self._chapterMap()[topic]
        if self.notes is not None:
            from dartlab.engines.dart.docs.notes import _REGISTRY as _NOTES_REGISTRY
            if topic in _NOTES_REGISTRY:
                return "XI"
        return "XII"

    def _boardTopics(self) -> list[str]:
        cacheKey = "_boardTopics"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        ordered: list[str] = []
        seen: set[str] = set()

        sections = self._profileAccessor.sections
        if sections is not None and "topic" in sections.columns:
            for topic in sections["topic"].to_list():
                if not isinstance(topic, str) or not topic or topic in seen:
                    continue
                ordered.append(topic)
                seen.add(topic)

        if self._hasFinance and self._ratioSeries() is not None and "ratios" not in seen:
            ordered.append("ratios")
            seen.add("ratios")

        self._cache[cacheKey] = ordered
        return ordered

    def _topicLabel(self, topic: str) -> str:
        if topic == "CIS":
            return "포괄손익계산서"
        if topic == "SCE":
            return "자본변동표"
        if topic in _TOPIC_LABELS:
            return _TOPIC_LABELS[topic]
        entry = _getEntry(topic)
        if entry is not None:
            return entry.label
        for name, label in _ALL_PROPERTIES:
            if name == topic:
                return label
        return topic

    def _sectionShowResult(self, topic: str) -> ShowResult | None:
        """sections에서 topic의 text/table 수평 행을 분리하여 ShowResult 반환."""
        topicFrame = self._sectionTopicRaw(topic)
        if topicFrame is None:
            return None
        hasBlockType = "blockType" in topicFrame.columns
        textFrame = topicFrame.filter(pl.col("blockType") == "text") if hasBlockType else topicFrame
        tableFrame = topicFrame.filter(pl.col("blockType") == "table") if hasBlockType else pl.DataFrame()
        text = textFrame if not textFrame.is_empty() else None
        table = tableFrame if not tableFrame.is_empty() else None
        if text is None and table is None:
            return None
        return ShowResult(text=text, table=table)

    def _sectionTopicRaw(self, topic: str) -> pl.DataFrame | None:
        """sections에서 topic의 원본 수평 행(text+table) 반환."""
        docsSections = self.docs.sections
        if docsSections is not None and "topic" in docsSections.columns:
            topicFrame = docsSections.filter(pl.col("topic") == topic)
            if not topicFrame.is_empty():
                return topicFrame

        profileSections = self._profileAccessor.sections
        if profileSections is not None and "topic" in profileSections.columns:
            topicFrame = profileSections.filter(pl.col("topic") == topic)
            if not topicFrame.is_empty():
                return topicFrame
        return None

    def _cleanSectionText(self, textFrame: pl.DataFrame | None, period: str | None) -> pl.DataFrame | None:
        """text 행에서 메타 컬럼 제거 + all-null 기간 제거."""
        if textFrame is None or textFrame.is_empty():
            return None
        metaCols = {"chapter", "topic", "blockType"}
        periodCols = [c for c in textFrame.columns if c not in metaCols]
        if not periodCols:
            return None
        df = textFrame.select(periodCols)
        # all-null 기간 제거
        keepCols = [c for c in df.columns if df[c].null_count() < df.height]
        if not keepCols:
            return None
        df = df.select(keepCols)
        return self._applyPeriodFilter(df, period) if not df.is_empty() else None

    def _cleanSectionTable(self, topic: str, period: str | None) -> pl.DataFrame | None:
        """table 행을 구조화 DataFrame으로 변환 (finance IS/BS처럼)."""
        if topic in self._AUTO_SUBTOPIC_SKIP:
            return None
        result = self._topicSubtables(topic)
        if result is None:
            return None
        from dartlab.engines.dart.docs.sections import parseSubtopicTable
        parsed = parseSubtopicTable(result, numeric=False)
        if parsed is not None and parsed.df is not None:
            df = parsed.df
            if period is not None:
                periodCols = [c for c in df.columns if c != "항목"]
                matchedCols = [c for c in periodCols if period in c]
                if matchedCols:
                    df = df.select(["항목", *matchedCols])
            return df
        # 파싱 실패 시 subtopic wide 반환 (메타 컬럼 정리)
        wide = result.wide
        metaCols = {"topic", "sourceTopic", "subtopicOrder", "semanticTopic", "detailTopic"}
        keepCols = [c for c in wide.columns if c not in metaCols]
        if keepCols:
            wide = wide.select(keepCols)
        return self._applyPeriodFilter(wide, period) if not wide.is_empty() else None

    @staticmethod
    def _cleanSubtopicWide(df: pl.DataFrame) -> pl.DataFrame:
        """subtopic wide에서 메타 컬럼 제거 + subtopic→항목 통일."""
        _DROP_META = {"topic", "sourceTopic", "subtopicOrder", "semanticTopic", "detailTopic"}
        dropCols = [c for c in df.columns if c in _DROP_META]
        if dropCols:
            df = df.drop(dropCols)
        if "subtopic" in df.columns:
            df = df.rename({"subtopic": "항목"})
        return df

    @staticmethod
    def _ensurePeriodAscending(df: pl.DataFrame) -> pl.DataFrame:
        """기간 컬럼을 오름차순으로 정렬."""
        nonPeriodCols = [c for c in df.columns if not _isPeriodColumn(c)]
        periodCols = [c for c in df.columns if _isPeriodColumn(c)]
        if len(periodCols) < 2:
            return df
        sortedPeriods = sorted(periodCols)
        if periodCols == sortedPeriods:
            return df
        return df.select([*nonPeriodCols, *sortedPeriods])

    @staticmethod
    def _dropOldPeriodColumns(df: pl.DataFrame, minYear: int) -> pl.DataFrame:
        """기간 컬럼 중 minYear 미만 연도를 제거."""
        keepCols = []
        for c in df.columns:
            if _isPeriodColumn(c) and int(c[:4]) < minYear:
                continue
            keepCols.append(c)
        if len(keepCols) == len(df.columns):
            return df
        return df.select(keepCols)

    def _trimOldPeriods(self, result: Any) -> Any:
        """show() 반환값에서 _MIN_YEAR 이전 기간 제거."""
        if result is None:
            return None
        minYear = self._MIN_YEAR
        if isinstance(result, ShowResult):
            text = self._dropOldPeriodColumns(result.text, minYear) if result.text is not None else None
            table = self._dropOldPeriodColumns(result.table, minYear) if result.table is not None else None
            # 기간 컬럼이 모두 제거된 경우
            if text is not None:
                hasPeriod = any(_isPeriodColumn(c) for c in text.columns)
                if not hasPeriod:
                    text = None
            if table is not None:
                hasPeriod = any(_isPeriodColumn(c) for c in table.columns)
                if not hasPeriod:
                    table = None
            if text is None and table is None:
                return None
            return ShowResult(text=text, table=table)
        if isinstance(result, pl.DataFrame):
            trimmed = self._dropOldPeriodColumns(result, minYear)
            # period 컬럼이 없는 DF (리스트형 report)는 그대로 반환
            return trimmed
        return result

    @staticmethod
    def _unpivotTopicRows(topicFrame: pl.DataFrame) -> pl.DataFrame:
        """topic × period 수평 행을 세로로 전환. blockType 유지."""
        metaCols = {"chapter", "topic", "blockType"}
        periodCols = [c for c in topicFrame.columns if c not in metaCols]
        hasBlockType = "blockType" in topicFrame.columns
        rows: list[dict[str, str | None]] = []
        for i in range(topicFrame.height):
            ch = topicFrame["chapter"][i] if "chapter" in topicFrame.columns else None
            tp = topicFrame["topic"][i] if "topic" in topicFrame.columns else None
            bt = topicFrame["blockType"][i] if hasBlockType else None
            for col in periodCols:
                val = topicFrame[col][i]
                if val is not None and str(val).strip():
                    rows.append({
                        "chapter": ch, "topic": tp, "blockType": bt,
                        "period": col, "content": str(val),
                    })
        if not rows:
            return pl.DataFrame({"chapter": [], "topic": [], "blockType": [], "period": [], "content": []})
        return pl.DataFrame(rows)

    def _topicBlocks(self, topic: str) -> pl.DataFrame | None:
        blocks = self._retrievalBlocks()
        if blocks is None or blocks.is_empty():
            return None
        topicBlocks = blocks.filter(pl.col("topic") == topic)
        if topicBlocks.is_empty():
            return None
        return topicBlocks

    def _topicChangeLedger(self, topic: str) -> pl.DataFrame | None:
        cacheKey = f"_topicLedger:{topic}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        blocks = self._topicBlocks(topic)
        result = _buildTopicChangeLedger(blocks)
        self._cache[cacheKey] = result
        return result

    def _topicEvidence(self, topic: str, period: str) -> pl.DataFrame:
        cacheKey = f"_topicEvidence:{topic}:{period}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        blocks = self._topicBlocks(topic)
        result = _buildTopicEvidence(blocks, period)
        self._cache[cacheKey] = result
        return result

    def _reportFrame(self, topic: str, *, raw: bool = False) -> pl.DataFrame | None:
        if self.report is None:
            return None
        apiType = _REPORT_TOPIC_TO_API_TYPE.get(topic, topic)
        if apiType not in self.report.apiTypes:
            return None
        # pivot 5개는 toWide()로 사용자 친화적 테이블 반환
        pivotName = apiType if apiType in _ReportAccessor._PIVOT_NAMES else topic
        if pivotName in _ReportAccessor._PIVOT_NAMES:
            result = getattr(self.report, pivotName, None)
            if result is not None and hasattr(result, "toWide"):
                wide = result.toWide()
                if wide is not None:
                    if not raw and "metric" in wide.columns:
                        wide = wide.rename({"metric": "항목"})
                    return wide
        df = self.report.extractAnnual(apiType)
        if df is None or df.is_empty():
            return df
        _META_COLS = {"stlm_dt", "apiType", "stockCode", "year", "quarter", "quarterNum"}
        dropCols = [c for c in df.columns if c in _META_COLS]
        if dropCols:
            df = df.drop(dropCols)
        if raw:
            return df
        # 영문 컬럼 → 한글 매핑 (OpenDART 공식)
        renameMap = {c: _REPORT_COL_KR[c] for c in df.columns if c in _REPORT_COL_KR}
        if renameMap:
            # 중복 한글명 방지: 이미 존재하는 컬럼명은 건너뜀
            existing = set(df.columns)
            renameMap = {k: v for k, v in renameMap.items() if v not in existing or k == v}
            if renameMap:
                df = df.rename(renameMap)
        return df

    def _applyPeriodFilter(self, payload: Any, period: str | None) -> Any:
        if period is None or not isinstance(payload, pl.DataFrame) or payload.is_empty():
            return payload

        if period in payload.columns:
            keepCols = [c for c in payload.columns if not _isPeriodColumn(c)]
            keepCols.append(period)
            return payload.select(keepCols)

        if "period" in payload.columns:
            return payload.filter(pl.col("period") == period)
        if "year" in payload.columns:
            return payload.filter(pl.col("year").cast(pl.Utf8) == period)
        return payload

    _MIN_YEAR = 2016

    def show(self, topic: str, *, period: str | None = None, raw: bool = False) -> Any:
        result = self._showCore(topic, period=period, raw=raw)
        return self._trimOldPeriods(result)

    def _showCore(self, topic: str, *, period: str | None = None, raw: bool = False) -> Any:
        if topic == "docsStatus":
            return _noticeFrame(topic, "현재 사업보고서 부재")

        if topic in {"BS", "IS", "CIS", "CF", "SCE"}:
            return self._applyPeriodFilter(getattr(self, topic), period)

        if topic == "ratios":
            ratioSeries = self._ratioSeries()
            if ratioSeries is None:
                return None
            series, years = ratioSeries
            templateKey = _ratioTemplateKeyForIndustryGroup(getattr(self.sector, "industryGroup", None))
            fieldNames = _RATIO_TEMPLATE_FIELDS.get(templateKey)
            ratioFrame = _ratioSeriesToDataFrame(series, years, fieldNames=fieldNames)
            return self._applyPeriodFilter(ratioFrame, period)

        if topic in {"salesOrder", "riskDerivative", "segments", "rawMaterial", "costByNature"}:
            if topic == "costByNature" and not self._hasSectionTitleHint("costByNature"):
                return None
            if raw:
                subtopicFrame = self._sectionsSubtopicLong(topic)
                if subtopicFrame is not None:
                    return self._applyPeriodFilter(subtopicFrame, period)
            else:
                subtopicFrame = self._sectionsSubtopicWide(topic)
                if subtopicFrame is not None:
                    subtopicFrame = self._cleanSubtopicWide(subtopicFrame)
                    return self._applyPeriodFilter(subtopicFrame, period)
            fallback_payload = {
                "salesOrder": self._safePrimary("salesOrder"),
                "riskDerivative": self._safePrimary("riskDerivative"),
                "segments": self._safePrimary("segments"),
                "rawMaterial": self._rawMaterialLegacy(),
                "costByNature": self._safePrimary("costByNature") if self._hasDocsTopicHint("costByNature") else None,
            }[topic]
            if fallback_payload is not None:
                payload = self._ensurePeriodAscending(fallback_payload)
                # account/subtopic 등 → 항목 통일
                if "account" in payload.columns:
                    payload = payload.rename({"account": "항목"})
                elif "subtopic" in payload.columns:
                    payload = payload.rename({"subtopic": "항목"})
                return self._applyPeriodFilter(payload, period)
            return None

        reportFrame = self._reportFrame(topic, raw=raw)
        if reportFrame is not None:
            return self._applyPeriodFilter(reportFrame, period)

        if self.notes is not None:
            from dartlab.engines.dart.docs.notes import _REGISTRY as _NOTES_REGISTRY
            if topic in _NOTES_REGISTRY:
                return self._applyPeriodFilter(self.notes._get(topic), period)

        # sections에서 text/table 분리하여 ShowResult 반환
        showResult = self._sectionShowResult(topic)
        if showResult is not None:
            # text: 메타 컬럼 제거 + all-null 기간 제거
            text = self._cleanSectionText(showResult.text, period)
            # table: 구조화 DataFrame (finance IS/BS처럼)
            table = self._cleanSectionTable(topic, period)
            if text is None and table is None:
                return None
            return ShowResult(text=text, table=table)

        if not self._hasDocs:
            return _noticeFrame(topic, "현재 사업보고서 부재")

        try:
            payload = getattr(self, topic)
        except AttributeError:
            return None
        return self._applyPeriodFilter(payload, period)

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
        if topic == "docsStatus" and not self._hasDocs:
            return {
                "topic": topic,
                "period": period,
                "primarySource": "docs",
                "fallbackSources": [],
                "selectedPayloadRef": None,
                "availableSources": [],
                "whySelected": "docs unavailable",
            }
        if topic == "ratios":
            ratioSeries = self._ratioSeries()
            templateKey = _ratioTemplateKeyForIndustryGroup(getattr(self.sector, "industryGroup", None))
            rowCount = None
            yearCount = None
            coverage = "missing"
            if ratioSeries is not None:
                series, years = ratioSeries
                fieldNames = _RATIO_TEMPLATE_FIELDS.get(templateKey)
                ratioFrame = _ratioSeriesToDataFrame(series, years, fieldNames=fieldNames)
                rowCount = None if ratioFrame is None else ratioFrame.height
                yearCount = len(years)
                if ratioFrame is not None and rowCount >= 30 and yearCount >= 5:
                    coverage = "full"
                elif ratioFrame is not None and rowCount > 0:
                    coverage = "partial"
            return {
                "topic": topic,
                "period": period,
                "primarySource": "finance",
                "fallbackSources": [],
                "selectedPayloadRef": "finance:RATIO",
                "availableSources": [] if ratioSeries is None else [{
                    "source": "finance",
                    "rows": 1,
                    "payloadRef": "finance:RATIO",
                    "summary": "annual ratio series" if templateKey is None else f"annual ratio series ({templateKey} template)",
                    "priority": 300,
                }],
                "whySelected": "finance authoritative priority" if templateKey is None else f"finance authoritative priority with {templateKey} industry template",
                "template": templateKey or "general",
                "rowCount": rowCount,
                "yearCount": yearCount,
                "coverage": coverage,
            }
        return self._profileAccessor.trace(topic, period=period)

    def diff(
        self,
        topic: str | None = None,
        fromPeriod: str | None = None,
        toPeriod: str | None = None,
    ) -> pl.DataFrame | None:
        """기간간 텍스트 변경 비교.

        사용법::

            c.diff()                          # 전체 topic 변경 요약
            c.diff("businessOverview")        # 특정 topic 변경 이력
            c.diff("businessOverview", "2024", "2025")  # 줄 단위 diff
        """
        from dartlab.engines.dart.docs.sections.diff import sectionsDiff, topicDiff

        docsSections = self.docs.sections
        if docsSections is None:
            return None

        # 줄 단위 상세 diff (인터리빙 순서로 맥락 유지)
        if topic is not None and fromPeriod is not None and toPeriod is not None:
            result = topicDiff(docsSections, topic, fromPeriod, toPeriod)
            if result is None:
                return None
            import difflib
            filtered = docsSections.filter(pl.col("topic") == topic)
            if filtered.height == 0:
                return None
            fromText = str(filtered.item(0, fromPeriod) or "")
            toText = str(filtered.item(0, toPeriod) or "")
            fromLines = fromText.splitlines()
            toLines = toText.splitlines()
            rows: list[dict[str, str | int]] = []
            lineNo = 0
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
                None, fromLines, toLines,
            ).get_opcodes():
                if tag == "equal":
                    for line in fromLines[i1:i2]:
                        lineNo += 1
                        rows.append({"line": lineNo, "status": " ", "text": line})
                elif tag == "insert":
                    for line in toLines[j1:j2]:
                        lineNo += 1
                        rows.append({"line": lineNo, "status": "+", "text": line})
                elif tag == "delete":
                    for line in fromLines[i1:i2]:
                        lineNo += 1
                        rows.append({"line": lineNo, "status": "-", "text": line})
                elif tag == "replace":
                    for line in fromLines[i1:i2]:
                        lineNo += 1
                        rows.append({"line": lineNo, "status": "-", "text": line})
                    for line in toLines[j1:j2]:
                        lineNo += 1
                        rows.append({"line": lineNo, "status": "+", "text": line})
            return pl.DataFrame(rows) if rows else None

        diffResult = sectionsDiff(docsSections)

        # 특정 topic 변경 이력
        if topic is not None:
            topicEntries = [e for e in diffResult.entries if e.topic == topic]
            if not topicEntries:
                return pl.DataFrame({
                    "fromPeriod": [], "toPeriod": [],
                    "status": [], "fromLen": [], "toLen": [],
                    "delta": [], "deltaRate": [],
                })
            return pl.DataFrame([
                {
                    "fromPeriod": e.fromPeriod,
                    "toPeriod": e.toPeriod,
                    "status": e.status,
                    "fromLen": e.fromLen,
                    "toLen": e.toLen,
                    "delta": e.toLen - e.fromLen,
                    "deltaRate": round((e.toLen - e.fromLen) / e.fromLen, 3) if e.fromLen > 0 else None,
                }
                for e in topicEntries
            ])

        # 전체 요약
        return pl.DataFrame([
            {
                "chapter": s.chapter,
                "topic": s.topic,
                "periods": s.totalPeriods,
                "changed": s.changedCount,
                "stable": s.stableCount,
                "changeRate": round(s.changeRate, 3),
            }
            for s in diffResult.summaries
        ])

    def table(
        self,
        topic: str,
        subtopic: str | None = None,
        *,
        numeric: bool = False,
        period: str | None = None,
    ) -> Any:
        """subtopic wide 셀의 markdown table을 구조화 DataFrame으로 파싱.

        Args:
            topic: docs topic 이름
            subtopic: 파싱할 subtopic 이름 (None이면 첫 번째 subtopic)
            numeric: True이면 금액 문자열을 float로 변환
            period: 기간 필터 (예: "2024")

        Returns:
            ParsedSubtopicTable 또는 파싱 불가 시 None

        Example::

            c.table("employee")                    # 첫 번째 subtopic
            c.table("employee", "직원현황")         # 특정 subtopic
            c.table("employee", numeric=True)       # 숫자 변환
        """
        result = self._topicSubtables(topic)
        if result is None:
            return None
        from dartlab.engines.dart.docs.sections import parseSubtopicTable
        parsed = parseSubtopicTable(result, subtopic, numeric=numeric)
        if parsed is None:
            return None
        if period is not None and parsed.df is not None:
            periodCols = [c for c in parsed.df.columns if c != "항목"]
            matchedCols = [c for c in periodCols if period in c]
            if matchedCols:
                from dataclasses import replace
                filteredDf = parsed.df.select(["항목", *matchedCols])
                return replace(parsed, df=filteredDf)
        return parsed

    @property
    def topics(self) -> list[str]:
        return list(self._boardTopics())

    @property
    def sources(self) -> pl.DataFrame:
        rows = []
        for source, raw in (
            ("docs", self.rawDocs),
            ("finance", self.rawFinance),
            ("report", self.rawReport),
        ):
            rows.append({
                "source": source,
                "available": raw is not None,
                "rows": raw.height if raw is not None else None,
                "cols": raw.width if raw is not None else None,
                "shape": _shapeString(raw),
            })
        return pl.DataFrame(rows)

    def _buildProfile(self, *, raw: bool) -> _BoardView:
        cacheKey = "_profileRawView" if raw else "_profileView"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        payload: OrderedDict[str, OrderedDict[str, Any]] = OrderedDict(
            (title, OrderedDict()) for title in _CHAPTER_TITLES.values()
        )
        for topic in self._boardTopics():
            topicPayload = self.show(topic, raw=raw)
            if topicPayload is None:
                continue
            chapter = self._chapterForTopic(topic)
            chapterTitle = _CHAPTER_TITLES.get(chapter, _CHAPTER_TITLES["XII"])
            payload[chapterTitle][topic] = topicPayload

        payload = OrderedDict((chapter, topics) for chapter, topics in payload.items() if topics)
        profile = _BoardView(self, payload, raw=raw)
        self._cache[cacheKey] = profile
        return profile

    @property
    def index(self) -> pl.DataFrame:
        """현재 공개 Company 구조 인덱스 DataFrame.

        sections 메타데이터 + finance/report 존재 확인만으로 구성.
        개별 파서를 호출하지 않아 빠르다 (lazy).
        """
        cacheKey = "_lazyIndex"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        rows: list[dict[str, Any]] = []

        if not self._hasDocs:
            rows.append({
                "chapter": "안내",
                "topic": "docsStatus",
                "label": "사업보고서",
                "kind": "notice",
                "source": "docs",
                "periods": "-",
                "shape": "missing",
                "preview": "현재 사업보고서 부재",
                "_sortKey": (0, 0),
            })

        _STMT_ORDER = {"BS": 0, "IS": 1, "CIS": 2, "CF": 3, "SCE": 4}
        for stmt in ("BS", "IS", "CIS", "CF", "SCE"):
            df = getattr(self, stmt, None)
            if df is None:
                continue
            periodCols = [c for c in df.columns if _isPeriodColumn(c)]
            periods = f"{periodCols[0]}..{periodCols[-1]}" if len(periodCols) > 1 else (periodCols[0] if periodCols else "-")
            rows.append({
                "chapter": _CHAPTER_TITLES.get("III", "III"),
                "topic": stmt,
                "label": self._topicLabel(stmt),
                "kind": "finance",
                "source": "finance",
                "periods": periods,
                "shape": _shapeString(df),
                "preview": f"{df.height} accounts",
                "_sortKey": (3, _STMT_ORDER[stmt]),
            })

        rsPair = self._ratioSeries() if self._hasFinance else None
        if rsPair is not None:
            series, years = rsPair
            ratioData = series.get("RATIO", {})
            from dartlab.engines.common.finance.ratios import RATIO_CATEGORIES
            metricCount = sum(
                1 for _, fields in RATIO_CATEGORIES
                for f in fields
                if ratioData.get(f) and any(v is not None for v in ratioData[f])
            )
            periods = f"{years[0]}..{years[-1]}" if len(years) > 1 else (years[0] if years else "-")
            rows.append({
                "chapter": _CHAPTER_TITLES.get("III", "III"),
                "topic": "ratios",
                "label": "재무비율",
                "kind": "finance",
                "source": "finance",
                "periods": periods,
                "shape": f"{metricCount}x{len(years) + 2}",
                "preview": f"{metricCount} metrics",
                "_sortKey": (3, 5),
            })

        sec = self.docs.sections
        if sec is not None and "topic" in sec.columns:
            periodCols = [c for c in sec.columns if _isPeriodColumn(c)]
            periodRange = f"{periodCols[0]}..{periodCols[-1]}" if len(periodCols) > 1 else (periodCols[0] if periodCols else "-")
            hasChapterCol = "chapter" in sec.columns
            for rowIdx, row in enumerate(sec.iter_rows(named=True)):
                topic = row["topic"]
                if not isinstance(topic, str) or not topic:
                    continue
                nonNull = sum(1 for c in periodCols if row.get(c) is not None)
                preview = "-"
                for col in periodCols:
                    val = row.get(col)
                    if val is not None:
                        text = _normalizeTextCell(val)[:80]
                        preview = f"{col}: {text}"
                        break
                chapter = row.get("chapter") if hasChapterCol else self._chapterForTopic(topic)
                if not isinstance(chapter, str) or not chapter:
                    chapter = self._chapterForTopic(topic)
                chapterNum = _CHAPTER_ORDER.get(chapter, 12)
                rows.append({
                    "chapter": _CHAPTER_TITLES.get(chapter, chapter),
                    "topic": topic,
                    "label": self._topicLabel(topic),
                    "kind": "docs",
                    "source": "docs",
                    "periods": periodRange,
                    "shape": f"{nonNull}기간",
                    "preview": preview,
                    "_sortKey": (chapterNum, 100 + rowIdx),
                })

        if self._hasReport:
            from dartlab.engines.dart.report.types import API_TYPES, API_TYPE_LABELS
            existingTopics = {r["topic"] for r in rows}
            for rIdx, apiType in enumerate(API_TYPES):
                if apiType in existingTopics:
                    continue
                df = self.report.extract(apiType)
                if df is None or df.is_empty():
                    continue
                chapter = self._chapterForTopic(apiType)
                chapterNum = _CHAPTER_ORDER.get(chapter, 12)
                rows.append({
                    "chapter": _CHAPTER_TITLES.get(chapter, chapter),
                    "topic": apiType,
                    "label": API_TYPE_LABELS.get(apiType, apiType),
                    "kind": "report",
                    "source": "report",
                    "periods": "-",
                    "shape": _shapeString(df),
                    "preview": API_TYPE_LABELS.get(apiType, apiType),
                    "_sortKey": (chapterNum, 200 + rIdx),
                })

        rows.sort(key=lambda r: r.get("_sortKey", (99, 999)))
        for r in rows:
            r.pop("_sortKey", None)

        df = pl.DataFrame(rows) if rows else pl.DataFrame(schema={
            "chapter": pl.Utf8, "topic": pl.Utf8, "label": pl.Utf8,
            "kind": pl.Utf8, "source": pl.Utf8,
            "periods": pl.Utf8, "shape": pl.Utf8, "preview": pl.Utf8,
        })
        self._cache[cacheKey] = df
        return df

    @property
    def board(self) -> pl.DataFrame:
        """Deprecated alias for index."""
        return self.index

    @property
    def profile(self) -> _BoardView:
        """향후 보고서형 렌더로 확장될 예약 Company 뷰."""
        return self._buildProfile(raw=False)

    @property
    def retrievalBlocks(self) -> pl.DataFrame | None:
        """원문 markdown 보존 retrieval block DataFrame."""
        return self.docs.retrievalBlocks

    @property
    def contextSlices(self) -> pl.DataFrame | None:
        """LLM 투입용 context slice DataFrame."""
        return self.docs.contextSlices

    # ── holderOverview (별도 함수) ──

    @property
    def holderOverview(self) -> Any:
        """5% 이상 주주, 소액주주, 의결권 현황."""
        if not self._hasDocs:
            return None
        cacheKey = "holderOverview"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab import config
        if config.verbose:
            print(f"  ▶ {self.corpName} · 주주현황")
        result = _import_and_call(
            "dartlab.engines.dart.docs.finance.majorHolder", "holderOverview", self.stockCode,
        )
        self._cache[cacheKey] = result
        return result

    # ── fsSummary (별도 — 파라미터 있음) ──

    def fsSummary(self, ifrsOnly: bool = True, period: str = "y"):
        """요약재무정보 시계열 + 브릿지 매칭 + 전환점 탐지."""
        return self._call_module("fsSummary", ifrsOnly=ifrsOnly, period=period)

    # ── financeEngine (숫자 재무 데이터) ──

    def _getFinanceBuild(self, period: str = "q", fsDivPref: str = "CFS"):
        """finance parquet 시계열 빌드 (캐싱).

        Args:
            period: "q" (분기별 standalone), "y" (연도별), "cum" (분기별 누적).
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).
        """
        cacheKey = f"_finance_{period}_{fsDivPref}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        from dartlab.engines.dart.finance.pivot import buildAnnual, buildCumulative, buildTimeseries

        builders = {"q": buildTimeseries, "y": buildAnnual, "cum": buildCumulative}
        builder = builders.get(period, buildTimeseries)
        result = builder(self.stockCode, fsDivPref=fsDivPref)
        self._cache[cacheKey] = result
        return result

    def getTimeseries(self, period: str = "q", fsDivPref: str = "CFS"):
        """재무 시계열 조회.

        Args:
            period: "q" (분기별 standalone), "y" (연도별), "cum" (분기별 누적).
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).

        Returns:
            (series, periods) 또는 None.
            series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}
            periods = ["2016-Q1", ...] (q/cum) 또는 ["2016", ...] (y)

        Example::

            c = Company("005930")
            series, periods = c.getTimeseries("y")
            series, periods = c.getTimeseries("q", fsDivPref="OFS")
        """
        return self._getFinanceBuild(period, fsDivPref)

    def getRatios(self, fsDivPref: str = "CFS"):
        """재무비율 계산.

        Args:
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).

        Returns:
            RatioResult dataclass.

        Example::

            c = Company("005930")
            c.getRatios().roe
            c.getRatios("OFS").debtRatio
        """
        cacheKey = f"_ratios_{fsDivPref}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.common.finance.ratios import calcRatios
        archetypeOverride = _ratioArchetypeOverrideForIndustryGroup(getattr(self.sector, "industryGroup", None))
        ts = self._getFinanceBuild("q", fsDivPref)
        result = None
        if ts is not None:
            series, _ = ts
            result = calcRatios(series, archetypeOverride=archetypeOverride)

        if _shouldFallbackToAnnualRatios(result, archetypeOverride):
            annual = self._getFinanceBuild("y", fsDivPref)
            if annual is not None:
                annualSeries, _ = annual
                annualResult = calcRatios(annualSeries, annual=True, archetypeOverride=archetypeOverride)
                if _ratioResultHasHeadlineSignal(annualResult):
                    result = annualResult

        self._cache[cacheKey] = result
        return result

    @property
    def ratios(self):
        """재무비율 (연결 기준, ROE, ROA, 마진, 부채비율 등).

        Returns:
            RatioResult dataclass.

        Example::

            c = Company("005930")
            c.ratios.roe            # 8.57
            c.ratios.operatingMargin  # 10.88
            c.ratios.debtRatio      # 27.93
        """
        return self.getRatios("CFS")

    @property
    def timeseries(self):
        """분기별 standalone 시계열 (연결 기준).

        Returns:
            (series, periods) 또는 None.
            series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}
            periods = ["2016-Q1", "2016-Q2", ..., "2024-Q4"]

        Example::

            c = Company("005930")
            series, periods = c.timeseries
            series["IS"]["sales"]  # 분기별 매출 시계열
        """
        return self.finance.timeseries

    @property
    def annual(self):
        """연도별 시계열 (연결 기준).

        Returns:
            (series, years) 또는 None.

        Example::

            c = Company("005930")
            series, years = c.annual
            series["IS"]["sales"]  # 연도별 매출 시계열
        """
        return self.finance.annual

    @property
    def cumulative(self):
        """분기별 누적 시계열 (연결 기준).

        Returns:
            (series, periods) 또는 None.

        Example::

            c = Company("005930")
            series, periods = c.cumulative
        """
        return self.finance.cumulative

    @property
    def sceMatrix(self):
        """자본변동표 연도별 매트릭스 (연결 기준).

        Returns:
            (matrix, years) 또는 None.
            matrix[year][cause][detail] = 금액
            years = ["2016", ..., "2024"]

        Example::

            c = Company("005930")
            matrix, years = c.sceMatrix
            matrix["2024"]["net_income"]["retained_earnings"]
        """
        return self.finance.sceMatrix

    @property
    def sce(self):
        """자본변동표 DataFrame (연결 기준).

        Returns:
            계정명 × 연도 컬럼 DataFrame 또는 None.

        Example::

            c = Company("005930")
            c.sce
        """
        return self.finance.sce

    @property
    def SCE(self):
        """자본변동표 DataFrame (대문자 alias)."""
        return self.finance.SCE

    @property
    def ratioSeries(self):
        """재무비율 연도별 시계열 (IS/BS/CF와 동일한 dict 구조).

        Returns:
            ({"RATIO": {snakeId: [v1, v2, ...]}}, years) 또는 None.

        Example::

            c = Company("005930")
            series, years = c.ratioSeries
            series["RATIO"]["roe"]  # [8.69, 13.20, 16.55, ...]
        """
        return self.finance.ratioSeries

    # ── 섹터 분류 ──

    @property
    def sector(self):
        """WICS 투자 섹터 분류 (KIND 업종 + 키워드 기반).

        Returns:
            SectorInfo (sector, industryGroup, confidence, source).

        Example::

            c = Company("005930")
            c.sector              # SectorInfo(IT/반도체와반도체장비, conf=1.00, src=override)
            c.sector.sector       # Sector.IT
            c.sector.industryGroup  # IndustryGroup.SEMICONDUCTOR
        """
        cacheKey = "_sector"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.sector import classify
        kindDf = getKindList()
        row = kindDf.filter(pl.col("종목코드") == self.stockCode)
        kindIndustry = row["업종"][0] if row.height > 0 and "업종" in kindDf.columns else None
        mainProducts = row["주요제품"][0] if row.height > 0 and "주요제품" in kindDf.columns else None
        result = classify(self.corpName or "", kindIndustry, mainProducts)
        self._cache[cacheKey] = result
        return result

    @property
    def sectorParams(self):
        """현재 종목의 섹터별 밸류에이션 파라미터.

        Returns:
            SectorParams (discountRate, growthRate, perMultiple, ...).

        Example::

            c = Company("005930")
            c.sectorParams.perMultiple   # 15
            c.sectorParams.discountRate  # 13.0
        """
        cacheKey = "_sectorParams"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.sector import getParams
        result = getParams(self.sector)
        self._cache[cacheKey] = result
        return result

    # ── 규모 랭크 ──

    @property
    def rank(self):
        """전체 시장 + 섹터 내 규모 순위 (매출/자산/성장률).

        스냅샷이 없으면 None 반환. buildSnapshot()으로 사전 빌드 필요.

        Returns:
            RankInfo 또는 스냅샷 미빌드 시 None.

        Example::

            from dartlab.engines.insight import buildSnapshot
            buildSnapshot()

            c = Company("005930")
            c.rank                    # RankInfo(삼성전자, 매출 2/2192, 섹터 2/467, large)
            c.rank.revenueRank        # 2
            c.rank.revenueRankInSector # 2
            c.rank.sizeClass          # "large"
        """
        cacheKey = "_rank"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.rank.rank import getRank
        result = getRank(self.stockCode)
        self._cache[cacheKey] = result
        return result

    # ── 인사이트 분석 ──

    @property
    def insights(self):
        """종합 인사이트 분석 (7영역 등급 + 이상치 + 요약).

        Returns:
            AnalysisResult 또는 finance 데이터 없으면 None.

        Example::

            c = Company("005930")
            c.insights.grades()       # {'performance': 'A', ...}
            c.insights.summary        # "삼성전자는 실적, 재무건전성 등..."
            c.insights.anomalies      # [Anomaly(...), ...]
            c.insights.profile        # "premium"
        """
        if not self._hasFinance:
            return None
        cacheKey = "_insights"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.insight import analyze
        result = analyze(self.stockCode, company=self)
        self._cache[cacheKey] = result
        return result

    # ── 전체 추출 ──

    def all(self) -> dict[str, Any]:
        """전체 데이터를 dict로 반환.

        Returns:
            {"BS": DataFrame, "IS": DataFrame, "dividend": DataFrame, ...}
            notes 항목은 "notes" 키 아래 dict로 포함.
            finance 항목은 "timeseries", "ratios" 키로 포함.
        """
        from dartlab import config
        from dartlab.engines.dart.docs.notes import _REGISTRY as notes_registry

        nNotes = len(notes_registry) if self._hasDocs else 0
        total = len(_ALL_PROPERTIES) + nNotes + 3
        result: dict[str, Any] = {}

        if config.verbose:
            from alive_progress import alive_bar
            with alive_bar(total, title=f"▶ {self.corpName}") as bar:
                _log = logging.getLogger("dartlab.engines.dart.company")
                for name, label in _ALL_PROPERTIES:
                    bar.text = label
                    try:
                        config.verbose = False
                        result[name] = getattr(self, name)
                        config.verbose = True
                    except (KeyError, ValueError, TypeError, FileNotFoundError, OSError) as e:
                        _log.debug("all(): %s failed — %s", name, e)
                        result[name] = None
                        config.verbose = True
                    bar()

                if self._hasDocs and self.notes is not None:
                    for noteName in notes_registry:
                        krName = notes_registry[noteName][1]
                        bar.text = krName
                        try:
                            config.verbose = False
                            result.setdefault("notes", {})[noteName] = self.notes._get(noteName)
                            config.verbose = True
                        except (KeyError, ValueError, TypeError, FileNotFoundError, OSError) as e:
                            _log.debug("all(): notes.%s failed — %s", noteName, e)
                            result.setdefault("notes", {})[noteName] = None
                            config.verbose = True
                        bar()

                bar.text = "시계열"
                result["timeseries"] = self.timeseries
                bar()
                bar.text = "연도별"
                result["annual"] = self.annual
                bar()
                bar.text = "재무비율"
                result["ratios"] = self.ratios
                bar()
        else:
            _log = logging.getLogger("dartlab.engines.dart.company")
            for name, label in _ALL_PROPERTIES:
                try:
                    result[name] = getattr(self, name)
                except (KeyError, ValueError, TypeError, FileNotFoundError, OSError) as e:
                    _log.debug("all(): %s failed — %s", name, e)
                    result[name] = None

            if self._hasDocs and self.notes is not None:
                notes_result = {}
                for noteName in notes_registry:
                    try:
                        notes_result[noteName] = self.notes._get(noteName)
                    except (KeyError, ValueError, TypeError, FileNotFoundError, OSError) as e:
                        _log.debug("all(): notes.%s failed — %s", noteName, e)
                        notes_result[noteName] = None
                result["notes"] = notes_result

            result["timeseries"] = self.timeseries
            result["annual"] = self.annual
            result["ratios"] = self.ratios

        return result

    # ── Excel 내보내기 ──

    def toExcel(
        self,
        outputPath: str | None = None,
        modules: list[str] | None = None,
    ) -> str:
        """Excel 파일로 내보내기.

        Args:
            outputPath: 저장 경로. None이면 '{종목코드}_{회사명}.xlsx'.
            modules: 포함할 시트. None이면 전체.
                가능한 값: "IS", "BS", "CF", "ratios", "dividend", "employee"

        Returns:
            저장된 파일 경로.

        Example::

            c = Company("005930")
            c.toExcel()                          # 005930_삼성전자.xlsx
            c.toExcel("output.xlsx")             # 지정 경로
            c.toExcel(modules=["IS", "BS"])      # 시트 선택
        """
        from dartlab.export.excel import exportToExcel
        return exportToExcel(self, outputPath=outputPath, modules=modules)

    # ── get() — 모듈 전체 결과 객체 접근 ──

    def get(self, name: str, **kwargs) -> Any:
        """모듈의 전체 결과 객체를 반환 (복수 DataFrame 접근용).

        Args:
            name: 모듈명 (dividend, audit, statements 등).

        Returns:
            해당 모듈의 Result 객체 전체.

        Example::

            r = c.get("audit")     # AuditResult
            r.opinionDf            # 감사의견
            r.feeDf                # 감사보수
        """
        if name == "holderOverview":
            return self.holderOverview
        return self._call_module(name, **kwargs)

    # ── LLM 분석 ──

    def ask(
        self,
        question: str,
        *,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        provider: str | None = None,
        model: str | None = None,
        stream: bool = False,
        **kwargs,
    ) -> str:
        """LLM에게 이 기업에 대해 질문.

        Args:
            question: 질문 텍스트 (한국어 또는 영어)
            include: 명시적으로 포함할 데이터 ["BS", "dividend", ...]
            exclude: 제외할 데이터
            provider: per-call provider override
            model: per-call model override
            stream: True면 터미널에 스트리밍 출력 후 전체 텍스트 반환
            **kwargs: LLMConfig override (temperature, max_tokens, ...)

        Returns:
            LLM 응답 텍스트

        Example::

            c = Company("005930")
            c.ask("재무 건전성을 분석해줘")
            c.ask("배당 추세", include=["dividend", "IS"])
            c.ask("부채 리스크", provider="ollama", model="llama3.1")
        """
        from dartlab.engines.ai import get_config
        from dartlab.engines.ai.context import (
            _get_sector,
            build_compact_context,
            build_context,
        )
        from dartlab.engines.ai.pipeline import run_pipeline
        from dartlab.engines.ai.prompts import _classify_question, build_system_prompt
        from dartlab.engines.ai.providers import create_provider

        config_ = get_config()
        overrides = {
            k: v
            for k, v in {"provider": provider, "model": model, **kwargs}.items()
            if v is not None
        }
        if overrides:
            config_ = config_.merge(overrides)

        use_compact = config_.provider in ("ollama", "codex", "claude-code")

        if use_compact:
            context_text, included_tables = build_compact_context(
                self, question, include=include, exclude=exclude,
            )
        else:
            context_text, included_tables = build_context(
                self, question, include=include, exclude=exclude,
            )

        if not use_compact:
            pipeline_result = run_pipeline(self, question, included_tables)
            if pipeline_result:
                context_text = context_text + pipeline_result

        sector = _get_sector(self)
        question_type = _classify_question(question)
        system = build_system_prompt(
            config_.system_prompt,
            included_modules=included_tables,
            sector=sector,
            question_type=question_type,
            compact=use_compact,
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"{context_text}\n\n---\n\n질문: {question}"},
        ]

        llm = create_provider(config_)

        if stream:
            chunks = []
            for chunk in llm.stream(messages):
                print(chunk, end="", flush=True)
                chunks.append(chunk)
            print()
            return "".join(chunks)

        response = llm.complete(messages)
        response.context_tables = included_tables

        from dartlab import config
        if config.verbose:
            print(f"  [LLM] {response.provider}/{response.model}")
            if response.usage:
                print(f"  [LLM] tokens: {response.usage.get('total_tokens', '?')}")

        return response.answer

    def chat(
        self,
        question: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        max_turns: int = 5,
        on_tool_call=None,
        on_tool_result=None,
        **kwargs,
    ) -> str:
        """에이전트 모드: LLM이 필요한 도구를 직접 선택하여 분석.

        ask()와 달리 모든 데이터를 미리 로딩하지 않고,
        LLM이 tool calling으로 필요한 데이터를 요청한다.

        Args:
            question: 질문 텍스트
            provider: per-call provider override
            model: per-call model override
            max_turns: 최대 도구 호출 반복 횟수
            on_tool_call: 도구 호출 시 콜백 (UI용)
            on_tool_result: 도구 결과 시 콜백 (UI용)
            **kwargs: LLMConfig override

        Returns:
            LLM 최종 응답 텍스트

        Example::

            c = Company("005930")
            c.chat("재무 건전성을 분석하고 이상 징후를 찾아줘")
            c.chat("배당 추세", provider="ollama", model="llama3.1")
        """
        from dartlab.engines.ai import get_config
        from dartlab.engines.ai.agent import AGENT_SYSTEM_ADDITION, agent_loop
        from dartlab.engines.ai.prompts import build_system_prompt
        from dartlab.engines.ai.providers import create_provider

        config_ = get_config()
        overrides = {
            k: v
            for k, v in {"provider": provider, "model": model, **kwargs}.items()
            if v is not None
        }
        if overrides:
            config_ = config_.merge(overrides)

        system = build_system_prompt(config_.system_prompt) + AGENT_SYSTEM_ADDITION
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"기업: {self.corpName} ({self.stockCode})\n\n{question}"},
        ]

        llm = create_provider(config_)
        return agent_loop(
            llm, messages, self,
            max_turns=max_turns,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
        )

    @property
    def market(self) -> str:
        """시장 코드."""
        return "KR"

    @property
    def currency(self) -> str:
        """통화 코드."""
        return "KRW"


