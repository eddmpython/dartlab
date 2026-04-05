"""Loughran-McDonald 기반 한/영 금융 감성 사전.

원본: Loughran & McDonald (2011) — 재무 텍스트 전용 감성 분류.
한국어 목록: DART 공시 패턴 기반 구축.
"""

NEGATIVE_KR: set[str] = {
    "손실", "부실", "위험", "불확실", "소송", "제재", "하락", "감소", "적자",
    "부도", "채무불이행", "파산", "횡령", "배임", "분식", "감사의견거절",
    "영업정지", "상장폐지", "부실채권", "대손", "충당부채", "우발부채",
    "불공정", "담합", "과징금", "벌금", "시정명령", "영업손실", "자본잠식",
    "유동성위기", "지급불능", "무배당", "매출감소", "이익감소", "수주감소",
    "해고", "구조조정", "폐업", "철수", "매각", "손상차손", "감액",
    "평가손실", "환차손", "대손상각", "연체", "부실화", "경영악화",
    "실적부진", "영업적자", "당기순손실", "채무초과", "감자", "상환불능",
    "신용등급하향", "하향조정", "실적하락", "역성장", "수요감소",
}

POSITIVE_KR: set[str] = {
    "성장", "증가", "개선", "확대", "흑자", "호조", "상승", "수주",
    "신규", "진출", "투자", "배당", "인수", "합병", "시너지", "혁신",
    "특허", "수상", "인증", "흑자전환", "사상최대", "매출증가",
    "이익증가", "배당확대", "자사주", "주주환원", "시장점유율", "경쟁력",
    "원가절감", "효율", "생산성", "연구개발", "기술력", "수출증가",
    "해외진출", "신사업", "실적개선", "수주증가", "수익개선", "원가개선",
    "신제품", "신기술", "최대실적", "성장동력", "다각화", "견조", "양호",
}

NEGATIVE_EN: set[str] = {
    "loss", "decline", "adverse", "impairment", "litigation", "default",
    "bankruptcy", "fraud", "violation", "penalty", "risk", "uncertain",
    "weak", "negative", "decrease", "deteriorat", "layoff", "restructur",
    "writedown", "deficit", "delinquen", "foreclosur", "insolven",
    "unfavorabl", "downturn", "misstat", "restat", "terminat",
    "suspend", "revok", "sanction", "forfeit", "obsolet", "underperform",
    "shortfall", "breach", "noncomplian",
}

POSITIVE_EN: set[str] = {
    "growth", "increase", "improve", "expand", "profit", "strong",
    "positive", "gain", "dividend", "innovation", "record", "exceed",
    "outperform", "upgrade", "momentum", "recovery", "robust",
    "surge", "breakthrough", "synergy", "favorable", "strength",
    "upturn", "achieve", "succeed", "efficien", "productiv",
    "opportunity", "advanc", "benefit",
}

UNCERTAINTY_KR: set[str] = {
    "불확실", "변동", "예측불가", "리스크", "우려", "가능성", "잠재",
    "미확정", "유보", "조건부", "불투명", "불안정", "급변",
}

LITIGIOUS_KR: set[str] = {
    "소송", "분쟁", "중재", "제소", "청구", "손해배상", "위반",
    "위법", "과태료", "시정", "고발", "행정처분", "징계", "수사",
}
