"""edinet 엔진 스펙 — 코드에서 자동 추출."""

from __future__ import annotations


def buildSpec() -> dict:
    """edinet 엔진 스펙 반환."""
    return {
        "name": "edinet",
        "description": "일본 EDINET 전자공시 — 유가증권보고서 sections + XBRL 재무 정규화",
        "summary": {
            "market": "JP",
            "currency": "JPY",
            "accountingStandards": ["J-GAAP", "IFRS", "US-GAAP"],
            "dataSource": "EDINET API v2 (金融庁)",
            "namespaces": ["docs", "finance"],
        },
        "detail": {
            "docs": {
                "sections": "유가증권보고서 topic × period 수평화",
                "sectionMapper": "일본어 section title → topicId (sectionMappings.json)",
                "topicCount": "초기 ~45개, 실험 기반 확장",
            },
            "finance": {
                "mapper": "J-GAAP/IFRS XBRL element → snakeId (7단계 파이프라인)",
                "pivot": "분기별 시계열 피벗",
                "statements": ["BS", "IS", "CF", "CIS"],
            },
            "openapi": {
                "base": "https://api.edinet-fsa.go.jp/api/v2",
                "documents": "서류 목록 조회 (날짜별)",
                "download": "서류 ZIP 다운로드 (XBRL/CSV/PDF)",
                "edinetCodes": "기업 마스터 목록",
            },
            "publicAPI": [
                "Company(edinetCode) — EDINET Company 객체",
                "Company.sections — sections 수평화",
                "Company.show(topic) — topic별 데이터",
                "Company.BS / IS / CF — 재무제표 바로가기",
                "Company.index — 전체 topic 요약 보드",
            ],
        },
    }
