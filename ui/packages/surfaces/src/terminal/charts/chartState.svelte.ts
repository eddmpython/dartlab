// 차트 UI 상태 SSOT — ChartCtl runes 클래스 + 공유 상수. PriceChart(effects)·ChartMenus(일반)·
// ChartRibbon(전체화면)이 같은 인스턴스를 공유한다 — 상태 중복 0. 차트 인스턴스 명령(드로잉 생성 등)은
// 상태가 아니므로 콜백으로 — "상태에 요청 넣고 effect 소비" 안티패턴 금지.
const browser = typeof window !== 'undefined'; // $app/environment 결합 제거 (4a-3)
import { BT_PRESETS, BT_COSTS, type BtPresetKey, type BtPresetDef, type BtParamDef, type BtCostsBp, type BtStopConfig, type StrategySlot, type StrategyRule, type RulePreset } from '../lib/backtest';
import { STRAT_COLORS } from './btLayer';
import { IND_DEFS } from './indicatorParams';
import { EVENT_CAT_KEYS } from '../lib/eventRail';
import type { IndexRef } from '@dartlab/ui-contracts';

// 차트 주체(subject) 토글 + 지수 picker 컨트롤 번들 — subject 는 데이터 로드 때문에 CenterStack 소유(ctl 미상향, 01 §2.5)라
// CenterStack → PriceChart → ChartMenus 로 내려 한 줄(.chartTopBar)에서 렌더한다. 값은 라이브, setter 는 CenterStack 상태 변경.
export interface IndexControl {
	subject: 'price' | 'index';
	indexRef: IndexRef | null;
	query: string;
	results: IndexRef[];
	catalog: IndexRef[]; // 전체 지수 카탈로그(시장군 그룹 select 브라우징 — "뭐가 있는지" 발견)
	setSubject: (s: 'price' | 'index') => void;
	pick: (r: IndexRef) => void;
	search: (q: string) => void;
}

export type SubKey = 'VOL' | 'TVAL' | 'MACD' | 'RSI' | 'KDJ' | 'OBV' | 'CCI' | 'WR' | 'DMI' | 'MTM' | 'ROC' | 'TRIX' | 'PSY' | 'VR' | 'BRAR' | 'BIAS' | 'CR' | 'DMA' | 'EMV' | 'AO' | 'PVT' | 'AVP';
export const SUB_ALL: SubKey[] = ['VOL', 'TVAL', 'MACD', 'RSI', 'KDJ', 'OBV', 'CCI', 'WR', 'DMI', 'MTM', 'ROC', 'TRIX', 'PSY', 'VR', 'BRAR', 'BIAS', 'CR', 'DMA', 'EMV', 'AO', 'PVT', 'AVP'];
export type OverlayKey = 'MA' | 'EMA' | 'SMA' | 'BOLL' | 'BBI' | 'SAR' | 'ICHI' | 'ENV';
export const OVERLAY_ALL: OverlayKey[] = ['MA', 'EMA', 'SMA', 'BOLL', 'BBI', 'SAR', 'ICHI', 'ENV'];
// klinecharts YAxisType enum 은 'log' (logarithmic 아님 — 오기 시 조용히 무시되어 로그축이 죽는다)
export type YMode = 'normal' | 'log' | 'percentage';
// 'ha'(하이킨아시)는 klinecharts 네이티브 타입이 아니라 reapply 데이터 변환(heikinAshi) — 차트엔 candle_solid 로 적용.
export type CandleStyle = 'candle_solid' | 'candle_up_stroke' | 'ohlc' | 'area' | 'ha';

// 페인 지표 카탈로그 그룹 — 증권사 지표트리 멘탈모델 (리본 [+] 팝오버 3행)
export const SUB_GROUPS: { kr: string; en: string; keys: SubKey[] }[] = [
	{ kr: '추세', en: 'Trend', keys: ['MACD', 'DMI', 'DMA', 'TRIX'] },
	{ kr: '모멘텀', en: 'Momentum', keys: ['RSI', 'KDJ', 'WR', 'CCI', 'MTM', 'ROC', 'BIAS', 'PSY', 'BRAR', 'CR', 'AO'] },
	{ kr: '거래량', en: 'Volume', keys: ['VOL', 'TVAL', 'OBV', 'VR', 'EMV', 'PVT', 'AVP'] }
];
// 한국식 명칭 병기 (코드 0줄 대체 — 이격도=BIAS·스토캐스틱=KDJ·ADX=DMI)
export const SUB_HINT: Partial<Record<SubKey, string>> = { BIAS: '이격도', KDJ: '스토캐스틱', DMI: 'ADX', TVAL: '거래대금' };
export const OVERLAY_HINT: Partial<Record<OverlayKey, string>> = { ICHI: '일목균형표', ENV: '엔벨로프', BOLL: '볼린저' };

export const PERIODS = ['1M', '3M', '6M', '1Y', '3Y', 'MAX'] as const;
export type PeriodKey = (typeof PERIODS)[number];
export const PERIOD_N: Record<string, number> = { '1M': 22, '3M': 66, '6M': 132, '1Y': 252, '3Y': 750, MAX: 100000 };
// 검증 구간 빠른선택 = dataToT(최신) 기준 캘린더 역산 개월수 (MAX 는 dataFromT 직행). 일봉 슬라이싱은 엔진이 거래일로 스냅.
export const PERIOD_MONTHS: Record<string, number> = { '1M': 1, '3M': 3, '6M': 6, '1Y': 12, '3Y': 36 };
function subYmdMonths(ymd: string, months: number): string {
	const d = new Date(Date.UTC(+ymd.slice(0, 4), +ymd.slice(4, 6) - 1, +ymd.slice(6, 8)));
	d.setUTCMonth(d.getUTCMonth() - months);
	const p = (n: number) => String(n).padStart(2, '0');
	return `${d.getUTCFullYear()}${p(d.getUTCMonth() + 1)}${p(d.getUTCDate())}`;
}
// 봉 주기 — 1/3/5분은 서버 실시간 분봉, 일봉은 원본, 주/월/분기/년은 클라이언트 집계(aggregateCandles).
// TF_DIV = 거래일 환산 제수. 분봉은 기간 칩의 "보이는 봉 수"만 따로 환산한다(PriceChart).
export type MinuteTfKey = '1m' | '3m' | '5m';
export type TfKey = MinuteTfKey | 'D' | 'W' | 'M' | 'Q' | 'Y';
export const MINUTE_TFS: MinuteTfKey[] = ['1m', '3m', '5m'];
export const isMinuteTf = (tf: TfKey): tf is MinuteTfKey => (MINUTE_TFS as readonly string[]).includes(tf);
export const TFS: { v: TfKey; kr: string; en: string }[] = [
	{ v: '1m', kr: '1분', en: '1m' },
	{ v: '3m', kr: '3분', en: '3m' },
	{ v: '5m', kr: '5분', en: '5m' },
	{ v: 'D', kr: '일', en: 'D' },
	{ v: 'W', kr: '주', en: 'W' },
	{ v: 'M', kr: '월', en: 'M' },
	{ v: 'Q', kr: '분기', en: 'Q' },
	{ v: 'Y', kr: '년', en: 'Y' }
];
export const TF_DIV: Record<TfKey, number> = { '1m': 1, '3m': 1, '5m': 1, D: 1, W: 5, M: 21, Q: 63, Y: 252 };
export const YMODES: { v: YMode; kr: string; en: string }[] = [
	{ v: 'normal', kr: '일반', en: 'Linear' },
	{ v: 'log', kr: '로그', en: 'Log' },
	{ v: 'percentage', kr: '%', en: '%' }
];
export const CANDLES: { v: CandleStyle; kr: string; en: string }[] = [
	{ v: 'candle_solid', kr: '캔들', en: 'Candle' },
	{ v: 'candle_up_stroke', kr: '속빈', en: 'Hollow' },
	{ v: 'ohlc', kr: '바', en: 'Bar' },
	{ v: 'area', kr: '라인', en: 'Line' },
	{ v: 'ha', kr: '하이킨아시', en: 'HA' }
];
export const DRAW_TOOLS: { name: string; icon: string; kr: string; en: string }[] = [
	{ name: 'segment', icon: '╱', kr: '추세선', en: 'Trend' },
	{ name: 'rayLine', icon: '⟋', kr: '레이', en: 'Ray' },
	{ name: 'priceLine', icon: '─', kr: '가격선', en: 'Price' },
	{ name: 'horizontalStraightLine', icon: '═', kr: '수평선', en: 'Horiz' },
	{ name: 'verticalStraightLine', icon: '║', kr: '수직선', en: 'Vert' },
	{ name: 'fibonacciLine', icon: '⌖', kr: '피보나치', en: 'Fib' },
	{ name: 'parallelStraightLine', icon: '⫽', kr: '평행채널', en: 'Channel' },
	{ name: 'priceChannelLine', icon: '⫻', kr: '가격채널', en: 'PriceCh' },
	{ name: 'anchoredVWAP', icon: '⚓', kr: '앵커VWAP', en: 'AVWAP' },
	{ name: 'positionTool', icon: '⚖', kr: '포지션', en: 'R:R' },
	{ name: 'MEASURE', icon: '📏', kr: '측정', en: 'Measure' },
	{ name: 'TEXTNOTE', icon: 'T', kr: '텍스트', en: 'Text' }
];

export const ECON_MAX = 3; // 경제지표 동시 표시 상한 (시각·툴팁 밀도)

const PREFS_KEY = 'dlTerm.chart'; // 차트 환경 설정 영속 (전역 1키 — 차트 습관은 회사 무관)

export class ChartCtl {
	period = $state<PeriodKey>('1Y');
	tf = $state<TfKey>('D'); // 봉 주기 (일/주/월) — MAX 등 바스페이스 1px 미달 시 자동 상향
	adj = $state(true); // 수정주가 (등락률 체이닝 — 분할·병합·권리락 보정) — HTS 기본 ON
	overlays = $state<OverlayKey[]>(['MA']);
	subs = $state<SubKey[]>(['VOL', 'RSI']);
	econ = $state<string[]>([]);
	yMode = $state<YMode>('normal');
	candleStyle = $state<CandleStyle>('candle_solid');
	showEvents = $state(false);
	showBand = $state(false);
	showRefs = $state(false); // 52주 고가·저가·전일종가 기준선
	showVP = $state(false); // 매물대 (Volume Profile)
	// 이벤트 레일(하단 공시 dot) 카테고리 필터 — 끈 카테고리 집합(eventRail.EVENT_CATS 키). 기본 [] = 전부 ON.
	// off-set 모델 = 향후 추가될 이벤트타입(뉴스 등)도 기본 노출(enabled-set 이면 신규는 기본 숨김 = 발견성 손해).
	railCatsOff = $state<string[]>([]);
	magnet = $state(false);
	stayDraw = $state(false); // 연속 그리기 — 도형 완성 후 같은 도구 자동 재시작 (TV Stay in Drawing Mode)
	full = $state(false);
	// 바 리플레이 (TV Bar Replay, 일·집계봉 EOD) — 영속 제외 (세션·시점 한정 모드).
	// idx = 현재 봉(표시 시계열 인덱스), start/len 은 PriceChart.enterReplay 가 진입 시점에 기록.
	replay = $state<{ on: boolean; idx: number; playing: boolean; start: number; len: number }>({ on: false, idx: 0, playing: false, start: 0, len: 0 });
	replayMs = $state<400 | 150>(400); // 자동재생 간격 — 1×(400ms) / 2.5×(150ms) 2단
	// 다전략 슬롯(N≤3) — 빈 배열 = BT off. 한 차트에 A·B·(A+B 조합)을 색별로 동시 비교(01 §3.1).
	btStrategies = $state<StrategySlot[]>([]);
	btFocus = $state(0); // 마커·리포트·파라미터 포커스 슬롯 인덱스
	btCosts = $state(true);
	btCostsBp = $state<BtCostsBp>({ ...BT_COSTS });
	btOosSplit = $state<number>(0); // OOS 학습/검증 분할 비율 (0=없음, 0.7=70:30, 0.6=60:40). 세션 한정.
	btStop = $state<BtStopConfig>({}); // 손절/익절 %(S2) — 전 슬롯 공유. 빈값=미적용(회귀 0). "당일 인트라바 가정" 라벨.
	// 전략 도크(좌측 영구 패널) 열림 — 세션 한정. ChartMenus 로컬 btOpen 을 상향(차트 클릭에 안 닫히는 SSOT).
	// 차트 워크스페이스 레이아웃(좌 도크 | 차트)이 이 값을 읽어 도크를 마운트한다. 닫아도 btStrategies 는 유지(재오픈 시 복원).
	btDockOpen = $state(false);
	// 백테스트 보고서 모드 — true 면 CenterStack 하단(재무그래프+판정+DuPont)을 BacktestReport 로 스왑(차트는 고정·비파괴).
	// 다이얼로그 폐기의 SSOT: HonestyFooter '백테스팅 상세'·도크가 이 값을 토글, CenterStack 이 읽어 하단을 가른다.
	btReportMode = $state(false);
	// 백테스트 스코프 — 단일종목(기본) / 시장(index 타이밍) / 유니버스(횡단면 팩터). 제어·엔진경로·보고서 변형을 가른다.
	btScope = $state<'single' | 'market' | 'universe'>('single');
	// 차트↔보고서 양방향 포커스 — 차트 호버 봉 ts(YYYYMMDD). 보고서 거래행 co-highlight 용(단방향 상태, effect 소비 금지).
	btHoverBar = $state<string | null>(null);
	// 보고서 상세 통계(tearsheet) 접힘 — false 면 도크(밴드·히어로·매매표)만, true 면 무거운 통계 펼침. BtChip '상세 ▸' 가 연다.
	btTearsheetOpen = $state(false);
	// 차트→보고서 역 hover-sync — 차트 crosshair 가 거래봉 위면 그 진입일 ts(YYYYMMDD), 아니면 null. 보고서가 그 행 하이라이트(루프 완성). btHoverBar 와 분리(차트 자기 스크롤 방지).
	btCrosshairTs = $state<string | null>(null);
	// 백테스트 검증 구간 — 커스텀 시작/종료(YYYYMMDD). 둘 다 set 이면 period 칩 대신 이 구간(엔진 입력 슬라이싱·차트 줌 동기). null = period 칩.
	btWinFrom = $state<string | null>(null);
	btWinTo = $state<string | null>(null);
	// 가용 데이터 범위(YYYYMMDD) — PriceChart 가 데이터 로드·백필마다 publish. 검증 구간 날짜 입력의 min/max·빠른선택 기준·기본 전체창의 SSOT.
	dataFromT = $state<string | null>(null);
	dataToT = $state<string | null>(null);
	get btCustomWin(): boolean { return !!this.btWinFrom && !!this.btWinTo; }
	/** period → dataToT(최신) 기준 시작일 (MAX·범위초과는 dataFromT 로 clamp). 범위 미상이면 null. */
	private _periodFrom(p: PeriodKey): string | null {
		const to = this.dataToT, lo = this.dataFromT;
		if (!to || !lo) return null;
		if (p === 'MAX') return lo;
		const f = subYmdMonths(to, PERIOD_MONTHS[p] ?? 12);
		return f < lo ? lo : f;
	}
	/** 빠른선택 — period 를 시작/종료 날짜창으로 환산해 설정(데이터 범위 미상이면 무동작). 검증 구간은 항상 날짜창. */
	setWindowPeriod(p: PeriodKey) {
		const from = this._periodFrom(p);
		if (!from || !this.dataToT) return;
		this.btWinFrom = from;
		this.btWinTo = this.dataToT;
	}
	/** 현재 창과 일치하는 period 칩(하이라이트). 전체=MAX 우선, 커스텀(미일치)이면 null. */
	get btWindowChip(): PeriodKey | null {
		const to = this.dataToT, lo = this.dataFromT;
		if (!this.btCustomWin || !to || !lo || this.btWinTo !== to) return null;
		if (this.btWinFrom === lo) return 'MAX';
		for (const p of ['1M', '3M', '6M', '1Y', '3Y'] as const) if (this.btWinFrom === this._periodFrom(p)) return p;
		return null;
	}
	/** 창이 전체 데이터의 진부분집합인가 = 체리피킹 위험(전체기간이면 경고 없음). 범위 미상이면 false. */
	get btWindowIsSubset(): boolean {
		if (!this.btCustomWin || !this.dataFromT || !this.dataToT) return false;
		return this.btWinFrom! > this.dataFromT || this.btWinTo! < this.dataToT;
	}
	/** 커스텀 구간 설정(둘 다 유효해야 활성). from>to 면 스왑, 데이터 있는 날짜로 clamp(국면 프리셋이 범위 밖이어도 안전). */
	setCustomWin(from: string, to: string) {
		if (!from || !to) return;
		let [f, t] = from <= to ? [from, to] : [to, from];
		if (this.dataFromT && f < this.dataFromT) f = this.dataFromT;
		if (this.dataToT && t > this.dataToT) t = this.dataToT;
		this.btWinFrom = f;
		this.btWinTo = t;
	}
	indParams = $state<Record<string, number[]>>({}); // 지표별 calcParams 오버라이드 (없으면 내장 기본)
	compares = $state<{ code: string; name: string }[]>([]); // 종목비교 (최대 3, 세션 한정 — 회사 컨텍스트)
	private prevYMode: YMode = 'normal'; // 비교 진입 전 y축 — 마지막 비교 해제 시 복귀
	private btIdSeq = 0; // 슬롯 고유 id 카운터
	drawCount = $state(0); // 그리기 버튼 하이라이트용 (드로잉 본체는 PriceChart drawMap)
	// 포커스 슬롯 호환 getter — Ribbon/Menus 의 라벨·활성표시가 단일 API 로 읽던 것 보존(N-row UI 와 무관).
	get focusSlot(): StrategySlot | null { return this.btStrategies[this.btFocus] ?? this.btStrategies[0] ?? null; }
	get btKey(): BtPresetKey | null { return this.focusSlot?.preset ?? null; }
	get activeBt(): BtPresetDef | null { const k = this.btKey; return k ? BT_PRESETS.find((d) => d.key === k) ?? null : null; }
	get btOn(): boolean { return this.btStrategies.length > 0; }

	constructor() {
		this.hydrate();
	}

	// localStorage 설정 복원 — 화이트리스트 검증 통과 값만 채택 (스키마 드리프트·손상 방어).
	// showBand 는 회사별 valBand 유무에 묶여 제외, btKey 류는 세션 한정이라 제외.
	private hydrate(): void {
		if (!browser) return;
		try {
			const raw = localStorage.getItem(PREFS_KEY);
			if (!raw) return;
			const p = JSON.parse(raw) as Record<string, unknown>;
			if (Array.isArray(p.overlays)) this.overlays = p.overlays.filter((k): k is OverlayKey => OVERLAY_ALL.includes(k as OverlayKey));
			if (Array.isArray(p.subs)) this.subs = p.subs.filter((k): k is SubKey => SUB_ALL.includes(k as SubKey));
			if (Array.isArray(p.econ)) this.econ = p.econ.filter((x): x is string => typeof x === 'string').slice(0, ECON_MAX);
			if (PERIODS.includes(p.period as PeriodKey)) this.period = p.period as PeriodKey;
			if (TFS.some((t) => t.v === p.tf)) this.tf = p.tf as TfKey;
			if (YMODES.some((y) => y.v === p.yMode)) this.yMode = p.yMode as YMode;
			if (CANDLES.some((cd) => cd.v === p.candleStyle)) this.candleStyle = p.candleStyle as CandleStyle;
			if (typeof p.adj === 'boolean') this.adj = p.adj;
			if (typeof p.showEvents === 'boolean') this.showEvents = p.showEvents;
			if (typeof p.showRefs === 'boolean') this.showRefs = p.showRefs;
			if (typeof p.showVP === 'boolean') this.showVP = p.showVP;
			if (Array.isArray(p.railCatsOff)) this.railCatsOff = p.railCatsOff.filter((x): x is string => typeof x === 'string' && EVENT_CAT_KEYS.includes(x));
			if (typeof p.magnet === 'boolean') this.magnet = p.magnet;
			if (typeof p.stayDraw === 'boolean') this.stayDraw = p.stayDraw;
			if (p.indParams && typeof p.indParams === 'object') {
				const ip: Record<string, number[]> = {};
				for (const [k, v] of Object.entries(p.indParams as Record<string, unknown>)) {
					if (IND_DEFS[k] && Array.isArray(v) && v.length && v.every((x) => Number.isFinite(x))) ip[k] = v as number[];
				}
				if (Object.keys(ip).length) this.indParams = ip;
			}
		} catch {
			/* 손상 — 기본값 유지 */
		}
	}

	/** 차트 환경 저장 — PriceChart 의 persist effect 가 변경 시마다 호출. */
	persist(): void {
		if (!browser) return;
		try {
			localStorage.setItem(
				PREFS_KEY,
				JSON.stringify({
					overlays: this.overlays, subs: this.subs, econ: this.econ, period: this.period, tf: this.tf,
					yMode: this.yMode, candleStyle: this.candleStyle, indParams: this.indParams,
					adj: this.adj, showEvents: this.showEvents, showRefs: this.showRefs, showVP: this.showVP, railCatsOff: this.railCatsOff, magnet: this.magnet, stayDraw: this.stayDraw
				})
			);
		} catch {
			/* quota — 무해 */
		}
	}

	/** 리플레이 한 봉 전진 — 끝 봉 도달 시 자동재생만 정지 (idx 불변). */
	replayStep() {
		if (!this.replay.on) return;
		if (this.replay.idx >= this.replay.len - 1) {
			this.replay.playing = false;
			return;
		}
		this.replay.idx++;
	}
	/** 리플레이 한 봉 뒤로 — 가설→확인→되감기 학습 루프의 절반. 최소 1봉(빈 차트 방지). */
	replayStepBack() {
		if (!this.replay.on || this.replay.idx <= 1) return;
		this.replay.playing = false; // 되감는 순간 자동재생 정지 (수동 검토 모드)
		this.replay.idx--;
	}
	/** 리플레이 시작점 복귀 (⏮) — 자동재생 정지 동행. */
	replayRestart() {
		if (!this.replay.on) return;
		this.replay.idx = this.replay.start;
		this.replay.playing = false;
	}
	/** 리플레이 종료 — PriceChart 의 replay effect 가 전체 시계열을 복원한다. */
	replayExit() {
		this.replay.on = false;
		this.replay.playing = false;
	}
	toggleSub(k: SubKey) {
		this.subs = this.subs.includes(k) ? this.subs.filter((x) => x !== k) : [...this.subs, k];
	}
	toggleOverlay(k: OverlayKey) {
		this.overlays = this.overlays.includes(k) ? this.overlays.filter((x) => x !== k) : [...this.overlays, k];
	}
	toggleEcon(id: string) {
		this.econ = this.econ.includes(id) ? this.econ.filter((x) => x !== id) : this.econ.length >= ECON_MAX ? this.econ : [...this.econ, id];
	}
	/** 이벤트 레일 카테고리가 켜져 있나 (off-set 에 없으면 ON). */
	railCatOn(key: string): boolean {
		return !this.railCatsOff.includes(key);
	}
	/** 전체(모든 카테고리 ON) 상태인가 — 드롭다운 "전체" 활성 표시용. */
	get railAllOn(): boolean {
		return this.railCatsOff.length === 0;
	}
	toggleRailCat(key: string) {
		this.railCatsOff = this.railCatsOff.includes(key) ? this.railCatsOff.filter((k) => k !== key) : [...this.railCatsOff, key];
	}
	/** 전체 보기 — 끈 카테고리 모두 해제. */
	showAllRailCats() {
		this.railCatsOff = [];
	}
	/** 비교 전체 해제 — 회사 전환 시 호출 (이전 회사 기준 비교는 무의미). */
	clearCompares() {
		if (!this.compares.length) return;
		this.compares = [];
		this.yMode = this.prevYMode;
	}
	// 종목비교 토글 — 첫 추가 시 % 축 자동 전환(HTS 동작), 마지막 제거 시 이전 축 복귀
	toggleCompare(p: { code: string; name: string }) {
		if (this.compares.some((x) => x.code === p.code)) {
			this.compares = this.compares.filter((x) => x.code !== p.code);
			if (!this.compares.length) this.yMode = this.prevYMode;
		} else if (this.compares.length < 3) {
			if (!this.compares.length) {
				this.prevYMode = this.yMode;
				this.yMode = 'percentage';
			}
			this.compares = [...this.compares, p];
		}
	}
	/** 첫 미사용 전략 색 — 위치/성과 무관 고정(색 충돌 0, 순서 신호 0). 위치 기반(length 인덱스)은
	 *  remove+add 시 동색 충돌 + 미묘한 순위 신호 → 04 §6 "색=성과 무관 고정". */
	private _nextColor(): string {
		const used = new Set(this.btStrategies.map((s) => s.color));
		return STRAT_COLORS.find((c) => !used.has(c)) ?? STRAT_COLORS[0];
	}
	/** 전략 슬롯 추가 (≤3). 새 슬롯에 포커스 — 추가 즉시 그 전략 마커·리포트. */
	addStrategy(pd: BtPresetDef) {
		if (this.btStrategies.length >= 3) return;
		const color = this._nextColor();
		const slot: StrategySlot = { id: `s${++this.btIdSeq}`, preset: pd.key, params: Object.fromEntries(pd.params.map((x) => [x.name, x.def])), color, label: pd.kr };
		this.btStrategies = [...this.btStrategies, slot];
		this.btFocus = this.btStrategies.length - 1;
	}
	removeStrategy(i: number) {
		if (i < 0 || i >= this.btStrategies.length) return;
		this.btStrategies = this.btStrategies.filter((_, k) => k !== i);
		this.btFocus = Math.min(this.btFocus, Math.max(0, this.btStrategies.length - 1));
	}
	/** 슬롯 i 의 프리셋 교체 (색·id 유지, 파라미터 기본값 리셋). */
	setSlotPreset(i: number, pd: BtPresetDef) {
		if (i < 0 || i >= this.btStrategies.length) return;
		this.btStrategies = this.btStrategies.map((s, k) =>
			k === i ? { ...s, preset: pd.key, params: Object.fromEntries(pd.params.map((x) => [x.name, x.def])), label: pd.kr } : s
		);
	}
	stepSlotParam(i: number, pp: BtParamDef, dir: 1 | -1) {
		const cur = this.btStrategies[i];
		if (!cur) return;
		const v = cur.params[pp.name] ?? pp.def;
		const nv = Math.max(pp.min, Math.min(pp.max, +(v + dir * pp.step).toFixed(2)));
		const params = { ...cur.params, [pp.name]: nv };
		if (params.fast != null && params.slow != null && params.fast >= params.slow) return; // 단기 < 장기 (maCross·macdCross 공통)
		this.btStrategies = this.btStrategies.map((s, k) => (k === i ? { ...s, params } : s));
	}
	setBtFocus(i: number) { if (i >= 0 && i < this.btStrategies.length) this.btFocus = i; }
	clearBtAll() { this.btStrategies = []; this.btFocus = 0; }
	/** rule 프리셋 추가(편집 가능 — 빌더에서 조건 수정). 전문가급 조작패널. */
	addRulePreset(rp: RulePreset) {
		if (this.btStrategies.length >= 3) return;
		const color = this._nextColor();
		this.btStrategies = [...this.btStrategies, { id: `s${++this.btIdSeq}`, preset: 'maCross', params: {}, color, label: rp.kr, rule: rp.make() }];
		this.btFocus = this.btStrategies.length - 1;
	}
	/** 빈 커스텀 룰(직접 조립) 추가 — 진입 1조건·청산 1조건 시드. */
	addCustomRule() {
		if (this.btStrategies.length >= 3) return;
		const color = this._nextColor();
		const seed: StrategyRule = {
			entry: [{ left: 'rsi', leftParams: { period: 14 }, op: '<', right: { kind: 'const', value: 30 } }],
			entryCombine: 'AND',
			exit: [{ left: 'rsi', leftParams: { period: 14 }, op: '>', right: { kind: 'const', value: 70 } }],
			exitCombine: 'OR'
		};
		this.btStrategies = [...this.btStrategies, { id: `s${++this.btIdSeq}`, preset: 'maCross', params: {}, color, label: '커스텀', rule: seed }];
		this.btFocus = this.btStrategies.length - 1;
	}
	/** 슬롯 i 의 룰 교체(조건 빌더가 새 룰 객체 조립 후 호출). */
	setSlotRule(i: number, rule: StrategyRule) {
		if (i < 0 || i >= this.btStrategies.length) return;
		this.btStrategies = this.btStrategies.map((s, k) => (k === i ? { ...s, rule } : s));
	}
	// setCalcParams 는 동등성 비교 없이 무조건 전봉 재계산 — same-value 가드 필수.
	setIndParams(name: string, next: number[]) {
		const cur = this.indParams[name] ?? IND_DEFS[name]?.defaults;
		if (cur && cur.length === next.length && cur.every((v, i) => v === next[i])) return;
		this.indParams = { ...this.indParams, [name]: next };
	}
	resetIndParams(name: string) {
		if (!(name in this.indParams)) return;
		const { [name]: _, ...rest } = this.indParams;
		this.indParams = rest;
	}
	clearAllIndicators() {
		this.overlays = [];
		this.subs = [];
		this.econ = [];
	}
}
