"""Topic/Chapter 한글 레이블 — AI 도구 enum + UI 공유 source of truth.

UI topicLabels.js와 동일한 매핑 + AI용 검색 aliases.
aliases: LLM이 한국어 질문에서 topic을 찾을 때 사용하는 추가 키워드.
"""

from __future__ import annotations

TOPIC_LABELS: dict[str, dict[str, str | list[str]]] = {
    # ── I. 회사의 개요 ──
    "companyOverview": {"label": "회사 개요", "aliases": ["회사", "개요", "기업정보", "기업개요"]},
    "companyHistory": {"label": "회사 연혁", "aliases": ["연혁", "역사"]},
    "capitalChange": {"label": "자본금 변동", "aliases": ["자본금", "유상증자", "무상증자"]},
    "shareCapital": {"label": "주식 현황", "aliases": ["주식", "발행주식", "주식수"]},
    "articlesOfIncorporation": {"label": "정관 사항", "aliases": ["정관"]},
    # ── II. 사업의 내용 ──
    "businessOverview": {"label": "사업 개요", "aliases": ["사업", "매출구성", "시장점유율", "사업내용"]},
    "productService": {"label": "사업 내용", "aliases": ["제품", "서비스", "주요제품"]},
    "rawMaterial": {"label": "원재료", "aliases": ["원재료", "원자재", "소재"]},
    "salesOrder": {"label": "매출/수주", "aliases": ["수주", "매출현황", "수주잔고"]},
    "riskDerivative": {"label": "위험관리/파생", "aliases": ["파생상품", "헤지", "환위험", "리스크", "위험요인", "리스크요인"]},
    "majorContractsAndRnd": {"label": "주요 계약/R&D", "aliases": ["연구개발", "R&D", "특허"]},
    "otherReferences": {"label": "기타 참고사항", "aliases": []},
    # ── III. 재무에 관한 사항 ──
    "fsSummary": {"label": "재무제표 요약", "aliases": ["재무요약", "비용성격별", "부문정보"]},
    "consolidatedStatements": {"label": "연결 재무제표", "aliases": ["연결재무제표"]},
    "consolidatedNotes": {"label": "연결 주석", "aliases": ["주석", "비용성격별분류", "리스", "우발채무주석", "공정가치"]},
    "financialStatements": {"label": "개별 재무제표", "aliases": ["개별재무제표", "별도재무제표"]},
    "financialNotes": {"label": "개별 주석", "aliases": ["개별주석"]},
    "fundraising": {"label": "자금조달", "aliases": ["자금조달", "차입금", "사채"]},
    # ── 재무제표 (finance 대체) ──
    "BS": {"label": "재무상태표", "aliases": ["재무상태표", "자산", "부채", "자본"]},
    "IS": {"label": "손익계산서", "aliases": ["손익계산서", "매출액", "영업이익", "당기순이익"]},
    "CIS": {"label": "포괄손익계산서", "aliases": ["포괄손익"]},
    "CF": {"label": "현금흐름표", "aliases": ["현금흐름", "영업활동", "투자활동", "재무활동"]},
    "SCE": {"label": "자본변동표", "aliases": ["자본변동"]},
    "ratios": {"label": "재무비율", "aliases": ["재무비율", "ROE", "ROA", "부채비율", "유동비율"]},
    # ── IV. 감사 ──
    "audit": {"label": "감사 의견", "aliases": ["감사", "감사의견"]},
    "internalControl": {"label": "내부통제", "aliases": ["내부통제", "내부회계"]},
    "auditContract": {"label": "감사 계약", "aliases": []},
    "nonAuditContract": {"label": "비감사 계약", "aliases": []},
    # ── V. 경영진 분석 ──
    "mdna": {"label": "경영진 분석(MD&A)", "aliases": ["경영진분석", "MD&A"]},
    "mdnaOverview": {"label": "경영진 분석 의견", "aliases": ["경영진", "분석의견"]},
    "cautionaryStatement": {"label": "전망 주의사항", "aliases": []},
    "financialConditionAndResults": {"label": "재무상태 및 영업실적", "aliases": ["영업실적"]},
    "investorProtection": {"label": "투자자 보호", "aliases": []},
    "liquidityAndCapitalResources": {"label": "유동성/자본조달", "aliases": ["유동성", "자본조달"]},
    "otherFinance": {"label": "기타 재무", "aliases": []},
    # ── VI. 이사회 ──
    "boardOfDirectors": {"label": "이사회", "aliases": ["이사회", "이사"]},
    "shareholderMeeting": {"label": "주주총회", "aliases": ["주주총회"]},
    "auditSystem": {"label": "감사 체계", "aliases": ["감사위원회"]},
    "outsideDirector": {"label": "사외이사", "aliases": ["사외이사"]},
    # ── VII. 주주 ──
    "majorHolder": {"label": "주요 주주", "aliases": ["최대주주", "지분", "대주주"]},
    "majorHolderChange": {"label": "주주 변동", "aliases": ["지분변동"]},
    "minorityHolder": {"label": "소수주주", "aliases": ["소액주주"]},
    "stockTotal": {"label": "주식 총수", "aliases": ["주식총수"]},
    "treasuryStock": {"label": "자기주식", "aliases": ["자사주", "자기주식"]},
    "dividend": {"label": "배당", "aliases": ["배당금", "배당정책", "배당수익률", "DPS"]},
    # ── VIII. 임직원 ──
    "employee": {"label": "직원 현황", "aliases": ["직원", "인원", "종업원"]},
    "executivePay": {"label": "임원 보수", "aliases": ["임원보수", "보수"]},
    "executive": {"label": "임원 현황", "aliases": ["임원"]},
    "executivePayAllTotal": {"label": "전체 보수 총액", "aliases": []},
    "executivePayIndividual": {"label": "개인별 보수", "aliases": []},
    "topPay": {"label": "5억이상 상위 보수", "aliases": []},
    "unregisteredExecutivePay": {"label": "미등기임원 보수", "aliases": []},
    # ── IX. 계열회사 ──
    "affiliateGroup": {"label": "계열회사", "aliases": ["계열사", "자회사", "그룹사"]},
    "investedCompany": {"label": "투자회사", "aliases": ["투자"]},
    # ── X. 특수관계 ──
    "relatedPartyTx": {"label": "특수관계 거래", "aliases": ["관계사거래", "특수관계"]},
    # ── XI. 기타 ──
    "corporateBond": {"label": "사채 관리", "aliases": ["사채", "회사채"]},
    "privateOfferingUsage": {"label": "사모자금 사용", "aliases": []},
    "publicOfferingUsage": {"label": "공모자금 사용", "aliases": []},
    "shortTermBond": {"label": "단기사채", "aliases": []},
    "disclosureChanges": {"label": "공시변경 사항", "aliases": ["공시변경"]},
    "contingentLiability": {"label": "우발채무", "aliases": ["우발채무", "약정"]},
    "sanction": {"label": "제재/조치", "aliases": ["제재"]},
    "subsequentEvents": {"label": "후발사건", "aliases": ["후발사건"]},
    "expertConfirmation": {"label": "전문가 확인", "aliases": []},
    "ceoConfirmation": {"label": "대표이사 확인", "aliases": []},
    # ── XII. 상세표 ──
    "appendixSchedule": {"label": "부속명세서", "aliases": []},
    "subsidiaryDetail": {"label": "종속회사 상세", "aliases": []},
    "affiliateGroupDetail": {"label": "계열회사 상세", "aliases": []},
    "investmentInOtherDetail": {"label": "타법인 출자 상세", "aliases": []},
    "rndDetail": {"label": "R&D 상세", "aliases": []},
}


def topicLabel(topic: str) -> str:
    """topic의 한국어 라벨 반환."""
    entry = TOPIC_LABELS.get(topic)
    return entry["label"] if entry else topic


def buildTopicEnumDescription(topicNames: list[str]) -> str:
    """topic 목록에서 enum description 문자열 생성. LLM tool schema용."""
    parts = []
    for t in topicNames:
        entry = TOPIC_LABELS.get(t)
        if entry:
            label = entry["label"]
            aliases = entry.get("aliases", [])
            if aliases:
                parts.append(f"{t}={label}/{'/'.join(aliases[:3])}")
            else:
                parts.append(f"{t}={label}")
        else:
            parts.append(t)
    return ", ".join(parts)
