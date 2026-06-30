import { MACRO_SERIES, type MacroLatest, type MacroSeriesDef, type FinCard, type FinSeries, type Num, type MacroPoint, type MacroSimFile } from '@dartlab/ui-contracts';
import type { CoMover } from './coMovement';
import type { Company, Lang, MacroExposureIndicatorPayload, MacroExposureQualityPayload, MacroFile, MacroRegimeModel, MacroRegimePayload, MacroSide, MacroTransmissionEdge, MacroTransmissionPayload, Tailwind, Tone } from './types';
import { EDGE_SECTOR_TO_TAILWIND, CURRENT_MACRO_EDGE_SECTOR_KEYS, classifyTailwind, hasNegativeTailwind } from './macroMappings';

export type MacroLensTab = 'dashboard' | 'transmission' | 'sources';
export type MacroMarket = 'KR' | 'US' | 'GLOBAL';
export type MacroChannel = 'revenue' | 'margin' | 'balanceSheet' | 'cashFlow' | 'valuation';

export interface MacroDriverView {
	id: string;
	label: string;
	group: string;
	seriesId: string;
	unit: string;
	source: 'ECOS' | 'FRED';
	value: string;
	change: string;
	asOf: string;
	spark: number[];
	directionSemantics: string;
	defaultLagMonths: number | null;
	relevance: 'primary' | 'secondary' | 'context';
	pressureLevel: 'high' | 'medium' | 'low' | 'blocked';
	pressureReason: string;
	coMovement: {
		corr: number;
		n: number;
		window: string;
		label: string;
		status: 'candidate' | 'unstable' | 'missing';
	} | null;
	freshness: {
		status: 'fresh' | 'watch' | 'stale' | 'unknown';
		daysLag: number | null;
		label: string;
	};
	transform: string;
	sourceLineage: string;
	qualityHint: string;
}

export interface MacroTransmissionEdgeView {
	id: string;
	driverId: string;
	driverLabel: string;
	market: MacroMarket;
	sectorKey: string;
	sectorLabel: string;
	channel: MacroChannel;
	financialLine: string;
	valuationLever: 'discountRate' | 'growth' | 'margin' | 'multiple' | 'riskPremium';
	sign: 'positive' | 'negative' | 'mixed' | 'unknown';
	lagMonths: [number, number] | null;
	confidence: 'high' | 'medium' | 'low' | 'blocked';
	evidenceLevel: 'observed' | 'sectorPrior' | 'template';
	requiredCompanyEvidence: string[];
	falsifiers: string[];
	sourceRefs: string[];
	note: string;
}

export interface MacroCheckpointView {
	id: string;
	label: string;
	value: string;
	tone: Tone;
	reason: string;
	source: string;
}

export interface MacroFalsifierView {
	id: string;
	type: 'coMovement' | 'quality' | 'missingCompanyEvidence' | 'staleData';
	driverId?: string;
	label: string;
	severity: 'info' | 'warning' | 'blocker';
	detail: string;
	sourceRef: string;
}

export interface MacroScenarioView {
	id: string;
	label: string;
	driverId: string;
	shock: string;
	firstBreak: string;
	expectedDirection: string;
	impactedFinancialLine: string;
	valuationLever: string;
	falsifier: string;
	requiredEvidence: string[];
	nextSurface: string;
	readiness: {
		status: 'ready' | 'needsEvidence' | 'blocked';
		reason: string;
	};
}

export interface MacroExposureQualityView {
	method: string | null;
	modelVersion: string | null;
	targetMetric: string | null;
	minObs: number | null;
	status: 'quantCandidate' | 'qualitativeOnly' | 'blocked';
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

export interface MacroExposureIndicatorView {
	method: string | null;
	modelVersion: string | null;
	targetMetric: string | null;
	minObs: number | null;
	label: string;
	seriesId: string;
	axis: string;
	rSquared: number | null;
	nObs: number | null;
	window: string | null;
	frequency: 'monthly' | 'quarterly' | 'annual' | null;
	lagMonths: number | null;
	coverage: 'company' | 'sectorOnly' | 'missing';
	sourceRef: string;
	sourceRefs: string[];
	latestChange: number | null;
	impact: string;
}

export interface MacroReleaseView {
	driverId: string;
	label: string;
	source: 'ECOS' | 'FRED';
	frequency: string;
	lastObservation: string;
	nextCheck: string;
	daysLag: number | null;
	staleAfterDays: number;
	status: 'fresh' | 'watch' | 'stale' | 'unknown';
	sourceRef: string;
}

export interface MacroSourcePacketView {
	driverId: string;
	label: string;
	seriesId: string;
	source: 'ECOS' | 'FRED';
	unit: string;
	frequency: string;
	asOf: string;
	value: string;
	change: string;
	transform: string;
	status: 'fresh' | 'watch' | 'stale' | 'unknown' | 'missing';
	artifactPath: string;
	sourceRef: string;
	lineage: string;
	qualityHint: string;
}

export interface MacroContributionComponentView {
	id: string;
	label: string;
	value: number;
	detail: string;
	status: 'ok' | 'watch' | 'blocked';
	sourceRef: string;
}

export interface MacroContributionView {
	driverId: string;
	label: string;
	summary: string;
	components: MacroContributionComponentView[];
	sourceRef: string;
}

export interface MacroCoMovePointView {
	ym: string;
	x: number;
	y: number;
	px: number;
	py: number;
	latest: boolean;
	label: string;
}

export interface MacroCoMoveGateView {
	driverId: string;
	label: string;
	corr: number | null;
	n: number | null;
	window: string;
	status: 'candidate' | 'unstable' | 'missing';
	sourceRef: string;
	detail: string;
	points: MacroCoMovePointView[];
	displayedPoints: number;
	lagLabel: string;
	formula: string;
	limitations: string[];
	xZero: number;
	yZero: number;
	xRange: string;
	yRange: string;
}

export interface MacroEvidenceGateView {
	id: 'macroData' | 'path' | 'comove' | 'company' | 'quant';
	labelKr: string;
	labelEn: string;
	value: string;
	detailKr: string;
	detailEn: string;
	status: 'ok' | 'watch' | 'blocked';
	sourceRef: string;
	blocks: string[];
}

export interface MacroMissingView {
	id: string;
	status: 'missing' | 'partial' | 'notWiredYet' | 'staleRisk';
	reason: string;
	sourceRef: string;
}

export interface MacroLensSnapshot {
	asOf: {
		macro: string | null;
		price: string | null;
		finance: string | null;
	};
	company: {
		code: string;
		name: string;
		sector: { kr: string; en: string };
		industry: string;
	};
	marketPhase: {
		kr: MacroPhaseView | null;
		us: MacroPhaseView | null;
	};
	drivers: MacroDriverView[];
	topPressures: MacroDriverView[];
	transmissionEdges: MacroTransmissionEdgeView[];
	companyCheckpoints: MacroCheckpointView[];
	sectorBinding: {
		tailwind: Tailwind | null;
		top: { id: string; kr: string; en: string; blended: number }[];
		bottom: { id: string; kr: string; en: string; blended: number }[];
	};
	exposureQuality: MacroExposureQualityView;
	exposureIndicators: MacroExposureIndicatorView[];
	releaseRail: MacroReleaseView[];
	sourcePackets: MacroSourcePacketView[];
	contributionStacks: MacroContributionView[];
	coMoveGates: MacroCoMoveGateView[];
	evidenceGates: MacroEvidenceGateView[];
	falsifiers: MacroFalsifierView[];
	scenarios: MacroScenarioView[];
	sourceRefs: string[];
	missing: MacroMissingView[];
	glance?: MacroGlanceView;
	macroPath?: MacroPathView;
	marketOnly?: boolean;
	// 국면 렌즈(Regime Lens·초강화) · 읽기전용 표시 데이터. macro.regime 부재 시 undefined(렌즈 숨김).
	regime?: MacroRegimeView;
}

export interface MacroPhaseView {
	market: 'KR' | 'US';
	phase: string;
	label: string;
	quadrant: string;
	growth: string;
	inflation: string;
	description: string;
}

export interface RegimeQuadrantCellView {
	key: 'stagflation' | 'reflation' | 'deflation' | 'goldilocks';
	labelKr: string;
	labelEn: string;
	growth: 'rising' | 'falling';
	inflation: 'rising' | 'falling';
}

export interface RegimeMarketView {
	market: 'KR' | 'US';
	cellKey: RegimeQuadrantCellView['key'] | null;
	phase: string;
	phaseLabel: string;
	quadrantLabel: string;
	growth: string;
	inflation: string;
	confidence: string | null;
	hasQuadrant: boolean;
	lensConflict: boolean;
	transitionLabel: string;
	hasTransitionProgress: boolean;
	// 구조화 전이 · 평면 계기가 양언어로 직접 렌더(전이신호 from→to·진행률·신호 충족수). null=미산출.
	transition: {
		fromKr: string; fromEn: string; toKr: string; toEn: string;
		progressPct: number | null; triggered: number; total: number;
	} | null;
	assets: { key: string; labelKr: string; labelEn: string; weight: string; tone: 'ow' | 'uw' | 'nu' }[];
	description: string;
}

export interface RegimeQuadrantView {
	asOf: string | null;
	cells: RegimeQuadrantCellView[];
	markets: RegimeMarketView[];
	freshness: {
		status: 'fresh' | 'watch' | 'stale' | 'unknown';
		label: string;
		daysLag: number | null;
	};
	lensConflict: boolean;
}

// ───────────────────────── 국면 렌즈 (Regime Lens · 초강화) ─────────────────────────
// 읽기전용 view-model. 점수·서수 badge·합산 0 · N 타일 나란히 + 불일치 모델명 텍스트.
// 각 타일은 자기 호라이즌·시간성·freshness 를 독립 표기(단일 '12M·확률' 프레임 금지).
// i18n: 사용자 노출 산문은 view-model 이 양언어({kr,en})로 합성, 템플릿이 T(x.kr,x.en) 로 고른다
// (라벨/노트/캡션 EN 패리티 · backend 한국어 enum 은 결정론 매핑으로 EN 라벨 보강).
export type RegimeText = { kr: string; en: string };
export interface RegimeTileView {
	model: 'probit' | 'sahm' | 'lei' | 'hamilton';
	modelName: string;
	zoneLabel: RegimeText; // 주역(13px/700) · 상태성 라벨. status-only 면 '표시 보류'.
	secondary: string | null; // probit ~20% 등 보조(수치·중립). 없으면 null.
	gaugeValue: number | null; // 0~1 게이지 기하 입력(probit=probability·hamilton=contractionProb). 확률 아닌 모델(sahm/lei)=null. 표현 아님(데이터).
	bucket: 0 | 1 | 2 | null; // 위험 군집(bucketOf SSOT·0 낮음/1 상승/2 높음). 색축 결정론 · UI 재유도 금지. status-only=null.
	horizonLabel: RegimeText; // 호라이즌 + 시간성 (예: '12M·leading')
	scaleLabel: RegimeText; // 자기 척도 (예: '확률·T10Y3M')
	asOf: string | null;
	stale: boolean;
	staleLabel: string | null;
	suppressed: boolean; // status-only(게이트 탈락·데이터 부족) → dim 렌더.
	statusText: RegimeText | null; // status-only 모델의 사유 텍스트.
	note: RegimeText; // title/aria · precisionNote·overlapNote·이중계상 노트.
}
export interface RegimeYieldCurveView {
	available: boolean;
	curveShapeLabel: RegimeText;
	spread: number | null; // 10Y-3M 스프레드 원수치(온도계 기하 입력·%p). 0 미만=역전.
	spreadText: string; // 예 '+0.40%p'
	asOf: string | null;
	note: RegimeText; // '형태=NS·spread=T10Y3M 동일곡선 · probit과 독립 신호 아님'
}
export interface RegimeGaRBarView {
	key: 'gar5' | 'gar25' | 'median' | 'gar75' | 'gar95';
	label: string; // 분위 백분율 라벨(언어중립): '5%' / '25%' / '50%' / '75%' / '95%'
	value: number;
	frac: number; // 0~1 막대 길이(분위 범위 정규화).
}
export interface RegimeGaRView {
	available: boolean;
	bars: RegimeGaRBarView[];
	skewness: number | null;
	tailRiskLabel: RegimeText;
	horizonLabel: RegimeText; // '4Q 전향 분포'
	asOf: string | null;
	note: RegimeText; // 'FCI 조건부 GDP 성장률 분위 [조건부 분포·점추정 아님]'
}
export interface RegimeBandView {
	available: boolean;
	points: number[]; // 가로 스파크용 절대 침체확률(0~1·고정축). per-window 재정규화 금지.
	caption: RegimeText; // 'Hamilton 수축확률 N분기(회고적·smoothed)'
	asOf: string | null;
}
export interface RegimeQuadrantDirectionView {
	available: boolean;
	growthLabel: RegimeText; // '성장↑' 등
	inflationLabel: RegimeText;
	assets: { key: string; label: string; labelEn: string; weight: string }[];
	alignment: RegimeText | null; // focusChannelAlignment 결과(서술만). 없으면 null.
}
export interface RegimeMarketLensView {
	market: 'KR' | 'US';
	// confluence 헤더 · 'N모델 중 M 유효 · 호라이즌·시간성 상이 · 동의: <text>'
	validCount: number;
	totalCount: number;
	agreement: RegimeText;
	tiles: RegimeTileView[];
	notApplicable: { id: string; label: string; reason: RegimeText }[]; // KR 'US 전용'/'단위 parity 미확정' 회색 라벨.
	yieldCurve: RegimeYieldCurveView | null; // KR 없음(US 전용).
	gar: RegimeGaRView | null; // KR 없음.
	band: RegimeBandView | null; // KR 없음.
	quadrant: RegimeQuadrantDirectionView | null;
}
export interface MacroRegimeView {
	available: boolean; // macro.regime 존재 여부.
	transitionFraction: { fraction: string; from: string; to: string } | null; // A블록 US 전향 분수(fraction='1/3' 중립·'충족'/'met' 은 템플릿).
	kr: RegimeMarketLensView | null;
	us: RegimeMarketLensView | null;
}

export interface MacroPathSectorNode {
	key: string;
	labelKr: string;
	labelEn: string;
	industryId: string | null;
	tailwindKey: string | null;
	blended: number | null;
	tailwindLabelKr: string;
	tailwindLabelEn: string;
	tone: Tone;
	missingTailwind: boolean;
	active: boolean;
}

export interface MacroPathLinkView {
	id: string;
	driverId: string;
	driverLabel: string;
	channel: MacroChannel;
	channelLabelKr: string;
	channelLabelEn: string;
	sectorKeys: string[];
	sectorNodes: MacroPathSectorNode[];
	market: MacroMarket;
	sign: 'positive' | 'negative' | 'mixed' | 'unknown';
	signLabel: string;
	evidenceLevel: 'observed' | 'sectorPrior' | 'template';
	evidenceLabel: 'OBS' | 'PRIOR' | 'TPL';
	confidence: 'high' | 'medium' | 'low' | 'blocked';
	styleClass: string;
	signClass: string;
	opacity: number;
	financialLine: string;
	valuationLever: string;
	lagLabel: string;
	note: string;
	sourceRefs: string[];
	active: boolean;
	allSector: boolean;
}

export interface MacroPathView {
	asOf: string | null;
	mode: 'compact' | 'full';
	driverNodes: { id: string; label: string; market: MacroMarket; freshnessStatus: string }[];
	channelNodes: { id: MacroChannel; labelKr: string; labelEn: string }[];
	sectorNodes: MacroPathSectorNode[];
	links: MacroPathLinkView[];
	allSectorLinks: MacroPathLinkView[];
	missing: MacroMissingView[];
	coverageKeys: string[];
	hasNegativeTailwind: boolean;
	captionKr: string;
	captionEn: string;
}

export interface MacroGlanceView {
	asOf: string | null;
	regime: RegimeQuadrantView;
	path: MacroPathView;
	sectorTailwinds: { id: string; kr: string; en: string; blended: number; tailwindKey?: string }[];
}

// ─────────────────────── Transmission/Path/Sources 산문 i18n (빌드타임 해석) ───────────────────────
// 내부 콘텐츠 데이터는 양언어({kr,en}) 로 보관하고, 빌더가 활성 언어로 *평문 string* 으로 해석한다.
// OUTPUT view-model 필드 타입은 string/string[] 그대로(렌더·테스트 불변). 국면 렌즈 subsystem 은
// 자체 {kr,en}+T() 메커니즘을 쓰므로 본 L 해석기는 그쪽에 절대 침투하지 않는다.
type Bi = { kr: string; en: string };
// 활성 언어로 평문 string 을 고르는 해석기 팩토리. 빌더 진입부에서 1회 생성해 헬퍼로 내린다.
const makeL = (lang: Lang) => (kr: string, en: string): string => (lang === 'en' ? en : kr);
type LFn = ReturnType<typeof makeL>;

interface EdgeTemplate {
	driverId: string;
	market: MacroMarket;
	sectors: string[];
	channel: MacroChannel;
	financialLine: Bi;
	valuationLever: MacroTransmissionEdgeView['valuationLever'];
	sign: MacroTransmissionEdgeView['sign'];
	lagMonths: [number, number] | null;
	confidence: MacroTransmissionEdgeView['confidence'];
	evidenceLevel: MacroTransmissionEdgeView['evidenceLevel'];
	requiredCompanyEvidence: Bi[];
	note: Bi;
}

const DRIVER_SEMANTICS: Record<string, { direction: Bi; lag: number | null }> = {
	USDKRW: { direction: { kr: '상승은 원화 약세. 수출 환산매출과 수입원가가 동시에 움직인다.', en: 'A rise means a weaker won; export translation revenue and import costs move together.' }, lag: 1 },
	BASE_RATE: { direction: { kr: '상승은 차입비용과 할인율 상승 압력으로 전파될 수 있다.', en: 'A rise can transmit as higher borrowing costs and discount-rate pressure.' }, lag: 6 },
	FEDFUNDS: { direction: { kr: '상승은 글로벌 할인율·달러 유동성 압력으로 전파될 수 있다.', en: 'A rise can transmit as global discount-rate and dollar-liquidity pressure.' }, lag: 6 },
	DGS10: { direction: { kr: '상승은 장기 할인율과 multiple 압박으로 전파될 수 있다.', en: 'A rise can transmit as a higher long-term discount rate and multiple compression.' }, lag: 3 },
	CPI: { direction: { kr: '상승은 가격전가와 비용압박을 동시에 확인해야 한다.', en: 'A rise requires checking pricing pass-through and cost pressure together.' }, lag: 3 },
	CPIAUCSL: { direction: { kr: '상승은 미국 긴축·수요 둔화 압력으로 전파될 수 있다.', en: 'A rise can transmit as US tightening and demand-slowdown pressure.' }, lag: 3 },
	EXPORT: { direction: { kr: '상승은 외부수요와 국내 제조업 매출 환경을 보여준다.', en: 'A rise reflects external demand and the domestic manufacturing revenue environment.' }, lag: 1 },
	IPI: { direction: { kr: '상승은 생산·가동률 환경 개선 신호다.', en: 'A rise signals an improving output and utilization environment.' }, lag: 1 },
	CLI: { direction: { kr: '상승은 경기 선행 모멘텀 개선 신호다.', en: 'A rise signals improving leading-cycle momentum.' }, lag: 3 },
	BAMLH0A0HYM2: { direction: { kr: '상승은 신용위험과 자금조달 압력 확대 신호다.', en: 'A rise signals widening credit risk and funding pressure.' }, lag: 3 },
	NFCI: { direction: { kr: '상승은 금융여건 긴축 신호다.', en: 'A rise signals tighter financial conditions.' }, lag: 3 },
	VIXCLS: { direction: { kr: '상승은 위험회피와 equity risk premium 확대 신호다.', en: 'A rise signals risk-off and a widening equity risk premium.' }, lag: 0 },
	DCOILWTICO: { direction: { kr: '상승은 에너지 매출 증가 요인, 제조 원가 상승 요인일 수 있다.', en: 'A rise can lift energy revenue while raising manufacturing costs.' }, lag: 1 },
	PCOPPUSDM: { direction: { kr: '상승은 글로벌 제조·전기화 수요와 원가 압력을 동시에 시사한다.', en: 'A rise points to both global manufacturing/electrification demand and cost pressure.' }, lag: 1 },
	PPI_SEMI: { direction: { kr: '상승은 반도체 제품가격 환경 개선 또는 원가 전가 신호다.', en: 'A rise signals an improving semiconductor price environment or cost pass-through.' }, lag: 1 },
	PPI_CHEM: { direction: { kr: '상승은 화학 제품가격과 원가 전가력을 동시에 확인해야 한다.', en: 'A rise requires checking chemical product prices and cost pass-through together.' }, lag: 1 },
	PPI_STEEL: { direction: { kr: '상승은 철강 판가와 수요 환경을 함께 본다.', en: 'A rise is read alongside steel selling prices and the demand environment.' }, lag: 1 },
	PPI_AUTO: { direction: { kr: '상승은 자동차 판가·원가 전가력을 함께 본다.', en: 'A rise is read alongside auto selling prices and cost pass-through.' }, lag: 1 },
	PPI_DISPLAY: { direction: { kr: '상승은 디스플레이 가격 환경 개선 신호다.', en: 'A rise signals an improving display price environment.' }, lag: 1 },
	PPI_ELEC: { direction: { kr: '상승은 전기전자 판가와 부품 원가를 함께 본다.', en: 'A rise is read alongside electronics selling prices and component costs.' }, lag: 1 },
	PPI_OIL: { direction: { kr: '상승은 정유·석화 판가와 원재료 원가를 동시에 확인하게 만든다.', en: 'A rise requires checking refining/petrochemical prices and raw-material costs together.' }, lag: 1 }
};

const SECTOR_DRIVER: Record<string, string[]> = {
	semiconductor: ['PPI_SEMI', 'USDKRW', 'EXPORT', 'DCOILWTICO', 'BAMLH0A0HYM2'],
	auto: ['PPI_AUTO', 'USDKRW', 'EXPORT', 'BASE_RATE', 'DCOILWTICO'],
	electronics: ['PPI_ELEC', 'USDKRW', 'EXPORT', 'DGS10'],
	chemical: ['PPI_CHEM', 'DCOILWTICO', 'USDKRW', 'EXPORT'],
	battery: ['PPI_CHEM', 'PCOPPUSDM', 'USDKRW', 'DGS10'],
	steel: ['PPI_STEEL', 'PCOPPUSDM', 'EXPORT', 'USDKRW'],
	shipbuilding: ['USDKRW', 'EXPORT', 'BASE_RATE', 'PPI_STEEL'],
	finance: ['BASE_RATE', 'DGS10', 'BAMLH0A0HYM2', 'NFCI'],
	construction: ['BASE_RATE', 'HOUSE_PRICE', 'BAMLH0A0HYM2'],
	realestate: ['BASE_RATE', 'HOUSE_PRICE', 'DGS10'],
	energy: ['DCOILWTICO', 'USDKRW', 'CPI'],
	retail: ['CPI', 'CSI', 'BASE_RATE'],
	cosmetics: ['USDKRW', 'EXPORT', 'CSI'],
	software: ['DGS10', 'FEDFUNDS', 'NASDAQCOM'],
	pharma: ['DGS10', 'FEDFUNDS', 'USDKRW'],
	telecom: ['BASE_RATE', 'CPI', 'DGS10'],
	food: ['CPI', 'DCOILWTICO', 'USDKRW'],
	logistics: ['DCOILWTICO', 'EXPORT', 'USDKRW']
};

const EDGE_TEMPLATES: EdgeTemplate[] = [
	{
		driverId: 'USDKRW',
		market: 'KR',
		sectors: ['semiconductor', 'auto', 'electronics', 'shipbuilding', 'chemical', 'battery', 'steel', 'cosmetics', 'logistics'],
		channel: 'revenue',
		financialLine: { kr: '매출 성장률 / 환산손익', en: 'Revenue growth / FX translation P&L' },
		valuationLever: 'growth',
		sign: 'mixed',
		lagMonths: [0, 3],
		confidence: 'medium',
		evidenceLevel: 'sectorPrior',
		requiredCompanyEvidence: [{ kr: '해외 매출 비중', en: 'Overseas revenue share' }, { kr: '외화 매출·매입 통화', en: 'FX revenue/purchase currency' }, { kr: 'FX 손익 주석', en: 'FX gain/loss footnote' }],
		note: { kr: '원화 약세는 수출 환산매출에는 유리할 수 있지만 달러 원가·부채가 있으면 상쇄된다.', en: 'A weaker won can help export translation revenue, but dollar costs and debt offset it.' }
	},
	{
		driverId: 'EXPORT',
		market: 'KR',
		sectors: ['semiconductor', 'auto', 'electronics', 'shipbuilding', 'chemical', 'steel', 'battery', 'logistics'],
		channel: 'revenue',
		financialLine: { kr: '매출 성장률 / 가동률', en: 'Revenue growth / utilization' },
		valuationLever: 'growth',
		sign: 'positive',
		lagMonths: [1, 6],
		confidence: 'medium',
		evidenceLevel: 'observed',
		requiredCompanyEvidence: [{ kr: '수출·해외 법인 매출', en: 'Export / overseas-subsidiary revenue' }, { kr: '주요 제품 수요', en: 'Key product demand' }, { kr: '재고와 수주', en: 'Inventory and order backlog' }],
		note: { kr: '수출 모멘텀은 제조업 매출 환경의 1차 driver다.', en: 'Export momentum is the primary driver of the manufacturing revenue environment.' }
	},
	{
		driverId: 'BASE_RATE',
		market: 'KR',
		sectors: ['all'],
		channel: 'balanceSheet',
		financialLine: { kr: '이자비용 / 차입 재조달', en: 'Interest expense / debt refinancing' },
		valuationLever: 'discountRate',
		sign: 'negative',
		lagMonths: [3, 12],
		confidence: 'medium',
		evidenceLevel: 'template',
		requiredCompanyEvidence: [{ kr: '부채비율', en: 'Debt-to-equity ratio' }, { kr: '단기차입금', en: 'Short-term borrowings' }, { kr: '이자보상배율', en: 'Interest coverage ratio' }, { kr: '차입금 만기', en: 'Debt maturity profile' }],
		note: { kr: '금리는 손익의 이자비용과 가치평가 할인율에 동시에 닿는다.', en: 'Rates touch both interest expense in the P&L and the valuation discount rate.' }
	},
	{
		driverId: 'DGS10',
		market: 'US',
		sectors: ['software', 'pharma', 'battery', 'semiconductor', 'electronics', 'all'],
		channel: 'valuation',
		financialLine: { kr: 'multiple / 할인율', en: 'Multiple / discount rate' },
		valuationLever: 'discountRate',
		sign: 'negative',
		lagMonths: [0, 6],
		confidence: 'low',
		evidenceLevel: 'template',
		requiredCompanyEvidence: [{ kr: '장기 성장 기대', en: 'Long-term growth expectations' }, { kr: 'PER/PBR 위치', en: 'PER/PBR positioning' }, { kr: '현금흐름 기간 구조', en: 'Cash-flow duration structure' }],
		note: { kr: '장기금리는 성장주 multiple과 risk premium을 흔드는 공통 driver다.', en: 'Long-term rates are a common driver swinging growth-stock multiples and the risk premium.' }
	},
	{
		driverId: 'BAMLH0A0HYM2',
		market: 'US',
		sectors: ['all'],
		channel: 'valuation',
		financialLine: { kr: '신용스프레드 / 위험프리미엄', en: 'Credit spread / risk premium' },
		valuationLever: 'riskPremium',
		sign: 'negative',
		lagMonths: [0, 3],
		confidence: 'medium',
		evidenceLevel: 'observed',
		requiredCompanyEvidence: [{ kr: '신용등급', en: 'Credit rating' }, { kr: '차입 의존도', en: 'Debt dependence' }, { kr: '만기 구조', en: 'Maturity structure' }],
		note: { kr: 'HY spread 확대는 위험자산 전반의 요구수익률 상승 신호다.', en: 'A widening HY spread signals higher required returns across risk assets broadly.' }
	},
	{
		driverId: 'DCOILWTICO',
		market: 'GLOBAL',
		sectors: ['energy', 'chemical', 'auto', 'logistics', 'food'],
		channel: 'margin',
		financialLine: { kr: '매출총이익률 / 원가율', en: 'Gross margin / cost ratio' },
		valuationLever: 'margin',
		sign: 'mixed',
		lagMonths: [0, 3],
		confidence: 'medium',
		evidenceLevel: 'sectorPrior',
		requiredCompanyEvidence: [{ kr: '원재료 비중', en: 'Raw-material share' }, { kr: '가격 전가력', en: 'Pricing pass-through power' }, { kr: '재고 회전', en: 'Inventory turnover' }, { kr: '연료비 비중', en: 'Fuel-cost share' }],
		note: { kr: '유가는 에너지 매출과 제조·물류 원가에 반대 방향으로 작용할 수 있다.', en: 'Oil prices can act in opposite directions on energy revenue versus manufacturing/logistics costs.' }
	},
	{
		driverId: 'CPI',
		market: 'KR',
		sectors: ['retail', 'food', 'telecom', 'construction', 'all'],
		channel: 'margin',
		financialLine: { kr: '판가 / 비용 전가', en: 'Selling price / cost pass-through' },
		valuationLever: 'margin',
		sign: 'mixed',
		lagMonths: [1, 6],
		confidence: 'low',
		evidenceLevel: 'template',
		requiredCompanyEvidence: [{ kr: '가격 전가력', en: 'Pricing pass-through power' }, { kr: '원가 구조', en: 'Cost structure' }, { kr: '수요 탄력성', en: 'Demand elasticity' }],
		note: { kr: '물가는 판가 인상 여지와 수요 둔화를 동시에 만든다.', en: 'Inflation creates both room for price hikes and demand softening at once.' }
	},
	{
		driverId: 'PPI_SEMI',
		market: 'KR',
		sectors: ['semiconductor'],
		channel: 'margin',
		financialLine: { kr: '제품가격 / 영업이익률', en: 'Product price / operating margin' },
		valuationLever: 'margin',
		sign: 'positive',
		lagMonths: [0, 3],
		confidence: 'medium',
		evidenceLevel: 'observed',
		requiredCompanyEvidence: [{ kr: '제품 믹스', en: 'Product mix' }, { kr: '재고 평가', en: 'Inventory valuation' }, { kr: '가동률', en: 'Utilization rate' }],
		note: { kr: '반도체 PPI는 제품가격 환경의 직접 proxy로 쓸 수 있다.', en: 'Semiconductor PPI can serve as a direct proxy for the product-price environment.' }
	},
	{
		driverId: 'PPI_CHEM',
		market: 'KR',
		sectors: ['chemical', 'battery'],
		channel: 'margin',
		financialLine: { kr: '제품가격 / 스프레드', en: 'Product price / spread' },
		valuationLever: 'margin',
		sign: 'mixed',
		lagMonths: [0, 3],
		confidence: 'medium',
		evidenceLevel: 'observed',
		requiredCompanyEvidence: [{ kr: '원재료-제품 스프레드', en: 'Feedstock-to-product spread' }, { kr: '고객 전가력', en: 'Pass-through power to customers' }, { kr: '재고', en: 'Inventory' }],
		note: { kr: '화학 PPI는 판가와 원가 전가력을 함께 확인해야 한다.', en: 'Chemical PPI requires checking selling prices and cost pass-through together.' }
	},
	{
		driverId: 'PPI_STEEL',
		market: 'KR',
		sectors: ['steel', 'shipbuilding'],
		channel: 'margin',
		financialLine: { kr: '판가 / 원재료 스프레드', en: 'Selling price / raw-material spread' },
		valuationLever: 'margin',
		sign: 'mixed',
		lagMonths: [0, 3],
		confidence: 'medium',
		evidenceLevel: 'observed',
		requiredCompanyEvidence: [{ kr: '철강재 매입·판매 구조', en: 'Steel purchase/sale structure' }, { kr: '장기계약 가격', en: 'Long-term contract pricing' }],
		note: { kr: '철강 PPI는 철강사는 판가, 수요처는 원가로 전파된다.', en: 'Steel PPI transmits as selling prices for steelmakers and as costs for downstream buyers.' }
	},
	{
		driverId: 'PPI_AUTO',
		market: 'KR',
		sectors: ['auto'],
		channel: 'margin',
		financialLine: { kr: '판가 / 영업이익률', en: 'Selling price / operating margin' },
		valuationLever: 'margin',
		sign: 'mixed',
		lagMonths: [0, 3],
		confidence: 'medium',
		evidenceLevel: 'observed',
		requiredCompanyEvidence: [{ kr: '판매가격', en: 'Selling price' }, { kr: '부품 원가', en: 'Component costs' }, { kr: '인센티브', en: 'Incentives' }, { kr: '환율', en: 'Exchange rate' }],
		note: { kr: '자동차 PPI는 가격 전가력과 수요 둔화를 같이 확인해야 한다.', en: 'Auto PPI requires checking pricing pass-through and demand softening together.' }
	}
];

// 내부 시나리오 콘텐츠 · 산문 필드는 양언어({kr,en}), 빌더가 L 로 평문 string 해석.
// id/driverId/valuationLever/shock 은 언어중립 토큰(시리즈ID·숫자·%·레버 enum) → 그대로 string.
interface ScenarioTemplate {
	id: string;
	driverId: string;
	shock: string;
	valuationLever: string;
	label: Bi;
	firstBreak: Bi;
	expectedDirection: Bi;
	impactedFinancialLine: Bi;
	falsifier: Bi;
	requiredEvidence: Bi[];
	nextSurface: Bi;
}

const SCENARIOS: ScenarioTemplate[] = [
	{ id: 'fx10', label: { kr: '원/달러 +10%', en: 'USD/KRW +10%' }, driverId: 'USDKRW', shock: 'USDKRW +10%', firstBreak: { kr: '수출 환산매출 또는 수입원가', en: 'Export translation revenue or import costs' }, expectedDirection: { kr: '수출 환산매출과 달러 원가가 동시에 움직임', en: 'Export translation revenue and dollar costs move together' }, impactedFinancialLine: { kr: '매출 성장률 / 매출총이익률', en: 'Revenue growth / gross margin' }, valuationLever: 'growth / margin', falsifier: { kr: '달러 원가·부채·헤지 정책 확인 전 방향 단정 금지', en: 'Do not assert direction before checking dollar costs, debt, and hedging policy' }, requiredEvidence: [{ kr: '해외 매출 비중', en: 'Overseas revenue share' }, { kr: '외화 원가', en: 'FX-denominated costs' }, { kr: 'FX 손익', en: 'FX gain/loss' }], nextSurface: { kr: '재무제표 분석 · 매출/원가/주석', en: 'Financial statement analysis · revenue/cost/footnotes' } },
	{ id: 'rate100', label: { kr: '기준금리 +100bp', en: 'Base rate +100bp' }, driverId: 'BASE_RATE', shock: 'BASE_RATE +1.0%p', firstBreak: { kr: '이자비용과 할인율', en: 'Interest expense and discount rate' }, expectedDirection: { kr: '차입 의존 기업에는 비용·할인율 상승 압력', en: 'Upward cost and discount-rate pressure on debt-dependent firms' }, impactedFinancialLine: { kr: '이자비용 / 순이익 / multiple', en: 'Interest expense / net income / multiple' }, valuationLever: 'discountRate', falsifier: { kr: '순현금·고정금리 장기차입이면 약화', en: 'Weakened if net cash or fixed-rate long-term debt' }, requiredEvidence: [{ kr: '부채비율', en: 'Debt-to-equity ratio' }, { kr: '단기차입', en: 'Short-term borrowings' }, { kr: '이자보상배율', en: 'Interest coverage ratio' }], nextSurface: { kr: '재무제표 분석 · 안정성/현금흐름', en: 'Financial statement analysis · stability/cash flow' } },
	{ id: 'oil30', label: { kr: 'WTI +30%', en: 'WTI +30%' }, driverId: 'DCOILWTICO', shock: 'WTI +30%', firstBreak: { kr: '원재료·연료비 또는 에너지 매출', en: 'Raw-material/fuel costs or energy revenue' }, expectedDirection: { kr: '에너지는 매출 증가 요인, 제조·물류는 원가 상승 요인 확인', en: 'A revenue tailwind for energy; check it as a cost headwind for manufacturing/logistics' }, impactedFinancialLine: { kr: '매출총이익률 / 원가율', en: 'Gross margin / cost ratio' }, valuationLever: 'margin', falsifier: { kr: '가격 전가·재고평가·원가 계약 확인 전 단정 금지', en: 'Do not assert before checking pass-through, inventory valuation, and cost contracts' }, requiredEvidence: [{ kr: '원재료 비중', en: 'Raw-material share' }, { kr: '가격 전가력', en: 'Pricing pass-through power' }, { kr: '재고', en: 'Inventory' }], nextSurface: { kr: '재무제표 분석 · 마진/재고', en: 'Financial statement analysis · margin/inventory' } },
	{ id: 'exportDown', label: { kr: '수출 YoY -10%', en: 'Exports YoY -10%' }, driverId: 'EXPORT', shock: 'EXPORT YoY -10%', firstBreak: { kr: '외부수요와 가동률', en: 'External demand and utilization' }, expectedDirection: { kr: '수출 제조업 매출·가동률 압박 가능', en: 'Possible pressure on export-manufacturing revenue and utilization' }, impactedFinancialLine: { kr: '매출 성장률 / 재고 / 가동률', en: 'Revenue growth / inventory / utilization' }, valuationLever: 'growth', falsifier: { kr: '시장점유율·제품 믹스·단가가 반대 방향이면 약화', en: 'Weakened if market share, product mix, or unit price move the other way' }, requiredEvidence: [{ kr: '수출 매출', en: 'Export revenue' }, { kr: '수주', en: 'Order intake' }, { kr: '재고', en: 'Inventory' }], nextSurface: { kr: '산업/동종업종 비교', en: 'Industry / peer comparison' } },
	{ id: 'hy200', label: { kr: 'HY spread +200bp', en: 'HY spread +200bp' }, driverId: 'BAMLH0A0HYM2', shock: 'HY spread +2.0%p', firstBreak: { kr: '위험프리미엄과 차입 접근성', en: 'Risk premium and access to borrowing' }, expectedDirection: { kr: '레버리지 기업의 요구수익률·차입 접근성 압력', en: 'Pressure on required returns and borrowing access for leveraged firms' }, impactedFinancialLine: { kr: '신용스프레드 / 금융비용 / multiple', en: 'Credit spread / financing cost / multiple' }, valuationLever: 'riskPremium', falsifier: { kr: '현금 보유·모회사 지원·만기 여유 확인 전 단정 금지', en: 'Do not assert before checking cash holdings, parent support, and maturity headroom' }, requiredEvidence: [{ kr: '신용등급', en: 'Credit rating' }, { kr: '만기', en: 'Maturity' }, { kr: '현금 보유', en: 'Cash holdings' }], nextSurface: { kr: '신용/리스크 경고등', en: 'Credit / risk warning panel' } }
];

const CORE_DRIVER_IDS = ['USDKRW', 'BASE_RATE', 'CPI', 'EXPORT', 'DGS10', 'BAMLH0A0HYM2', 'DCOILWTICO'];
const MS_DAY = 24 * 60 * 60 * 1000;
const REGIME_CELLS: RegimeQuadrantCellView[] = [
	{ key: 'stagflation', labelKr: '스태그플레이션', labelEn: 'Stagflation', growth: 'falling', inflation: 'rising' },
	{ key: 'reflation', labelKr: '리플레이션', labelEn: 'Reflation', growth: 'rising', inflation: 'rising' },
	{ key: 'deflation', labelKr: '디플레이션', labelEn: 'Deflation', growth: 'falling', inflation: 'falling' },
	{ key: 'goldilocks', labelKr: '골디락스', labelEn: 'Goldilocks', growth: 'rising', inflation: 'falling' }
];
const ASSET_ROWS = [
	{ key: 'equity', labelKr: '주식', labelEn: 'Equity' },
	{ key: 'bond', labelKr: '채권', labelEn: 'Bond' },
	{ key: 'commodity', labelKr: '원자재', labelEn: 'Comdty' },
	{ key: 'gold', labelKr: '금', labelEn: 'Gold' },
	{ key: 'tips', labelKr: '물가채', labelEn: 'TIPS' },
	{ key: 'cash', labelKr: '현금', labelEn: 'Cash' }
];
const CHANNEL_LABELS: Record<MacroChannel, { kr: string; en: string }> = {
	revenue: { kr: '매출', en: 'Sales' },
	margin: { kr: '마진', en: 'Margin' },
	balanceSheet: { kr: '차입', en: 'Debt' },
	cashFlow: { kr: '현금', en: 'Cash' },
	valuation: { kr: '밸류', en: 'Value' }
};

const fmtDate = (d?: string | null) => d ? (d.length === 8 ? `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}` : d) : '·';

function fmtLatest(m: MacroLatest): string {
	const v = m.v.toLocaleString('en-US', { maximumFractionDigits: m.def.digits ?? 2 });
	const signed = m.def.yoy && m.v > 0 ? '+' + v : v;
	const u = m.def.unit;
	return u === 'pt' || u === '원' ? signed : u === '$' ? '$' + signed : u === '$/t' ? '$' + signed : signed + u;
}

function fmtChange(m: MacroLatest): string {
	if (m.chg == null) return '·';
	const digits = m.def.digits ?? 2;
	// 부호는 표시 정밀도로 반올림한 값 기준 · raw 가 -0.3·digits 0 이면 "0"인데 raw 부호로 "-0" 나오던 버그.
	const rounded = Number(m.chg.toFixed(digits));
	const v = Math.abs(rounded).toLocaleString('en-US', { maximumFractionDigits: digits });
	const sign = rounded > 0 ? '+' : rounded < 0 ? '-' : '';
	return `${sign}${v}${m.def.unit === 'pt' || m.def.unit === '원' ? '' : m.def.unit}`;
}

function parseYmd(d?: string | null): number | null {
	if (!d || d.length < 8) return null;
	const t = Date.UTC(+d.slice(0, 4), +d.slice(4, 6) - 1, +d.slice(6, 8));
	return Number.isFinite(t) ? t : null;
}

function daysLag(d?: string | null): number | null {
	const t = parseYmd(d);
	if (t == null) return null;
	return Math.max(0, Math.floor((Date.now() - t) / MS_DAY));
}

function transformOf(def: MacroSeriesDef): string {
	if (def.yoy) return 'YoY + latest delta';
	if (def.unit === '%' || def.unit === '%p') return 'level + rate delta';
	if (def.unit === '원') return 'FX level + latest delta';
	if (def.unit === '$' || def.unit === '$/t') return 'commodity level + latest delta';
	return 'level + latest delta';
}

function freshnessOf(def: MacroSeriesDef, d: string, L: LFn): MacroDriverView['freshness'] {
	const lag = daysLag(d);
	if (lag == null) return { status: 'unknown', daysLag: null, label: L('기준일 확인 필요', 'asOf date needs verification') };
	const staleAfter = staleAfterDaysOf(def);
	if (lag > staleAfter) return { status: 'stale', daysLag: lag, label: `stale ${lag}d` };
	if (lag > staleAfter * 0.65) return { status: 'watch', daysLag: lag, label: `watch ${lag}d` };
	return { status: 'fresh', daysLag: lag, label: `fresh ${lag}d` };
}

function staleAfterDaysOf(def: MacroSeriesDef): number {
	if (def.src === 'fred') return 10;
	if (def.id === 'BASE_RATE') return 65;
	return 75;
}

function cadenceDaysOf(def: MacroSeriesDef): number {
	if (def.src === 'fred') return 7;
	if (def.id === 'BASE_RATE') return 60;
	return 35;
}

function frequencyOf(def: MacroSeriesDef): string {
	if (def.src === 'fred') return 'FRED rolling/daily check';
	if (def.id === 'BASE_RATE') return 'ECOS policy event';
	return def.yoy ? 'ECOS monthly YoY' : 'ECOS monthly';
}

function addDaysYmd(d: string, days: number): string {
	const t = parseYmd(d);
	if (t == null) return '·';
	const next = new Date(t + days * MS_DAY);
	const y = next.getUTCFullYear();
	const m = `${next.getUTCMonth() + 1}`.padStart(2, '0');
	const day = `${next.getUTCDate()}`.padStart(2, '0');
	return `${y}-${m}-${day}`;
}

function componentStatus(value: number): MacroContributionComponentView['status'] {
	return value >= 0.67 ? 'ok' : value >= 0.25 ? 'watch' : 'blocked';
}

function confidenceScore(edge: MacroTransmissionEdgeView | undefined): number {
	if (!edge || edge.confidence === 'blocked') return 0;
	const conf = edge.confidence === 'high' ? 1 : edge.confidence === 'medium' ? 0.72 : 0.42;
	const evidence = edge.evidenceLevel === 'observed' ? 1 : edge.evidenceLevel === 'sectorPrior' ? 0.65 : 0.38;
	return Math.min(1, conf * evidence);
}

function freshnessScore(status: MacroDriverView['freshness']['status']): number {
	return status === 'fresh' ? 1 : status === 'watch' ? 0.55 : status === 'unknown' ? 0.25 : 0.05;
}

function hasCompanyExposureEvidence(q: MacroExposureQualityView): boolean {
	return q.coverage === 'company' && q.nObs != null;
}

function quantEvidenceOpen(q: MacroExposureQualityView): boolean {
	return q.status === 'quantCandidate'
		&& hasCompanyExposureEvidence(q)
		&& q.rSquared != null
		&& !!q.window
		&& !!q.frequency
		&& (q.minObs == null || q.nObs! >= q.minObs);
}

function quantEvidenceBlocks(q: MacroExposureQualityView): string[] {
	const out: string[] = [];
	if (q.status !== 'quantCandidate') out.push(`status ${q.status}`);
	if (q.coverage !== 'company') out.push(`coverage ${q.coverage}`);
	if (q.nObs == null) out.push('nObs missing');
	else if (q.minObs != null && q.nObs < q.minObs) out.push(`nObs ${q.nObs} < minObs ${q.minObs}`);
	if (q.rSquared == null) out.push('R² missing');
	if (!q.window) out.push('window missing');
	if (!q.frequency) out.push('frequency missing');
	return out.length ? out : [q.blockedReason || 'quality gate closed'];
}

function exposureQualityScore(q: MacroExposureQualityView): number {
	if (quantEvidenceOpen(q)) return 0.86;
	if (q.status === 'qualitativeOnly' || hasCompanyExposureEvidence(q) || q.coverage === 'sectorOnly') return 0.42;
	return 0.08;
}

function changeIntensity(m: MacroLatest): number {
	if (m.chg == null || !Number.isFinite(m.chg)) return 0;
	const abs = Math.abs(m.chg);
	const unit = m.def.unit;
	if (unit === '%' || unit === '%p') return Math.min(24, abs * 6);
	if (unit === '원') return Math.min(24, abs / 4);
	if (unit === '$') return Math.min(24, abs * 2.5);
	if (unit === '$/t') return Math.min(24, abs / 120);
	if (unit === 'pt') return Math.min(24, (abs / Math.max(1, Math.abs(m.v))) * 500);
	return Math.min(24, abs);
}

function signedValue(v: number, maximumFractionDigits = 2): string {
	const abs = Math.abs(v).toLocaleString('en-US', { maximumFractionDigits });
	return `${v > 0 ? '+' : v < 0 ? '-' : ''}${abs}`;
}

function paddedDomain(values: number[]): [number, number] {
	const finite = values.filter((v) => Number.isFinite(v));
	if (!finite.length) return [-1, 1];
	let lo = Math.min(0, ...finite);
	let hi = Math.max(0, ...finite);
	if (lo === hi) {
		const pad = Math.max(0.01, Math.abs(lo) * 0.12);
		return [lo - pad, hi + pad];
	}
	const pad = (hi - lo) * 0.08;
	return [lo - pad, hi + pad];
}

function domainPct(v: number, lo: number, hi: number): number {
	const span = hi - lo || 1;
	return Math.max(0, Math.min(100, ((v - lo) / span) * 100));
}

function buildCoMoveScatter(cm: CoMover | undefined, L: LFn): Pick<MacroCoMoveGateView, 'points' | 'displayedPoints' | 'lagLabel' | 'formula' | 'limitations' | 'xZero' | 'yZero' | 'xRange' | 'yRange'> {
	const raw = (cm?.points ?? [])
		.filter((p) => Number.isFinite(p.macroDiff) && Number.isFinite(p.stockReturn))
		.slice(-72);
	const [xMin, xMax] = paddedDomain(raw.map((p) => p.macroDiff));
	const [yMin, yMax] = paddedDomain(raw.map((p) => p.stockReturn));
	return {
		points: raw.map((p, i) => ({
			ym: p.ym,
			x: p.macroDiff,
			y: p.stockReturn,
			px: domainPct(p.macroDiff, xMin, xMax),
			py: 100 - domainPct(p.stockReturn, yMin, yMax),
			latest: i === raw.length - 1,
			label: `${p.ym}: macro Δ ${signedValue(p.macroDiff, 2)} · stock ${signedValue(p.stockReturn * 100, 1)}%`
		})),
		displayedPoints: raw.length,
		lagLabel: 'lag 0M',
		formula: L('x=거시 월말값 1차차분 · y=종목 월수익률', 'x = macro month-end first difference · y = stock monthly return'),
		limitations: [L('월말 겹침 표본', 'month-end overlap sample'), L('발표일·revision 미반영', 'release date/revisions not reflected'), L('outlier·우연상관 민감', 'sensitive to outliers and spurious correlation')],
		xZero: domainPct(0, xMin, xMax),
		yZero: 100 - domainPct(0, yMin, yMax),
		xRange: `${signedValue(xMin, 2)} to ${signedValue(xMax, 2)}`,
		yRange: `${signedValue(yMin * 100, 1)}% to ${signedValue(yMax * 100, 1)}%`
	};
}

function coMovementOf(cm: CoMover | undefined, L: LFn): MacroDriverView['coMovement'] | null {
	if (!cm) return null;
	const abs = Math.abs(cm.corr);
	const status: NonNullable<MacroDriverView['coMovement']>['status'] = cm.n >= 24 && abs >= 0.45 ? 'candidate' : 'unstable';
	const sign = cm.corr > 0 ? '+' : '';
	return {
		corr: cm.corr,
		n: cm.n,
		window: `${cm.n}M overlap`,
		status,
		label: `${status === 'candidate' ? L('탐색 후보', 'candidate') : L('불안정', 'unstable')} corr ${sign}${cm.corr.toFixed(2)} · n=${cm.n}`
	};
}

function pressureLevel(relevance: MacroDriverView['relevance'], m: MacroLatest, coMovement: MacroDriverView['coMovement'] | null, freshness: MacroDriverView['freshness']): MacroDriverView['pressureLevel'] {
	if (freshness.status === 'stale') return 'blocked';
	if (relevance === 'primary' && coMovement?.status === 'candidate') return 'high';
	if (relevance === 'primary') return changeIntensity(m) >= 10 ? 'high' : 'medium';
	if (relevance === 'secondary' && coMovement?.status === 'candidate') return 'medium';
	if (relevance === 'secondary' && changeIntensity(m) >= 12) return 'medium';
	return 'low';
}

function pressureReason(relevance: MacroDriverView['relevance'], m: MacroLatest, coMovement: MacroDriverView['coMovement'] | null, freshness: MacroDriverView['freshness'], L: LFn): string {
	const rel = relevance === 'primary' ? L('섹터 직접 driver', 'direct sector driver') : relevance === 'secondary' ? L('공통 매크로 driver', 'common macro driver') : L('맥락 지표', 'context indicator');
	const chg = m.chg == null ? L('최근 변화 없음', 'no recent change') : `${L('최근 변화', 'recent change')} ${fmtChange(m)}`;
	const co = coMovement ? coMovement.label : L('동행상관 미확인', 'co-movement not confirmed');
	return `${rel} · ${chg} · ${co} · ${freshness.label}`;
}

function qualityHintOf(relevance: MacroDriverView['relevance'], coMovement: MacroDriverView['coMovement'] | null, freshness: MacroDriverView['freshness'], L: LFn): string {
	if (freshness.status === 'stale') return L('차단: 거시 관측 stale', 'blocked: stale macro observation');
	if (coMovement?.status === 'candidate') return L('동행 후보 · 회사 증거 필요', 'co-movement candidate; company evidence still required');
	if (relevance === 'primary') return L('업종 경로 있음 · 회귀 품질 대기', 'sector path available; regression quality pending');
	if (relevance === 'secondary') return L('거시 맥락 · 회사별 노출 대기', 'macro context; company-specific exposure pending');
	return L('맥락 전용', 'context only');
}

function phaseView(market: 'KR' | 'US', side: MacroSide | undefined, L: LFn): MacroPhaseView | null {
	if (!side) return null;
	const q = side.quadrant;
	return {
		market,
		phase: side.phase,
		label: side.phaseLabel || side.phase,
		quadrant: q?.quadrantLabel || q?.quadrant || L('상세 없음', 'no detail'),
		growth: q?.growth || '·',
		inflation: q?.inflation || '·',
		description: q?.description || L('국면 상세 데이터 없음', 'no regime detail data')
	};
}

function assetTone(weight?: string): 'ow' | 'uw' | 'nu' {
	return weight === 'overweight' ? 'ow' : weight === 'underweight' ? 'uw' : 'nu';
}

function cellFromSide(side?: MacroSide): RegimeQuadrantCellView['key'] | null {
	const q = side?.quadrant;
	const key = q?.quadrant;
	if (key === 'stagflation' || key === 'reflation' || key === 'deflation' || key === 'goldilocks') return key;
	const growth = q?.growth;
	const inflation = q?.inflation;
	if (growth === 'falling' && inflation === 'rising') return 'stagflation';
	if (growth === 'rising' && inflation === 'rising') return 'reflation';
	if (growth === 'falling' && inflation === 'falling') return 'deflation';
	if (growth === 'rising' && inflation === 'falling') return 'goldilocks';
	return null;
}

// phase enum → 양언어 라벨 (전이 from/to·사이클 표기 공용). 미등록은 원문 유지(날조 금지).
const PHASE_LABEL: Record<string, { kr: string; en: string }> = {
	expansion: { kr: '확장', en: 'Expansion' },
	slowdown: { kr: '둔화', en: 'Slowdown' },
	contraction: { kr: '수축', en: 'Contraction' },
	recovery: { kr: '회복', en: 'Recovery' },
	stagflation: { kr: '스태그플레이션', en: 'Stagflation' },
	reflation: { kr: '리플레이션', en: 'Reflation' },
	deflation: { kr: '디플레이션', en: 'Deflation' },
	goldilocks: { kr: '골디락스', en: 'Goldilocks' }
};

function buildTransition(side?: MacroSide): RegimeMarketView['transition'] {
	const tr = side?.transition;
	if (!tr || !tr.from || !tr.to) return null;
	const from = PHASE_LABEL[tr.from] ?? { kr: tr.from, en: tr.from };
	const to = PHASE_LABEL[tr.to] ?? { kr: tr.to, en: tr.to };
	const triggered = tr.triggered?.length ?? 0;
	const pending = tr.pending?.length ?? 0;
	return {
		fromKr: from.kr, fromEn: from.en, toKr: to.kr, toEn: to.en,
		progressPct: typeof tr.progress === 'number' ? Math.round(tr.progress) : null,
		triggered, total: triggered + pending
	};
}

function transitionLabel(side?: MacroSide): { label: string; hasProgress: boolean } {
	const tr = side?.transition;
	if (!tr) return { label: '전이신호 미산출', hasProgress: false };
	const progress = typeof tr.progress === 'number' ? `${tr.progress}%` : '미확정';
	const from = tr.from || '?';
	const to = tr.to || '?';
	const triggered = tr.triggered?.length ?? 0;
	const pending = tr.pending?.length ?? 0;
	return { label: `${from}→${to} · ${progress} · ${triggered}/${triggered + pending} 신호`, hasProgress: typeof tr.progress === 'number' };
}

function freshnessFromAsOf(asOf?: string | null): RegimeQuadrantView['freshness'] {
	const lag = daysLag((asOf || '').replaceAll('-', ''));
	if (lag == null) return { status: 'unknown', label: 'asOf 없음', daysLag: null };
	if (lag > 10) return { status: 'stale', label: `${lag}일 경과`, daysLag: lag };
	if (lag > 5) return { status: 'watch', label: `${lag}일 경과`, daysLag: lag };
	return { status: 'fresh', label: `${lag}일`, daysLag: lag };
}

function buildRegimeMarket(market: 'KR' | 'US', side?: MacroSide): RegimeMarketView {
	const q = side?.quadrant;
	const cellKey = cellFromSide(side);
	const phase = side?.phase ?? 'unknown';
	const phaseLabel = side?.phaseLabel || phase;
	const quadrantLabel = q?.quadrantLabel || q?.quadrant || '국면 상세 데이터 없음';
	const tr = transitionLabel(side);
	return {
		market,
		cellKey,
		phase,
		phaseLabel,
		quadrantLabel,
		growth: q?.growth || '·',
		inflation: q?.inflation || '·',
		confidence: q?.confidence || side?.confidence || null,
		hasQuadrant: !!q,
		lensConflict: !!q && phase !== q.quadrant,
		transitionLabel: tr.label,
		hasTransitionProgress: tr.hasProgress,
		transition: buildTransition(side),
		assets: ASSET_ROWS.map((asset) => ({
			...asset,
			weight: q?.assetImplication?.[asset.key] ?? 'neutral',
			tone: assetTone(q?.assetImplication?.[asset.key])
		})),
		description: q?.description || '국면 상세 데이터 없음'
	};
}

export function buildRegimeQuadrant(macro: MacroFile | null): RegimeQuadrantView {
	const markets = [buildRegimeMarket('KR', macro?.kr), buildRegimeMarket('US', macro?.us)];
	return {
		asOf: macro?.asOf ?? null,
		cells: REGIME_CELLS,
		markets,
		freshness: freshnessFromAsOf(macro?.asOf ?? null),
		lensConflict: markets.some((m) => m.lensConflict)
	};
}

function evidenceStyle(edge: MacroTransmissionEdge): { styleClass: string; opacity: number; label: 'OBS' | 'PRIOR' | 'TPL' } {
	if (edge.evidenceLevel === 'observed') return { styleClass: 'observed', opacity: 1, label: 'OBS' };
	if (edge.evidenceLevel === 'sectorPrior') return { styleClass: 'prior', opacity: 0.65, label: 'PRIOR' };
	return { styleClass: 'template', opacity: 0.45, label: 'TPL' };
}

function signClass(sign: MacroTransmissionEdge['sign']): string {
	return sign === 'positive' ? 'pos' : sign === 'negative' ? 'neg' : sign === 'mixed' ? 'mix' : 'unk';
}

function pathSectorNode(
	key: string,
	sectorTailwinds: { id: string; kr: string; en: string; blended: number; tailwindKey?: string }[],
	activeIndustryId?: string
): MacroPathSectorNode {
	const map = EDGE_SECTOR_TO_TAILWIND[key] ?? { industryId: null, tailwindKey: null, kr: key, en: key };
	const tw = map.tailwindKey ? sectorTailwinds.find((row) => row.tailwindKey === map.tailwindKey || row.id === map.industryId) : null;
	const cls = tw ? classifyTailwind(tw.blended) : null;
	return {
		key,
		labelKr: map.kr,
		labelEn: map.en,
		industryId: map.industryId,
		tailwindKey: map.tailwindKey,
		blended: tw?.blended ?? null,
		tailwindLabelKr: cls?.labelKr ?? 'tailwind 미산출',
		tailwindLabelEn: cls?.labelEn ?? 'tailwind missing',
		tone: cls?.tone ?? 'neutral',
		missingTailwind: !tw,
		active: !!activeIndustryId && map.industryId === activeIndustryId
	};
}

export function buildMacroPath(
	transmission: MacroTransmissionPayload | null | undefined,
	sectorTailwinds: { id: string; kr: string; en: string; blended: number; tailwindKey?: string }[],
	opts: { activeIndustryId?: string; mode?: 'compact' | 'full'; lang?: Lang } = {}
): MacroPathView {
	const lang = opts.lang ?? 'kr';
	const L = makeL(lang);
	// 경로 driver 라벨 · 전파 payload driver 는 labelKr 만 보유. EN 은 MACRO_SERIES 정의 EN 라벨로 보강.
	const driverLabelOf = (id: string, payloadLabelKr?: string): string =>
		lang === 'en' ? (macroDefOf(id)?.en || payloadLabelKr || id) : (payloadLabelKr || id);
	const mode = opts.mode ?? 'compact';
	const missing: MacroMissingView[] = [];
	if (!transmission?.edges?.length) {
		missing.push({ id: 'macro-path', status: 'missing', reason: 'macro.transmission edges unavailable', sourceRef: 'dashboards/macro.json#transmission' });
	}
	const driverById = new Map((transmission?.drivers ?? []).map((driver) => [driver.id, driver]));
	const sectorByKey = new Map<string, MacroPathSectorNode>();
	const links: MacroPathLinkView[] = [];
	const allSectorLinks: MacroPathLinkView[] = [];
	for (const edge of transmission?.edges ?? []) {
		const style = evidenceStyle(edge);
		const blocked = edge.confidence === 'blocked';
		const sectors = (edge.sectorKeys?.length ? edge.sectorKeys : ['unknown']);
		const allSector = sectors.length === 1 && sectors[0] === 'all';
		const sectorNodes = allSector
			? [pathSectorNode('all', sectorTailwinds, opts.activeIndustryId)]
			: sectors.map((key) => pathSectorNode(key, sectorTailwinds, opts.activeIndustryId));
		for (const node of sectorNodes) sectorByKey.set(node.key, node);
		const driver = driverById.get(edge.driverId);
		const channelLabel = CHANNEL_LABELS[edge.channel];
		const view: MacroPathLinkView = {
			id: edge.id,
			driverId: edge.driverId,
			driverLabel: driverLabelOf(edge.driverId, driver?.labelKr),
			channel: edge.channel,
			channelLabelKr: channelLabel?.kr ?? edge.channel,
			channelLabelEn: channelLabel?.en ?? edge.channel,
			sectorKeys: sectors,
			sectorNodes,
			market: edge.market,
			sign: edge.sign,
			signLabel: edge.sign === 'positive' ? '+' : edge.sign === 'negative' ? '-' : edge.sign === 'mixed' ? '±' : '?',
			evidenceLevel: edge.evidenceLevel,
			evidenceLabel: style.label,
			confidence: edge.confidence,
			styleClass: blocked ? 'blocked' : style.styleClass,
			signClass: blocked ? 'blocked' : signClass(edge.sign),
			opacity: blocked ? 0.3 : style.opacity,
			financialLine: trText(edge.financialLine, lang, TR_FINLINE_EN),
			valuationLever: edge.valuationLever,
			lagLabel: normalizeLag(edge.lagMonths) ? `${normalizeLag(edge.lagMonths)![0]}-${normalizeLag(edge.lagMonths)![1]}M` : '·',
			note: noteFromTransmission(edge, L, lang),
			sourceRefs: edge.sourceRefs?.length ? edge.sourceRefs : [edge.sourceRef ?? `macro.transmission:edge:${edge.id}`],
			active: sectorNodes.some((node) => node.active),
			allSector
		};
		if (allSector) allSectorLinks.push(view);
		else links.push(view);
	}
	const sortedSectors = [...sectorByKey.values()].sort((a, b) => {
		if (a.key === 'all') return 1;
		if (b.key === 'all') return -1;
		if (a.blended == null && b.blended == null) return a.labelKr.localeCompare(b.labelKr);
		if (a.blended == null) return 1;
		if (b.blended == null) return -1;
		return b.blended - a.blended;
	});
	const negative = hasNegativeTailwind(sectorTailwinds);
	return {
		asOf: transmission?.asOf ?? null,
		mode,
		driverNodes: (transmission?.drivers ?? []).map((d) => ({
			id: d.id,
			label: driverLabelOf(d.id, d.labelKr),
			market: d.market,
			freshnessStatus: d.sourceLineage?.status ?? 'unknown'
		})),
		channelNodes: Object.entries(CHANNEL_LABELS).map(([id, label]) => ({ id: id as MacroChannel, labelKr: label.kr, labelEn: label.en })),
		sectorNodes: sortedSectors,
		links,
		allSectorLinks,
		missing: [...missing, ...((transmission?.missing ?? []) as MacroMissingView[])],
		coverageKeys: [...CURRENT_MACRO_EDGE_SECTOR_KEYS],
		hasNegativeTailwind: negative,
		captionKr: negative ? '음수 blended 섹터만 역풍으로 표시' : '전 섹터 약순풍 - 절대 역풍 없음',
		captionEn: negative ? 'Only negative blended sectors are headwind' : 'All sectors weak-positive - no absolute headwind'
	};
}

export function buildMacroGlanceView(
	macro: MacroFile | null,
	sectorTailwinds: { id: string; kr: string; en: string; blended: number; tailwindKey?: string }[],
	opts: { activeIndustryId?: string; mode?: 'compact' | 'full'; transmission?: MacroTransmissionPayload | null; lang?: Lang } = {}
): MacroGlanceView {
	return {
		asOf: macro?.asOf ?? null,
		regime: buildRegimeQuadrant(macro),
		path: buildMacroPath(opts.transmission ?? macro?.transmission ?? null, sectorTailwinds, opts),
		sectorTailwinds
	};
}

function toneFromValue(v: number | null, goodHigh = true): Tone {
	if (v == null) return 'neutral';
	if (goodHigh) return v >= 10 ? 'up' : v >= 3 ? 'good' : v >= 0 ? 'neutral' : 'warn';
	return v <= 80 ? 'up' : v <= 150 ? 'good' : v <= 250 ? 'warn' : 'down';
}

function buildCheckpoints(co: Company, L: LFn): MacroCheckpointView[] {
	const f = co.fundamentals;
	const cf = co.financials.cf;
	const fcf = cf.fcf;
	return [
		{
			id: 'sector',
			label: L('섹터 전파', 'Sector transmission'),
			value: co.tailwind ? `${L(co.tailwind.label, co.tailwind.labelEn)} ${co.tailwind.blended.toFixed(2)}` : '·',
			tone: co.tailwind?.tone ?? 'neutral',
			reason: L('현재 macro sectorTailwind와 선택 업종의 방향', 'Direction of the current macro sectorTailwind and the selected industry'),
			source: 'macro.sectorTailwind'
		},
		{
			id: 'margin',
			label: L('마진 흡수력', 'Margin absorption'),
			value: f.opm == null ? '·' : `${f.opm.toFixed(1)}%`,
			tone: toneFromValue(f.opm),
			reason: L('원가·환율 충격이 영업이익률에 흡수되는지 보는 1차 checkpoint', 'First checkpoint for whether cost and FX shocks are absorbed into the operating margin'),
			source: 'company.fundamentals.opm'
		},
		{
			id: 'debt',
			label: L('금리 민감도', 'Rate sensitivity'),
			value: f.dr == null ? '·' : `${f.dr.toFixed(0)}%`,
			tone: toneFromValue(f.dr, false),
			reason: L('금리와 신용스프레드 충격이 이자비용·재조달로 닿는 경로', 'The path by which rate and credit-spread shocks reach interest expense and refinancing'),
			source: 'company.fundamentals.dr'
		},
		{
			id: 'cashFlow',
			label: L('현금흐름 흡수', 'Cash-flow absorption'),
			value: fcf == null ? '·' : `${fcf.toFixed(2)}${L('조', 'tn')}`,
			tone: fcf == null ? 'neutral' : fcf > 0 ? 'good' : 'warn',
			reason: L('마진·수요 충격이 실제 현금흐름을 잠식하는지 확인', 'Whether margin and demand shocks erode actual cash flow'),
			source: 'company.financials.cf.fcf'
		},
		{
			id: 'valuation',
			label: L('밸류 lever', 'Valuation lever'),
			value: co.valuation?.per == null ? '·' : `PER ${co.valuation.per.toFixed(1)}x`,
			tone: 'neutral',
			reason: L('금리·성장률·마진 충격이 multiple 또는 할인율로 번역되는 위치', 'Where rate, growth, and margin shocks translate into the multiple or discount rate'),
			source: 'company.valuation'
		}
	];
}

// MACRO_SERIES def.group(한국어 SSOT) → EN. driver 표 group 라벨 EN 패리티(payload group 영어enum 은 override 제거됨).
const GROUP_EN: Record<string, string> = {
	'경기·심리': 'Cycle/Sentiment', '미국고용·생산': 'US Employment/Output', '미국금리': 'US Rates',
	'미국물가': 'US Inflation', '미국신용': 'US Credit', '미국증시': 'US Equities', '부동산': 'Real Estate',
	'생산자물가': 'Producer Prices', '수출': 'Exports', '원자재': 'Commodities', '통화': 'Money',
	'한국금리': 'KR Rates', '한국물가': 'KR Inflation', '한국생산': 'KR Output', '환율': 'FX'
};
const UNIT_EN: Record<string, string> = { '원': 'KRW' };

function buildDrivers(latest: MacroLatest[], industry: string, coMovers: CoMover[], lang: Lang): MacroDriverView[] {
	const L = makeL(lang);
	const relevant = new Set(SECTOR_DRIVER[industry] ?? []);
	const latestById = new Map(latest.map((m) => [m.def.id, m]));
	const coById = new Map(coMovers.map((m) => [m.id, m]));
	const defs = MACRO_SERIES.filter((d) => latestById.has(d.id));
	return defs.map((def) => {
		const m = latestById.get(def.id)!;
		const meta = DRIVER_SEMANTICS[def.id] ?? { direction: { kr: '방향성 의미는 driver별 맥락과 같이 해석한다.', en: 'Direction is interpreted together with each driver’s context.' }, lag: null };
		const source: MacroDriverView['source'] = def.src === 'ecos' ? 'ECOS' : 'FRED';
		const relevance: MacroDriverView['relevance'] =
			relevant.has(def.id) ? 'primary' : CORE_DRIVER_IDS.includes(def.id) ? 'secondary' : 'context';
		const freshness = freshnessOf(def, m.d, L);
		const coMovement = coMovementOf(coById.get(def.id), L);
		const transform = transformOf(def);
		const level = pressureLevel(relevance, m, coMovement, freshness);
		return {
			id: def.id,
			label: lang === 'en' ? (def.en || def.kr) : def.kr,
			group: def.group ? (lang === 'en' ? (GROUP_EN[def.group] ?? def.group) : def.group) : L('기타', 'Other'),
			seriesId: def.id,
			unit: lang === 'en' ? (UNIT_EN[def.unit] ?? def.unit) : def.unit,
			source,
			value: fmtLatest(m),
			change: fmtChange(m),
			asOf: fmtDate(m.d),
			spark: m.spark,
			directionSemantics: L(meta.direction.kr, meta.direction.en),
			defaultLagMonths: meta.lag,
			relevance,
			pressureLevel: level,
			pressureReason: pressureReason(relevance, m, coMovement, freshness, L),
			coMovement,
			freshness,
			transform,
			sourceLineage: `${source} · obs ${fmtDate(m.d)} · ${transform} · ${freshness.label}`,
			qualityHint: qualityHintOf(relevance, coMovement, freshness, L)
		};
	}).sort((a, b) => {
		const r = { primary: 0, secondary: 1, context: 2 };
		const p = { high: 0, medium: 1, low: 2, blocked: 3 };
		const ac = a.coMovement ? Math.abs(a.coMovement.corr) : 0;
		const bc = b.coMovement ? Math.abs(b.coMovement.corr) : 0;
		return r[a.relevance] - r[b.relevance] || p[a.pressureLevel] - p[b.pressureLevel] || bc - ac || a.group.localeCompare(b.group) || a.label.localeCompare(b.label);
	});
}

function normalizeLag(lag: number[] | [number, number] | null | undefined): [number, number] | null {
	if (!lag || lag.length < 2) return null;
	const start = Number(lag[0]);
	const end = Number(lag[1]);
	return Number.isFinite(start) && Number.isFinite(end) ? [start, end] : null;
}

function transmissionLineageOf(driver: MacroTransmissionPayload['drivers'][number]): string {
	const lineage = driver.sourceLineage;
	if (!lineage) return `${driver.source} · ${driver.sourceSeriesId} · ${driver.transform}`;
	const date = lineage.date ? fmtDate(lineage.date) : '·';
	return `${lineage.source} · ${lineage.sourceSeriesId} · obs ${date} · ${driver.transform} · ${lineage.status}`;
}

function applyTransmissionDriverLineage(drivers: MacroDriverView[], payload: MacroTransmissionPayload | null | undefined, L: LFn): MacroDriverView[] {
	if (!payload?.drivers?.length) return drivers;
	const byId = new Map(payload.drivers.map((d) => [d.id, d]));
	return drivers.map((driver) => {
		const row = byId.get(driver.id);
		if (!row) return driver;
		const lineage = row.sourceLineage;
		return {
			...driver,
			source: row.source,
			seriesId: row.sourceSeriesId || driver.seriesId,
			transform: row.transform || driver.transform,
			// unit·group·directionSemantics 는 payload 가 한국어/영어enum raw 라 EN/KR 양쪽서 역누출 →
			// def 기반 양언어 해소값(driver.*)을 유지(payload 는 lineage 만 제공·series 메타는 def SSOT).
			defaultLagMonths: normalizeLag(row.defaultLagMonths)?.[1] ?? driver.defaultLagMonths,
			asOf: lineage?.date ? fmtDate(lineage.date) : driver.asOf,
			sourceLineage: transmissionLineageOf(row),
			qualityHint: lineage?.status === 'missing' ? L('차단: 거시 전파 lineage 없음', 'blocked: macro transmission lineage missing') : driver.qualityHint
		};
	});
}

function transmissionEdgeMatches(edge: MacroTransmissionEdge, sectorKey: string): boolean {
	const sectors = Array.isArray(edge.sectorKeys) ? edge.sectorKeys : [];
	return sectors.includes('all') || sectors.includes(sectorKey);
}

// 전송 페이로드(macro.json transmission)의 한국어 edge 콘텐츠 → EN. payload 는 backend bake(한국어 단일 문자열)이라
// UI-local 결정론 매핑으로 EN 모드를 해소한다. 미매핑은 원문(한국어) 유지 · EN 날조 금지(정직). 어휘는 EDGE_TEMPLATES/DRIVER_SEMANTICS EN 과 일관.
const TR_FINLINE_EN: Record<string, string> = {
	'매출 성장률 / 가동률': 'Revenue growth / utilization',
	'매출 성장률 / 환산손익': 'Revenue growth / FX translation P&L',
	'매출총이익률 / 원가율': 'Gross margin / cost ratio',
	'순이자마진 / 조달비용': 'Net interest margin / funding cost',
	'신용스프레드 / 위험프리미엄': 'Credit spread / risk premium',
	'이자비용 / 차입 재조달': 'Interest expense / debt refinancing',
	'판가 / 비용 전가': 'Selling price / cost pass-through'
};
const TR_EVIDENCE_EN: Record<string, string> = {
	'FX 손익 주석': 'FX gain/loss footnote', '가격 전가력': 'Pricing power', '규제 요금': 'Regulated tariff',
	'금리민감자산': 'Rate-sensitive assets', '단기차입금': 'Short-term borrowings', '대손비용': 'Credit-loss expense',
	'만기 구조': 'Maturity structure', '부채비율': 'Debt-to-equity ratio', '수요 탄력성': 'Demand elasticity',
	'수출 매출': 'Export revenue', '신용등급': 'Credit rating', '연료비 비중': 'Fuel cost share',
	'예대금리차': 'Loan-deposit spread', '외화 매출·매입 통화': 'FX revenue/purchase currency', '원재료 비중': 'Raw-material share',
	'이자보상배율': 'Interest coverage ratio', '재고 회전': 'Inventory turnover', '재고와 수주': 'Inventory and orders',
	'조달 구조': 'Funding structure', '주요 제품 수요': 'Key-product demand', '차입 의존도': 'Borrowing dependence',
	'차입금 만기': 'Debt maturity', '해외 매출 비중': 'Overseas revenue share', '현금 보유': 'Cash holdings'
};
const TR_FALSIFIER_EN: Record<string, string> = {
	'가격 규제로 판가 전가 불가': 'Price regulation prevents cost pass-through',
	'고정금리 장기차입 중심': 'Mostly fixed-rate long-term debt',
	'내수 매출 중심': 'Mostly domestic revenue',
	'달러 원가 비중이 해외 매출 효과를 상쇄': 'Dollar cost share offsets the overseas-revenue effect',
	'대손비용 증가가 NIM 개선을 상쇄': 'Rising credit-loss expense offsets NIM improvement',
	'무차입 또는 충분한 현금': 'Debt-free or ample cash',
	'방어적 현금흐름': 'Defensive cash flow',
	'순현금 기업': 'Net-cash company',
	'실질소득 둔화로 물량 감소': 'Real-income slowdown reduces volume',
	'에너지 매출 비중 우세': 'Energy revenue share dominates',
	'원가 전가 계약': 'Cost pass-through contracts',
	'이자수익이 비용을 상쇄': 'Interest income offsets the cost',
	'재고 과잉으로 출하 증가가 매출로 이어지지 않음': 'Excess inventory means higher shipments do not become revenue',
	'재고평가 이익': 'Inventory valuation gain',
	'정부/모회사 지원 가능성': 'Possible government/parent support',
	'조달비용이 대출금리보다 빠르게 상승': 'Funding cost rises faster than lending rates',
	'헤지 정책으로 환산 민감도 약화': 'Hedging policy weakens translation sensitivity'
};
const trText = (s: string, lang: Lang, map: Record<string, string>): string => (lang === 'en' ? (map[s] ?? s) : s);
const trList = (arr: string[] | undefined, lang: Lang, map: Record<string, string>): string[] => (arr ?? []).map((s) => trText(s, lang, map));

function noteFromTransmission(edge: MacroTransmissionEdge, L: LFn, lang: Lang): string {
	const required = edge.requiredCompanyEvidence?.length ? `${L('회사 증거', 'Company evidence')}: ${trList(edge.requiredCompanyEvidence, lang, TR_EVIDENCE_EN).slice(0, 3).join(' · ')}` : L('회사 증거 필요', 'Company evidence required');
	const falsifier = edge.falsifiers?.length ? `${L('반증', 'Falsifier')}: ${trText(edge.falsifiers[0], lang, TR_FALSIFIER_EN)}` : L('반증 조건은 source packet에서 확인', 'Falsifier conditions are confirmed in the source packet');
	return `${required}. ${falsifier}.`;
}

function buildEdgesFromTransmission(co: Company, drivers: MacroDriverView[], payload: MacroTransmissionPayload | null | undefined, L: LFn, lang: Lang): MacroTransmissionEdgeView[] {
	if (!payload?.edges?.length) return [];
	const driverById = new Map(drivers.map((d) => [d.id, d]));
	const payloadDrivers = new Map(payload.drivers.map((d) => [d.id, d]));
	const sectorLabel = (lang === 'en' ? co.sector.en : co.sector.kr) || co.industry;
	return payload.edges
		.filter((e) => transmissionEdgeMatches(e, co.industry))
		.slice(0, 12)
		.map((e) => {
			const driver = driverById.get(e.driverId);
			const payloadDriver = payloadDrivers.get(e.driverId);
			const blocked = !driver || payloadDriver?.sourceLineage?.status === 'missing';
			const sourceRefs = [
				e.sourceRef ?? `macro.transmission:edge:${e.id}`,
				...(e.sourceRefs ?? []),
				payloadDriver ? transmissionLineageOf(payloadDriver) : `driver:${e.driverId}:missing`
			];
			return {
				id: e.id,
				driverId: e.driverId,
				driverLabel: driver?.label ?? payloadDriver?.labelKr ?? e.driverId,
				market: e.market,
				sectorKey: co.industry,
				sectorLabel,
				channel: e.channel,
				financialLine: trText(e.financialLine, lang, TR_FINLINE_EN),
				valuationLever: e.valuationLever,
				sign: e.sign,
				lagMonths: normalizeLag(e.lagMonths),
				confidence: blocked ? 'blocked' : e.confidence,
				evidenceLevel: e.evidenceLevel,
				requiredCompanyEvidence: trList(e.requiredCompanyEvidence, lang, TR_EVIDENCE_EN),
				falsifiers: trList(e.falsifiers, lang, TR_FALSIFIER_EN),
				sourceRefs,
				note: blocked ? `${noteFromTransmission(e, L, lang)} ${L('최신 driver 관측 lineage가 닫혀 있어 정량 claim은 잠근다.', 'The latest driver observation lineage is closed, so quantitative claims are locked.')}` : noteFromTransmission(e, L, lang)
			};
		});
}

function buildMarketEdgesFromTransmission(drivers: MacroDriverView[], payload: MacroTransmissionPayload | null | undefined, L: LFn, lang: Lang): MacroTransmissionEdgeView[] {
	if (!payload?.edges?.length) return [];
	const driverById = new Map(drivers.map((d) => [d.id, d]));
	const payloadDrivers = new Map(payload.drivers.map((d) => [d.id, d]));
	return payload.edges.slice(0, 16).map((e) => {
		const driver = driverById.get(e.driverId);
		const payloadDriver = payloadDrivers.get(e.driverId);
		const blocked = !driver || payloadDriver?.sourceLineage?.status === 'missing';
		const sectorKeys = e.sectorKeys?.length ? e.sectorKeys : ['unknown'];
		const sectorLabels = sectorKeys.map((key) => { const map = EDGE_SECTOR_TO_TAILWIND[key]; return map ? (lang === 'en' ? map.en : map.kr) : key; });
		const sourceRefs = [
			e.sourceRef ?? `macro.transmission:edge:${e.id}`,
			...(e.sourceRefs ?? []),
			payloadDriver ? transmissionLineageOf(payloadDriver) : `driver:${e.driverId}:missing`
		];
		return {
			id: e.id,
			driverId: e.driverId,
			driverLabel: driver?.label ?? payloadDriver?.labelKr ?? e.driverId,
			market: e.market,
			sectorKey: sectorKeys[0] ?? 'unknown',
			sectorLabel: sectorLabels.join(' · '),
			channel: e.channel,
			financialLine: trText(e.financialLine, lang, TR_FINLINE_EN),
			valuationLever: e.valuationLever,
			sign: e.sign,
			lagMonths: normalizeLag(e.lagMonths),
			confidence: blocked ? 'blocked' : e.confidence,
			evidenceLevel: e.evidenceLevel,
			requiredCompanyEvidence: trList(e.requiredCompanyEvidence, lang, TR_EVIDENCE_EN),
			falsifiers: trList(e.falsifiers, lang, TR_FALSIFIER_EN),
			sourceRefs,
			note: blocked ? `${noteFromTransmission(e, L, lang)} ${L('최신 driver 관측 lineage가 닫혀 있어 정량 claim은 잠근다.', 'The latest driver observation lineage is closed, so quantitative claims are locked.')}` : noteFromTransmission(e, L, lang)
		};
	});
}

function buildEdges(co: Company, drivers: MacroDriverView[], payload: MacroTransmissionPayload | null | undefined, L: LFn, lang: Lang): MacroTransmissionEdgeView[] {
	const transmissionEdges = buildEdgesFromTransmission(co, drivers, payload, L, lang);
	if (transmissionEdges.length) return transmissionEdges;
	const driverById = new Map(drivers.map((d) => [d.id, d]));
	const sectorLabel = (lang === 'en' ? co.sector.en : co.sector.kr) || co.industry;
	const selected = EDGE_TEMPLATES
		.filter((e) => e.sectors.includes('all') || e.sectors.includes(co.industry))
		.slice(0, 8);
	return selected.map((e, i) => {
		const driver = driverById.get(e.driverId);
		const blocked = !driver;
		const note = L(e.note.kr, e.note.en);
		return {
			id: `${e.driverId}-${e.channel}-${i}`,
			driverId: e.driverId,
			driverLabel: driver?.label ?? e.driverId,
			market: e.market,
			sectorKey: co.industry,
			sectorLabel,
			channel: e.channel,
			financialLine: L(e.financialLine.kr, e.financialLine.en),
			valuationLever: e.valuationLever,
			sign: e.sign,
			lagMonths: e.lagMonths,
			confidence: blocked ? 'blocked' : e.confidence,
			evidenceLevel: e.evidenceLevel,
			requiredCompanyEvidence: e.requiredCompanyEvidence.map((x) => L(x.kr, x.en)),
			falsifiers: [],
			sourceRefs: [driver?.seriesId ?? e.driverId, blocked ? 'notWiredYet' : 'sector prior', 'company checkpoints'],
			note: blocked ? `${note} ${L('최신 시계열이 MacroPort에 없어서 전파 edge는 차단 상태로만 표시한다.', 'The latest time series is absent from MacroPort, so the transmission edge is shown only in a blocked state.')}` : note
		};
	});
}

function buildFalsifiers(coMovers: CoMover[], drivers: MacroDriverView[], macro: MacroFile | null, exposureQuality: MacroExposureQualityView, L: LFn): MacroFalsifierView[] {
	const byId = new Map(drivers.map((d) => [d.id, d]));
	const out: MacroFalsifierView[] = [];
	for (const cm of coMovers.slice(0, 5)) {
		const d = byId.get(cm.id);
		if (!d) continue;
		const signal = d.coMovement;
		const window = signal?.window ?? `${cm.n}M overlap`;
		out.push({
			id: `co-${cm.id}`,
			type: 'coMovement',
			driverId: cm.id,
			label: `${d.label} ${signal?.label ?? `corr ${cm.corr > 0 ? '+' : ''}${cm.corr.toFixed(2)}`}`,
			severity: signal?.status === 'candidate' ? 'info' : 'warning',
			detail: L(
				`최근 겹친 ${cm.n}개월(${window}) 월수익률과 거시 1차차분의 Pearson 상관. lag 안정성·회사 증거 전에는 인과나 beta로 승격하지 않는다.`,
				`Pearson correlation of monthly returns and the macro first difference over the last overlapping ${cm.n} months (${window}). Not promoted to causality or beta before lag stability and company evidence.`
			),
			sourceRef: 'terminal coMovement'
		});
	}
	for (const d of drivers.filter((x) => x.freshness.status === 'stale').slice(0, 3)) {
		out.push({
			id: `stale-${d.id}`,
			type: 'staleData',
			driverId: d.id,
			label: `${d.label} ${L('기준일 stale', 'asOf stale')}`,
			severity: 'warning',
			detail: `${d.sourceLineage}. ${L('최신 국면 해석과 전파 경로 우선순위는 낮춰서 읽는다.', 'Read the latest-regime interpretation and transmission-path priority with reduced weight.')}`,
			sourceRef: d.sourceLineage
		});
	}
	if (!out.length) out.push({
		id: 'co-missing',
		type: 'coMovement',
		label: L('동행상관 미계산', 'Co-movement not computed'),
		severity: 'warning',
		detail: L('가격 월수익률과 거시 시계열의 겹친 표본이 부족하거나 아직 차트 계산 전이다.', 'The overlap sample of monthly price returns and macro series is insufficient, or the chart has not been computed yet.'),
		sourceRef: 'terminal coMovement'
	});
	if (!macro?.asOf) out.push({
		id: 'macro-date',
		type: 'staleData',
		label: L('macro 기준일 없음', 'No macro asOf date'),
		severity: 'warning',
		detail: L('macro.asOf가 없으면 최신 국면 해석으로 단정하지 않는다.', 'Without macro.asOf, do not assert a latest-regime interpretation.'),
		sourceRef: 'dashboards/macro.json'
	});
	if (quantEvidenceOpen(exposureQuality)) {
		out.push({
			id: 'company-exposure-quality',
			type: 'quality',
			label: L('회사 노출 품질 후보', 'Company exposure quality candidate'),
			severity: 'info',
			detail: `nObs ${exposureQuality.nObs ?? '·'}, R² ${exposureQuality.rSquared ?? '·'}, ${exposureQuality.window ?? L('window 없음', 'no window')}. ${L('정량 후보지만 추천·목표가로 번역하지 않는다.', 'A quantitative candidate, but not translated into a recommendation or price target.')}`,
			sourceRef: exposureQuality.sourceRef
		});
	} else {
		out.push({
			id: 'company-evidence',
			type: 'missingCompanyEvidence',
			label: exposureQuality.status === 'blocked' ? L('회사 고유 노출 잠김', 'Company-specific exposure locked') : L('회사 고유 노출은 정성 단계', 'Company-specific exposure is at the qualitative stage'),
			severity: exposureQuality.status === 'blocked' ? 'blocker' : 'warning',
			detail: exposureQuality.blockedReason || exposureQuality.reason,
			sourceRef: exposureQuality.sourceRef
		});
	}
	return out;
}

function buildScenarios(drivers: MacroDriverView[], edges: MacroTransmissionEdgeView[], L: LFn): MacroScenarioView[] {
	const driverById = new Map(drivers.map((d) => [d.id, d]));
	const edgeByDriver = new Map(edges.map((e) => [e.driverId, e]));
	return SCENARIOS.map((s) => {
		const driver = driverById.get(s.driverId);
		const edge = edgeByDriver.get(s.driverId);
		const missing = edge?.requiredCompanyEvidence ?? s.requiredEvidence.map((x) => L(x.kr, x.en));
		const readiness: MacroScenarioView['readiness'] =
			!driver ? { status: 'blocked', reason: L('관측 드라이버가 없거나 미배선', 'driver observation missing or not wired') } :
			edge?.confidence === 'blocked' ? { status: 'blocked', reason: L('전파 edge 미배선', 'transmission edge is not wired') } :
			driver.coMovement?.status === 'candidate' ? { status: 'needsEvidence', reason: L('동행 존재 · 회사 증거·회귀 품질 대기', 'co-movement exists; company evidence and regression quality pending') } :
			{ status: 'needsEvidence', reason: L('업종 경로만 · 회사 증거 필요', 'sector path only; company evidence required') };
		return {
			id: s.id,
			driverId: s.driverId,
			shock: s.shock,
			label: L(s.label.kr, s.label.en),
			firstBreak: L(s.firstBreak.kr, s.firstBreak.en),
			expectedDirection: L(s.expectedDirection.kr, s.expectedDirection.en),
			falsifier: L(s.falsifier.kr, s.falsifier.en),
			nextSurface: L(s.nextSurface.kr, s.nextSurface.en),
			requiredEvidence: missing,
			impactedFinancialLine: edge?.financialLine ?? L(s.impactedFinancialLine.kr, s.impactedFinancialLine.en),
			valuationLever: edge?.valuationLever ?? s.valuationLever,
			readiness
		};
	}).slice(0, 5);
}

// analysis.macroExposure(finance.json) 가 한국어로 bake 하는 reason/impact → EN. label 은 macro 시계열명이라 macroDefOf().en 으로 해소.
const EXPOSURE_REASON_EN: Record<string, string> = {
	'연간 매출 성장률과 매크로 지표 변화율의 공개 품질 계약입니다.': 'Public quality contract between annual revenue growth and macro indicator change rates.',
	'회사 매출과 매크로 지표의 겹친 표본이 부족합니다.': 'Overlap sample between company revenue and macro indicators is insufficient.',
	'회사 매출과 매크로 지표의 공개 품질 계약입니다.': 'Public quality contract between company revenue and macro indicators.'
};
const EXPOSURE_IMPACT_EN: Record<string, string> = { '상승': 'Rising', '하락': 'Falling', '혼재': 'Mixed' };
// macroExposure.selected[].label 의 한국어 macro 시계열명 → EN. macroDefOf 가 못 잡는 series(MACRO_SERIES 43 id 밖)도 포함.
const EXPOSURE_SERIES_EN: Record<string, string> = {
	'WTI 유가': 'WTI crude', '구리': 'Copper', '기준금리': 'Policy rate', '기초화학PPI': 'Basic-chemicals PPI',
	'내구재 주문': 'Durable-goods orders', '미국 산업생산': 'US industrial production', '반도체PPI(한국)': 'Semiconductor PPI (KR)',
	'산업생산': 'Industrial production', '산업생산지수': 'Industrial production index', '상품수출': 'Goods exports',
	'서비스업 생산': 'Services production', '석유제품PPI': 'Petroleum-products PPI', '소비자물가': 'Consumer prices (CPI)',
	'식료품PPI': 'Food-products PPI', '아파트가격': 'Apartment prices', '원/달러': 'USD/KRW', '의약품PPI': 'Pharmaceuticals PPI',
	'자동차PPI(한국)': 'Auto PPI (KR)', '플라스틱PPI': 'Plastics PPI', '하이일드 스프레드': 'High-yield spread'
};

function normalizeExposureQuality(q: MacroExposureQualityPayload | undefined | null, code: string, L: LFn): MacroExposureQualityView | null {
	if (!q) return null;
	const status: MacroExposureQualityView['status'] =
		q.status === 'quantCandidate' || q.status === 'qualitativeOnly' || q.status === 'blocked'
			? q.status
			: 'blocked';
	return {
		method: q.method ?? null,
		modelVersion: q.modelVersion ?? null,
		targetMetric: q.targetMetric ?? null,
		minObs: typeof q.minObs === 'number' ? q.minObs : null,
		status,
		reason: q.reason ? L(q.reason, EXPOSURE_REASON_EN[q.reason] ?? q.reason) : L('회사 매출과 매크로 지표의 공개 품질 계약입니다.', 'Public quality contract between company revenue and macro indicators.'),
		blockedReason: q.blockedReason || (status === 'quantCandidate' ? '' : L('품질 게이트 닫힘', 'quality gate closed')),
		missingEvidence: Array.isArray(q.missingEvidence) ? q.missingEvidence : [],
		sourceRef: q.sourceRef || `analysis.macroExposure:${code}`,
		nObs: typeof q.nObs === 'number' ? q.nObs : null,
		rSquared: typeof q.rSquared === 'number' ? q.rSquared : null,
		window: q.window ?? null,
		frequency: q.frequency ?? null,
		lagMonths: typeof q.lagMonths === 'number' ? q.lagMonths : null,
		coverage: q.coverage ?? 'missing'
	};
}

function normalizeExposureIndicators(rows: MacroExposureIndicatorPayload[] | undefined | null, L: LFn): MacroExposureIndicatorView[] {
	if (!Array.isArray(rows)) return [];
	return rows.slice(0, 6).map((row) => ({
		method: row.method ?? null,
		modelVersion: row.modelVersion ?? null,
		targetMetric: row.targetMetric ?? null,
		minObs: typeof row.minObs === 'number' ? row.minObs : null,
		// label 은 macro 시계열명(한국어 bake) · EXPOSURE_SERIES_EN(전수) → macroDefOf().en 순으로 EN 해소(미상이면 원문 유지).
		label: L(row.label || row.seriesId, EXPOSURE_SERIES_EN[row.label ?? ''] || macroDefOf(row.seriesId)?.en || row.label || row.seriesId),
		seriesId: row.seriesId,
		axis: row.axis || 'macro',
		rSquared: typeof row.rSquared === 'number' ? row.rSquared : null,
		nObs: typeof row.nObs === 'number' ? row.nObs : null,
		window: row.window ?? null,
		frequency: row.frequency ?? null,
		lagMonths: typeof row.lagMonths === 'number' ? row.lagMonths : null,
		coverage: row.coverage ?? 'missing',
		sourceRef: row.sourceRef,
		sourceRefs: Array.isArray(row.sourceRefs) ? row.sourceRefs : [],
		latestChange: typeof row.latestChange === 'number' ? row.latestChange : null,
		impact: row.impact ? L(row.impact, EXPOSURE_IMPACT_EN[row.impact] ?? row.impact) : '·'
	}));
}

function buildExposureQuality(co: Company, L: LFn): MacroExposureQualityView {
	const actual = normalizeExposureQuality(co.macroExposure?.exposureQuality, co.code, L);
	if (actual) return actual;
	return {
		method: null,
		modelVersion: null,
		targetMetric: null,
		minObs: null,
		status: 'qualitativeOnly',
		reason: L('회사별 회귀/민감도는 nObs/R²/window/lag/coverage 공개 계약 전까지 정성 경로만 표시', 'Per-company regression/sensitivity shows only the qualitative path until the nObs/R²/window/lag/coverage public contract.'),
		blockedReason: L('nObs/R²/window/lag/coverage/sourceRef 공개 계약 전', 'Before the nObs/R²/window/lag/coverage/sourceRef public contract'),
		missingEvidence: ['nObs', 'R²', 'window', 'lag', 'company exposure sourceRef'],
		sourceRef: 'analysis.macroExposure pending',
		nObs: null,
		rSquared: null,
		window: null,
		frequency: null,
		lagMonths: null,
		coverage: 'sectorOnly'
	};
}

function buildMissing(args: { macro: MacroFile | null; macroLatest: MacroLatest[]; edges: MacroTransmissionEdgeView[]; coMovers: CoMover[]; transmission?: MacroTransmissionPayload | null; L: LFn }): MacroMissingView[] {
	const { L } = args;
	const out: MacroMissingView[] = [];
	if (!args.macro) out.push({ id: 'macro-json', status: 'missing', reason: L('거시 국면 artifact 없음', 'macro regime artifact unavailable'), sourceRef: 'dashboards/macro.json' });
	if (!args.macroLatest.length) out.push({ id: 'macro-latest', status: 'missing', reason: L('거시 최신 관측 없음', 'macro latest observations unavailable'), sourceRef: 'macro/{fred,ecos}/observations.parquet' });
	if (!args.transmission) out.push({ id: 'macro-transmission', status: 'notWiredYet', reason: L('macro.transmission 페이로드 부재 · UI 폴백 템플릿 사용', 'macro.transmission payload not present in macro artifact; using UI fallback templates'), sourceRef: 'dashboards/macro.json#transmission' });
	if (!args.edges.length) out.push({ id: 'transmission-edge', status: 'notWiredYet', reason: L('이 회사의 업종 전파 edge 없음', 'sector transmission edge unavailable for this company'), sourceRef: args.transmission ? 'dartlab://macro/transmission' : 'Macro Lens EDGE_TEMPLATES' });
	if (!args.coMovers.length) out.push({ id: 'co-movement', status: 'partial', reason: L('겹침 표본 부족 또는 차트 동행 미계산', 'overlap sample insufficient or chart co-movement not calculated'), sourceRef: 'terminal coMovement' });
	for (const m of args.transmission?.missing ?? []) out.push(m);
	return out;
}

function buildEvidenceGates(args: {
	asOf: string | null;
	drivers: MacroDriverView[];
	topPressures: MacroDriverView[];
	edges: MacroTransmissionEdgeView[];
	exposureQuality: MacroExposureQualityView;
	edgeSourceRef: string;
}): MacroEvidenceGateView[] {
	const criticalDrivers = args.drivers.filter((d) => d.relevance === 'primary');
	const freshnessScope = criticalDrivers.length ? criticalDrivers : args.drivers.filter((d) => d.relevance !== 'context').slice(0, 5);
	const stale = freshnessScope.filter((d) => d.freshness.status === 'stale');
	const watch = freshnessScope.filter((d) => d.freshness.status === 'watch');
	const observed = args.edges.filter((e) => e.evidenceLevel === 'observed' && e.confidence !== 'blocked');
	const usableEdges = args.edges.filter((e) => e.confidence !== 'blocked');
	const pathSourceMissing = !args.edges.length || /missing|template/i.test(args.edgeSourceRef);
	const pathBlocks = pathSourceMissing
		? [args.edges.length ? 'macro.transmission source missing; fallback template is not claim evidence' : 'macro transmission edge missing']
		: args.edges.filter((e) => e.confidence === 'blocked').map((e) => `${e.driverId}: ${e.sourceRefs.join(' · ')}`);
	const pathStatus: MacroEvidenceGateView['status'] = pathSourceMissing || !usableEdges.length ? 'blocked' : observed.length ? 'ok' : 'watch';
	const candidates = args.drivers.filter((d) => d.coMovement?.status === 'candidate');
	const coWindows = candidates.map((d) => `${d.id}:${d.coMovement?.window ?? 'window?'}`);
	const companyHasEvidence = args.exposureQuality.coverage === 'company' && args.exposureQuality.nObs != null;
	const quantOpen = quantEvidenceOpen(args.exposureQuality);
	const qualityDetailKr = `nObs ${args.exposureQuality.nObs ?? '·'} · R² ${args.exposureQuality.rSquared ?? '·'} · ${args.exposureQuality.window ?? 'window 없음'}`;
	const qualityDetailEn = `nObs ${args.exposureQuality.nObs ?? '·'} · R² ${args.exposureQuality.rSquared ?? '·'} · ${args.exposureQuality.window ?? 'no window'}`;
	const companyBlocks = companyHasEvidence ? [] : (args.exposureQuality.missingEvidence.length ? args.exposureQuality.missingEvidence : [`coverage ${args.exposureQuality.coverage}`, 'company sample absent']);
	const quantBlocks = quantOpen ? [] : quantEvidenceBlocks(args.exposureQuality);
	return [
		{
			id: 'macroData',
			labelKr: '시계열',
			labelEn: 'Series',
			value: stale.length ? 'STALE' : watch.length ? 'WATCH' : 'OK',
			detailKr: args.asOf ?? 'macro 기준일 없음',
			detailEn: args.asOf ?? 'macro asOf missing',
			status: stale.length ? 'blocked' : watch.length ? 'watch' : 'ok',
			sourceRef: 'dashboards/macro.json + macro observations',
			blocks: stale.map((d) => `${d.id}: ${d.freshness.label}`)
		},
		{
			id: 'path',
			labelKr: '경로',
			labelEn: 'Path',
			value: pathStatus === 'blocked' ? 'LOCK' : `${observed.length}/${args.edges.length}`,
			detailKr: pathSourceMissing ? '전파 source 결손' : observed.length ? '관측 edge' : '섹터 prior/template',
			detailEn: pathSourceMissing ? 'transmission source missing' : observed.length ? 'observed edges' : 'sector prior/template',
			status: pathStatus,
			sourceRef: args.edgeSourceRef,
			blocks: pathBlocks
		},
		{
			id: 'comove',
			labelKr: '동행',
			labelEn: 'Co-move',
			value: candidates.length ? `${candidates.length}` : 'LOW',
			detailKr: candidates.length ? coWindows.join(', ') : '인과 아님',
			detailEn: candidates.length ? coWindows.join(', ') : 'not causal',
			status: candidates.length ? 'watch' : 'blocked',
			sourceRef: 'terminal coMovement',
			blocks: candidates.length ? [] : ['corr/n/window candidate absent']
		},
		{
			id: 'company',
			labelKr: '회사노출',
			labelEn: 'Company',
			value: companyHasEvidence ? 'OBS' : args.exposureQuality.coverage === 'sectorOnly' ? 'PRIOR' : 'LOCK',
			detailKr: companyHasEvidence ? qualityDetailKr : '회사 표본 없음',
			detailEn: companyHasEvidence ? qualityDetailEn : 'company sample absent',
			status: companyHasEvidence ? (quantOpen ? 'ok' : 'watch') : 'blocked',
			sourceRef: args.exposureQuality.sourceRef,
			blocks: companyBlocks
		},
		{
			id: 'quant',
			labelKr: '민감도',
			labelEn: 'Beta',
			value: quantOpen ? 'OPEN' : 'LOCK',
			detailKr: quantOpen ? qualityDetailKr : (args.exposureQuality.blockedReason || 'quality gate closed'),
			detailEn: quantOpen ? qualityDetailEn : (args.exposureQuality.blockedReason || 'quality gate closed'),
			status: quantOpen ? 'ok' : 'blocked',
			sourceRef: args.exposureQuality.sourceRef,
			blocks: quantBlocks
		}
	];
}

function buildReleaseRail(drivers: MacroDriverView[]): MacroReleaseView[] {
	return drivers.slice(0, 10).map((driver) => {
		const def = macroDefOf(driver.id);
		const staleAfterDays = def ? staleAfterDaysOf(def) : 75;
		const cadenceDays = def ? cadenceDaysOf(def) : 35;
		return {
			driverId: driver.id,
			label: driver.label,
			source: driver.source,
			frequency: def ? frequencyOf(def) : 'unknown frequency',
			lastObservation: driver.asOf,
			nextCheck: addDaysYmd(driver.asOf.replaceAll('-', ''), cadenceDays),
			daysLag: driver.freshness.daysLag,
			staleAfterDays,
			status: driver.freshness.status,
			sourceRef: `${driver.source}:${driver.seriesId}:freshness-policy`
		};
	});
}

function buildSourcePackets(drivers: MacroDriverView[], payload?: MacroTransmissionPayload | null): MacroSourcePacketView[] {
	const payloadDrivers = new Map((payload?.drivers ?? []).map((d) => [d.id, d]));
	return drivers.slice(0, 16).map((driver) => {
		const def = macroDefOf(driver.id);
		const row = payloadDrivers.get(driver.id);
		const lineage = row?.sourceLineage;
		const artifactPath = lineage?.artifactPath || `macro/${driver.source === 'ECOS' ? 'ecos' : 'fred'}/observations.parquet`;
		const status = lineage?.status === 'missing' ? 'missing' : driver.freshness.status;
		return {
			driverId: driver.id,
			label: driver.label,
			seriesId: driver.seriesId,
			source: driver.source,
			unit: driver.unit,
			frequency: def ? frequencyOf(def) : 'unknown frequency',
			asOf: lineage?.date ? fmtDate(lineage.date) : driver.asOf,
			value: driver.value,
			change: driver.change,
			transform: driver.transform,
			status,
			artifactPath,
			sourceRef: `${artifactPath}#${driver.seriesId}`,
			lineage: driver.sourceLineage,
			qualityHint: driver.qualityHint
		};
	});
}

function buildContributionStacks(
	drivers: MacroDriverView[],
	edges: MacroTransmissionEdgeView[],
	latest: MacroLatest[],
	exposureQuality: MacroExposureQualityView,
	L: LFn
): MacroContributionView[] {
	const latestById = new Map(latest.map((m) => [m.def.id, m]));
	return drivers.slice(0, 10).map((driver) => {
		const macroLatest = latestById.get(driver.id);
		const edge = edges.find((e) => e.driverId === driver.id);
		const move = macroLatest ? Math.min(1, changeIntensity(macroLatest) / 24) : 0;
		const path = confidenceScore(edge);
		const co = driver.coMovement ? Math.min(1, Math.abs(driver.coMovement.corr)) : 0;
		const fresh = freshnessScore(driver.freshness.status);
		const company = exposureQualityScore(exposureQuality);
		const components: MacroContributionComponentView[] = [
			{
				id: 'move',
				label: L('최근 변화', 'Recent change'),
				value: move,
				detail: macroLatest ? `${driver.change} · ${driver.asOf}` : 'latest observation missing',
				status: componentStatus(move),
				sourceRef: driver.sourceLineage
			},
			{
				id: 'path',
				label: L('전파 경로', 'Transmission path'),
				value: path,
				detail: edge ? `${edge.evidenceLevel} · ${edge.confidence} · ${edge.channel}` : 'mapped edge absent',
				status: componentStatus(path),
				sourceRef: edge?.sourceRefs[0] ?? 'macro.transmission edge missing'
			},
			{
				id: 'comove',
				label: L('동행 후보', 'Co-movement candidate'),
				value: co,
				detail: driver.coMovement?.label ?? 'co-movement absent',
				status: driver.coMovement?.status === 'candidate' ? 'ok' : driver.coMovement ? 'watch' : 'blocked',
				sourceRef: 'terminal coMovement'
			},
			{
				id: 'freshness',
				label: L('신선도', 'Freshness'),
				value: fresh,
				detail: driver.freshness.label,
				status: componentStatus(fresh),
				sourceRef: `${driver.source}:${driver.seriesId}:freshness-policy`
			},
			{
				id: 'company',
				label: L('회사 품질', 'Company quality'),
				value: company,
				detail: `${exposureQuality.status} · nObs ${exposureQuality.nObs ?? '·'} · R² ${exposureQuality.rSquared ?? '·'}`,
				status: componentStatus(company),
				sourceRef: exposureQuality.sourceRef
			}
		];
		const open = components.filter((c) => c.status === 'ok').length;
		const watch = components.filter((c) => c.status === 'watch').length;
		return {
			driverId: driver.id,
			label: driver.label,
			summary: `${open} open · ${watch} watch · ${components.length - open - watch} locked`,
			components,
			sourceRef: `MacroLens:contributionStack:${driver.id}`
		};
	});
}

function buildCoMoveGates(drivers: MacroDriverView[], coMovers: CoMover[], L: LFn): MacroCoMoveGateView[] {
	const coById = new Map(coMovers.map((m) => [m.id, m]));
	return drivers
		.filter((driver) => driver.relevance !== 'context')
		.slice(0, 10)
		.map((driver) => {
			const cm = coById.get(driver.id);
			const scatter = buildCoMoveScatter(cm, L);
			return {
				driverId: driver.id,
				label: driver.label,
				corr: driver.coMovement?.corr ?? null,
				n: driver.coMovement?.n ?? null,
				window: driver.coMovement?.window ?? 'overlap missing',
				status: driver.coMovement?.status ?? 'missing',
				sourceRef: 'terminal coMovement',
				detail: driver.coMovement
					? `${driver.coMovement.label}. ${L('각 점은 월별 macro 1차차분(x)과 종목 월수익률(y)이다. 방향성 claim이나 beta가 아니라 동행 후보 gate다.', 'Each point is the monthly macro first difference (x) and the stock monthly return (y). It is a co-movement candidate gate, not a directional claim or beta.')}`
					: L('가격과 macro observation의 겹친 표본이 부족하다.', 'The overlap sample of price and macro observations is insufficient.'),
				...scatter
			};
		});
}

export function buildMacroLensSnapshot(args: {
	co: Company;
	macro: MacroFile | null;
	transmission?: MacroTransmissionPayload | null;
	macroLatest: MacroLatest[];
	sectorTailwinds: { id: string; kr: string; en: string; blended: number; tailwindKey?: string }[];
	coMovers: CoMover[];
	lang?: Lang;
}): MacroLensSnapshot {
	const { co, macro, transmission = macro?.transmission ?? null, macroLatest, sectorTailwinds, coMovers } = args;
	const lang = args.lang ?? 'kr';
	const L = makeL(lang);
	const drivers = applyTransmissionDriverLineage(buildDrivers(macroLatest, co.industry, coMovers, lang), transmission, L);
	const priorityRank = { high: 0, medium: 1, low: 2, blocked: 3 };
	const topPressures = [...drivers]
		.filter((d) => d.relevance !== 'context' && d.pressureLevel !== 'blocked')
		.sort((a, b) => priorityRank[a.pressureLevel] - priorityRank[b.pressureLevel])
		.slice(0, 3);
	const edges = buildEdges(co, drivers, transmission, L, lang);
	const checkpoints = buildCheckpoints(co, L);
	const scenarios = buildScenarios(drivers, edges, L);
	const exposureQuality = buildExposureQuality(co, L);
	const exposureIndicators = normalizeExposureIndicators(co.macroExposure?.selected, L);
	const releaseRail = buildReleaseRail(drivers);
	const sourcePackets = buildSourcePackets(drivers, transmission);
	const contributionStacks = buildContributionStacks(drivers, edges, macroLatest, exposureQuality, L);
	const coMoveGates = buildCoMoveGates(drivers, coMovers, L);
	const falsifiers = buildFalsifiers(coMovers, drivers, macro, exposureQuality, L);
	const marketPhase = {
		kr: phaseView('KR', macro?.kr, L),
		us: phaseView('US', macro?.us, L)
	};
	const missing = buildMissing({ macro, macroLatest, edges, coMovers, transmission, L });
	const edgeSourceRef = transmission ? 'dartlab://macro/transmission' : 'macro transmission edge template';
	const evidenceGates = buildEvidenceGates({ asOf: macro?.asOf ?? null, drivers, topPressures, edges, exposureQuality, edgeSourceRef });
	const financePeriod = co.trendQuarter?.periods.at(-1) ?? co.trendAnnual?.periods.at(-1) ?? null;
	// 국면 렌즈 sub-view · focusCell(초점 채널)을 view-model 차원에서 계산해 국면↔노출 다리(§6.3) 연결.
	const regimeFocus = pickFocusCell(buildExposureMatrixRows(drivers, topPressures, edges, MAP_CHANNEL_ORDER));
	const regime = buildRegimeView(macro, regimeFocus);
	return {
		asOf: {
			macro: macro?.asOf ?? null,
			price: co.price.asOf ?? null,
			finance: financePeriod
		},
		company: {
			code: co.code,
			name: lang === 'en' ? (co.name.en || co.name.kr) : co.name.kr,
			sector: { kr: co.sector.kr, en: co.sector.en },
			industry: co.industry
		},
		marketPhase,
		drivers,
		topPressures: topPressures.length ? topPressures : drivers.slice(0, 3),
		transmissionEdges: edges,
		companyCheckpoints: checkpoints,
		sectorBinding: {
			tailwind: co.tailwind,
			top: sectorTailwinds.slice(0, 4),
			bottom: sectorTailwinds.length > 4 ? sectorTailwinds.slice(-4).reverse() : []
		},
		exposureQuality,
		exposureIndicators,
		releaseRail,
		sourcePackets,
		contributionStacks,
		coMoveGates,
		evidenceGates,
		falsifiers,
		scenarios,
		sourceRefs: [
			L('출처: 한국은행 ECOS · FRED (St. Louis Fed)', 'Source: BOK ECOS · FRED (St. Louis Fed)'),
			'dashboards/macro.json',
			...(transmission?.sourceRefs ?? []),
			'macro/{fred,ecos}/observations.parquet',
			exposureQuality.sourceRef,
			'terminal Company snapshot',
			'coMovement: monthly stock return vs macro diff',
			...exposureIndicators.flatMap((x) => [x.sourceRef, ...x.sourceRefs]).filter(Boolean),
			...drivers.slice(0, 8).map((d) => `${d.id}: ${d.sourceLineage}`)
		],
		missing,
		glance: buildMacroGlanceView(macro, sectorTailwinds, { activeIndustryId: co.industry, mode: 'compact', transmission: transmission ?? macro?.transmission ?? null, lang }),
		macroPath: buildMacroPath(transmission ?? macro?.transmission, sectorTailwinds, { activeIndustryId: co.industry, mode: 'full', lang }),
		marketOnly: false,
		regime
	};
}

function marketOnlyExposureQuality(L: LFn): MacroExposureQualityView {
	return {
		method: null,
		modelVersion: null,
		targetMetric: null,
		minObs: null,
		status: 'blocked',
		reason: L('종목을 선택하면 회사 노출 checkpoint를 계산한다.', 'Select a stock to compute company exposure checkpoints.'),
		blockedReason: 'company not selected',
		missingEvidence: ['company selection'],
		sourceRef: 'terminal macro market-only',
		nObs: null,
		rSquared: null,
		window: null,
		frequency: null,
		lagMonths: null,
		coverage: 'missing'
	};
}

function marketOnlyCheckpoints(L: LFn): MacroCheckpointView[] {
	return [
		{ id: 'sector', label: L('섹터 전파', 'Sector transmission'), value: L('종목 선택 후', 'After selecting a stock'), tone: 'neutral', reason: L('회사 업종이 선택되면 해당 경로를 하이라이트한다.', 'When the company industry is selected, the relevant path is highlighted.'), source: 'company selection' },
		{ id: 'margin', label: L('마진 흡수력', 'Margin absorption'), value: 'LOCK', tone: 'neutral', reason: L('회사 재무제표 선택 전에는 계산하지 않는다.', 'Not computed before company financial statements are selected.'), source: 'company.fundamentals' },
		{ id: 'debt', label: L('금리 민감도', 'Rate sensitivity'), value: 'LOCK', tone: 'neutral', reason: L('차입·이자보상배율은 종목 선택 후 확인한다.', 'Borrowings and interest coverage are checked after selecting a stock.'), source: 'company.fundamentals' },
		{ id: 'cashFlow', label: L('현금흐름 흡수', 'Cash-flow absorption'), value: 'LOCK', tone: 'neutral', reason: L('현금흐름 checkpoint는 종목 선택 후 확인한다.', 'Cash-flow checkpoints are checked after selecting a stock.'), source: 'company.financials' }
	];
}

export function buildMarketMacroLensSnapshot(args: {
	macro: MacroFile | null;
	macroLatest: MacroLatest[];
	sectorTailwinds: { id: string; kr: string; en: string; blended: number; tailwindKey?: string }[];
	lang?: Lang;
}): MacroLensSnapshot {
	const { macro, macroLatest, sectorTailwinds } = args;
	const lang = args.lang ?? 'kr';
	const L = makeL(lang);
	const transmission = macro?.transmission ?? null;
	const drivers = applyTransmissionDriverLineage(buildDrivers(macroLatest, '', [], lang), transmission, L);
	const priorityRank = { high: 0, medium: 1, low: 2, blocked: 3 };
	const topPressures = [...drivers]
		.filter((d) => d.relevance !== 'context' && d.pressureLevel !== 'blocked')
		.sort((a, b) => priorityRank[a.pressureLevel] - priorityRank[b.pressureLevel])
		.slice(0, 3);
	const edges = buildMarketEdgesFromTransmission(drivers, transmission, L, lang);
	const exposureQuality = marketOnlyExposureQuality(L);
	const releaseRail = buildReleaseRail(drivers);
	const sourcePackets = buildSourcePackets(drivers, transmission);
	const contributionStacks = buildContributionStacks(drivers, edges, macroLatest, exposureQuality, L);
	const coMoveGates = buildCoMoveGates(drivers, [], L);
	const marketPhase = {
		kr: phaseView('KR', macro?.kr, L),
		us: phaseView('US', macro?.us, L)
	};
	const missing = buildMissing({ macro, macroLatest, edges, coMovers: [], transmission, L });
	const edgeSourceRef = transmission ? 'dartlab://macro/transmission' : 'macro transmission missing';
	const evidenceGates = buildEvidenceGates({ asOf: macro?.asOf ?? null, drivers, topPressures, edges, exposureQuality, edgeSourceRef });
	// 국면 렌즈 · market-only 는 회사 초점채널 없음(focusCell blocked/none 시 alignment null·다리 미렌더).
	const regimeFocus = pickFocusCell(buildExposureMatrixRows(drivers, topPressures, edges, MAP_CHANNEL_ORDER));
	const regime = buildRegimeView(macro, regimeFocus);
	const falsifiers = buildFalsifiers([], drivers, macro, exposureQuality, L);
	return {
		asOf: {
			macro: macro?.asOf ?? null,
			price: null,
			finance: null
		},
		company: {
			code: 'MARKET',
			name: 'Market Macro',
			sector: { kr: '종목 선택 전', en: 'before selection' },
			industry: ''
		},
		marketPhase,
		drivers,
		topPressures: topPressures.length ? topPressures : drivers.slice(0, 3),
		transmissionEdges: edges,
		companyCheckpoints: marketOnlyCheckpoints(L),
		sectorBinding: {
			tailwind: null,
			top: sectorTailwinds.slice(0, 4),
			bottom: sectorTailwinds.length > 4 ? sectorTailwinds.slice(-4).reverse() : []
		},
		exposureQuality,
		exposureIndicators: [],
		releaseRail,
		sourcePackets,
		contributionStacks,
		coMoveGates,
		evidenceGates,
		falsifiers,
		scenarios: buildScenarios(drivers, edges, L),
		sourceRefs: [
			L('출처: 한국은행 ECOS · FRED (St. Louis Fed)', 'Source: BOK ECOS · FRED (St. Louis Fed)'),
			'dashboards/macro.json',
			...(transmission?.sourceRefs ?? []),
			'macro/{fred,ecos}/observations.parquet',
			'terminal macro market-only',
			...drivers.slice(0, 8).map((d) => `${d.id}: ${d.sourceLineage}`)
		],
		missing,
		glance: buildMacroGlanceView(macro, sectorTailwinds, { mode: 'compact', lang }),
		macroPath: buildMacroPath(transmission, sectorTailwinds, { mode: 'full', lang }),
		marketOnly: true,
		regime
	};
}

export function macroDefOf(id: string): MacroSeriesDef | null {
	return MACRO_SERIES.find((s) => s.id === id) ?? null;
}

export interface MacroExposureMatrixRow {
	driver: MacroDriverView;
	cells: (MacroTransmissionEdgeView | null)[]; // length === channels.length
	filledCount: number;
}

// 닷그리드(Exposure Map) 행 = driver, 열 = channel. 빈 셀은 null로 두고 filledCount 내림차순
// 안정 정렬(입력 순서 보존) 후 cap 6. dialog에서 buildExposureRows를 대체하는 view-model 이관 함수.
export function buildExposureMatrixRows(
	drivers: MacroDriverView[],
	topPressures: MacroDriverView[],
	edges: MacroTransmissionEdgeView[],
	channels: MacroChannel[]
): MacroExposureMatrixRow[] {
	const seen = new Set<string>();
	const ranking: MacroDriverView[] = [];
	for (const d of [...topPressures, ...drivers.filter((x) => x.relevance === 'secondary')]) {
		if (seen.has(d.id)) continue;
		seen.add(d.id);
		ranking.push(d);
	}
	const rows: MacroExposureMatrixRow[] = ranking.map((driver) => {
		const cells = channels.map((ch) => edges.find((e) => e.driverId === driver.id && e.channel === ch) ?? null);
		return { driver, cells, filledCount: cells.filter(Boolean).length };
	});
	// filledCount 내림차순 안정 정렬: 입력 인덱스를 tie-break로 보존.
	return rows
		.map((row, index) => ({ row, index }))
		.sort((a, b) => b.row.filledCount - a.row.filledCount || a.index - b.index)
		.map((x) => x.row)
		.slice(0, 6);
}

const FOCUS_EVIDENCE_RANK: Record<MacroTransmissionEdgeView['evidenceLevel'], number> = {
	observed: 0,
	sectorPrior: 1,
	template: 2
};
const FOCUS_CONFIDENCE_RANK: Record<MacroTransmissionEdgeView['confidence'], number> = {
	high: 0,
	medium: 1,
	low: 2,
	blocked: 3
};
// 채널 우선순위(매출>마진>밸류>차입>현금) · enum 순서 아님(명시 배열).
const FOCUS_CHANNEL_PRIORITY: MacroChannel[] = ['revenue', 'margin', 'valuation', 'balanceSheet', 'cashFlow'];
// Exposure Map 채널 열 순서(dialog channels 와 동일·SSOT). 국면↔노출 다리(focusCell) 계산용.
const MAP_CHANNEL_ORDER: MacroChannel[] = ['revenue', 'margin', 'balanceSheet', 'cashFlow', 'valuation'];

// 초점 전파사슬 셀 선택: evidenceLevel(observed>sectorPrior>template) → confidence(high>medium>low)
// → 채널 우선순위 배열 → driverId 사전순. change·lag 길이는 의도적으로 미사용(움직임=신호 오독 차단).
// 동일 입력 → 동일 출력(결정성). 채움 셀 0개면 null.
export function pickFocusCell(
	rows: MacroExposureMatrixRow[]
): { driver: MacroDriverView; edge: MacroTransmissionEdgeView; channel: MacroChannel } | null {
	type Candidate = { driver: MacroDriverView; edge: MacroTransmissionEdgeView; channel: MacroChannel };
	const candidates: Candidate[] = [];
	for (const row of rows) {
		for (const edge of row.cells) {
			if (edge) candidates.push({ driver: row.driver, edge, channel: edge.channel });
		}
	}
	if (!candidates.length) return null;
	const channelRank = (ch: MacroChannel) => {
		const idx = FOCUS_CHANNEL_PRIORITY.indexOf(ch);
		return idx === -1 ? FOCUS_CHANNEL_PRIORITY.length : idx;
	};
	candidates.sort((a, b) =>
		FOCUS_EVIDENCE_RANK[a.edge.evidenceLevel] - FOCUS_EVIDENCE_RANK[b.edge.evidenceLevel]
		|| FOCUS_CONFIDENCE_RANK[a.edge.confidence] - FOCUS_CONFIDENCE_RANK[b.edge.confidence]
		|| channelRank(a.channel) - channelRank(b.channel)
		|| (a.edge.driverId < b.edge.driverId ? -1 : a.edge.driverId > b.edge.driverId ? 1 : 0)
	);
	return candidates[0];
}

// ───────────────────────── 국면 렌즈 view-model 헬퍼 (초강화·전부 점수 아님) ─────────────────────────

// A블록 전향 분수 · 백분율 없이 정수 분수만(progress·% 미사용). transition null → null(렌더 0).
// fraction 은 언어중립 'triggered/total' 만. '충족'/'met' 접미는 템플릿이 T() 로 붙인다(i18n).
// 재설계가 삭제 예정인 transitionLabel(`${progress}%` 방출)을 재사용하지 않는 신규 전용 함수.
export function transitionFraction(side?: MacroSide | null): { fraction: string; from: string; to: string } | null {
	const tr = side?.transition;
	if (!tr) return null;
	const triggered = tr.triggered?.length ?? 0;
	const pending = tr.pending?.length ?? 0;
	const total = triggered + pending;
	const from = tr.from || '?';
	const to = tr.to || '?';
	return { fraction: `${triggered}/${total}`, from, to };
}

// 4모델 zone 어휘 → 결정론적 공통 3단계 bucket {확장 0·경계 1·침체 2}. (§3.3 표 SSOT)
// probit moderate→0 흡수(거짓 divergence 차단). status-only/null → null(유효 아님, 제외).
// 색 정렬·서수 badge 아님 · agree/diverge 텍스트 파생에만 쓴다.
export function bucketOf(model: MacroRegimeModel | undefined | null): 0 | 1 | 2 | null {
	if (!model || model.status) return null;
	const zone = typeof model.zone === 'string' ? model.zone : null;
	const signal = typeof model.signal === 'string' ? model.signal : null;
	const cp = typeof model.contractionProb === 'number' ? model.contractionProb : null;
	// probit (4단계 zone, moderate 흡수)
	if (zone === 'low' || zone === 'moderate') return 0;
	if (zone === 'elevated') return 1;
	if (zone === 'high') return 2;
	// sahm (3단계 zone)
	if (zone === 'normal') return 0;
	if (zone === 'warning') return 1;
	if (zone === 'recession') return 2;
	// lei (범주형 signal)
	if (signal === 'expansion') return 0;
	if (signal === 'caution') return 1;
	if (signal === 'recession_warning') return 2;
	// hamilton (생 float contractionProb·null 이면 status 동반이라 위에서 컷)
	if (cp != null) {
		if (cp < 0.25) return 0;
		if (cp < 0.5) return 1;
		return 2;
	}
	return null;
}

const BUCKET_LABEL = ['확장', '경계', '침체'] as const;
const BUCKET_LABEL_EN = ['Expansion', 'Caution', 'Recession'] as const;

// agree/diverge · 점수·서수·badge 0. 불일치 모델명 동반 텍스트만. 양언어({kr,en}) 합성(템플릿 T()).
// (a) 유효(게이트 통과·bucket 존재) <2 → '교차 불가 (유효 N개)'.
// (b) ≥2 → 다수 bucket 방향 + 불일치 모델명 명시. 단 인접 bucket(0-1,1-2)은 동의(2단계 이상만 불일치).
// probit·yieldCurve 이중계상 가드는 호출부에서 yieldCurve 를 별도 표로 넣지 않음으로 보장(probit 1표).
export function agreementOf(models: { model: string; bucket: 0 | 1 | 2 | null }[]): RegimeText {
	const valid = models.filter((m) => m.bucket != null) as { model: string; bucket: 0 | 1 | 2 }[];
	if (valid.length < 2) return { kr: `교차 불가 (유효 ${valid.length}개)`, en: `cross-check N/A (${valid.length} valid)` };
	// 다수 bucket(최빈값·동률이면 더 낮은 bucket=덜 비관적).
	const counts: Record<number, number> = { 0: 0, 1: 0, 2: 0 };
	for (const v of valid) counts[v.bucket]++;
	let majority: 0 | 1 | 2 = 0;
	for (const b of [0, 1, 2] as const) if (counts[b] > counts[majority]) majority = b;
	// 동률(다른 bucket 이 majority 와 같은 표) → 더 낮은 bucket 을 택한 게 임의가 아님을 정직 표면화.
	const tie = ([0, 1, 2] as const).some((b) => b !== majority && counts[b] === counts[majority]);
	const tieKr = tie ? ' · 동률·덜 비관적 채택' : '';
	const tieEn = tie ? ' · tie · less-pessimistic chosen' : '';
	// 다수에서 2단계 이상 벌어진 모델만 불일치(인접 동의).
	const disagreeing = valid.filter((v) => Math.abs(v.bucket - majority) >= 2);
	if (!disagreeing.length) {
		return {
			kr: `동의 · ${BUCKET_LABEL[majority]} 방향 ${valid.length}모델 일치(인접 bucket 포함)${tieKr}`,
			en: `agree · ${BUCKET_LABEL_EN[majority]} direction across ${valid.length} models (adjacent buckets incl.)${tieEn}`
		};
	}
	const namesKr = disagreeing.map((v) => `${v.model} ${BUCKET_LABEL[v.bucket]}`).join(' · ');
	const namesEn = disagreeing.map((v) => `${v.model} ${BUCKET_LABEL_EN[v.bucket]}`).join(' · ');
	return {
		kr: `동의 낮음 · 다수 ${BUCKET_LABEL[majority]} vs ${namesKr}`,
		en: `low agreement · majority ${BUCKET_LABEL_EN[majority]} vs ${namesEn}`
	};
}

// 국면축(quadrant 방향) ↔ 종목 노출축(C블록 초점채널) 다리 · 라벨만(점수·판정·민감도 0).
// 정합/역방향 *서술*만. '수혜/유리' 확정·민감도 숫자·매수 시사 0. quadrant·focusCell 부재 → null.
export function focusChannelAlignment(
	quadrant: { growth?: string; inflation?: string } | undefined | null,
	focusCell: { channel: MacroChannel; edge: { sign: MacroTransmissionEdgeView['sign'] } } | undefined | null
): RegimeText | null {
	if (!quadrant || !focusCell) return null;
	const growth = quadrant.growth;
	if (growth !== 'rising' && growth !== 'falling') return null;
	const growthArrowKr = growth === 'rising' ? '성장↑' : '성장↓';
	const growthArrowEn = growth === 'rising' ? 'growth↑' : 'growth↓';
	const channelLabelKr = CHANNEL_LABELS[focusCell.channel]?.kr ?? focusCell.channel;
	const channelLabelEn = CHANNEL_LABELS[focusCell.channel]?.en ?? focusCell.channel;
	const channelUpper = focusCell.channel.toUpperCase();
	// edge.sign positive = 국면 성장방향과 같이 움직임, negative = 반대. mixed/unknown → 방향 불명.
	const sign = focusCell.edge.sign;
	if (sign === 'positive') {
		return {
			kr: `초점채널 ${channelUpper}(${channelLabelKr}) 방향 정합 · 현 국면(${growthArrowKr})과 같은 방향`,
			en: `focus channel ${channelUpper}(${channelLabelEn}) aligned · same direction as regime (${growthArrowEn})`
		};
	}
	if (sign === 'negative') {
		return {
			kr: `초점채널 ${channelUpper}(${channelLabelKr}) 역방향 · 현 국면(${growthArrowKr})과 반대`,
			en: `focus channel ${channelUpper}(${channelLabelEn}) opposite · against regime (${growthArrowEn})`
		};
	}
	return {
		kr: `초점채널 ${channelUpper}(${channelLabelKr}) 방향 혼재 · 현 국면(${growthArrowKr}) 정합 불명`,
		en: `focus channel ${channelUpper}(${channelLabelEn}) mixed · alignment with regime (${growthArrowEn}) unclear`
	};
}

// ── 국면 렌즈 sub-view 조립 (얇은 매핑·파생 계산 0) ──
const REGIME_MODEL_NAME: Record<string, string> = { probit: 'probit', sahm: 'Sahm', lei: 'LEI', hamilton: 'Hamilton' };
const REGIME_SCALE: Record<string, RegimeText> = {
	probit: { kr: '확률·T10Y3M', en: 'prob·T10Y3M' },
	sahm: { kr: '%p·UNRATE', en: '%p·UNRATE' },
	lei: { kr: '%YoY·CBLEI', en: '%YoY·CBLEI' },
	hamilton: { kr: '확률·GDP', en: 'prob·GDP' }
};
// backend(macro.json regime) 가 한국어로 bake 하는 유한 enum 의 EN 라벨 · 결정론 매핑(타일 face EN 패리티).
const ZONE_EN: Record<string, string> = { low: 'Low', moderate: 'Moderate', elevated: 'Elevated', high: 'High', normal: 'Normal', warning: 'Warning', recession: 'Recession' };
const SIGNAL_EN: Record<string, string> = { expansion: 'Expansion', caution: 'Caution', recession_warning: 'Recession warning' };
// horizon/timeKind 토큰 중 한국어만 EN 으로(나머지는 이미 영문 · pass-through).
const REGIME_TOKEN_EN: Record<string, string> = { '동행': 'coincident', 'trigger(동행)': 'trigger(coincident)', '선행': 'leading', '회고': 'retrospective' };
const regimeTokenEn = (t: string): string => REGIME_TOKEN_EN[t] ?? t;
// status-only 사유 · 알려진 backend 문자열의 EN(미상이면 KR pass-through, suppressed dim 메타라 영향 작음).
const REGIME_STATUS_EN: Record<string, string> = {
	'EM 미수렴': 'EM not converged', '데이터 없음': 'no data', '표시 보류': 'suppressed',
	'단위 parity 미확정·표시 보류': 'unit parity unconfirmed · suppressed', '표본 부족·표시 보류': 'insufficient sample · suppressed'
};
const regimeStatusEn = (s: string): string => REGIME_STATUS_EN[s] ?? s;

function regimeStale(asOf: string | undefined, staleAfterDays: number | undefined): { stale: boolean; label: string | null } {
	const lag = daysLag((asOf || '').replaceAll('-', ''));
	if (lag == null || staleAfterDays == null) return { stale: false, label: null };
	if (lag > staleAfterDays) return { stale: true, label: `STALE ${lag}d` };
	return { stale: false, label: null };
}

function buildRegimeTile(id: 'probit' | 'sahm' | 'lei' | 'hamilton', model: MacroRegimeModel | undefined): RegimeTileView {
	const modelName = REGIME_MODEL_NAME[id] ?? id;
	const scaleLabel = REGIME_SCALE[id] ?? { kr: '', en: '' };
	const horizon = typeof model?.horizon === 'string' ? model.horizon : '';
	const timeKind = typeof model?.timeKind === 'string' ? model.timeKind : '';
	const horizonLabel: RegimeText = {
		kr: [horizon, timeKind].filter(Boolean).join('·') || '·',
		en: [horizon, timeKind].filter(Boolean).map(regimeTokenEn).join('·') || '·'
	};
	const asOf = typeof model?.asOf === 'string' ? model.asOf : null;
	const fresh = regimeStale(model?.asOf, model?.staleAfterDays);
	if (!model || model.status) {
		const statusKr = model?.status ?? '데이터 없음';
		return {
			model: id, modelName, zoneLabel: { kr: '표시 보류', en: 'suppressed' }, secondary: null, gaugeValue: null, bucket: null,
			horizonLabel, scaleLabel, asOf, stale: fresh.stale, staleLabel: fresh.label,
			suppressed: true, statusText: { kr: statusKr, en: regimeStatusEn(statusKr) },
			note: { kr: statusKr, en: regimeStatusEn(statusKr) }
		};
	}
	// 주역 라벨 = 모델별 상태 라벨(kr=backend bake, en=enum 결정론 매핑).
	const zone = typeof model.zone === 'string' ? model.zone : null;
	const signal = typeof model.signal === 'string' ? model.signal : null;
	const zoneKr = typeof model.zoneLabel === 'string' ? model.zoneLabel
		: typeof model.signalLabel === 'string' ? model.signalLabel
		: typeof model.contractionProb === 'number' ? `수축 ${Math.round(model.contractionProb * 100)}%`
		: '·';
	const zoneEn = (zone && ZONE_EN[zone]) || (signal && SIGNAL_EN[signal])
		|| (typeof model.contractionProb === 'number' ? `contraction ${Math.round(model.contractionProb * 100)}%` : null)
		|| zoneKr;
	const zoneLabel: RegimeText = { kr: zoneKr, en: zoneEn };
	let secondary: string | null = null;
	let note: RegimeText = { kr: '', en: '' };
	// 게이지 기하 입력 · probit=원확률(0~1), hamilton=수축확률. 확률 아닌 모델은 null(아크/링 미렌더).
	const gaugeValue: number | null = id === 'probit'
		? (typeof model.probability === 'number' ? model.probability : typeof model.probabilityRounded === 'number' ? model.probabilityRounded : null)
		: id === 'hamilton' && typeof model.contractionProb === 'number' ? model.contractionProb
		: null;
	if (id === 'probit') {
		const pr = typeof model.probabilityRounded === 'number' ? model.probabilityRounded : null;
		secondary = pr != null ? `~${Math.round(pr * 100)}%` : null;
		note = {
			kr: typeof model.precisionNote === 'string' ? model.precisionNote : 'Estrella-Mishkin 고정계수·표준오차 미산출(점추정)',
			en: 'Estrella-Mishkin fixed coefficients · no standard error (point estimate)'
		};
	} else if (id === 'lei') {
		note = {
			kr: typeof model.overlapNote === 'string' ? model.overlapNote : 'term-spread·initial-claims 내포(probit/Sahm 부분 상관)',
			en: 'embeds term-spread·initial-claims (partial correlation with probit/Sahm)'
		};
	} else if (id === 'hamilton') {
		note = { kr: '회고적 regime·smoothed', en: 'retrospective regime · smoothed' };
	} else if (id === 'sahm') {
		const v = typeof model.value === 'number' ? model.value : null;
		secondary = v != null ? `${v.toFixed(2)}%p` : null;
		note = { kr: '실시간 침체 시작 트리거(동행)', en: 'real-time recession-start trigger (coincident)' };
	}
	return {
		model: id, modelName, zoneLabel, secondary, gaugeValue, bucket: bucketOf(model),
		horizonLabel, scaleLabel, asOf, stale: fresh.stale, staleLabel: fresh.label,
		suppressed: false, statusText: null, note
	};
}

function buildGaRView(gar: MacroRegimePayload['gar']): RegimeGaRView | null {
	if (!gar || gar.status || typeof gar.gar5 !== 'number') return null;
	const all = [
		{ key: 'gar5' as const, label: '5%', value: gar.gar5 },
		{ key: 'gar25' as const, label: '25%', value: gar.gar25 },
		{ key: 'median' as const, label: '50%', value: gar.median },
		{ key: 'gar75' as const, label: '75%', value: gar.gar75 },
		{ key: 'gar95' as const, label: '95%', value: gar.gar95 }
	];
	const raw = all.filter((b): b is { key: RegimeGaRBarView['key']; label: string; value: number } => typeof b.value === 'number');
	const vals = raw.map((b) => b.value);
	const min = Math.min(...vals, 0);
	const max = Math.max(...vals, 0);
	const span = max - min || 1;
	const bars: RegimeGaRBarView[] = raw.map((b) => ({ ...b, frac: Math.max(0.04, (b.value - min) / span) }));
	const h = gar.horizon ?? 4;
	const tailKr = typeof gar.tailRiskLabel === 'string' ? gar.tailRiskLabel : (typeof gar.tailRisk === 'string' ? gar.tailRisk : '·');
	const tailEn = typeof gar.tailRisk === 'string' ? gar.tailRisk : (typeof gar.tailRiskLabel === 'string' ? gar.tailRiskLabel : '·');
	return {
		available: true,
		bars,
		skewness: typeof gar.skewness === 'number' ? gar.skewness : null,
		tailRiskLabel: { kr: tailKr, en: tailEn },
		horizonLabel: { kr: `${h}Q 전향 분포`, en: `${h}Q forward distribution` },
		asOf: typeof gar.asOf === 'string' ? gar.asOf : null,
		note: {
			kr: typeof gar.seriesNote === 'string' ? gar.seriesNote : 'FCI 조건부 GDP 성장률 분위(점추정 아닌 조건부 분포)',
			en: 'FCI-conditional GDP growth quantiles (conditional distribution, not a point estimate)'
		}
	};
}

function buildBandView(band: MacroRegimePayload['regimeBand']): RegimeBandView | null {
	if (!band || band.status || !Array.isArray(band.band) || !band.band.length) return null;
	// 절대 침체확률(0~1) 그대로 · 렌더러 bandPoints 가 고정 0~1 축에 그린다(per-window 재정규화 금지·진폭 정직).
	const vals = band.band.slice(0, 24).map((v) => Math.max(0, Math.min(1, v)));
	return {
		available: true,
		points: vals,
		caption: {
			kr: `Hamilton 수축확률 ${vals.length}분기(회고적·smoothed)`,
			en: `Hamilton contraction prob, ${vals.length} quarters (retrospective · smoothed)`
		},
		asOf: typeof band.asOf === 'string' ? band.asOf : null
	};
}

function motionArrow(value: string | undefined, kind: 'growth' | 'inflation'): RegimeText {
	const kr = kind === 'growth' ? '성장' : '물가';
	const en = kind === 'growth' ? 'growth' : 'inflation';
	const arrow = value === 'rising' ? '↑' : value === 'falling' ? '↓' : '·';
	return { kr: `${kr}${arrow}`, en: `${en}${arrow}` };
}

const REGIME_ASSET_LABEL: Record<string, string> = {
	equity: '주식', bond: '채권', commodity: '원자재', gold: '금', tips: 'TIPS', cash: '현금'
};
const REGIME_ASSET_LABEL_EN: Record<string, string> = {
	equity: 'Equity', bond: 'Bonds', commodity: 'Commodities', gold: 'Gold', tips: 'TIPS', cash: 'Cash'
};
// KR LEI growthLabel(backend 한국어) → EN. KR notApplicable reason(backend 한국어) → EN.
// KR forecast growthLabel 실제 producer enum = {확장·수축·안정}(forecast.py) · '안정' 매핑 필수(미매핑 시 EN 누출). 나머지는 안전 여유.
const GROWTH_LABEL_EN: Record<string, string> = { '확장': 'Expansion', '수축': 'Contraction', '안정': 'Stable', '둔화': 'Slowdown', '회복': 'Recovery', '횡보': 'Flat' };
const REGIME_REASON_EN: Record<string, string> = { 'US 전용': 'US-only', 'US 중심(FCI 입력)': 'US-centric (FCI input)' };

function buildQuadrantDirection(
	side: MacroSide | undefined,
	alignment: RegimeText | null
): RegimeQuadrantDirectionView | null {
	const q = side?.quadrant;
	if (!q) return null;
	const assets = Object.entries(q.assetImplication ?? {}).map(([key, weight]) => ({
		key, label: REGIME_ASSET_LABEL[key] ?? key, labelEn: REGIME_ASSET_LABEL_EN[key] ?? key, weight: String(weight)
	}));
	return {
		available: true,
		growthLabel: motionArrow(q.growth, 'growth'),
		inflationLabel: motionArrow(q.inflation, 'inflation'),
		assets,
		alignment
	};
}

// US 국면 렌즈 · confluence 4타일 + 수익률곡선 + GaR + band + quadrant 방향.
function buildUsLens(payload: MacroRegimePayload, side: MacroSide | undefined, alignment: RegimeText | null): RegimeMarketLensView {
	const models = payload.forecast?.models ?? {};
	const ids: ('probit' | 'sahm' | 'lei' | 'hamilton')[] = ['probit', 'sahm', 'lei', 'hamilton'];
	const tiles = ids.map((id) => buildRegimeTile(id, models[id]));
	// agreement: probit·yieldCurve 이중계상 가드 · yieldCurve 는 별도 표로 넣지 않음(probit 1표).
	const buckets = ids.map((id) => ({ model: REGIME_MODEL_NAME[id] ?? id, bucket: bucketOf(models[id]) }));
	const validCount = buckets.filter((b) => b.bucket != null).length;
	const rates = payload.rates;
	const yieldCurve: RegimeYieldCurveView | null = rates && !rates.missing?.length && typeof rates.spread10y3m === 'number'
		? {
			available: true,
			curveShapeLabel: { kr: rates.curveShapeLabel || rates.curveShape || '·', en: rates.curveShape || rates.curveShapeLabel || '·' },
			spread: rates.spread10y3m as number,
			spreadText: `${rates.sign === '-' ? '' : '+'}${(rates.spread10y3m as number).toFixed(2)}%p`,
			asOf: typeof rates.asOf === 'string' ? rates.asOf : null,
			note: { kr: '형태=NS·spread=T10Y3M 동일곡선 · probit과 독립 신호 아님', en: 'shape=NS·spread=T10Y3M same curve · not an independent signal from probit' }
		}
		: null;
	return {
		market: 'US',
		validCount,
		totalCount: ids.length,
		agreement: agreementOf(buckets),
		tiles,
		notApplicable: [],
		yieldCurve,
		gar: buildGaRView(payload.gar),
		band: buildBandView(payload.regimeBand),
		quadrant: buildQuadrantDirection(side, alignment)
	};
}

// KR 국면 렌즈 · CLI momentum 1타일 + probit/sahm/hamilton 'US 전용'/'단위 parity' 회색 라벨.
function buildKrLens(payload: MacroRegimePayload, side: MacroSide | undefined, alignment: RegimeText | null): RegimeMarketLensView {
	const lei = payload.forecast?.models?.lei;
	const tiles: RegimeTileView[] = [];
	if (lei && !lei.status) {
		const cliMomentum = typeof lei.cliMomentum === 'number' ? lei.cliMomentum : null;
		const growthLabel = typeof lei.growthLabel === 'string' ? lei.growthLabel : '·';
		const fresh = regimeStale(lei.asOf, lei.staleAfterDays);
		tiles.push({
			model: 'lei', modelName: 'CLI momentum',
			zoneLabel: { kr: growthLabel, en: GROWTH_LABEL_EN[growthLabel] ?? growthLabel },
			secondary: cliMomentum != null ? `Δ${cliMomentum.toFixed(2)}` : null,
			gaugeValue: null, bucket: bucketOf(lei),
			horizonLabel: { kr: '6-9M 선행', en: '6-9M leading' }, scaleLabel: { kr: 'CLI·ECOS', en: 'CLI·ECOS' },
			asOf: typeof lei.asOf === 'string' ? lei.asOf : null,
			stale: fresh.stale, staleLabel: fresh.label,
			suppressed: false, statusText: null,
			note: { kr: 'OECD CLI momentum (KR forecast 는 CLI composite · US 와 다른 shape)', en: 'OECD CLI momentum (KR forecast is a CLI composite · different shape from US)' }
		});
	}
	const missing = payload.forecast?.missing ?? [];
	const naLabel: Record<string, string> = { probit: 'probit', sahm: 'Sahm', hamilton: 'Hamilton', gar: 'GaR' };
	const notApplicable = missing.map((m) => {
		const reasonKr = m.status === 'notApplicable' ? (m.reason || 'US 전용') : m.status;
		const reasonEn = m.status === 'notApplicable'
			? (REGIME_REASON_EN[m.reason || 'US 전용'] ?? (m.reason || 'US-only'))
			: regimeStatusEn(m.status);
		return { id: m.id, label: naLabel[m.id] ?? m.id, reason: { kr: reasonKr, en: reasonEn } };
	});
	return {
		market: 'KR',
		validCount: tiles.length,
		totalCount: 1,
		// KR 은 단일 모델(CLI momentum)이라 교차검증 불가 · agreementOf(전부 null) 의 '(유효 0개)' 가
		// 헤더 validCount(=1)와 모순되므로, 카운트 없는 단일모델 문구로 대체(#KR-AGREE 정직 교정).
		agreement: tiles.length
			? { kr: '교차 불가 · 단일 모델(CLI momentum)', en: 'cross-check N/A · single model (CLI momentum)' }
			: { kr: '교차 불가 · 유효 모델 없음', en: 'cross-check N/A · no valid model' },
		tiles,
		notApplicable,
		yieldCurve: null, // US 전용.
		gar: null, // US 중심.
		band: null,
		quadrant: buildQuadrantDirection(side, alignment)
	};
}

// macro.regime → MacroRegimeView. 부재 시 { available:false } (렌즈 숨김·안전). 전향 분수는 macro.us.transition 라이브.
export function buildRegimeView(
	macro: MacroFile | null,
	focusCell: { channel: MacroChannel; edge: { sign: MacroTransmissionEdgeView['sign'] } } | null | undefined
): MacroRegimeView {
	const transition = transitionFraction(macro?.us);
	const regime = macro?.regime;
	if (!regime) {
		return { available: false, transitionFraction: transition, kr: null, us: null };
	}
	const usAlignment = focusChannelAlignment(macro?.us?.quadrant, focusCell);
	const krAlignment = focusChannelAlignment(macro?.kr?.quadrant, focusCell);
	return {
		available: true,
		transitionFraction: transition,
		kr: regime.kr ? buildKrLens(regime.kr, macro?.kr, krAlignment) : null,
		us: regime.us ? buildUsLens(regime.us, macro?.us, usAlignment) : null
	};
}

// ───────────────────────── 거시 국면 · 근거지표 고밀도 차트 (MacroRegimeDialog 전용) ─────────────────────────
// 좌측 「거시 국면」 다이얼로그가 보여주는 테마별 복합차트(성장/물가/금리/금융조건) 스펙 + 빌더.
// 데이터는 rt.macro.getSeries(macro/{src}/observations.parquet) 라이브 · 백엔드·HF 무변경. MiniFinChart(FinCard) SSOT 렌더.
// 순수함수: end month 를 데이터에서 유도(now 미사용) → 결정론·단위테스트 가능.

interface MacroChartSeriesSpec {
	id: string; // MACRO_SERIES seriesId
	nameKr: string;
	nameEn: string;
	color: string;
	type: 'bar' | 'line';
	axis?: 'r';
}
interface MacroChartSpec {
	key: string;
	titleKr: string;
	titleEn: string;
	unit: string; // 좌축 단위 라벨 (동질 유지 · 우축 series 는 자체 스케일·범례에 '(우)' 표기)
	series: MacroChartSeriesSpec[];
}

/** 근거지표 차트 스펙 · 시장별 4 테마. seriesId 는 전부 contracts MACRO_SERIES 화이트리스트 실재. */
export const MACRO_EVIDENCE_SPECS: Record<'KR' | 'US', MacroChartSpec[]> = {
	US: [
		{ key: 'usGrowth', titleKr: '성장 · 산업생산·고용', titleEn: 'Growth · IP & payrolls', unit: '%', series: [
			{ id: 'INDPRO', nameKr: '산업생산 YoY', nameEn: 'IP YoY', color: '#5b9bf0', type: 'line' },
			{ id: 'PAYEMS', nameKr: '고용 YoY', nameEn: 'Payrolls YoY', color: '#34d399', type: 'line' }
		] },
		{ key: 'usInflation', titleKr: '물가 · CPI·근원·PCE', titleEn: 'Inflation · CPI/core/PCE', unit: '%', series: [
			{ id: 'CPIAUCSL', nameKr: 'CPI YoY', nameEn: 'CPI YoY', color: '#f0616f', type: 'line' },
			{ id: 'CPILFESL', nameKr: '근원 CPI', nameEn: 'Core CPI', color: '#fbbf24', type: 'line' },
			{ id: 'PCEPI', nameKr: 'PCE YoY', nameEn: 'PCE YoY', color: '#a78bfa', type: 'line' }
		] },
		{ key: 'usRates', titleKr: '금리·정책 · 연준·2년·10년', titleEn: 'Rates & policy', unit: '%', series: [
			{ id: 'FEDFUNDS', nameKr: '연준 기준금리', nameEn: 'Fed funds', color: '#f0616f', type: 'line' },
			{ id: 'DGS2', nameKr: '2년', nameEn: '2Y', color: '#fbbf24', type: 'line' },
			{ id: 'DGS10', nameKr: '10년', nameEn: '10Y', color: '#5b9bf0', type: 'line' }
		] },
		{ key: 'usFinancial', titleKr: '금융조건 · 커브·신용·변동성', titleEn: 'Financial · curve/credit/vol', unit: '%p', series: [
			{ id: 'T10Y2Y', nameKr: '장단기차(10Y-2Y)', nameEn: '10Y-2Y', color: '#5b9bf0', type: 'bar' },
			{ id: 'BAMLH0A0HYM2', nameKr: '하이일드 스프레드', nameEn: 'HY spread', color: '#f0616f', type: 'line' },
			{ id: 'VIXCLS', nameKr: 'VIX(우)', nameEn: 'VIX (R)', color: '#a78bfa', type: 'line', axis: 'r' }
		] }
	],
	KR: [
		{ key: 'krGrowth', titleKr: '성장 · 산업생산·수출', titleEn: 'Growth · IP & exports', unit: '%', series: [
			{ id: 'IPI', nameKr: '산업생산 YoY', nameEn: 'IP YoY', color: '#5b9bf0', type: 'line' },
			{ id: 'EXPORT', nameKr: '수출 YoY', nameEn: 'Exports YoY', color: '#34d399', type: 'line' }
		] },
		{ key: 'krInflation', titleKr: '물가 · CPI·제조 PPI', titleEn: 'Inflation · CPI & mfg PPI', unit: '%', series: [
			{ id: 'CPI', nameKr: '소비자물가 YoY', nameEn: 'CPI YoY', color: '#f0616f', type: 'line' },
			{ id: 'PPI_MFG', nameKr: '제조업 PPI YoY', nameEn: 'Mfg PPI YoY', color: '#fbbf24', type: 'line' }
		] },
		{ key: 'krRates', titleKr: '금리·환율 · 기준금리·원달러', titleEn: 'Rate & FX', unit: '%', series: [
			{ id: 'BASE_RATE', nameKr: '한은 기준금리', nameEn: 'BOK rate', color: '#f0616f', type: 'line' },
			{ id: 'USDKRW', nameKr: '원/달러(우)', nameEn: 'USD/KRW (R)', color: '#5b9bf0', type: 'line', axis: 'r' }
		] },
		{ key: 'krSentiment', titleKr: '경기·심리 · 선행·소비', titleEn: 'Cycle & sentiment', unit: 'pt', series: [
			{ id: 'CLI', nameKr: '경기선행지수', nameEn: 'CLI', color: '#5b9bf0', type: 'line' },
			{ id: 'CSI', nameKr: '소비자심리', nameEn: 'Consumer sentiment', color: '#34d399', type: 'line' }
		] }
	]
};

const MACRO_EVIDENCE_MONTHS = 48;

// 최신월(endYm) 기준 n 개월 월축 ('YYYYMM' 오름차순). now 미사용 · endYm 은 데이터에서 유도.
function macroMonthsAxis(endYm: string, n: number): string[] {
	let y = Number(endYm.slice(0, 4));
	let m = Number(endYm.slice(4, 6));
	const out: string[] = [];
	for (let i = 0; i < n; i += 1) {
		out.push(`${y}${String(m).padStart(2, '0')}`);
		m -= 1;
		if (m === 0) { m = 12; y -= 1; }
	}
	return out.reverse();
}

// 월축 정렬 · 각 월에 해당 월 이하 마지막 관측을 carry-forward(ffill). 일/월/분기 혼재 시리즈를 균일화.
// 첫 관측 이전 월은 null(선두 gap → MiniFinChart pen-up). pts 는 d 오름차순 가정(getSeries 가 정렬).
function macroAlignToMonths(pts: MacroPoint[], axis: string[]): Num[] {
	const out: Num[] = [];
	let j = 0;
	let last: number | null = null;
	for (const ym of axis) {
		while (j < pts.length && pts[j].d.slice(0, 6) <= ym) { last = pts[j].v; j += 1; }
		out.push(last);
	}
	return out;
}

/**
 * 시장별 근거지표 복합차트 · MACRO_EVIDENCE_SPECS 를 observations 시계열(seriesMap)로 채워 FinCard[] 산출.
 * end month 는 데이터 최신월에서 유도(결정론). 결측 시리즈는 제외, 한 카드의 모든 시리즈가 비면 카드 자체 제외.
 */
export function buildMacroEvidenceCards(
	market: 'KR' | 'US',
	seriesMap: Record<string, MacroPoint[]>,
	lang: Lang
): { periods: string[]; cards: FinCard[] } {
	const specs = MACRO_EVIDENCE_SPECS[market] ?? [];
	let endYm = '';
	for (const spec of specs) {
		for (const s of spec.series) {
			const pts = seriesMap[s.id];
			if (pts && pts.length) {
				const ym = pts[pts.length - 1].d.slice(0, 6);
				if (ym > endYm) endYm = ym;
			}
		}
	}
	if (!endYm) return { periods: [], cards: [] };
	const axis = macroMonthsAxis(endYm, MACRO_EVIDENCE_MONTHS);
	const periods = axis.map((ym) => `${ym.slice(2, 4)}.${ym.slice(4, 6)}`);
	const cards: FinCard[] = [];
	for (const spec of specs) {
		const series: FinSeries[] = [];
		for (const s of spec.series) {
			const pts = seriesMap[s.id];
			if (!pts || !pts.length) continue;
			const data = macroAlignToMonths(pts, axis);
			if (data.every((v) => v == null)) continue;
			series.push({ name: lang === 'en' ? s.nameEn : s.nameKr, data, color: s.color, type: s.type, ...(s.axis ? { axis: s.axis } : {}) });
		}
		if (series.length) cards.push({ key: spec.key, title: lang === 'en' ? spec.titleEn : spec.titleKr, unit: spec.unit, series });
	}
	return { periods, cards };
}

// ───────────────────────── 거시 forward 시뮬 · BVAR 팬·IRF·국면경로 (MacroRegimeDialog 전망 섹션) ─────────────────────────
// macro/sim/{market}.json (rt.macro.getSim) → 뷰모델. 팬 = 과거 실적(실선) + 미래 p50/p5/p95(밴드) FinCard.
// 결정론: 해석적 BVAR(난수 0)이라 같은 데이터 같은 화면. fail-closed: status≠'ok'·regimePath.status 면 표시 보류.

export interface MacroSimRegimePathView {
	forward: { h: number; p: number }[];
	history: number[];
	current: number;
	ergodic: number;
}
export interface MacroSimIrfView {
	shockLabel: string;
	caveat: string;
	vars: { label: string; data: number[] }[];
}
export interface MacroSimScenarioView {
	key: string;
	label: string;
	condLabel: string;
}
export interface MacroSimView {
	status: 'ok' | 'holdback';
	asOf: string;
	horizon: number;
	periods: string[];
	fanCards: FinCard[];
	/** 시나리오 칩(정책금리 충격 프리셋). 빈 배열이면 칩 미렌더. */
	scenarios: MacroSimScenarioView[];
	/** 활성 시나리오(칩 선택 시) · fanCards 에 조건부 중앙 overlay + '조건부 가정' 배지. null=기준. */
	activeScenario: MacroSimScenarioView | null;
	regimePath: MacroSimRegimePathView | null;
	irf: MacroSimIrfView | null;
	honesty: { sampleN: number | null; calibrated: boolean; note: string };
}

// asOf('YYYY-MM') 기준 back 개월 과거 + fwd 개월 미래 월축 라벨('YY.MM'). asOf 는 마지막 실적월.
function simMonthAxis(asOf: string, back: number, fwd: number): string[] {
	let y = Number(asOf.slice(0, 4));
	let m = Number(asOf.slice(5, 7));
	if (!y || !m) return [];
	const out: string[] = [];
	// 과거: asOf-(back-1) .. asOf
	let sy = y;
	let sm = m - (back - 1);
	while (sm <= 0) { sm += 12; sy -= 1; }
	for (let i = 0; i < back; i += 1) {
		out.push(`${String(sy).slice(2, 4)}.${String(sm).padStart(2, '0')}`);
		sm += 1;
		if (sm > 12) { sm = 1; sy += 1; }
	}
	// 미래: asOf+1 .. asOf+fwd
	y = Number(asOf.slice(0, 4));
	m = Number(asOf.slice(5, 7));
	for (let i = 0; i < fwd; i += 1) {
		m += 1;
		if (m > 12) { m = 1; y += 1; }
		out.push(`${String(y).slice(2, 4)}.${String(m).padStart(2, '0')}`);
	}
	return out;
}

const SIM_HIST = 18;
const SIM_COLORS = { hist: '#7d8ea0', mid: '#5b9bf0', band: '#9ec5f5', scenario: '#f0a93b' };

/** macro/sim 파일 → 전망 시뮬 뷰. status≠'ok' 또는 fan 비면 holdback(섹션 미렌더).
 *  activeScenarioKey 지정 시 fanCards 에 해당 시나리오 조건부 중앙(별색) overlay + 배지. */
export function buildMacroSimView(sim: MacroSimFile | null, lang: Lang, activeScenarioKey: string | null = null): MacroSimView {
	const empty: MacroSimView = { status: 'holdback', asOf: sim?.asOf ?? '', horizon: sim?.horizon ?? 0, periods: [], fanCards: [], scenarios: [], activeScenario: null, regimePath: null, irf: null, honesty: { sampleN: null, calibrated: false, note: '' } };
	if (!sim || sim.status !== 'ok' || !sim.fan || !Object.keys(sim.fan).length) return empty;

	const horizon = sim.horizon || 12;
	const periods = simMonthAxis(sim.asOf, SIM_HIST, horizon);
	const T = (kr: string, en: string): string => (lang === 'en' ? en : kr);

	// 시나리오 칩 + 활성 시나리오(조건부 overlay). 활성 fan = 변수별 조건부 q50 라인 1개 추가.
	const simScenarios = sim.scenarios ?? [];
	const scenarios: MacroSimScenarioView[] = simScenarios.map((s) => ({ key: s.key, label: T(s.label, s.labelEn), condLabel: T(s.condLabel, s.condLabelEn) }));
	const activeRaw = activeScenarioKey ? simScenarios.find((s) => s.key === activeScenarioKey) ?? null : null;
	const activeScenario: MacroSimScenarioView | null = activeRaw ? { key: activeRaw.key, label: T(activeRaw.label, activeRaw.labelEn), condLabel: T(activeRaw.condLabel, activeRaw.condLabelEn) } : null;

	// 팬 FinCard · 변수당 1장: 과거 실적(실선) + 현재 anchor 에서 p50/p5/p95(밴드) 미래로.
	// 원유는 모델 control(물가퍼즐 해소용)이라 헤드라인 팬에서 제외 → 깔끔한 2×2.
	const fanCards: FinCard[] = [];
	for (const [label, v] of Object.entries(sim.fan)) {
		if (v.seriesId === 'DCOILWTICO') continue;
		const hist = (v.history ?? []).slice(-SIM_HIST);
		const padHist = new Array(Math.max(0, SIM_HIST - hist.length)).fill(null);
		const histData: Num[] = [...padHist, ...hist, ...new Array(horizon).fill(null)];
		const anchorIdx = SIM_HIST - 1; // 마지막 실적 인덱스
		const anchor = hist.length ? hist[hist.length - 1] : null;
		const fanOf = (q: number[]): Num[] => {
			const out: Num[] = new Array(SIM_HIST + horizon).fill(null);
			out[anchorIdx] = anchor; // 밴드를 현재에서 emanate
			for (let i = 0; i < q.length && i < horizon; i += 1) out[SIM_HIST + i] = q[i];
			return out;
		};
		const series: FinSeries[] = [
			{ name: T('실적', 'actual'), data: histData, color: SIM_COLORS.hist, type: 'line' },
			{ name: T('상위90', 'p90'), data: fanOf(v.q95), color: SIM_COLORS.band, type: 'line' },
			{ name: T('중앙', 'median'), data: fanOf(v.q50), color: SIM_COLORS.mid, type: 'line' },
			{ name: T('하위10', 'p10'), data: fanOf(v.q5), color: SIM_COLORS.band, type: 'line' }
		];
		// 조건부 overlay · 활성 시나리오의 같은 변수 조건부 q50(별색 1라인). baseline 밴드 위에 얹어 delta 가시.
		const condVar = activeRaw?.fan?.[label];
		if (condVar) series.push({ name: T('조건부', 'cond'), data: fanOf(condVar.q50), color: SIM_COLORS.scenario, type: 'line' });
		const unit = v.transform === 'logdiff100' ? '%' : '%';
		fanCards.push({ key: v.seriesId, title: `${label} · ${T(v.transform === 'logdiff100' ? '월간 변화' : '수준', v.transform === 'logdiff100' ? 'MoM' : 'level')}`, unit, series });
	}

	// 국면경로 · status 있으면 보류(null).
	const rp = sim.regimePath;
	const regimePath: MacroSimRegimePathView | null = rp && !rp.status && rp.forward?.length
		? { forward: rp.forward.map((f) => ({ h: f.h, p: f.pContraction })), history: rp.history ?? [], current: rp.current ?? 0, ergodic: rp.ergodic ?? 0 }
		: null;

	// IRF · 변수 경로만(문자열 키 제외).
	const irfVars = Object.entries(sim.irf).filter(([k, val]) => Array.isArray(val) && k !== 'caveat' && k !== 'shockLabel').map(([k, val]) => ({ label: k, data: val as number[] }));
	const irf: MacroSimIrfView | null = irfVars.length
		? { shockLabel: typeof sim.irf.shockLabel === 'string' ? sim.irf.shockLabel : T('정책금리 충격', 'policy-rate shock'), caveat: typeof sim.irf.caveat === 'string' ? sim.irf.caveat : '', vars: irfVars }
		: null;

	const nObs = typeof sim.model?.nObs === 'number' ? sim.model.nObs : null;
	const note = T(`표본 ${nObs ?? '?'}개월 · BVAR(해석적) · 추정 ${sim.asOf} · 런타임 계산 · scenario≠forecast`, `N=${nObs ?? '?'} · BVAR(analytic) · as of ${sim.asOf} · runtime · scenario≠forecast`);
	return { status: 'ok', asOf: sim.asOf, horizon, periods, fanCards, scenarios, activeScenario, regimePath, irf, honesty: { sampleN: nObs, calibrated: false, note } };
}
