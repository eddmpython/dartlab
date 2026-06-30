// EDGAR panel TOC 섹션 유효성 · `src/dartlab/providers/edgar/panel/build/mapper.py` 1:1 포팅.
//
// walker 의 `_ITEM_HEAD_RE` 가 prose 상호참조("as defined in Item 405 of Regulation S-K")·표지 보일러플레이트를
// Item 헤딩으로 오검출해 진짜 Item 본문을 가짜 섹션으로 흘린다(junk 가 빈 행 아니라 실본문 수백KB~MB swallow).
// 카탈로그 표준명 정확 일치(catalog[num]===tail)가 단일 게이트 · canonicalItem 이 진짜 헤딩엔 표준명을 강제하므로,
// prose tail·카탈로그 밖 번호(405/601/103)·표지(==form)는 표준명과 불일치 → junk. panel 데이터엔 보존, TOC 만 거름.

// SEC 표준 item 카탈로그 (mapper.ITEM_NAMES_10K 1:1). 표준명 정확 일치가 유효성 게이트라 값이 byte-identical 이어야 함.
export const ITEM_NAMES_10K: Record<string, string> = {
	'1': 'Business',
	'1A': 'Risk Factors',
	'1B': 'Unresolved Staff Comments',
	'1C': 'Cybersecurity',
	'2': 'Properties',
	'3': 'Legal Proceedings',
	'4': 'Mine Safety Disclosures',
	'5': "Market for Registrant's Common Equity",
	'6': 'Selected Financial Data',
	'7': "Management's Discussion and Analysis",
	'7A': 'Quantitative and Qualitative Disclosures About Market Risk',
	'8': 'Financial Statements and Supplementary Data',
	'9': 'Changes in and Disagreements with Accountants',
	'9A': 'Controls and Procedures',
	'9B': 'Other Information',
	'10': 'Directors, Executive Officers and Corporate Governance',
	'11': 'Executive Compensation',
	'12': 'Security Ownership of Certain Beneficial Owners',
	'13': 'Certain Relationships and Related Transactions',
	'14': 'Principal Accountant Fees and Services',
	'15': 'Exhibits, Financial Statement Schedules',
	'16': 'Form 10-K Summary'
};
export const ITEM_NAMES_10Q: Record<string, string> = {
	'1': 'Financial Statements',
	'2': "Management's Discussion and Analysis",
	'3': 'Quantitative and Qualitative Disclosures About Market Risk',
	'4': 'Controls and Procedures'
};

// 재무제표 terse 키 → 사람 라벨 (TOC 표시용). sectionKey·panel 데이터는 BS/IS 보존(라벨만 표시 변환).
export const STMT_LABELS: Record<string, string> = {
	BS: 'Balance Sheet',
	IS: 'Income Statement',
	CF: 'Cash Flow Statement',
	CIS: 'Comprehensive Income',
	EF: "Stockholders' Equity"
};

const ITEM_RE = /^item\s+(\d+[A-Za-z]?)\b\.?\s*(.*)/i; // mapper._ITEM_RE 1:1 (anchored)

export type EdgarSectionStatus = 'navi' | 'stmt' | 'junk';

// EDGAR sectionLeaf 의 TOC navigability · 'navi'(유효 표준 Item) / 'stmt'(재무제표 본표) / 'junk'(오검출·표지).
// mapper.edgarSectionStatus 1:1.
export function edgarSectionStatus(form: string, sectionLeaf: string): EdgarSectionStatus {
	if (!sectionLeaf || sectionLeaf === form) return 'junk'; // 표지/front-matter (chapter==section)
	if (sectionLeaf in STMT_LABELS) return 'stmt'; // 재무제표 본표 (disclosureKey 앵커, relabel)
	const m = ITEM_RE.exec(sectionLeaf);
	if (!m) return 'junk'; // Item 형식 아닌 narrative (preamble 등)
	const num = m[1].toUpperCase();
	const tail = (m[2] ?? '').trim();
	const catalog = form === '10-Q' ? ITEM_NAMES_10Q : form === '10-K' ? ITEM_NAMES_10K : null;
	if (catalog === null) return 'navi'; // 카탈로그 없는 폼(20-F 등) · 과잉필터 회피(honest)
	return catalog[num] === tail ? 'navi' : 'junk'; // 표준명 정확 일치만 navigable
}
