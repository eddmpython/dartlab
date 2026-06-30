// 스캔 등급 설명 다이얼로그용 큐레이션 맵 · ★사람 작성(자동 생성 금지, feedback_no_docstring_auto_sweep 정합).
// 각 등급 축이 *무엇을* 보는지(what) + 등급이 매겨지는 근거(basis). 사다리 자체는 engine.ts GRADE_SCALE 가 SSOT.
// 금지: 인과 단정("…면 주가 상승")·매수/매도 신호·"좋은 주식". 등급 = fact 아닌 *판정*이므로 근거+기준만 기술한다.
//
// 키 = COMPOSITE_AXES[].key (engine.ts): prof·growth·debt·liq·eff·qual·gov·stab·audit·cap (순서형) + cf(분류).
// 순서형 10축은 등급 사다리·레이더 스포크 대상. cf(현금흐름)는 순서 없는 8패턴 → CF_PATTERN_GUIDE 별도(사다리·색 금지).

export interface GradeGuideEntry {
	kr: { what: string; basis: string };
	en: { what: string; basis: string };
}

export const GRADE_GUIDE: Record<string, GradeGuideEntry> = {
	prof: {
		kr: { what: '돈을 버는 힘 · 영업이익률·ROE 수준', basis: '최근 영업이익률과 자기자본이익률을 등급 사다리에 대응(공시 재무 기준)' },
		en: { what: 'Earning power · OP margin & ROE level', basis: 'Latest OP margin and ROE mapped to the ladder (from filed financials)' }
	},
	growth: {
		kr: { what: '외형 성장 · 매출 추세', basis: '다년 매출 증가율(CAGR/YoY)을 사다리에 대응' },
		en: { what: 'Top-line growth · revenue trajectory', basis: 'Multi-year revenue growth (CAGR/YoY) mapped to the ladder' }
	},
	gov: {
		kr: { what: '거버넌스 · 지배구조·공시 충실도', basis: 'scan ecosystem 거버넌스 신호를 A~E 5단으로 대응' },
		en: { what: 'Governance · ownership & disclosure quality', basis: 'Scan ecosystem governance signals mapped to A-E' }
	},
	qual: {
		kr: { what: '이익의 질 · 이익이 현금·본업으로 뒷받침되는 정도', basis: '발생액·현금화·일회성 비중 신호를 사다리에 대응' },
		en: { what: 'Earnings quality · how cash- and core-backed profit is', basis: 'Accrual / cash-conversion / one-off signals mapped to the ladder' }
	},
	liq: {
		kr: { what: '단기 지급 능력 · 유동성', basis: '유동비율 등 단기 상환 여력 신호를 사다리에 대응' },
		en: { what: 'Short-term solvency · liquidity', basis: 'Current ratio and short-term coverage signals mapped to the ladder' }
	},
	debt: {
		kr: { what: '재무 안정 · 부채비율·이자보상배율(레버리지·상환 능력)', basis: '부채비율·단기채무·이자보상배율(ICR) 신호를 4단(안전/관찰/주의/고위험)으로 대응' },
		en: { what: 'Solvency · leverage & interest coverage', basis: 'Debt ratio / short-term debt / ICR mapped to 4 tiers (safe→high-risk)' }
	},
	eff: {
		kr: { what: '효율성 · 자산을 매출로 돌리는 회전 속도', basis: '자산회전율·현금전환주기(CCC) 신호를 4단(우수/양호/보통/비효율)으로 대응. 회전 무의미 업종은 "해당없음"(척도 밖·중립)' },
		en: { what: 'Efficiency · how fast assets turn into sales', basis: 'Asset turnover / cash-conversion cycle mapped to 4 tiers. Turnover-irrelevant sectors are "N/A" (off-scale, neutral)' }
	},
	audit: {
		kr: { what: '감사 위험 · 감사의견·감사인 교체 등 회계 경고 신호', basis: '감사의견·감사인 변경·특기사항을 4단(안전/관찰/주의/고위험)으로 대응' },
		en: { what: 'Audit risk · audit opinion / auditor-change warning signals', basis: 'Audit opinion / auditor change / emphasis-of-matter mapped to 4 tiers (safe→high-risk)' }
	},
	stab: {
		kr: { what: '경영권 안정 · 최대주주 지분 등 지배 안정성(재무 레버리지 아님)', basis: 'insider 최대주주 지분·지분변동 신호를 5단(안정/보통/취약/경고/위험)으로 대응. 지분 미확인은 척도 밖(중립)' },
		en: { what: 'Control stability · controlling-shareholder ownership (not financial leverage)', basis: 'Insider largest-holder stake / change mapped to 5 tiers. Unconfirmed stake is off-scale (neutral)' }
	},
	cap: {
		kr: { what: '주주환원 · 배당·자사주로 돌려주는 강도(증자 희석은 반대 방향)', basis: '배당·자사주 매입/소각·증자 신호를 4단(적극환원/환원형/중립/희석형)으로 대응' },
		en: { what: 'Capital return · dividends & buybacks (share issuance dilutes the other way)', basis: 'Dividend / buyback / issuance signals mapped to 4 tiers (active→dilutive)' }
	}
};

// 현금흐름(cf) · 순서 없는 8 라이프사이클 패턴. OCF/ICF/FINCF 부호 조합의 *유형*이라 등급 사다리·색·순위 금지.
// 사람 작성(자동 생성 금지). 금지: 인과 단정·매수/매도 신호. 부호 패턴을 중립 기술만.
export const CF_PATTERN_GUIDE: Record<string, { kr: string; en: string }> = {
	성장투자형: {
		kr: '영업현금 흑자(+)로 투자 유출(−)과 차입 상환(−)을 함께 감당하는 현금 구조.',
		en: 'Operating cash (+) funds both investment outflows (−) and debt repayment (−).'
	},
	공격성장형: {
		kr: '영업현금 흑자(+)에 외부 조달(+, 차입·증자)까지 더해 대규모 투자(−)에 투입하는 구조.',
		en: 'Operating cash (+) plus external financing (+) fund large investment (−).'
	},
	구조재편형: {
		kr: '영업현금 흑자(+)에 자산 매각(투자 유입 +)을 더해 부채를 상환(−)하는 구조.',
		en: 'Operating cash (+) and asset sales (investing +) repay debt (−).'
	},
	현금축적형: {
		kr: '영업·투자·재무 세 채널 모두에서 현금이 유입(+/+/+)되는 구조.',
		en: 'Cash flows in across operating, investing and financing (+/+/+).'
	},
	외부의존형: {
		kr: '영업현금 적자(−) 상태에서 외부 조달(+)로 투자·운영을 메우는 구조.',
		en: 'Operating cash is negative (−); external financing (+) covers the gap.'
	},
	축소정리형: {
		kr: '영업현금 적자(−)를 자산 매각(투자 유입 +)으로 메우고 부채를 상환(−)하는 구조.',
		en: 'Negative operating cash (−) covered by asset sales (+) while repaying debt (−).'
	},
	위기대응형: {
		kr: '영업현금 적자(−)를 자산 매각(+)과 외부 조달(+)로 동시에 메우는 구조.',
		en: 'Negative operating cash (−) covered by both asset sales (+) and financing (+).'
	},
	현금위기형: {
		kr: '영업·투자·재무 세 채널 모두에서 현금이 유출(−/−/−)되는 구조.',
		en: 'Cash flows out across operating, investing and financing (−/−/−).'
	}
};

// 현금흐름 패턴 → [영업(OCF), 투자(ICF), 재무(FINCF)] 부호. 패턴은 이 부호 3개로 정의되므로 역도출이 정확.
// '+' = 현금 유입, '−' = 유출(방향 표기 · 좋고 나쁨 아님). scan financial/cashflow.py _PATTERNS 와 1:1.
export const CF_PATTERN_SIGNS: Record<string, ['+' | '−', '+' | '−', '+' | '−']> = {
	성장투자형: ['+', '−', '−'],
	공격성장형: ['+', '−', '+'],
	구조재편형: ['+', '+', '−'],
	현금축적형: ['+', '+', '+'],
	외부의존형: ['−', '−', '+'],
	축소정리형: ['−', '+', '−'],
	위기대응형: ['−', '+', '+'],
	현금위기형: ['−', '−', '−']
};
