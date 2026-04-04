/**
 * Topic/Chapter 한글 레이블 매핑.
 * SectionsViewer, TopicRenderer 등에서 공유.
 */

export const TOPIC_LABELS = {
	companyOverview: "회사 개요", companyHistory: "회사 연혁", articlesOfIncorporation: "정관 사항",
	capitalChange: "자본금 변동", shareCapital: "주식 현황", dividend: "배당",
	productService: "사업 내용", rawMaterial: "원재료", businessOverview: "사업 개요",
	salesOrder: "매출/수주", riskDerivative: "위험관리/파생", majorContractsAndRnd: "주요 계약/R&D",
	otherReferences: "기타 참고사항", consolidatedStatements: "연결 재무제표", fsSummary: "재무제표 요약",
	consolidatedNotes: "연결 주석", financialStatements: "개별 재무제표", financialNotes: "개별 주석",
	fundraising: "자금조달", BS: "재무상태표", IS: "손익계산서", CIS: "포괄손익계산서",
	CF: "현금흐름표", SCE: "자본변동표", ratios: "재무비율", audit: "감사 의견",
	mdna: "경영진 분석(MD&A)", internalControl: "내부통제", auditContract: "감사 계약",
	nonAuditContract: "비감사 계약", boardOfDirectors: "이사회", shareholderMeeting: "주주총회",
	auditSystem: "감사 체계", outsideDirector: "사외이사", majorHolder: "주요 주주",
	majorHolderChange: "주주 변동", minorityHolder: "소수주주", stockTotal: "주식 총수",
	treasuryStock: "자기주식", employee: "직원 현황", executivePay: "임원 보수",
	executive: "임원 현황", executivePayAllTotal: "전체 보수 총액", executivePayIndividual: "개인별 보수",
	topPay: "5억이상 상위 보수", unregisteredExecutivePay: "미등기임원 보수", affiliateGroup: "계열회사",
	investedCompany: "투자회사", relatedPartyTx: "특수관계 거래", corporateBond: "사채 관리",
	privateOfferingUsage: "사모자금 사용", publicOfferingUsage: "공모자금 사용", shortTermBond: "단기사채",
	investorProtection: "투자자 보호", disclosureChanges: "공시변경 사항", contingentLiability: "우발채무",
	sanction: "제재/조치", subsequentEvents: "후발사건", expertConfirmation: "전문가 확인",
	subsidiaryDetail: "종속회사 상세", affiliateGroupDetail: "계열회사 상세",
	investmentInOtherDetail: "타법인 출자 상세", rndDetail: "R&D 상세",
};

export const CHAPTER_LABELS = {
	"I": "I. 회사의 개요", "II": "II. 사업의 내용", "III": "III. 재무에 관한 사항",
	"IV": "IV. 감사인의 감사의견 등", "V": "V. 이사의 경영진단 및 분석의견",
	"VI": "VI. 이사회 등 회사의 기관에 관한 사항", "VII": "VII. 주주에 관한 사항",
	"VIII": "VIII. 임원 및 직원 등에 관한 사항", "IX": "IX. 계열회사 등에 관한 사항",
	"X": "X. 대주주 등과의 거래내용", "XI": "XI. 그 밖에 투자자 보호를 위하여 필요한 사항",
	"XII": "XII. 상세표",
};

const ROMAN_ORDER = { I: 1, II: 2, III: 3, IV: 4, V: 5, VI: 6, VII: 7, VIII: 8, IX: 9, X: 10, XI: 11, XII: 12 };

export function romanToInt(ch) { return ROMAN_ORDER[ch] ?? 99; }
export function topicLabel(topic) { return TOPIC_LABELS[topic] || topic; }
export function chapterLabel(ch) { return CHAPTER_LABELS[ch] || ch || "기타"; }
