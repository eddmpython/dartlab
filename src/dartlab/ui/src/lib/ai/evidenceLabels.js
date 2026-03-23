const MODULE_LABELS = {
	BS: "재무상태표",
	IS: "손익계산서",
	CF: "현금흐름표",
	CIS: "포괄손익계산서",
	SCE: "자본변동표",
	ratios: "핵심 재무비율",
	fsSummary: "재무 요약",
	dividend: "배당 데이터",
	shareCapital: "자본 변동 데이터",
	employee: "임직원 데이터",
	executive: "임원 데이터",
	majorHolder: "최대주주 데이터",
	treasuryStock: "자기주식 데이터",
	audit: "감사 관련 데이터",
	businessOverview: "사업 개요",
	productService: "제품·서비스",
	disclosureChanges: "공시 변화",
	subsequentEvents: "후속 사건",
	riskDerivative: "리스크·파생상품",
	internalControl: "내부통제",
	governanceOverview: "지배구조 개요",
	boardOfDirectors: "이사회",
	holderOverview: "주주 구성",
	companyOverview: "회사 개요",
	companyHistory: "회사 연혁",
	costByNature: "성격별 비용 분류",
	rnd: "연구개발 데이터",
	segments: "사업부문 데이터",
	tangibleAsset: "유형자산",
	investmentInOther: "타법인 투자",
	investedCompany: "투자회사 현황",
	affiliateGroupDetail: "계열회사 현황",
	subsidiaryDetail: "종속회사 현황",
	contingentLiability: "우발채무",
	otherReference: "기타 참고 공시",
	_dart_openapi_filings: "최근 공시 목록",
	_diff: "공시 변화 비교",
};

const TOOL_LABELS = {
	list_live_filings: "실시간 공시 목록 조회",
	read_filing: "공시 원문 읽기",
	list_filings: "저장된 공시 목록 조회",
	show_topic: "공시 항목 조회",
	get_data: "재무·공시 데이터 조회",
	get_system_spec: "시스템 기능 확인",
	get_runtime_capabilities: "런타임 기능 확인",
};

function normalizeModuleName(name) {
	if (!name) return "";
	let normalized = String(name).trim();
	for (const prefix of ["report_", "module_", "section_"]) {
		if (normalized.startsWith(prefix)) {
			normalized = normalized.slice(prefix.length);
			break;
		}
	}
	return normalized;
}

export function formatEvidenceLabel(name, fallback = "관련 데이터") {
	if (!name) return fallback;
	const normalized = normalizeModuleName(name);
	return MODULE_LABELS[normalized] || MODULE_LABELS[name] || fallback;
}

export function formatToolLabel(name, fallback = "도구 활동") {
	if (!name) return fallback;
	return TOOL_LABELS[name] || fallback;
}

export function getIncludedEvidenceLabels(meta = null) {
	if (!meta) return [];
	if (Array.isArray(meta.includedEvidence) && meta.includedEvidence.length > 0) {
		return meta.includedEvidence
			.map(item => item?.label || formatEvidenceLabel(item?.name, null))
			.filter(Boolean);
	}
	return (meta.includedModules || [])
		.map(name => formatEvidenceLabel(name, null))
		.filter(Boolean);
}
