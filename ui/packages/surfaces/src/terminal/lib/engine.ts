// DartLab Terminal · compute engine (dartlab.js 포팅 + 데이터 정직성 수정).
//   · 연간 cf.op/inv/fin 은 실데이터 → CFO/CFI/CFF/FCF 실표시 (opening/closing 은 null → 제외)
//   · ecosystem YoY delta 는 99% null → finance 5Y 배열에서 직접 YoY 계산 (실데이터화)
//   · 합성 OHLC 제거 → 실 재무추세(매출·영업이익·이익률) annual/quarter
// 전역 없음: createEngine(raw) 가 raw 위에서 동작하는 순수 클로저 묶음을 반환.

import type {
	RawData,
	Company,
	Credit,
	Valuation,
	RiskFlag,
	Verdict,
	Tone,
	EcoNode,
	Num,
	TrendSeries,
	StatementRow,
	PercentileMetric,
	Financials,
	StackSeg,
	FinanceCompany,
	IndustryStat,
	Universe,
	UniversePercentile,
	CategoricalShare,
	PriceStat,
	Hist,
	RiskCatalogItem,
} from './types';
import { RISK_RULES, evalRiskCatalog, type RiskRuleCtx } from './riskRules';
import { INDUSTRY_TAILWIND_MAP, classifyTailwind } from './macroMappings';

const SECTOR_EN: Record<string, string> = {
	semiconductor: 'Semiconductors', auto: 'Automobile', energy: 'Energy', electronics: 'Electronics',
	chemical: 'Chemicals', aerospace: 'Aerospace & Defense', shipbuilding: 'Shipbuilding', steel: 'Steel',
	food: 'Food & Bev', software: 'Software', pharma: 'Pharma', finance: 'Financials', retail: 'Retail',
	construction: 'Construction', telecom: 'Telecom', media: 'Media', battery: 'Batteries', textile: 'Apparel',
	logistics: 'Logistics', cosmetics: 'Cosmetics', machinery: 'Machinery', paper: 'Paper', leisure: 'Leisure',
	electrical: 'Electrical', plastic: 'Plastics', realestate: 'Real Estate', education: 'Education',
	medicalDevice: 'Medical Devices', environment: 'Environment', buildingMaterials: 'Building Materials',
	railroad: 'Railroad', consulting: 'Holding/Consulting', agriculture: 'Agriculture', misc: 'Misc'
};
const SECTOR_KR: Record<string, string> = {
	semiconductor: '반도체', auto: '자동차', energy: '에너지', electronics: '전자', chemical: '화학',
	aerospace: '항공우주', shipbuilding: '조선', steel: '철강', food: '음식료', software: '소프트웨어',
	pharma: '제약바이오', finance: '금융', retail: '유통', construction: '건설', telecom: '통신',
	media: '미디어', battery: '2차전지', textile: '섬유의류', logistics: '물류', cosmetics: '화장품',
	machinery: '기계', paper: '제지', leisure: '레저', electrical: '전기', plastic: '플라스틱',
	realestate: '부동산', education: '교육', medicalDevice: '의료기기', environment: '환경',
	buildingMaterials: '건자재', railroad: '철도', consulting: '지주', agriculture: '농업', misc: '기타'
};
// 등급 사다리 SSOT · gradeTone/gradeScore 가 위치(좋음→나쁨)로 톤·점수(0~1)를 도출. scan 엔진 실제 출력값과 일치.
// 미수록 값(eff '해당없음'=N/A, stab '미확인')은 indexOf<0 → gradeScore null(레이더 스포크 생략)·gradeTone neutral(중립칩) · 거짓 순서 방지.
export const GRADE_SCALE: Record<string, string[]> = {
	prof: ['우수', '양호', '보통', '저수익', '적자'],
	growth: ['고성장', '성장', '정체', '역성장', '급감'],
	debt: ['안전', '관찰', '주의', '고위험'],
	liq: ['우수', '양호', '보통', '주의', '위험'],
	eff: ['우수', '양호', '보통', '비효율'], // scanEfficiency grade · '해당없음'(N/A)은 척도 밖(중립)
	qual: ['우수', '양호', '보통', '주의', '위험'],
	gov: ['A', 'B', 'C', 'D', 'E'],
	stab: ['안정', '보통', '취약', '경고', '위험'], // scan insider stability 실제 출력(옛 '불안정' 미발생·'미확인'은 척도 밖)
	audit: ['안전', '관찰', '주의', '고위험'], // scanAudit riskLevel 4단 (옛 3단 저/중/고 교체)
	cap: ['적극환원', '환원형', '중립', '희석형'] // scanCapital 분류 · 주주환원 강도
};

// ── 종합(composite) 축 SSOT ──
// 중간패널 칩·다이얼로그 블록·레이더 스포크를 *모두* 이 한 배열에서 파생한다(3-way 축 불일치 근절).
// 순서 = 분석가 읽기 흐름. kind='ordered' 만 레이더 스포크(gradeScore)·등급 사다리 대상.
// kind='class'(현금흐름 8패턴)은 순서가 없으므로 색·사다리·레이더에서 제외(거짓 순서 방지).
export interface CompositeAxis {
	key: string; // GRADE_SCALE·gradeTone·gradeScore·GRADE_GUIDE 공용 키
	kr: string;
	en: string;
	short: string; // 레이더 스포크 짧은 라벨(겹침 완화)
	group: string; // GROUP_COLOR 카테고리 색
	field: keyof EcoNode; // 등급 문자열이 담긴 EcoNode 필드
	kind: 'ordered' | 'class';
}
export const COMPOSITE_AXES: CompositeAxis[] = [
	{ key: 'prof', kr: '수익성', en: 'Profit', short: '수익', group: 'health', field: 'profGrade', kind: 'ordered' },
	{ key: 'growth', kr: '성장성', en: 'Growth', short: '성장', group: 'income', field: 'growthGrade', kind: 'ordered' },
	{ key: 'debt', kr: '재무안정', en: 'Solvency', short: '안정', group: 'health', field: 'debtGrade', kind: 'ordered' },
	{ key: 'liq', kr: '유동성', en: 'Liquidity', short: '유동', group: 'quality', field: 'liqGrade', kind: 'ordered' },
	{ key: 'eff', kr: '효율성', en: 'Efficiency', short: '효율', group: 'changes', field: 'effGrade', kind: 'ordered' },
	{ key: 'qual', kr: '이익질', en: 'Quality', short: '이익질', group: 'quality', field: 'qualGrade', kind: 'ordered' },
	{ key: 'gov', kr: '거버넌스', en: 'Govern', short: '거버넌스', group: 'governance', field: 'govGrade', kind: 'ordered' },
	{ key: 'stab', kr: '경영권안정', en: 'Control', short: '경영권', group: 'governance', field: 'stability', kind: 'ordered' },
	{ key: 'audit', kr: '감사', en: 'Audit', short: '감사', group: 'quality', field: 'auditRisk', kind: 'ordered' },
	{ key: 'cap', kr: '주주환원', en: 'Capital return', short: '환원', group: 'disclosure', field: 'capClass', kind: 'ordered' },
	{ key: 'cf', kr: '현금흐름', en: 'Cash flow', short: '현금', group: 'price', field: 'cfPattern', kind: 'class' }
];
// dartlab scan group colors · dartlab 토큰 계열로 정렬
const GROUP_COLOR: Record<string, string> = {
	identity: '#a3a8b3', income: '#60a5fa', health: '#34d399', governance: '#a78bfa',
	quality: '#fbbf24', workforce: '#f472b6', changes: '#ec4899', price: '#ea4647',
	valuation: '#34d399', disclosure: '#c084fc'
};
const MARKET_LABEL: Record<string, string> = { 유가증권: 'KOSPI', 코스닥: 'KOSDAQ', 코넥스: 'KONEX' };
// 블로그 공개 슬러그 정규화 · 옛 meta.json(6h 캐시 잔존)은 폴더명 그대로(정렬용 "NN-" 접두 포함)를
// 슬러그로 실었다. 공개 슬러그는 6자리 종목코드로 시작하므로, 코드 앞 1~3자리 접두일 때만 벗긴다
// (새 슬러그 "005930-…" 는 \d{1,3}- 패턴에 안 걸려 무변 · 멱등).
const normalizeBlogSlug = (s: string): string => s.replace(/^\d{1,3}-(?=[0-9A-Z]{6}-)/, '');
const rev = <T>(a: T[] | undefined): T[] => (a || []).slice().reverse();

// 법인명 정규화 · ㈜·(주)·주식회사·공백 제거 + 소문자. 출자 다이얼로그의 피출자사명→상장코드 exact 해소용.
// 영문약칭↔한글표기(예: 삼성SDS↔삼성에스디에스) 차이는 정규화로 못 풀어 미해소(=비상장 취급, 보수적).
function normalizeCorpName(s: string): string {
	return (s || '').replace(/㈜/g, '').replace(/\(주\)/g, '').replace(/주식회사/g, '').replace(/\s+/g, '').toLowerCase();
}
const num = (v: Num): Num => (v == null || Number.isNaN(v) ? null : v);
function lastNonNull(arr: Num[] | undefined): { v: number; i: number } | null {
	if (!arr) return null;
	for (let i = arr.length - 1; i >= 0; i--) {
		const x = arr[i];
		if (x != null) return { v: x, i };
	}
	return null;
}
function median(a: Num[]): number | null {
	const s = a.filter((x): x is number => x != null && Number.isFinite(x)).sort((x, y) => x - y);
	return s.length ? s[Math.floor(s.length / 2)] : null;
}
// 정렬값 배열 5분위(p10~p90) 선형보간 · 시장/전체 유니버스 분포곡선을 모집단 배열에서 라이브 산출(prebuild 불필요).
// 표본 < 10 이면 null · 분포 신뢰 부족(02 정직 가드 "n<10 분포 숨김"). DistCurve 는 band null 이면 미렌더.
function quantileBand(arr: Num[]): { p10: number; p25: number; median: number; p75: number; p90: number } | null {
	const xs = arr.filter((x): x is number => x != null && Number.isFinite(x)).sort((a, b) => a - b);
	if (xs.length < 10) return null;
	const q = (f: number): number => {
		const idx = (xs.length - 1) * f;
		const lo = Math.floor(idx);
		const hi = Math.ceil(idx);
		return lo === hi ? xs[lo] : xs[lo] + (xs[hi] - xs[lo]) * (idx - lo);
	};
	return { p10: q(0.1), p25: q(0.25), median: q(0.5), p75: q(0.75), p90: q(0.9) };
}
// 실도수 히스토그램 · 동종사 전체 값 배열을 robust 범위(p2~p98)로 클리핑해 N빈으로 집계(outlier 무력화).
// 5분위 보간(quantileBand)보다 정직: 실제 봉우리·gap·왜도를 그대로. 회사값은 범위 클램프 + 초과 표식.
function histOf(arr: Num[], companyVal: Num, bins = 22): Hist | null {
	const xs = arr.filter((x): x is number => x != null && Number.isFinite(x)).sort((a, b) => a - b);
	if (xs.length < 12) return null;
	const q = (f: number): number => {
		const idx = (xs.length - 1) * f;
		const lo = Math.floor(idx);
		const hi = Math.ceil(idx);
		return lo === hi ? xs[lo] : xs[lo] + (xs[hi] - xs[lo]) * (idx - lo);
	};
	let lo = q(0.02);
	let hi = q(0.98);
	if (!(hi > lo)) { lo = xs[0]; hi = xs[xs.length - 1]; } // 분포 폭 0(동일값 다수) 폴백
	if (!(hi > lo)) return null;
	const counts = new Array(bins).fill(0);
	for (const x of xs) {
		const c = Math.min(hi, Math.max(lo, x));
		let b = Math.floor(((c - lo) / (hi - lo)) * bins);
		if (b >= bins) b = bins - 1;
		if (b < 0) b = 0;
		counts[b]++;
	}
	const maxC = Math.max(...counts, 1);
	const frac = (v: number): number => Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
	const cv = companyVal != null && Number.isFinite(companyVal) ? companyVal : null;
	return {
		bins: counts.map((c) => c / maxC),
		companyFrac: cv == null ? null : frac(cv),
		companyOver: cv == null ? 0 : cv < lo ? -1 : cv > hi ? 1 : 0,
		medianFrac: frac(q(0.5)),
		lo,
		hi,
		n: xs.length
	};
}
function pctRank(arr: Num[], v: Num, lowerBetter?: boolean): number | null {
	const xs = arr.filter((x): x is number => x != null && Number.isFinite(x));
	if (!xs.length || v == null) return null;
	const below = xs.filter((x) => x <= v).length;
	let p = Math.round((below / xs.length) * 100);
	if (lowerBetter) p = 100 - p;
	return Math.max(1, Math.min(100, p));
}
export function gradeTone(scaleKey: string, val?: string): Tone {
	const sc = GRADE_SCALE[scaleKey];
	if (!sc || !val) return 'neutral';
	const i = sc.indexOf(val);
	if (i < 0) return 'neutral';
	const f = i / (sc.length - 1);
	return f <= 0.18 ? 'up' : f <= 0.45 ? 'good' : f <= 0.62 ? 'neutral' : f <= 0.8 ? 'warn' : 'down';
}
function gradeScore(scaleKey: string, val?: string): Num {
	const sc = GRADE_SCALE[scaleKey];
	if (!sc || !val) return null;
	const i = sc.indexOf(val);
	if (i < 0) return null;
	return 1 - i / (sc.length - 1);
}

// 통화별 raw 금액(원/USD) 포맷 · 시총·장부가 등. KRW=조/억, USD=$T/$B/$M. 통화 인식 SSOT.
// 재무 시리즈(이미 조 단위로 ÷1e12 된 값)는 fmtMoneyTril 을 쓴다(별 컨벤션).
export function fmtMoney(v: Num, currency = 'KRW'): string {
	if (v == null) return '·';
	if (currency === 'USD') {
		const a = Math.abs(v);
		if (a >= 1e12) return '$' + (v / 1e12).toLocaleString('en-US', { maximumFractionDigits: 2 }) + 'T';
		if (a >= 1e9) return '$' + (v / 1e9).toLocaleString('en-US', { maximumFractionDigits: 1 }) + 'B';
		if (a >= 1e6) return '$' + (v / 1e6).toLocaleString('en-US', { maximumFractionDigits: 1 }) + 'M';
		return '$' + v.toLocaleString('en-US', { maximumFractionDigits: 0 });
	}
	// 천단위 콤마 · 조/억 환산값도 콤마 적용(타법인 출자 장부가·시총 등 큰 금액 가독성).
	if (v >= 1e12) return (v / 1e12).toLocaleString('en-US', { maximumFractionDigits: 1 }) + '조';
	if (v >= 1e8) return Math.round(v / 1e8).toLocaleString('en-US') + '억';
	return v.toLocaleString('en-US');
}

// 이미 조(兆) 단위로 환산된 재무 시리즈 값(예 0.4162=$416B·300=300조) 포맷 · fmtMoney(raw)와 컨벤션 다름.
// KRW: v+'조'. USD: v≥1 → $vT, 아니면 $(v*1000)B (조달러→억/십억달러).
export function fmtMoneyTril(v: Num, currency = 'KRW'): string {
	if (v == null) return '·';
	if (currency === 'USD') {
		const a = Math.abs(v);
		if (a >= 1) return '$' + v.toLocaleString('en-US', { maximumFractionDigits: 2 }) + 'T';
		if (a >= 0.001) return '$' + (v * 1000).toLocaleString('en-US', { maximumFractionDigits: 1 }) + 'B';
		return '$' + (v * 1e6).toLocaleString('en-US', { maximumFractionDigits: 0 }) + 'M';
	}
	return v.toLocaleString('en-US', { maximumFractionDigits: 2 }) + '조';
}

export function fmtKRW(v: Num): string {
	return fmtMoney(v, 'KRW');
}

export interface Engine {
	raw: RawData;
	years: string[];
	source: string;
	buildCompany(code: string): Company | null;
	search(q: string): string | null;
	suggest(q: string, n?: number): { code: string; name: string; industry: string }[];
	featured(n?: number): string[];
	sectorPerf(): { id: string; kr: string; en: string; chg: number; n: number }[];
	sectorTailwinds(): { id: string; kr: string; en: string; blended: number; tailwindKey: string }[];
	priceOf(code: string): RawData['prices']['data'][string] | undefined;
	nameOf(code: string): string;
	// 피출자사명 → 상장 종목 해소(시총·최근 순익). 정규화 exact + 시총·재무 존재 게이트 · 미해소 = null(비상장 취급).
	lookupListed(name: string): { code: string; marketCap: number; net: number | null } | null;
	// 유니버스 교차 백분위 · co.percentile(업종 고정)과 달리 모집단(업종/시장/전체) 선택. 다이얼로그 전용(콜드 비용 0).
	percentileIn(code: string, universe: Universe): UniversePercentile | null;
	// 거시 산업 sweep · 한 산업의 cross-industry 비교 스냅샷(분포·scan grade 버킷%·gov 밸류·tailwind·멤버). 좌측 sweep·산업 다이얼로그 전용.
	industryMacro(id: string): IndustryMacro | null;
	industryMembers(id: string): IndustryMember[];
	industryTrails(): IndustryTrail[]; // 산업 연도별 이동 · (수익성 × 전년比 성장) 궤적. 지형도 시간축.
}

// ── 거시 산업 sweep 모델 (좌측 LeftRail 산업층 · IndustryDialog) ──
// 산업이 *주체* · 회사 주체 percentileIn 과 직교. 모두 baked(industryStats·ecosystem·gov prices) 합성, 새 fetch 0.
export interface IndustryDist {
	p10: number;
	p25: number;
	median: number;
	p75: number;
	p90: number;
	n: number;
}
export interface IndustryMacroMember {
	code: string;
	name: string;
	value: number;
}
export interface IndustryMember {
	code: string;
	name: string;
	margin: number; // opMargin % (가로)
	growth: number; // revCagr % (세로)
	cap: number; // gov 시총(크기) · 0 가능
	grade: string; // profGrade (수익성 등급)
	debtGrade: string; // debtGrade (재무 건전성) · 색=gradeTone('debt'). x축(수익성)과 직교.
}
export interface IndustryTrail {
	id: string;
	count: number; // 산업 멤버(상장 primary) 수
	pts: { year: string; x: number; y: number }[]; // 연도별 (영업이익률 median, 전년比 매출성장 median %). 오래된→최신, 끝점=최신연도
}
export interface IndustryMacro {
	id: string;
	kr: string;
	en: string;
	count: number; // 산업 멤버(상장 primary) 수
	dist: Record<string, IndustryDist | null>; // industryStats 분포(n<10 → null). opMargin·netMargin·roe·debtRatio·currentRatio·revCagr·netIncomeCagr·ccc·assetTurnover·icr
	marginIqr: number | null; // opMargin p75-p25 = 마진 양극화(polarization 마진렌즈)
	pbr: IndustryDist | null; // gov 시총/자본 분포(KRX 아님 · raw.prices=gov/prices). 밸류 양극화
	bucket: { profRisk: number; lossRisk: number; growthRisk: number; debtRisk: number; liqRisk: number; cfDistress: number }; // scan grade 악성 버킷 %(ordinal 평균 아님). profRisk=적자+저수익, lossRisk=적자만(혼합 방지)
	cfSignature: { pattern: string; share: number } | null; // cfPattern 최빈 = 산업 현금흐름 시그니처
	direction: { opMarginDelta: number | null; roeDelta: number | null; revenueYoyPct: number | null }; // YoY 방향(개선/악화) · 다년 CAGR과 직교(최근 변화), 구조 vs 순환 단서
	tailwind: number | null; // macro blended 순풍/역풍
	macroPhase: string;
	top: { roe: IndustryMacroMember[]; growth: IndustryMacroMember[]; risk: IndustryMacroMember[] }; // Q4 멤버 지형 → 종목 드릴인
}

export function createEngine(raw: RawData): Engine {
	// 회사 유니버스 SSOT 는 viewer 와 같은 ecosystem. search-index 는 검색용 메타데이터로만 보강하고,
	// ecosystem 에 없는 별도 시장(예: US) 행만 합친다.
	const publishedIndex = new Map(raw.index.map((r) => [r.stockCode, r]));
	const ecosystemRows: RawData['index'] = (raw.eco?.nodes || []).map((node) => {
		const indexed = publishedIndex.get(node.id);
		return {
			stockCode: node.id,
			corpName: node.label || indexed?.corpName || node.id,
			industry: node.industry || indexed?.industry || 'misc',
			stage: indexed?.stage || node.stageName,
			revenue: node.revenue ?? indexed?.revenue ?? null
		};
	});
	if (ecosystemRows.length) {
		const ecosystemCodes = new Set(ecosystemRows.map((r) => r.stockCode));
		raw = { ...raw, index: [...ecosystemRows, ...raw.index.filter((r) => !ecosystemCodes.has(r.stockCode))] };
	}
	const byCode: Record<string, RawData['index'][number]> = {};
	const normByName: Record<string, string> = {}; // 정규화 법인명 → stockCode (lookupListed). 첫 매칭 우선.
	for (const r of raw.index) {
		byCode[r.stockCode] = r;
		const k = normalizeCorpName(r.corpName);
		if (k && !(k in normByName)) normByName[k] = r.stockCode;
	}
	const ecoByCode: Record<string, EcoNode> = {};
	for (const n of raw.eco?.nodes || []) ecoByCode[n.id] = n;
	const years = raw.finance?.years || ['2021', '2022', '2023', '2024', '2025'];
	const nullSeries = (): Num[] => years.map(() => null);
	function emptyFinanceCompany(): FinanceCompany {
		return {
			is: { sales: nullSeries(), op: nullSeries(), net: nullSeries(), opMargin: nullSeries() },
			bs: {
				assets: {},
				liab: {},
				equity: {},
				totals: {
					totalAsset: nullSeries(),
					totalLiab: nullSeries(),
					totalEquity: nullSeries(),
					currAsset: nullSeries(),
					currLiab: nullSeries()
				}
			},
			cf: { op: null, inv: null, fin: null, opening: null, closing: null, fx: null },
			ratios: { roe: nullSeries(), debtRatio: nullSeries() },
			macroExposure: null
		};
	}
	const hasTerminalPrice = (code: string): boolean => !!raw.prices.data[code];

	// industry → nodes 인덱스 1 회 구축 → industryNodes O(1) (회사전환마다 2664 전수스캔 3 회 제거).
	const byIndustry: Record<string, EcoNode[]> = {};
	for (const n of Object.values(ecoByCode)) (byIndustry[n.industry] ||= []).push(n);
	const industryNodes = (industry: string): EcoNode[] => byIndustry[industry] || [];

	function deriveCredit(fin: RawData['finance']['companies'][string]): Credit {
		const dr = lastNonNull(fin.ratios.debtRatio);
		const roe = lastNonNull(fin.ratios.roe);
		const ca = lastNonNull(fin.bs.totals.currAsset);
		const cl = lastNonNull(fin.bs.totals.currLiab);
		const opm = lastNonNull(fin.is.opMargin);
		const op = lastNonNull(fin.is.op);
		const debtRatio = dr ? dr.v : null;
		const curr = ca && cl && cl.v ? (ca.v / cl.v) * 100 : null;
		const sCap = debtRatio == null ? 60 : Math.max(5, Math.min(100, 100 - debtRatio / 6));
		const sLiq = curr == null ? 60 : Math.max(5, Math.min(100, curr / 3));
		const sProf = opm == null ? 50 : Math.max(5, Math.min(100, 50 + opm.v * 2.2));
		const sCf = op == null ? 55 : Math.max(5, Math.min(100, op.v > 0 ? 92 : 35));
		const sStab = roe == null ? 55 : Math.max(5, Math.min(100, 55 + roe.v * 1.4));
		const health = Math.round(sCap * 0.26 + sLiq * 0.18 + sProf * 0.2 + sCf * 0.2 + sStab * 0.16);
		const grades: [number, string][] = [
			[95, 'dCR-AAA'], [88, 'dCR-AA+'], [82, 'dCR-AA'], [76, 'dCR-AA-'], [70, 'dCR-A+'], [63, 'dCR-A'],
			[56, 'dCR-A-'], [49, 'dCR-BBB+'], [42, 'dCR-BBB'], [35, 'dCR-BBB-'], [28, 'dCR-BB+'], [20, 'dCR-BB'],
			[12, 'dCR-B'], [0, 'dCR-CCC']
		];
		const grade = (grades.find((g) => health >= g[0]) || grades[grades.length - 1])[1];
		const pd = Math.max(0.005, Math.min(28, Math.pow((100 - health) / 100, 3.1) * 30)).toFixed(2) + '%';
		return {
			grade,
			healthScore: health,
			pd,
			tone: health >= 70 ? 'up' : health >= 49 ? 'good' : 'warn',
			tracks: [
				{ kr: '자본구조', en: 'Capital structure', score: Math.round(sCap) },
				{ kr: '유동성', en: 'Liquidity', score: Math.round(sLiq) },
				{ kr: '수익성', en: 'Profitability', score: Math.round(sProf) },
				{ kr: '현금흐름', en: 'Cash flow', score: Math.round(sCf) },
				{ kr: '재무안정성', en: 'Stability', score: Math.round(sStab) }
			],
			basis: { debtRatio, curr: curr == null ? null : Math.round(curr), opm: opm ? opm.v : null }
		};
	}

	function valuationOf(code: string): Valuation | null {
		const node = ecoByCode[code];
		const fin = raw.finance.companies[code];
		const px = raw.prices.data[code];
		if (!node || !fin || !px || !px.currentPrice) return null;
		const net = lastNonNull(fin.is.net);
		const eq = lastNonNull(fin.bs.totals.totalEquity);
		const shares = px.marketCap / px.currentPrice;
		const per = net && net.v > 0 ? px.marketCap / (net.v * 1e12) : null;
		const pbr = eq && eq.v > 0 ? px.marketCap / (eq.v * 1e12) : null;
		const perL: number[] = [];
		const pbrL: number[] = [];
		for (const n of industryNodes(node.industry)) {
			const f = raw.finance.companies[n.id];
			const p = raw.prices.data[n.id];
			if (!f || !p || !p.marketCap) continue;
			const nn = lastNonNull(f.is.net);
			const ee = lastNonNull(f.bs.totals.totalEquity);
			if (nn && nn.v > 0) {
				const x = p.marketCap / (nn.v * 1e12);
				if (x > 0 && x < 200) perL.push(x);
			}
			if (ee && ee.v > 0) {
				const x = p.marketCap / (ee.v * 1e12);
				if (x > 0 && x < 60) pbrL.push(x);
			}
		}
		const perMed = median(perL);
		const pbrMed = median(pbrL);
		const fairPer = perMed && net && net.v > 0 ? (perMed * net.v * 1e12) / shares : null;
		const fairPbr = pbrMed && eq && eq.v > 0 ? (pbrMed * eq.v * 1e12) / shares : null;
		const fair = [fairPer, fairPbr].filter((x): x is number => x != null && x > 0);
		const fairMid = fair.length ? fair.reduce((a, b) => a + b, 0) / fair.length : null;
		const upside = fairMid ? ((fairMid - px.currentPrice) / px.currentPrice) * 100 : null;
		const perPos = per != null && perMed ? (per <= perMed ? 'cheap' : 'rich') : null;
		return {
			per, pbr, perMed, pbrMed,
			fairLow: fair.length ? Math.min(...fair) : null,
			fairHigh: fair.length ? Math.max(...fair) : null,
			fairMid, upside, last: px.currentPrice, perPos
		};
	}

	// 위험 평가 컨텍스트 · EcoNode + 업종 중앙값(industryStats distribution). riskFlagsOf·riskCatalogOf 공유.
	// 규칙·임계·라벨은 lib/riskRules.ts SSOT (글랜스·다이얼로그 공동 소비, 로직 중복 0).
	function riskCtxOf(code: string): RiskRuleCtx {
		const e = ecoByCode[code] || ({} as EcoNode);
		const statsRec = raw.industryStats as Record<string, IndustryStat> | null;
		const median = (field: keyof EcoNode): number | null =>
			statsRec?.[e.industry]?.distribution?.[field as string]?.median ?? null;
		return { e, median };
	}

	function riskFlagsOf(code: string): RiskFlag[] {
		const ctx = riskCtxOf(code);
		// 점등(red/yellow)만 수집 · clear·na 는 글랜스 미표시(다이얼로그 전용).
		const lit = new Map<string, { hard: boolean; flag: RiskFlag }>();
		for (const rule of RISK_RULES) {
			const ev = rule.evaluate(ctx);
			if (ev && ev.lv !== 'clear') lit.set(rule.id, { hard: rule.hard, flag: { lv: ev.lv, kr: ev.kr, en: ev.en, d: ev.d } });
		}
		// 억제: 부채 부담(레벨) red 점등 시 부채비율 급증(변화)은 같은 부채 축 중복 → 제거.
		const db = lit.get('debtBurden');
		if (db && db.flag.lv === 'red') lit.delete('debtRatioSpike');
		// 정렬: red>yellow, 같은 레벨 내 절대수치 위반(hard) 우선. 집합은 불변(순서만).
		const lvRank = (lv: string): number => (lv === 'red' ? 0 : lv === 'yellow' ? 1 : 2);
		const out = [...lit.values()]
			.sort((a, b) => lvRank(a.flag.lv) - lvRank(b.flag.lv) || (a.hard === b.hard ? 0 : a.hard ? -1 : 1))
			.map((x) => x.flag);
		// fallback green · '검사한 임계 중' 한정(검사 안 한 차원까지 보증 안 함 = 거짓완결성 회피).
		if (!out.length) out.push({ lv: 'green', kr: '주요 위험 신호 없음', en: 'No major red flags', d: '검사 임계 중 초과 없음' });
		return out;
	}

	// 다이얼로그용 · 전체 차원 카탈로그 + 이 회사 현상태(점등/통과/판정불가). 억제·정렬 없음.
	function riskCatalogOf(code: string): RiskCatalogItem[] {
		return evalRiskCatalog(riskCtxOf(code));
	}

	function tailwindOf(industry: string): Company['tailwind'] {
		const k = INDUSTRY_TAILWIND_MAP[industry];
		const tw = k && raw.macro?.sectorTailwind ? raw.macro.sectorTailwind[k] : null;
		if (!tw) return null;
		const b = tw.blended;
		const cls = classifyTailwind(b);
		return {
			key: k, kr: SECTOR_KR[industry] || industry, en: SECTOR_EN[industry] || industry, blended: b, krScore: tw.kr, usScore: tw.us,
			label: cls.labelKr, labelEn: cls.labelEn,
			tone: cls.tone
		};
	}

	function verdictOf(co: Company): Verdict {
		const scores = co.radar.map((r) => r.s).filter((s): s is number => s != null);
		const gradeAvg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0.5;
		const up = co.valuation && co.valuation.upside != null ? co.valuation.upside : 0;
		const valScore = up > 25 ? 1 : up > 5 ? 0.72 : up > -15 ? 0.45 : 0.2;
		const r1y = co.price.ret1y == null ? 0 : co.price.ret1y;
		const momScore = r1y > 80 ? 0.85 : r1y > 20 ? 0.7 : r1y > -10 ? 0.5 : 0.25;
		const tw = co.tailwind;
		const twScore = tw ? Math.min(1, tw.blended / 0.6) : 0.5;
		const riskRed = co.risks.filter((x) => x.lv === 'red').length;
		let composite = 0.44 * gradeAvg + 0.18 * valScore + 0.14 * momScore + 0.18 * twScore + 0.06 * (riskRed ? 0 : 1);
		composite = Math.round(composite * 100);
		const band: Verdict['band'] =
			composite >= 74 ? { kr: '강세 · 우량', en: 'STRONG', tone: 'up' }
				: composite >= 60 ? { kr: '양호 · 관심', en: 'SOLID', tone: 'good' }
				: composite >= 46 ? { kr: '중립 · 관망', en: 'NEUTRAL', tone: 'neutral' }
				: composite >= 32 ? { kr: '주의 · 점검', en: 'CAUTION', tone: 'warn' }
				: { kr: '취약 · 회피', en: 'WEAK', tone: 'down' };
		const sorted = co.radar.filter((r) => r.s != null).slice().sort((a, b) => (b.s as number) - (a.s as number));
		const strengths: Verdict['strengths'] = [];
		const concerns: Verdict['concerns'] = [];
		for (const r of sorted.slice(0, 2)) if ((r.s as number) >= 0.6) strengths.push({ kr: `${r.kr} 우수 (상위)`, en: `Strong ${r.en}` });
		for (const r of sorted.slice(-2)) if ((r.s as number) <= 0.45) concerns.push({ kr: `${r.kr} 취약`, en: `Weak ${r.en}` });
		if (up != null && up > 15) strengths.push({ kr: `업종 대비 저평가 (+${up.toFixed(0)}% 여력)`, en: `Undervalued vs peers (+${up.toFixed(0)}%)` });
		if (up != null && up < -15) concerns.push({ kr: `업종 대비 고평가 (${up.toFixed(0)}%)`, en: `Rich vs peers (${up.toFixed(0)}%)` });
		if (r1y > 50) strengths.push({ kr: `1년 모멘텀 강함 (+${r1y.toFixed(0)}%)`, en: 'Strong 1Y momentum' });
		if (tw && tw.blended >= 0.4) strengths.push({ kr: `${tw.kr} 섹터 순풍`, en: `${tw.kr} sector tailwind` });
		for (const x of co.risks.filter((x) => x.lv === 'red').slice(0, 2)) concerns.push({ kr: x.kr, en: x.en });
		return {
			composite, band, strengths: strengths.slice(0, 3), concerns: concerns.slice(0, 3),
			riskRed, riskYellow: co.risks.filter((x) => x.lv === 'yellow').length
		};
	}

	// ── 유니버스 교차 백분위 (engine 내부, raw 클로저) ──
	// buildFundMetrics: 정량 13지표 백분위. peers(모집단)만 바꾸면 같은 산식이 업종/시장/전체로 · pctRank 는
	//   유니버스 무관 순수함수(로직 복제 0). band: useStatsBand=업종 industryStats(prebuilt), 아니면 peers 라이브 5분위.
	//   lowerBetter=true (부채비율·CCC·발생액비율) 는 pctRank 가 p 를 뒤집어 "상위 N%" 가 항상 우수를 뜻함.
	function buildFundMetrics(node: EcoNode, peers: EcoNode[], useStatsBand: boolean, withHist: boolean): PercentileMetric[] {
		const col = (f: keyof EcoNode): Num[] => peers.map((n) => (n[f] as Num) ?? null);
		const statsRec = raw.industryStats as Record<string, IndustryStat> | null;
		const dist = statsRec?.[node.industry]?.distribution;
		const bandOf = (field: keyof EcoNode): PercentileMetric['band'] => {
			if (useStatsBand) {
				// 업종 분포 밴드(industryStats) · public 만 실데이터, local(단일사) 은 null. distribution 키 = metric field 와 1:1.
				const d = dist?.[field as string];
				if (!d || d.p10 == null || d.p90 == null) return null;
				const med = d.median ?? d.p10;
				return { p10: d.p10, p25: d.p25 ?? med, median: med, p75: d.p75 ?? med, p90: d.p90 };
			}
			return quantileBand(col(field)); // 시장/전체 = 같은 모집단 배열 라이브 5분위(표본<10 → null, 백분위와 자기일관)
		};
		// 히스토그램은 모든 유니버스에서 *실제 peer 값 배열*로 산출(industryStats 보간 아님 → 더 정직). hot path(co.percentile)는 withHist=false 로 생략.
		const mk = (kr: string, en: string, axis: string, field: keyof EcoNode, unit: string, lower?: boolean): PercentileMetric | { p: null } => ({
			kr, en, axis, unit, lowerBetter: !!lower, v: node[field] as Num ?? null, p: pctRank(col(field), (node[field] as Num) ?? null, lower),
			band: bandOf(field), hist: withHist ? histOf(col(field), (node[field] as Num) ?? null) : null
		});
		return [
			mk('영업이익률', 'OP margin', 'prof', 'opMargin', '%'),
			mk('순이익률', 'Net margin', 'prof', 'netMargin', '%'),
			mk('ROE', 'ROE', 'prof', 'roe', '%'),
			mk('ROA', 'ROA', 'prof', 'roa', '%'),
			mk('매출성장', 'Rev growth', 'growth', 'revCagr', '%'),
			mk('순이익성장', 'Net growth', 'growth', 'netIncomeCagr', '%'),
			mk('부채비율', 'Debt ratio', 'debt', 'debtRatio', '%', true),
			mk('이자보상배율', 'Int. coverage', 'debt', 'icr', '배'),
			mk('유동비율', 'Current ratio', 'liq', 'currentRatio', '%'),
			mk('자산회전율', 'Asset turn', 'eff', 'assetTurnover', '배'),
			mk('현금전환주기', 'Cash cycle', 'eff', 'ccc', '일', true),
			mk('발생액비율', 'Accruals', 'qual', 'accrualRatio', '', true),
			mk('종합점수', 'Gov score', 'gov', 'govScore', '점')
		].filter((m): m is PercentileMetric => m.p != null);
	}

	// 정성(범주형) 등급 · 유니버스 내 *같은 등급 비중*(순위 아님, 가짜 백분위 금지 02 KILL#3). 거버넌스·경영권·감사·주주환원·현금흐름.
	const QUAL_KEYS = ['gov', 'stab', 'audit', 'cap', 'cf'];
	function buildQualShares(node: EcoNode, peers: EcoNode[]): CategoricalShare[] {
		return COMPOSITE_AXES.filter((a) => QUAL_KEYS.includes(a.key))
			.map((a) => {
				const scale = GRADE_SCALE[a.key] || []; // cf(class)는 척도 없음 → dist 비고(순서 없음, 막대 금지)
				const myVal = (node[a.field] as string | undefined) || '';
				const valued = peers.filter((pn) => !!(pn[a.field] as string | undefined));
				const vn = valued.length;
				const counts: Record<string, number> = {};
				for (const pn of valued) { const v = pn[a.field] as string; if (scale.includes(v)) counts[v] = (counts[v] || 0) + 1; }
				const same = myVal ? valued.filter((pn) => (pn[a.field] as string) === myVal).length : 0;
				// 등급레벨별 동종사 비중 · "이 잣대에서 어느 등급에 많이 몰렸나"(분포). 회사 등급은 cell 에서 하이라이트.
				const dist = scale.map((step) => ({ step, share: vn ? Math.round(((counts[step] || 0) / vn) * 100) : 0, tone: gradeTone(a.key, step) }));
				return { key: a.key, kr: a.kr, en: a.en, v: myVal, tone: gradeTone(a.key, myVal), sameShare: vn && myVal ? Math.round((same / vn) * 100) : null, peerN: vn, dist };
			})
			.filter((g) => !!g.v);
	}

	// 가격(PER/PBR) · EcoNode 에 없어 raw.finance+prices 에서 노드별 산출(valuationOf 동일 식·이상치 가드). 펀더와 *분리* 격자(02 KILL#2).
	function priceRatios(id: string): { per: number | null; pbr: number | null } {
		const f = raw.finance.companies[id];
		const p = raw.prices.data[id];
		if (!f || !p || !p.marketCap) return { per: null, pbr: null };
		const nn = lastNonNull(f.is.net);
		const ee = lastNonNull(f.bs.totals.totalEquity);
		let per: number | null = null;
		let pbr: number | null = null;
		if (nn && nn.v > 0) { const x = p.marketCap / (nn.v * 1e12); if (x > 0 && x < 200) per = x; }
		if (ee && ee.v > 0) { const x = p.marketCap / (ee.v * 1e12); if (x > 0 && x < 60) pbr = x; }
		return { per, pbr };
	}
	// 가격은 lowerBetter 모호(저PER=저평가 vs 우려) → 톤·우수 프레이밍 없이 분포 내 위치(p)만. quantileBand 로 곡선.
	function buildPriceStats(code: string, peers: EcoNode[]): { per: PriceStat; pbr: PriceStat } {
		const mine = priceRatios(code);
		const perCol: Num[] = [];
		const pbrCol: Num[] = [];
		for (const pn of peers) {
			const r = priceRatios(pn.id);
			if (r.per != null) perCol.push(r.per);
			if (r.pbr != null) pbrCol.push(r.pbr);
		}
		return {
			per: { v: mine.per, p: pctRank(perCol, mine.per), band: quantileBand(perCol), hist: histOf(perCol, mine.per), n: perCol.length },
			pbr: { v: mine.pbr, p: pctRank(pbrCol, mine.pbr), band: quantileBand(pbrCol), hist: histOf(pbrCol, mine.pbr), n: pbrCol.length }
		};
	}

	// co.percentile (업종 고정) · buildCompany 가 매번 호출하는 핫패스. 무손상 유지(grades/price 미산출=콜드비용 0).
	function industryPercentile(code: string): Company['percentile'] {
		const node = ecoByCode[code];
		if (!node) return null;
		const peers = industryNodes(node.industry);
		return { industry: node.industryName || SECTOR_KR[node.industry] || node.industry, n: peers.length, metrics: buildFundMetrics(node, peers, true, false) };
	}

	// 유니버스 교차 백분위 · 다이얼로그 전용(buildCompany 비경유 → 콜드비용 0). 모집단(업종/시장/전체) 선택만 분기.
	// 소속지수('index')는 구성종목 멤버십 데이터 부재로 BLOCKED(00 ④) · union 미포함, "시총상위N=KOSPI200" 위조 금지(02 KILL#5).
	function percentileIn(code: string, universe: Universe): UniversePercentile | null {
		const node = ecoByCode[code];
		if (!node) return null;
		const allNodes = raw.eco?.nodes ?? [];
		const peers =
			universe === 'industry' ? industryNodes(node.industry)
			: universe === 'market' ? allNodes.filter((n) => n.market === node.market)
			: allNodes;
		const label =
			universe === 'industry' ? (node.industryName || SECTOR_KR[node.industry] || node.industry)
			: universe === 'market' ? (MARKET_LABEL[node.market || ''] || node.market || 'KRX')
			: '전체상장사';
		return {
			universe,
			label,
			n: peers.length,
			metrics: buildFundMetrics(node, peers, universe === 'industry', true),
			grades: buildQualShares(node, peers),
			price: buildPriceStats(code, peers)
		};
	}

	function derivePeers(code: string, industry: string): Company['peers'] {
		return raw.index
			.filter((r) => r.industry === industry)
			.sort((a, b) => (b.revenue || 0) - (a.revenue || 0))
			.slice(0, 8)
			.map((r) => ({ code: r.stockCode, name: r.corpName, revenue: r.revenue, self: r.stockCode === code }));
	}

	// 실 재무추세: finance(연간) + quarters(분기). 합성 없음.
	function trendFromFinance(fin: RawData['finance']['companies'][string]): TrendSeries {
		return {
			periods: years,
			sales: fin.is.sales.slice(),
			op: fin.is.op.slice(),
			net: fin.is.net.slice(),
			opMargin: fin.is.opMargin.slice(),
			freq: 'annual'
		};
	}
	function trendFromQuarters(code: string): TrendSeries | null {
		const q = raw.quarters?.companies[code];
		if (!q || !q.is || !Array.isArray(q.is.sales) || !Array.isArray(q.is.op) || !Array.isArray(q.is.net)) return null;
		if (!q.is.sales.some((v) => v != null)) return null;
		const op = q.is.op;
		const opMargin = q.is.sales.map((s, i) => {
			const o = op[i];
			return s != null && s !== 0 && o != null ? +((o / s) * 100).toFixed(1) : null;
		});
		return {
			periods: raw.quarters?.periods || [],
			sales: q.is.sales.slice(),
			op: q.is.op.slice(),
			net: q.is.net.slice(),
			opMargin,
			freq: 'quarter'
		};
	}

	// ui/web 재무카드 · finance.json 5Y 에서 계산 (DuckDB 불필요, 즉시)
	function computeFinancials(fin: FinanceCompany): Financials {
		const yrs = years;
		const sales = fin.is.sales;
		const net = fin.is.net;
		const T = fin.bs.totals;
		const div = (a: Num, b: Num): Num => (a != null && b != null && b !== 0 ? a / b : null);
		const opMargin = fin.is.opMargin.slice();
		const netMargin = sales.map((s, i) => (s && net[i] != null ? +((net[i]! / s) * 100).toFixed(1) : null));
		const assetTurn = sales.map((s, i) => (s != null && T.totalAsset[i] ? +(s / T.totalAsset[i]!).toFixed(2) : null));
		const equityMult = T.totalAsset.map((a, i) => (a != null && T.totalEquity[i] ? +(a / T.totalEquity[i]!).toFixed(2) : null));
		const deRatio = T.totalLiab.map((l, i) => { const v = div(l, T.totalEquity[i]); return v == null ? null : +(v * 100).toFixed(0); });
		const currRatio = T.currAsset.map((c, i) => { const v = div(c, T.currLiab[i]); return v == null ? null : +(v * 100).toFixed(0); });
		const roe = fin.ratios.roe.slice();
		const li = (arr: Num[]): number | null => { for (let i = arr.length - 1; i >= 0; i--) if (arr[i] != null) return arr[i]; return null; };
		const A = fin.bs.assets || {};
		const at = (k: string): number => { const a = A[k]; return a && a.length ? a[a.length - 1] ?? 0 : 0; };
		const totAssetL = li(T.totalAsset) ?? 0;
		const sumBuckets = at('cash') + at('recv') + at('inv') + at('tang') + at('intan');
		const assetMix: StackSeg[] = [
			{ kr: '현금', v: at('cash'), color: '#60a5fa' },
			{ kr: '매출채권', v: at('recv'), color: '#34d399' },
			{ kr: '재고', v: at('inv'), color: '#fbbf24' },
			{ kr: '유형자산', v: at('tang'), color: '#ec4899' },
			{ kr: '무형자산', v: at('intan'), color: '#a78bfa' },
			{ kr: '기타', v: Math.max(0, +(totAssetL - sumBuckets).toFixed(2)), color: '#475569' }
		].filter((s) => s.v > 0);
		const liabL = li(T.totalLiab) ?? 0;
		const currL = li(T.currLiab) ?? 0;
		const eqL = li(T.totalEquity) ?? 0;
		const fundMix: StackSeg[] = [
			{ kr: '유동부채', v: currL, color: '#5681c4' },
			{ kr: '비유동부채', v: Math.max(0, liabL - currL), color: '#d65b56' },
			{ kr: '자본', v: eqL, color: '#34d399' }
		].filter((s) => s.v > 0);
		const cf = fin.cf || ({} as FinanceCompany['cf']);
		const fcf = cf.op != null && cf.inv != null ? +(cf.op + cf.inv).toFixed(2) : null;
		return {
			years: yrs,
			opMargin, netMargin, roe, assetTurn, equityMult, deRatio, currRatio,
			dupont: { netMargin: li(netMargin), assetTurn: li(assetTurn), equityMult: li(equityMult), roe: li(roe) },
			assetMix, fundMix,
			cf: { op: cf.op ?? null, inv: cf.inv ?? null, fin: cf.fin ?? null, fcf }
		};
	}

	function cagr(arr: Num[]): number | null {
		const a = arr.filter((v): v is number => v != null);
		if (a.length < 2 || a[0] <= 0) return null;
		return (Math.pow(a[a.length - 1] / a[0], 1 / (a.length - 1)) - 1) * 100;
	}

	// 회사별 결과 캐시 · raw 불변이므로 재선택 시 즉시 반환(buildCompanyImpl 의 전수스캔 반복 제거).
	const companyCache = new Map<string, Company | null>();
	function buildCompany(code: string): Company | null {
		if (companyCache.has(code)) return companyCache.get(code) ?? null;
		const co = buildCompanyImpl(code);
		companyCache.set(code, co);
		return co;
	}
	function buildCompanyImpl(code: string): Company | null {
		const fin = raw.finance.companies[code] ?? emptyFinanceCompany();
		const px = raw.prices.data[code];
		const idx = byCode[code];
		const eco = ecoByCode[code];
		if (!idx && !eco) return null;
		const node = eco || ({} as EcoNode);
		const yrs = rev(years);
		const name = idx ? idx.corpName : code;
		const industry = idx ? idx.industry : 'misc';
		const last = px?.currentPrice ?? null;
		const mktcapKRW = px?.marketCap ?? null;
		// 표시 통화 · finance 엔트리 currency 태그(US=USD). 기본 KRW(KR 무회귀).
		const currency = (fin as { currency?: string }).currency ?? 'KRW';

		const net = lastNonNull(fin.is.net);
		const sales = lastNonNull(fin.is.sales);
		const eq = lastNonNull(fin.bs.totals.totalEquity);
		const opm = lastNonNull(fin.is.opMargin);
		const roe = lastNonNull(fin.ratios.roe);
		const dr = lastNonNull(fin.ratios.debtRatio);
		const per = mktcapKRW != null && net && net.v > 0 ? mktcapKRW / (net.v * 1e12) : null;
		const pbr = mktcapKRW != null && eq && eq.v > 0 ? mktcapKRW / (eq.v * 1e12) : null;
		const psr = mktcapKRW != null && sales && sales.v > 0 ? mktcapKRW / (sales.v * 1e12) : null;
		const npm = net && sales && sales.v ? (net.v / sales.v) * 100 : null;

		const income = {
			periods: yrs,
			rows: [
				{ kr: '매출액', en: 'Revenue', id: 'sales', vals: rev(fin.is.sales) },
				{ kr: '영업이익', en: 'Operating income', id: 'op', vals: rev(fin.is.op) },
				{ kr: '영업이익률', en: 'OP margin %', id: 'opMargin', pct: true, vals: rev(fin.is.opMargin) },
				{ kr: '당기순이익', en: 'Net income', id: 'net', vals: rev(fin.is.net) }
			] as StatementRow[]
		};
		const T = fin.bs.totals;
		const nonCurr = rev(T.totalAsset).map((v, i) => {
			const c = rev(T.currAsset)[i];
			return v != null && c != null ? +(v - c).toFixed(2) : null;
		});
		const balance = {
			periods: yrs,
			rows: [
				{ kr: '유동자산', en: 'Current assets', id: 'currAsset', vals: rev(T.currAsset) },
				{ kr: '비유동자산', en: 'Non-current assets', id: 'nonCurr', vals: nonCurr },
				{ kr: '자산총계', en: 'Total assets', id: 'totalAsset', vals: rev(T.totalAsset) },
				{ kr: '유동부채', en: 'Current liabilities', id: 'currLiab', vals: rev(T.currLiab) },
				{ kr: '부채총계', en: 'Total liabilities', id: 'totalLiab', vals: rev(T.totalLiab) },
				{ kr: '자본총계', en: 'Total equity', id: 'totalEquity', vals: rev(T.totalEquity) }
			] as StatementRow[]
		};
		// 현금흐름: op/inv/fin 실데이터, FCF=op+inv. opening/closing 은 null 이라 제외(정직).
		const cf = fin.cf || ({} as RawData['finance']['companies'][string]['cf']);
		const fcf = cf.op != null && cf.inv != null ? +(cf.op + cf.inv).toFixed(2) : null;
		const cashflow = {
			periods: [yrs[0]],
			rows: [
				{ kr: '영업활동현금흐름', en: 'CFO', id: 'cfo', vals: [num(cf.op)] },
				{ kr: '투자활동현금흐름', en: 'CFI', id: 'cfi', vals: [num(cf.inv)] },
				{ kr: '재무활동현금흐름', en: 'CFF', id: 'cff', vals: [num(cf.fin)] },
				{ kr: '잉여현금흐름', en: 'Free cash flow', id: 'fcf', vals: [fcf] }
			] as StatementRow[]
		};

		const crVal = (() => {
			const c = lastNonNull(T.currAsset);
			const l = lastNonNull(T.currLiab);
			return c && l && l.v ? ((c.v / l.v) * 100).toFixed(0) + '%' : '·';
		})();
		const ratios = [
			{ kr: 'ROE', en: 'Return on equity', id: 'roe', v: roe ? roe.v.toFixed(1) + '%' : '·', tone: (roe && roe.v > 8 ? 'up' : 'neutral') as Tone },
			{ kr: '영업이익률', en: 'Operating margin', id: 'opm', v: opm ? opm.v.toFixed(1) + '%' : '·', tone: (opm && opm.v > 8 ? 'up' : opm && opm.v < 0 ? 'down' : 'neutral') as Tone },
			{ kr: '순이익률', en: 'Net margin', id: 'npm', v: npm != null ? npm.toFixed(1) + '%' : '·', tone: (npm != null && npm > 5 ? 'up' : npm != null && npm < 0 ? 'down' : 'neutral') as Tone },
			{ kr: '부채비율', en: 'Debt ratio', id: 'dr', v: dr ? dr.v.toFixed(1) + '%' : '·', tone: (dr && dr.v < 100 ? 'good' : dr && dr.v > 300 ? 'warn' : 'neutral') as Tone },
			{ kr: '유동비율', en: 'Current ratio', id: 'cr', v: crVal, tone: 'good' as Tone },
			{ kr: 'PER', en: 'P/E', id: 'per', v: per != null ? per.toFixed(1) + 'x' : '·', tone: 'neutral' as Tone },
			{ kr: 'PBR', en: 'P/B', id: 'pbr', v: pbr != null ? pbr.toFixed(2) + 'x' : '·', tone: 'neutral' as Tone },
			{ kr: 'PSR', en: 'P/S', id: 'psr', v: psr != null ? psr.toFixed(2) + 'x' : '·', tone: 'neutral' as Tone }
		];

		const salesCagr = cagr(fin.is.sales);
		const opmArr = fin.is.opMargin.filter((v): v is number => v != null);
		const opmDelta = opmArr.length >= 2 ? opmArr[opmArr.length - 1] - opmArr[0] : null;
		const credit = deriveCredit(fin);
		const tn = (b: unknown): Tone => (b ? 'up' : 'warn');
		const analysis = {
			summary: {
				kr: `${name}는 5년 매출 CAGR ${salesCagr != null ? (salesCagr >= 0 ? '+' : '') + salesCagr.toFixed(1) + '%' : '·'}, 최근 영업이익률 ${opm ? opm.v.toFixed(1) + '%' : '·'}. ROE ${roe ? roe.v.toFixed(1) + '%' : '·'} · 부채비율 ${dr ? dr.v.toFixed(0) + '%' : '·'}. dartlab 파생 신용 ${credit.grade}, 건전도 ${credit.healthScore}/100.`,
				en: `${name}: 5Y revenue CAGR ${salesCagr != null ? (salesCagr >= 0 ? '+' : '') + salesCagr.toFixed(1) + '%' : '·'}, latest OP margin ${opm ? opm.v.toFixed(1) + '%' : '·'}. ROE ${roe ? roe.v.toFixed(1) + '%' : '·'} · debt ${dr ? dr.v.toFixed(0) + '%' : '·'}. Derived credit ${credit.grade}, health ${credit.healthScore}/100.`
			},
			tracks: [
				{ kr: '수익성', en: 'Profitability', verdict: { kr: `영업이익률 ${opm ? opm.v.toFixed(1) + '%' : '·'}, 5년 ${opmDelta != null ? (opmDelta >= 0 ? '+' : '') + opmDelta.toFixed(1) + 'pp' : '·'}`, en: `OP margin ${opm ? opm.v.toFixed(1) + '%' : '·'}, 5Y ${opmDelta != null ? (opmDelta >= 0 ? '+' : '') + opmDelta.toFixed(1) + 'pp' : '·'}` }, tone: tn(opm && opm.v > 5), delta: opm ? opm.v.toFixed(1) + '%' : '·' },
				{ kr: '성장성', en: 'Growth', verdict: { kr: `매출 CAGR ${salesCagr != null ? salesCagr.toFixed(1) + '%' : '·'}`, en: `Revenue CAGR ${salesCagr != null ? salesCagr.toFixed(1) + '%' : '·'}` }, tone: tn(salesCagr != null && salesCagr > 0), delta: salesCagr != null ? (salesCagr >= 0 ? '+' : '') + salesCagr.toFixed(1) + '%' : '·' },
				{ kr: '안정성', en: 'Stability', verdict: { kr: `부채비율 ${dr ? dr.v.toFixed(0) + '%' : '·'} · 유동 ${credit.basis.curr != null ? credit.basis.curr + '%' : '·'}`, en: `Debt ${dr ? dr.v.toFixed(0) + '%' : '·'} · current ${credit.basis.curr != null ? credit.basis.curr + '%' : '·'}` }, tone: tn(dr && dr.v < 150), delta: dr ? dr.v.toFixed(0) + '%' : '·' },
				{ kr: '현금흐름', en: 'Cash flow', verdict: { kr: `영업CF ${cf.op != null ? cf.op + '조' : '·'} · FCF ${fcf != null ? fcf + '조' : '·'}`, en: `CFO ${cf.op != null ? cf.op + 'T' : '·'} · FCF ${fcf != null ? fcf + 'T' : '·'}` }, tone: tn(fcf != null && fcf > 0), delta: fcf != null ? (fcf >= 0 ? 'FCF+' : 'FCF-') : '·' },
				{ kr: '가치평가', en: 'Valuation', verdict: { kr: `PER ${per != null ? per.toFixed(1) + 'x' : '·'} · PBR ${pbr != null ? pbr.toFixed(2) + 'x' : '·'}`, en: `PER ${per != null ? per.toFixed(1) + 'x' : '·'} · PBR ${pbr != null ? pbr.toFixed(2) + 'x' : '·'}` }, tone: 'good' as Tone, delta: per != null ? per.toFixed(1) + 'x' : '·' }
			]
		};

		const blog = raw.meta?.blog ? raw.meta.blog[code] : undefined;
		const marketLabel = MARKET_LABEL[node.market || ''] || 'KRX';
		// ── 종합(composite) 축의 동종업종 백분위 · 등급을 매긴 *근거* ──
		// 핵심: 원시지표(영업이익률 등) 백분위가 아니라 *축 자체*를 백분위한다. 같은 축에서 동종사들의 등급을
		// gradeScore(0~1)로 환산해 회사 순위를 낸다. "이 축에서 업종 상위 N%" = 그 등급의 근거.
		// (원시지표 백분위는 우측 패널 = 다른 세션 담당 · 여긴 축 종합만.)
		const peers = industryNodes(industry);
		const axisStat = (a: CompositeAxis): { score: Num; topPct: number | null; n: number; dist: { step: string; share: number; tone: Tone }[]; sameShare: number | null } => {
			const myVal = node[a.field] as string | undefined;
			if (a.kind === 'class') {
				// 분류(현금흐름) · 순서 없음 → 순위·사다리 금지. 동종사 내 *같은 유형 비중*(빈도)만(순위 아님).
				const valued = peers.filter((pn) => !!(pn[a.field] as string | undefined));
				const same = myVal ? valued.filter((pn) => (pn[a.field] as string) === myVal).length : 0;
				const vn = valued.length;
				return { score: null, topPct: null, n: vn, dist: [], sameShare: vn && myVal ? Math.round((same / vn) * 100) : null };
			}
			const scale = GRADE_SCALE[a.key] || [];
			const myScore = gradeScore(a.key, myVal);
			const counts: Record<string, number> = {};
			const scores: number[] = [];
			for (const pn of peers) {
				const v = pn[a.field] as string | undefined;
				const s = gradeScore(a.key, v);
				if (s != null) scores.push(s);
				if (v && scale.includes(v)) counts[v] = (counts[v] || 0) + 1;
			}
			const scored = scores.length;
			const dist = scale.map((step) => ({ step, share: scored ? Math.round(((counts[step] || 0) / scored) * 100) : 0, tone: gradeTone(a.key, step) }));
			// 상위 N% = midrank 백분위(더 우수한 동종사 + 동급의 절반). 동률(같은 등급 다수)을 대칭 처리해
			// 다수가 몰린 등급에서 "바닥처럼 보이는" 왜곡을 막는다(순서형 ordinal 표준). 표본<5 → null(폴백).
			const better = scores.filter((x) => x > (myScore as number)).length;
			const tie = scores.filter((x) => x === myScore).length;
			const topPct = myScore == null || scored < 5 ? null : Math.max(1, Math.min(100, Math.round(((better + tie / 2) / scored) * 100)));
			return { score: myScore, topPct, n: scored, dist, sameShare: null };
		};
		// 종합 축 칩 · COMPOSITE_AXES SSOT 에서 파생(중간패널·다이얼로그·레이더 단일 출처). 결손 축은 누락(0대체 금지).
		// cf(kind='class')는 GRADE_SCALE 에 없어 gradeTone='neutral' → 중립칩(거짓 순서 색 방지). 각 칩에 축 백분위(topPct)·분포(dist) 동봉.
		const grades = COMPOSITE_AXES.map((a) => ({ a, v: (node[a.field] as string | undefined) || '' }))
			.filter((x) => !!x.v)
			.map(({ a, v }) => {
				const st = axisStat(a);
				return { key: a.key, kr: a.kr, en: a.en, v, kind: a.kind, tone: gradeTone(a.key, v), color: GROUP_COLOR[a.group] || '#a3a8b3', topPct: st.topPct, peerN: st.n, dist: st.dist, sameShare: st.sameShare };
			});
		// 레이더 = 순서형 종합 축만(cf 제외). 스포크 = *축 백분위*(피어 상대, 상위일수록 큼). 피어 부족 시 등급점수 폴백.
		const radar = COMPOSITE_AXES.filter((a) => a.kind === 'ordered').map((a) => {
			const st = axisStat(a);
			return { kr: a.kr, en: a.en, short: a.short, s: st.topPct != null ? (100 - st.topPct) / 100 : st.score };
		});

		// YoY 변화 · ecosystem delta 가 99% null 이므로 finance 5Y 배열에서 직접 계산 (실데이터).
		const yoyDelta = (arr: Num[]): Num => {
			const a = arr.filter((v): v is number => v != null);
			return a.length >= 2 ? +(a[a.length - 1] - a[a.length - 2]).toFixed(1) : null;
		};
		const salesYoy = (() => {
			const a = fin.is.sales.filter((v): v is number => v != null);
			return a.length >= 2 && a[a.length - 2] !== 0 ? +(((a[a.length - 1] - a[a.length - 2]) / Math.abs(a[a.length - 2])) * 100).toFixed(1) : null;
		})();
		const changes = [
			{ kr: 'ROE', en: 'ROE', v: yoyDelta(fin.ratios.roe), unit: '%p' },
			{ kr: '영업이익률', en: 'OP margin', v: yoyDelta(fin.is.opMargin), unit: '%p' },
			{ kr: '부채비율', en: 'Debt ratio', v: yoyDelta(fin.ratios.debtRatio), unit: '%p', invert: true },
			{ kr: '매출 YoY', en: 'Revenue YoY', v: salesYoy, unit: '%' }
		];

		const co: Company = {
			code,
			currency,
			marketLabel,
			name: { kr: name, en: name },
			sector: { kr: node.industryName || SECTOR_KR[industry] || industry, en: SECTOR_EN[industry] || industry },
			industry,
			stage: node.stageName || '',
			role: node.role || '',
			eco: node,
			grades,
			radar,
			changes,
			price: {
				last,
				mktcap: fmtMoney(mktcapKRW, currency),
				mktcapRaw: mktcapKRW,
				ret1m: px?.return1m ?? null, ret3m: px?.return3m ?? null, ret1y: px?.return1y ?? null,
				vol1y: px?.volatility1y ?? null, hi52: px?.week52High ?? null, lo52: px?.week52Low ?? null, vol: px?.volumeAvg30d ?? null,
				asOf: px ? fmtDate(px.priceUpdated) : '·'
			},
			fundamentals: { per, pbr, psr, npm, roe: roe ? roe.v : null, opm: opm ? opm.v : null, dr: dr ? dr.v : null },
			financials: computeFinancials(fin),
			trendAnnual: trendFromFinance(fin),
			trendQuarter: trendFromQuarters(code),
			income, balance, cashflow, ratios, credit, analysis,
			macroExposure: fin.macroExposure ?? null,
			peers: derivePeers(code, industry),
			story: blog ? { title: blog.title, date: blog.date, readTime: blog.readTime, slug: normalizeBlogSlug(blog.slug) } : null,
			percentile: null, valuation: null, risks: [], riskCatalog: [], tailwind: null,
			verdict: {} as Verdict
		};
		co.percentile = industryPercentile(code);
		co.valuation = valuationOf(code);
		co.risks = riskFlagsOf(code);
		co.riskCatalog = riskCatalogOf(code);
		co.tailwind = tailwindOf(industry);
		co.verdict = verdictOf(co);
		return co;
	}

	function search(q: string): string | null {
		q = (q || '').trim();
		if (!q) return null;
		if (byCode[q]) return q;
		const up = q.toUpperCase();
		const hit = raw.index.find(
			(r) => r.stockCode === q || r.corpName === q || r.corpName.includes(q) || r.corpName.toUpperCase() === up
		);
		if (hit) return hit.stockCode;
		return null;
	}

	// 출자 다이얼로그 · 피출자사명을 상장 종목으로 해소(보유지분 시가 환산용). 정규화 exact 매칭 +
	// 시총 존재 게이트. 재무 seed 결손은 net=null 로 남겨도 상장사 링크·시총은 보존한다.
	function lookupListed(name: string): { code: string; marketCap: number; net: number | null } | null {
		const k = normalizeCorpName(name);
		if (!k) return null;
		const code = normByName[k];
		if (!code) return null;
		const px = raw.prices.data[code];
		const fin = raw.finance.companies[code];
		if (!px || !px.marketCap) return null;
		const netLatest = fin ? lastNonNull(fin.is.net) : null; // 조 단위 → 원 환산
		return { code, marketCap: px.marketCap, net: netLatest ? netLatest.v * 1e12 : null };
	}

	// 자동완성: 코드/이름 부분일치 (viewer식 검색 드롭다운용)
	function suggest(q: string, n = 8): { code: string; name: string; industry: string }[] {
		q = (q || '').trim();
		if (!q) return [];
		const up = q.toUpperCase();
		const out: { code: string; name: string; industry: string }[] = [];
		const seen = new Set<string>();
		const push = (r: RawData['index'][number]) => {
			if (seen.has(r.stockCode)) return;
			seen.add(r.stockCode);
			out.push({ code: r.stockCode, name: r.corpName, industry: SECTOR_KR[r.industry] || r.industry });
		};
		// 1순위 정확/접두, 2순위 포함
		for (const r of raw.index) {
			if (out.length >= n) break;
			if (r.stockCode === q || r.corpName === q || r.corpName.startsWith(q) || r.corpName.toUpperCase().startsWith(up) || r.stockCode.startsWith(q)) push(r);
		}
		for (const r of raw.index) {
			if (out.length >= n) break;
			if (r.corpName.includes(q) || r.corpName.toUpperCase().includes(up)) push(r);
		}
		return out;
	}

	function featured(n = 14): string[] {
		const out: string[] = [];
		for (const r of raw.index) {
			if (hasTerminalPrice(r.stockCode)) out.push(r.stockCode);
			if (out.length >= n) break;
		}
		return out;
	}

	function sectorPerf() {
		const agg: Record<string, number[]> = {};
		for (const r of raw.index) {
			const p = raw.prices.data[r.stockCode];
			if (!p || p.return1m == null) continue;
			(agg[r.industry] = agg[r.industry] || []).push(p.return1m);
		}
		return Object.entries(agg)
			.map(([k, arr]) => ({ id: k, kr: SECTOR_KR[k] || k, en: SECTOR_EN[k] || k, chg: arr.reduce((a, b) => a + b, 0) / arr.length, n: arr.length }))
			.filter((s) => s.n >= 3)
			.sort((a, b) => b.chg - a.chg);
	}

	// 매크로 국면 → 섹터 순풍/역풍(blended) · INDUSTRY_TAILWIND_MAP·SECTOR_KR SSOT 재사용, blended 내림차순.
	function sectorTailwinds() {
		const tw = raw.macro?.sectorTailwind;
		if (!tw) return [];
		const seen = new Set<string>();
		const out: { id: string; kr: string; en: string; blended: number; tailwindKey: string }[] = [];
		for (const [id, key] of Object.entries(INDUSTRY_TAILWIND_MAP)) {
			const e = tw[key];
			if (!e || e.blended == null || seen.has(key)) continue;
			seen.add(key);
			out.push({ id, kr: SECTOR_KR[id] || id, en: SECTOR_EN[id] || id, blended: e.blended, tailwindKey: key });
		}
		return out.sort((a, b) => b.blended - a.blended);
	}

	// 거시 산업 sweep · scan grade 악성 버킷(04 §3 Rule 5: 버킷% 만, ordinal 평균 금지) · cf distress.
	const _RISK_BUCKET = {
		prof: new Set(['저수익', '적자']),
		loss: new Set(['적자']),
		growth: new Set(['역성장', '급감']),
		debt: new Set(['주의', '고위험']),
		liq: new Set(['주의', '위험'])
	};
	const _CF_DISTRESS = new Set(['현금위기형', '쇠퇴형', '외부의존형']);
	const _DISTRESS_DEBT = new Set(['주의', '고위험']); // 부실 멤버 선별 · 부채등급 위험권(절대 부채액 아님)

	function _band(arr: number[]): IndustryDist | null {
		const s = arr.filter((v) => v != null && !Number.isNaN(v)).sort((a, b) => a - b);
		if (s.length < 5) return null; // 표본부족 → null(0대체 금지)
		const q = (f: number): number => {
			const i = f * (s.length - 1);
			const lo = Math.floor(i);
			const hi = Math.ceil(i);
			return s[lo] + (s[hi] - s[lo]) * (i - lo);
		};
		return { p10: q(0.1), p25: q(0.25), median: q(0.5), p75: q(0.75), p90: q(0.9), n: s.length };
	}

	function industryMacro(id: string): IndustryMacro | null {
		const nodes = industryNodes(id);
		if (!nodes.length) return null;

		// (1) 재무 분포 · industryStats baked(n<10 → null, 04 §3 Rule 5)
		const sd = (raw.industryStats as Record<string, IndustryStat> | null)?.[id]?.distribution || {};
		const pick = (m: string): IndustryDist | null => {
			const d = sd[m];
			return d && d.median != null && d.p10 != null && d.p90 != null && (d.n ?? 0) >= 10
				? { p10: d.p10, p25: d.p25 ?? d.p10, median: d.median, p75: d.p75 ?? d.p90, p90: d.p90, n: d.n as number }
				: null;
		};
		const dist: Record<string, IndustryDist | null> = {};
		for (const m of ['opMargin', 'netMargin', 'roe', 'debtRatio', 'currentRatio', 'revCagr', 'netIncomeCagr', 'ccc', 'assetTurnover', 'icr']) dist[m] = pick(m);
		const om = dist.opMargin;
		const marginIqr = om ? +(om.p75 - om.p25).toFixed(2) : null;

		// (2) gov 시총/자본 → 산업 PBR 분포 (KRX 아님 · raw.prices = gov/prices/date/*.parquet)
		const pbrArr: number[] = [];
		for (const node of nodes) {
			const f = raw.finance.companies[node.id];
			const p = raw.prices.data[node.id];
			if (!f || !p || !p.marketCap) continue;
			const ee = lastNonNull(f.bs.totals.totalEquity);
			if (ee && ee.v > 0) {
				const x = p.marketCap / (ee.v * 1e12);
				if (x > 0 && x < 60) pbrArr.push(x); // 음수자본 제외 · 극단 클립
			}
		}
		const pbr = _band(pbrArr);

		// (3) scan grade 악성 버킷 % (ecosystem baked) · 버킷% 만(ordinal 평균 금지)
		const pct = (field: keyof EcoNode, bad: Set<string>): number => {
			const has = nodes.filter((n) => n[field]);
			if (!has.length) return 0;
			return +((has.filter((n) => bad.has(n[field] as string)).length / has.length) * 100).toFixed(1);
		};
		const bucket = {
			profRisk: pct('profGrade', _RISK_BUCKET.prof),
			lossRisk: pct('profGrade', _RISK_BUCKET.loss),
			growthRisk: pct('growthGrade', _RISK_BUCKET.growth),
			debtRisk: pct('debtGrade', _RISK_BUCKET.debt),
			liqRisk: pct('liqGrade', _RISK_BUCKET.liq),
			cfDistress: pct('cfPattern', _CF_DISTRESS)
		};
		// YoY 방향(개선/악화) · baked 델타 산업 median. 다년 CAGR(평균)과 직교: 최근 변화 = 구조 vs 순환 단서.
		const nodeMed = (field: keyof EcoNode): number | null => {
			const vals = nodes.map((n) => n[field]).filter((v): v is number => typeof v === 'number');
			if (vals.length < 5) return null;
			const s = [...vals].sort((a, b) => a - b);
			return +s[Math.floor(s.length / 2)].toFixed(2);
		};
		const direction = {
			opMarginDelta: nodeMed('opMarginDelta'),
			roeDelta: nodeMed('roeDelta'),
			revenueYoyPct: nodeMed('revenueYoyPct')
		};

		// cfPattern 최빈 = 산업 현금흐름 시그니처
		const cfCount: Record<string, number> = {};
		let cfTot = 0;
		for (const n of nodes) if (n.cfPattern) { cfCount[n.cfPattern] = (cfCount[n.cfPattern] || 0) + 1; cfTot++; }
		const cfTop = Object.entries(cfCount).sort((a, b) => b[1] - a[1])[0];
		const cfSignature = cfTop && cfTot ? { pattern: cfTop[0], share: Math.round((cfTop[1] / cfTot) * 100) } : null;

		// (4) 멤버 지형 · 지표 top5 → 종목 드릴인. '부실 주의' = distress 복합(고부채≠부실: CF·수익성·부채등급 합성).
		const distressed: IndustryMacroMember[] = nodes
			.filter((n) => (n.debtGrade && _DISTRESS_DEBT.has(n.debtGrade)) || n.profGrade === '적자' || (n.cfPattern && _CF_DISTRESS.has(n.cfPattern)))
			.sort((a, b) => (b.debtRatio ?? 0) - (a.debtRatio ?? 0))
			.slice(0, 5)
			.map((n) => ({ code: n.id, name: byCode[n.id]?.corpName || n.id, value: n.debtRatio ?? 0 }));
		const topBy = (field: keyof EcoNode, desc: boolean): IndustryMacroMember[] =>
			nodes
				.filter((n) => n[field] != null)
				.sort((a, b) => (desc ? (b[field] as number) - (a[field] as number) : (a[field] as number) - (b[field] as number)))
				.slice(0, 5)
				.map((n) => ({ code: n.id, name: byCode[n.id]?.corpName || n.id, value: n[field] as number }));

		const twKey = INDUSTRY_TAILWIND_MAP[id];
		const tw = twKey && raw.macro?.sectorTailwind ? raw.macro.sectorTailwind[twKey] : null;
		return {
			id,
			kr: SECTOR_KR[id] || id,
			en: SECTOR_EN[id] || id,
			count: nodes.length,
			dist,
			marginIqr,
			pbr,
			bucket,
			cfSignature,
			direction,
			tailwind: tw && tw.blended != null ? tw.blended : null,
			macroPhase: raw.macro?.kr?.phaseLabel || raw.macro?.kr?.phase || '',
			top: { roe: topBy('roe', true), growth: topBy('revCagr', true), risk: distressed }
		};
	}

	// 산업 내 회사 점들 · 회사 산포도(드릴). 가로=수익성(opMargin) · 세로=성장(revCagr) · 크기=gov 시총 · 색=수익성등급.
	// 위치 = 회사 실측값(사실, 판정 아님). margin·growth 둘 다 있는 회사만(양축 plot). cap 없으면 0(최소 크기).
	function industryMembers(id: string): IndustryMember[] {
		const out: IndustryMember[] = [];
		for (const n of industryNodes(id)) {
			if (typeof n.opMargin !== 'number' || typeof n.revCagr !== 'number') continue;
			out.push({
				code: n.id,
				name: byCode[n.id]?.corpName || n.id,
				margin: +n.opMargin.toFixed(2),
				growth: +n.revCagr.toFixed(2),
				cap: raw.prices.data[n.id]?.marketCap ?? 0,
				grade: n.profGrade || '',
				debtGrade: n.debtGrade || ''
			});
		}
		return out;
	}

	// 산업 연도별 이동 · finance 회사별 연도배열을 산업별 median 집계 → (수익성 × 전년比 성장) 궤적.
	// x=opMargin median(해당 연도) · y=전년比 매출성장 median(YoY, sales[y]/sales[y-1]-1). 끝점=최신연도.
	// 새 fetch 0(이미 로드된 finance+eco). 생존편향: 오늘 상장 멤버를 과거로 집계(상폐·비상장 제외).
	function industryTrails(): IndustryTrail[] {
		const fy = raw.finance.years || [];
		const med = (a: number[]): number => { const s = [...a].sort((p, q) => p - q); const k = Math.floor(s.length / 2); return s.length % 2 ? s[k] : (s[k - 1] + s[k]) / 2; };
		const out: IndustryTrail[] = [];
		for (const id of [...new Set((raw.eco?.nodes || []).map((n) => n.industry))]) {
			const nodes = industryNodes(id);
			if (nodes.length < 10) continue;
			const pts: { year: string; x: number; y: number }[] = [];
			for (let yi = 1; yi < fy.length; yi++) { // yi=1 부터 · YoY 는 직전연도 필요
				const margins: number[] = [], grows: number[] = [];
				for (const n of nodes) {
					const f = raw.finance.companies[n.id];
					if (!f) continue;
					const mg = f.is?.opMargin?.[yi];
					if (typeof mg === 'number') margins.push(mg);
					const s0 = f.is?.sales?.[yi - 1], s1 = f.is?.sales?.[yi];
					if (typeof s0 === 'number' && typeof s1 === 'number' && s0 > 0) grows.push((s1 / s0 - 1) * 100);
				}
				if (margins.length < 5 || grows.length < 5) continue; // 표본부족 연도 skip(04 §3 Rule 5)
				pts.push({ year: fy[yi], x: +med(margins).toFixed(2), y: +med(grows).toFixed(2) });
			}
			if (pts.length < 2) continue; // 궤적은 2점 이상
			out.push({ id, count: nodes.length, pts });
		}
		return out;
	}

	return {
		raw, years, source: 'HuggingFace · dartlab-data',
		buildCompany, search, suggest, featured, sectorPerf, sectorTailwinds, lookupListed, percentileIn, industryMacro, industryMembers, industryTrails,
		priceOf: (code: string) => raw.prices.data[code],
		nameOf: (code: string) => (byCode[code] ? byCode[code].corpName : code)
	};
}

function fmtDate(yyyymmdd: string): string {
	const s = String(yyyymmdd || '');
	if (s.length === 8) return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}`;
	return s;
}
