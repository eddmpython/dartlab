// 지표 파라미터 카탈로그 SSOT · klinecharts 내장 27종 + 커스텀(ICHI·ENV) 의 기본 calcParams 와 편집 규칙.
// 기본값은 klinecharts dist/index.esm.js 실측 추출값. 단 RSI·WR 은 라이브러리 기본(3선 6·12·24/6·10·14)이
// 비표준·과밀이라 전문가 표준(RSI 14 · WR 14 단선, TradingView/HTS 통용)으로 교정 · 생성 시 본 defaults 를
// 명시 전달한다(PriceChart reconcile). 편집 적용은 overrideIndicator({name, calcParams}, paneId)
// 만 사용한다 · override 경로의 minValue/maxValue 는 내부 오배선(setMinValue(maxValue))이라 절대 전달 금지.
// grow 지표(MA·EMA·RSI·WR·VOL·BIAS)만 라인 개수 가변(1~5 · 기본 팔레트 5색, 6번째부터 색 재사용이라 5 상한).
// BBI 는 calc 가 합/4 하드코딩 · 개수 잠금(값 편집만 허용).
export interface IndParamDef {
	kr: string;
	en: string;
	min: number;
	max: number;
	step: number;
}
export interface IndDef {
	defaults: number[];
	params: IndParamDef[]; // defaults 와 같은 길이. grow 지표는 추가분에 마지막 정의 재사용.
	grow?: boolean;
	hintKr?: string; // 라벨 병기 (예: ×0.01 스케일)
}

const period = (kr: string, en = kr, min = 2, max = 250, step = 1): IndParamDef => ({ kr, en, min, max, step });

export const IND_DEFS: Record<string, IndDef> = {
	// ── 주가 오버레이 ──
	MA: { defaults: [5, 10, 30, 60], params: [period('기간', 'period'), period('기간', 'period'), period('기간', 'period'), period('기간', 'period')], grow: true },
	EMA: { defaults: [6, 12, 20], params: [period('기간', 'period'), period('기간', 'period'), period('기간', 'period')], grow: true },
	SMA: { defaults: [12, 2], params: [period('기간', 'period'), { kr: '가중', en: 'weight', min: 1, max: 10, step: 1 }] },
	BOLL: { defaults: [20, 2], params: [period('기간', 'period', 5, 120), { kr: '승수', en: 'mult', min: 1, max: 4, step: 0.5 }] },
	BBI: { defaults: [3, 6, 12, 24], params: [period('기간1', 'p1', 1, 120), period('기간2', 'p2', 1, 120), period('기간3', 'p3', 1, 120), period('기간4', 'p4', 1, 120)] },
	SAR: { defaults: [2, 2, 20], params: [{ kr: '시작', en: 'start', min: 1, max: 10, step: 1 }, { kr: '스텝', en: 'step', min: 1, max: 10, step: 1 }, { kr: '최대', en: 'max', min: 10, max: 50, step: 5 }], hintKr: '×0.01' },
	ICHI: { defaults: [9, 26, 52], params: [{ kr: '전환', en: 'conv', min: 5, max: 30, step: 1 }, { kr: '기준', en: 'base', min: 10, max: 60, step: 1 }, { kr: '선행', en: 'lead', min: 30, max: 120, step: 1 }] },
	ENV: { defaults: [20, 6], params: [period('기간', 'period', 5, 120), { kr: '%', en: '%', min: 1, max: 20, step: 0.5 }] },
	// ── 페인 지표 ──
	VOL: { defaults: [5, 10, 20], params: [period('기간', 'period'), period('기간', 'period'), period('기간', 'period')], grow: true },
	MACD: { defaults: [12, 26, 9], params: [{ kr: '단기', en: 'fast', min: 2, max: 60, step: 1 }, { kr: '장기', en: 'slow', min: 5, max: 120, step: 1 }, { kr: '시그널', en: 'sig', min: 2, max: 60, step: 1 }] },
	RSI: { defaults: [14], params: [period('기간', 'period', 2, 120)], grow: true },
	KDJ: { defaults: [9, 3, 3], params: [period('K', 'K', 5, 30), period('D', 'D', 1, 10), period('J', 'J', 1, 10)] },
	WR: { defaults: [14], params: [period('기간', 'period', 2, 120)], grow: true },
	BIAS: { defaults: [6, 12, 24], params: [period('기간', 'period', 2, 120), period('기간', 'period', 2, 120), period('기간', 'period', 2, 120)], grow: true },
	OBV: { defaults: [30], params: [period('기간', 'period')] },
	CCI: { defaults: [20], params: [period('기간', 'period')] },
	BRAR: { defaults: [26], params: [period('기간', 'period')] },
	MTM: { defaults: [12, 6], params: [period('기간', 'period'), period('이평', 'ma')] },
	ROC: { defaults: [12, 6], params: [period('기간', 'period'), period('이평', 'ma')] },
	TRIX: { defaults: [12, 9], params: [period('기간', 'period'), period('이평', 'ma')] },
	PSY: { defaults: [12, 6], params: [period('기간', 'period'), period('이평', 'ma')] },
	VR: { defaults: [26, 6], params: [period('기간', 'period'), period('이평', 'ma')] },
	DMI: { defaults: [14, 6], params: [period('기간', 'period'), period('ADX', 'adx')] },
	EMV: { defaults: [14, 9], params: [period('기간', 'period'), period('이평', 'ma')] },
	AO: { defaults: [5, 34], params: [period('단기', 'fast'), period('장기', 'slow')] },
	CR: { defaults: [26, 10, 20, 40, 60], params: [period('기간', 'period'), period('MA1', 'ma1'), period('MA2', 'ma2'), period('MA3', 'ma3'), period('MA4', 'ma4')] },
	DMA: { defaults: [10, 50, 10], params: [period('단기', 'fast'), period('장기', 'slow'), period('이평', 'ma')] },
	PVT: { defaults: [], params: [] },
	AVP: { defaults: [], params: [] }
};

/** 칩 라벨 뒤 파라미터 요약 (예: ' 5·10·30·60'). 무파라미터 = 빈 문자열. */
export const paramSummary = (name: string, override?: number[]): string => {
	const d = IND_DEFS[name];
	if (!d || !d.defaults.length) return '';
	return ' ' + (override ?? d.defaults).join('·');
};
