"""dart/finance 엔진 스펙 — 코드에서 자동 추출."""

from __future__ import annotations


def buildSpec() -> dict:
    """dart/finance 엔진 스펙 반환."""
    import dataclasses

    from dartlab.core.finance.ratios import RatioResult

    ratioFields = [f.name for f in dataclasses.fields(RatioResult) if f.name != "warnings"]

    return {
        "name": "dart.finance",
        "description": "DART XBRL 재무제표 정규화 — 분기별 standalone 시계열",
        "summary": {
            "statements": ["IS", "BS", "CF", "SCE"],
            "period": "2019~2024 (분기별)",
            "mappedAccounts": 34171,
            "ratioCount": len(ratioFields),
        },
        "detail": {
            "normalization": {
                "IS": "누적→standalone 변환 (thstrm_add_amount)",
                "CF": "이전 분기 차분으로 standalone 변환",
                "BS": "시점 잔액 그대로",
                "SCE": "변동사유×자본항목 매트릭스 피벗 (sceMapper 2-tier 매핑)",
            },
            "mappingPipeline": [
                "prefix 제거",
                "ID_SYNONYMS 적용",
                "ACCOUNT_NAME_SYNONYMS 적용",
                "CORE_MAP 조회",
                "accountMappings.json 조회 (34,171개)",
                "괄호 제거 fallback",
            ],
            "ratios": ratioFields,
        },
    }
