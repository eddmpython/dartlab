import type {
	MacroTransmissionDriver as ContractMacroTransmissionDriver,
	MacroTransmissionEdge as ContractMacroTransmissionEdge,
	MacroTransmissionResult as ContractMacroTransmissionResult
} from '@dartlab/ui-contracts';

// DartLab Terminal · raw data file shapes + built Company shape.
// 스키마는 landing/static 의 실데이터에서 검증 (finance/macro/meta/prices/search-index/ecosystem/quarters/industryStats).
// 가짜 필드 없음 · cf.opening/closing 는 실데이터에서 null 이라 표면에 노출하지 않는다.

export type Num = number | null;
// ui/shared/chart 의 ChartSpec (loose · 차트 컴포넌트는 @ts-nocheck spec 객체 수신).
export type ChartSpec = Record<string, unknown>;
export type Lang = 'kr' | 'en';
export type Tone = 'up' | 'down' | 'good' | 'warn' | 'neutral';
export type Prov = 'real' | 'derived' | 'wire';

export type MacroExposureQualityStatus = 'quantCandidate' | 'qualitativeOnly' | 'blocked';
export interface MacroExposureQualityPayload {
	method?: string | null;
	modelVersion?: string | null;
	targetMetric?: string | null;
	minObs?: number | null;
	status: MacroExposureQualityStatus;
	reason: string;
	blockedReason: string;
	missingEvidence: string[];
	sourceRef: string;
	nObs: number | null;
	rSquared: number | null;
	window: string | null;
	frequency: 'monthly' | 'quarterly' | 'annual' | null;
	lagMonths: number | null;
	coverage: 'company' | 'sectorOnly' | 'missing';
}
export interface MacroExposureIndicatorPayload {
	method?: string | null;
	modelVersion?: string | null;
	targetMetric?: string | null;
	minObs?: number | null;
	label?: string;
	seriesId: string;
	axis?: string;
	rSquared: number | null;
	nObs: number | null;
	window: string | null;
	frequency?: 'monthly' | 'quarterly' | 'annual' | null;
	lagMonths?: number | null;
	coverage?: 'company' | 'sectorOnly' | 'missing';
	sourceRef: string;
	sourceRefs?: string[];
	latestChange?: number | null;
	impact?: string;
}
export interface MacroExposurePayload {
	stockCode?: string;
	selected?: MacroExposureIndicatorPayload[];
	selectedSource?: string;
	optimalBestR2?: number | null;
	genericBestR2?: number | null;
	exposureQuality: MacroExposureQualityPayload;
	netDirection?: 'positive' | 'negative' | 'neutral' | string;
	netDirectionLabel?: string;
}

// ───────────────────────── raw files ─────────────────────────
export interface FinanceCompany {
	is: { sales: Num[]; op: Num[]; net: Num[]; opMargin: Num[] };
	bs: {
		assets?: Record<string, Num[]>;
		liab?: Record<string, Num[]>;
		equity?: Record<string, Num[]>;
		totals: {
			totalAsset: Num[];
			totalLiab: Num[];
			totalEquity: Num[];
			currAsset: Num[];
			currLiab: Num[];
		};
	};
	cf: { op: Num; inv: Num; fin: Num; opening: Num; closing: Num; fx: Num };
	ratios: { roe: Num[]; debtRatio: Num[] };
	macroExposure?: MacroExposurePayload | null;
}
export interface FinanceFile {
	version?: string;
	years: string[];
	companies: Record<string, FinanceCompany>;
}

export interface QuartersCompany {
	is: { sales: Num[]; op: Num[]; net: Num[] };
	cf?: { ocf: Num[]; icf: Num[] };
	bs?: { totals?: Record<string, Num[]> };
}
export interface QuartersFile {
	periods: string[];
	companies: Record<string, QuartersCompany>;
}

export interface MacroQuadrant {
	quadrant: string;
	quadrantLabel: string;
	growth: string;
	inflation?: string;
	growthSignal?: number;
	inflationSignal?: number;
	assetImplication: Record<string, string>;
	confidence?: string;
	description: string;
}
export interface MacroTransition {
	from?: string;
	to?: string;
	progress?: number;
	triggered?: string[];
	pending?: string[];
}
export interface MacroSide {
	phase: string;
	phaseLabel: string;
	confidence?: string;
	signals?: string | string[] | Record<string, unknown> | null;
	transition?: MacroTransition | null;
	quadrant?: MacroQuadrant; // 빌더 입력 부족(cycle 결측) 시 부재 가능 · 소비처 옵셔널 접근 강제
}
export type MacroTransmissionDriver = ContractMacroTransmissionDriver;
export type MacroTransmissionEdge = ContractMacroTransmissionEdge;
export type MacroTransmissionPayload = ContractMacroTransmissionResult;
export interface TailwindEntry {
	kr: number;
	us: number;
	blended: number;
}
// ── regime 키 (초강화·prebuild 가 deploy 시 HF macro/regime/{kr,us}.json 에서 조립) ──
// sync(buildMacroRegime.py)가 동결한 forecast 4모델 + 수익률곡선 + GaR 분포 + Hamilton band.
// 모델 sub-key 의 필드는 게이트 통과 여부에 따라 가변(통과 시 값·탈락 시 status). view-model 이
// 옵셔널 접근으로 읽으므로 느슨하게 타이핑 · 모델 dict 는 Record<string, unknown> 로 두되,
// view-model 이 좁히는 키(zone/signal/contractionProb/status 등)는 인덱스 시그니처로 접근.
export interface MacroRegimeModel {
	status?: string;
	asOf?: string;
	seriesId?: string;
	seriesSource?: string;
	staleAfterDays?: number;
	horizon?: string;
	timeKind?: string;
	[key: string]: unknown;
}
export interface MacroRegimeMissing {
	id: string;
	status: string;
	reason?: string;
}
export interface MacroRegimePayload {
	market?: string;
	computedAt?: string;
	forecast?: {
		models?: Record<string, MacroRegimeModel>;
		missing?: MacroRegimeMissing[];
	};
	rates?: {
		spread10y3m?: number;
		sign?: string;
		curveShape?: string;
		curveShapeLabel?: string;
		curveSource?: string;
		asOf?: string;
		seriesId?: string;
		staleAfterDays?: number;
		missing?: MacroRegimeMissing[];
	};
	gar?: {
		gar5?: number;
		gar25?: number;
		median?: number;
		gar75?: number;
		gar95?: number;
		skewness?: number;
		tailRisk?: string;
		tailRiskLabel?: string;
		currentFCI?: number;
		observations?: number;
		horizon?: number;
		timeKind?: string;
		seriesNote?: string;
		asOf?: string;
		staleAfterDays?: number;
		revisionLabel?: string;
		status?: string;
	};
	regimeBand?: {
		band?: number[];
		converged?: boolean;
		separation?: number;
		timeKind?: string;
		horizon?: string;
		asOf?: string;
		staleAfterDays?: number;
		status?: string;
	};
}
export interface MacroFile {
	version?: string;
	asOf?: string;
	kr: MacroSide;
	us: MacroSide;
	sectorTailwind: Record<string, TailwindEntry>;
	transmission?: MacroTransmissionPayload | null;
	// 초강화 regime 키 · 옵셔널(현 라이브 macro.json 미보유·prebuild deploy 시 주입).
	regime?: { kr: MacroRegimePayload; us: MacroRegimePayload };
}

export interface BlogEntry {
	slug: string;
	title: string;
	date: string;
	readTime?: number | string;
	excerpt?: string;
}
export interface MetaFile {
	version?: string;
	blog?: Record<string, BlogEntry>;
}

export interface PriceRow {
	currentPrice: number;
	marketCap: number;
	return1m: Num;
	return3m: Num;
	return1y: Num;
	volatility1y: Num;
	week52High: Num;
	week52Low: Num;
	volumeAvg30d: Num;
	foreignPct: Num;
	beta: Num;
	priceUpdated: string;
}
export interface PricesFile {
	count?: number;
	data: Record<string, PriceRow>;
}

export interface IndexRow {
	stockCode: string;
	corpName: string;
	industry: string;
	stage?: string;
	revenue: Num;
}

export interface EcoNode {
	id: string;
	label?: string;
	industry: string;
	industryName?: string;
	market?: string;
	stageName?: string;
	role?: string;
	revenue?: Num;
	/** 상장사 내 매출비중(KSIC 산업 노드 상장 구성사 매출 합 분모). 시장점유율 아님(비상장·수입 제외). */
	marketShare?: Num;
	roe?: Num;
	opMargin?: Num;
	netMargin?: Num;
	roa?: Num;
	debtRatio?: Num;
	icr?: Num;
	currentRatio?: Num;
	assetTurnover?: Num;
	ccc?: Num;
	accrualRatio?: Num;
	govScore?: Num;
	revCagr?: Num;
	netIncomeCagr?: Num;
	industryRank?: Num;
	industryPeerCount?: Num;
	holderPct?: Num;
	holderChange?: Num;
	empCount?: Num;
	profGrade?: string;
	growthGrade?: string;
	debtGrade?: string;
	govGrade?: string;
	qualGrade?: string;
	liqGrade?: string;
	effGrade?: string;
	auditRisk?: string;
	stability?: string;
	capClass?: string;
	cfPattern?: string;
	roeDelta?: Num;
	opMarginDelta?: Num;
	debtRatioDelta?: Num;
	revenueYoyPct?: Num;
	deltaYear?: string | null;
}
export interface EcosystemFile {
	version?: string;
	nodes: EcoNode[];
	industries?: unknown[];
	industryFlows?: unknown[];
}

export interface IndustryDistribution {
	p10?: number;
	p25?: number;
	median?: number;
	p75?: number;
	p90?: number;
	mean?: number;
	n?: number;
}
export interface IndustryStat {
	id?: string;
	name?: string;
	distribution?: Record<string, IndustryDistribution>;
}
export type IndustryStatsFile = Record<string, IndustryStat> | { industries?: IndustryStat[] };

export interface RawData {
	finance: FinanceFile;
	macro: MacroFile | null;
	meta: MetaFile | null;
	prices: PricesFile;
	index: IndexRow[];
	eco: EcosystemFile | null;
	quarters: QuartersFile | null;
	// 업종 분포 통계(p10~p90 밴드) · map 이 쓰던 자산. public 셸은 로드, local 단일사 브리지는 null(정직). 필수=공동배선 강제.
	industryStats: IndustryStatsFile | null;
}

// ───────────────────────── built company ─────────────────────────
export interface Bilingual {
	kr: string;
	en: string;
}
export interface StatementRow {
	kr: string;
	en: string;
	id: string;
	pct?: boolean;
	vals: Num[];
}
export interface Statement {
	periods: string[];
	rows: StatementRow[];
}
export interface RatioRow {
	kr: string;
	en: string;
	id: string;
	v: string;
	tone: Tone;
}
export interface GradeChip {
	key: string;
	kr: string;
	en: string;
	v: string;
	tone: Tone;
	color: string;
	kind?: 'ordered' | 'class'; // 'class'(현금흐름)=순서 없음 → 다이얼로그 분류 변형(사다리·색·곡선 없음).
	// 종합 축의 동종업종 백분위 · 등급 근거(다이얼로그). 원시지표 백분위 아님(그건 우측 패널·다른 세션).
	topPct?: number | null; // 상위 N% = 동급 이상 동종사 비율(순서형만). 표본<5 → null.
	peerN?: number; // 동종사 표본 수(순서형=등급 보유사, 분류=값 보유사).
	dist?: { step: string; share: number; tone: Tone }[]; // 등급레벨별 동종사 비중 % + 톤(좋음→나쁨 색). 순서형 분포 막대.
	sameShare?: number | null; // 분류(cf) 전용 · 동종사 내 같은 유형 비중 %(순위 아님).
}
export interface RadarAxis {
	kr: string;
	en: string;
	short?: string; // 레이더 스포크 짧은 라벨(겹침 완화)
	s: Num;
}
export interface ChangeRow {
	kr: string;
	en: string;
	v: Num;
	unit: string;
	invert?: boolean;
}
export interface CreditTrack {
	kr: string;
	en: string;
	score: number;
}
export interface Credit {
	grade: string;
	healthScore: number;
	pd: string;
	tone: Tone;
	tracks: CreditTrack[];
	basis: { debtRatio: Num; curr: Num; opm: Num };
}
export interface RiskFlag {
	lv: 'red' | 'yellow' | 'green';
	kr: string;
	en: string;
	d: string;
}
// 위험 경고등 카탈로그 1행 · 다이얼로그(점검 차원 전체 + 이 회사 현상태)용. 글랜스 RiskFlag 와 별개 표면.
// status: red/yellow 점등 · clear 임계미달(통과) · na 판정불가(데이터 부재). 규칙 SSOT = lib/riskRules.ts.
export interface RiskCatalogItem {
	id: string;
	kr: string; // 차원명
	en: string;
	axis: string | null; // GradeExplainDialog 교차링크 키(없으면 null)
	whatKr: string;
	whatEn: string;
	thresholdKr: string; // 켜지는 조건
	thresholdEn: string;
	source: string; // dataSource 필드
	status: 'red' | 'yellow' | 'clear' | 'na';
	d: string; // 현재 실측값/detail
}
// 히스토그램 · 동종사 전체 값 배열의 실도수(막대 높이=몰린 정도). robust 범위(p2~p98)로 outlier 클리핑.
// 5분위 보간 곡선(band)보다 정직: 실제 봉우리·gap·왜도를 그대로 보인다.
export interface Hist {
	bins: number[]; // 막대 높이 0~1(최댓값 정규화). 길이 = 빈 개수.
	companyFrac: number | null; // [lo,hi] 내 회사 위치 0~1(클램프). null = 회사값 없음.
	companyOver: -1 | 0 | 1; // -1 범위 미만 / 0 범위 내 / 1 범위 초과(이상치 표식).
	medianFrac: number; // 중앙값 위치 0~1.
	lo: number;
	hi: number; // robust 범위(p2~p98).
	n: number; // 표본 수.
}
export interface PercentileMetric {
	kr: string;
	en: string;
	v: Num;
	p: number;
	unit: string;
	axis: string; // 등급축 key(prof/growth/stab/liq/qual/eff) · 등급기준 섹션·중간패널 그루핑용.
	lowerBetter?: boolean; // 낮을수록 우수(부채비율·CCC·발생액비율) · 방향 색띠(좋은 쪽) 좌우 결정용.
	// 업종 분포 밴드(industryStats) · public 만 실데이터, local(단일사 seed)·분포 부재 = null(다이얼로그 생략).
	// p10~p90 5분위점 = 분포곡선(skew 반영, 정규가정 아님)·회사 위치 마커 렌더용.
	band: { p10: number; p25: number; median: number; p75: number; p90: number } | null;
	hist?: Hist | null; // 실도수 히스토그램(다이얼로그 1차 시각). null = 표본<12 또는 미산출.
}
// ── 유니버스 교차 백분위 (PercentileCrossDialog) ──
// co.percentile(업종 고정, Company['percentile'])과 별개. percentileIn(code, universe) 가 반환.
// 소속지수('index')는 구성종목 멤버십 데이터 부재로 BLOCKED · union 미포함(00 ④ · 02 KILL#5).
export type Universe = 'industry' | 'market' | 'all';
export interface CategoricalShare {
	key: string;
	kr: string;
	en: string;
	v: string; // 회사 등급(범주형) · 0~100 백분위로 칠하지 않음(02 KILL#3).
	tone: Tone;
	sameShare: number | null; // 이 유니버스 내 같은 등급 비중 %(순위 아님).
	peerN: number; // 등급 보유 동종사 수.
	dist: { step: string; share: number; tone: Tone }[]; // 등급레벨별 동종사 비중(어느 등급에 많이 몰렸나). cf(class)는 빈 배열.
}
export interface PriceStat {
	v: number | null;
	// 분포 내 위치(낮을수록 작은 p) · lowerBetter 미적용. 가격 우열 모호(저PER=저평가 vs 우려)라 톤·우수 프레이밍 금지(02 KILL#2).
	p: number | null;
	band: { p10: number; p25: number; median: number; p75: number; p90: number } | null;
	hist?: Hist | null; // 가격 분포 히스토그램(중립 마커).
	n: number;
}
export interface UniversePercentile {
	universe: Universe;
	label: string; // 유니버스 라벨(업종명 / KOSPI·KOSDAQ / 전체상장사).
	n: number; // 모집단 표본 수(n<10 = 띠·곡선 숨김, 02 정직 가드).
	metrics: PercentileMetric[]; // 정량 13지표 · 업종=industryStats 밴드, 시장/전체=라이브 5분위.
	grades: CategoricalShare[]; // 정성 등급 동급비중(거버넌스·경영권·감사·주주환원·현금흐름).
	price: { per: PriceStat; pbr: PriceStat }; // 가격(펀더와 분리 격자).
}
export interface Valuation {
	per: Num;
	pbr: Num;
	perMed: Num;
	pbrMed: Num;
	fairLow: Num;
	fairHigh: Num;
	fairMid: Num;
	upside: Num;
	last: number;
	perPos: string | null;
}
export interface Tailwind {
	key: string;
	kr: string;
	en: string;
	blended: number;
	krScore: number;
	usScore: number;
	label: string;
	labelEn: string;
	tone: Tone;
}
export interface Verdict {
	composite: number;
	band: { kr: string; en: string; tone: Tone };
	strengths: Bilingual[];
	concerns: Bilingual[];
	riskRed: number;
	riskYellow: number;
}
export interface Peer {
	code: string;
	name: string;
	revenue: Num;
	self: boolean;
}
export interface TrendSeries {
	periods: string[];
	sales: Num[];
	op: Num[];
	net: Num[];
	opMargin: Num[];
	freq: 'annual' | 'quarter';
}
export interface AnalysisTrack {
	kr: string;
	en: string;
	verdict: Bilingual;
	tone: Tone;
	delta: string;
}
// ui/web 재무카드 포팅 · finance.json 5Y 에서 계산
export interface StackSeg {
	kr: string;
	v: number;
	color: string;
}
export interface Financials {
	years: string[]; // 오래된→최신
	opMargin: Num[];
	netMargin: Num[];
	roe: Num[];
	assetTurn: Num[]; // 매출/자산 (회전)
	equityMult: Num[]; // 자산/자본
	deRatio: Num[]; // 부채/자본 %
	currRatio: Num[]; // 유동자산/유동부채 %
	dupont: { netMargin: Num; assetTurn: Num; equityMult: Num; roe: Num }; // 최신
	assetMix: StackSeg[]; // 최신 자산 구성
	fundMix: StackSeg[]; // 최신 부채+자본 구성
	cf: { op: Num; inv: Num; fin: Num; fcf: Num };
}
export interface Company {
	code: string;
	/** 표시 통화 · KR='KRW'(조/억), US(EDGAR)='USD'($T/$B). buildCompany 가 finance 엔트리 currency 태그에서 채움. 기본 KRW(무회귀). */
	currency: string;
	marketLabel: string;
	name: Bilingual;
	sector: Bilingual;
	/** 산업 raw id (map/industries/{id}.json 키) · sector 는 라벨, 본 필드는 식별자. */
	industry: string;
	stage: string;
	role: string;
	eco: EcoNode;
	grades: GradeChip[];
	radar: RadarAxis[];
	changes: ChangeRow[];
	price: {
		last: Num;
		mktcap: string;
		mktcapRaw: Num; // 원 · 캔들 최신가 기준 시총 보정용
		ret1m: Num;
		ret3m: Num;
		ret1y: Num;
		vol1y: Num;
		hi52: Num;
		lo52: Num;
		vol: Num;
		asOf: string;
	};
	fundamentals: { per: Num; pbr: Num; psr: Num; npm: Num; roe: Num; opm: Num; dr: Num };
	financials: Financials;
	trendAnnual: TrendSeries;
	trendQuarter: TrendSeries | null;
	income: Statement;
	balance: Statement;
	cashflow: Statement;
	ratios: RatioRow[];
	credit: Credit;
	analysis: { summary: Bilingual; tracks: AnalysisTrack[] };
	macroExposure: MacroExposurePayload | null;
	peers: Peer[];
	story: { title: string; date: string; readTime?: number | string; slug: string } | null;
	percentile: { industry: string; n: number; metrics: PercentileMetric[] } | null;
	valuation: Valuation | null;
	risks: RiskFlag[];
	riskCatalog: RiskCatalogItem[]; // 위험 경고등 다이얼로그용 전체 차원 카탈로그 + 현상태(글랜스 risks 와 별개)
	tailwind: Tailwind | null;
	verdict: Verdict;
}
