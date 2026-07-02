<script lang="ts">
	// 전문 증권사급 주가차트 · klinecharts(v9) CORE. 차트 크롬은 모드별 컴포넌트로 분리:
	//   일반 = ChartMenus(칩+드롭다운) / 전체화면 = ChartRibbon(2단 전문 리본). 상태는 ChartCtl 단일 SSOT.
	// 본 컴포넌트 = 차트 인스턴스 수명주기 + 데이터(lazy 백필) + 상태→차트 반영 effect 들만.
	// 전체 이력(2010~) lazy 로드, 인스턴스 영속(회사전환=applyNewData, dispose 안 함). SSR 안전.
	import { untrack } from 'svelte';
	import { KRX_MIN_YEAR, MACRO_SERIES, MACRO_ATTRIBUTION, type Candle } from '@dartlab/ui-contracts';
	import { useDartLabRuntime } from '@dartlab/ui-runtime';
	import { aggregateCandles, adjustCandles, heikinAshi } from './candleMath';
	import type { Lang } from '../lib/types';
	import { runPortfolioBacktest, type PortfolioBtResult, type BtFullRef, buildGateSeries, ruleUsesGate } from '../lib/backtest';
	import { loadGateRows, type FundamentalGateRow } from '@dartlab/ui-runtime/data/gateRows'; // 펀더게이트(W2) PIT 행
	import { focusDisclosure } from '../lib/disclosureFocus.svelte'; // 공시 dot 클릭 → 우측 공시목록 그 날짜로
	import { rankCoMovers, type CoMover } from '../lib/coMovement';
	import { loadMarketIndexSeries, MARKET_INDEX_REFS, marketIndexDef } from '../lib/marketIndex';
	import { registerBtIndicators, buildBtExtend, applyBt, clearBt } from './btLayer';
	import { registerEconIndicator, ECON_INDICATOR, type EconExtend } from './econOverlay';
	import { registerExtraIndicators } from './extraIndicators';
	import { type ChartCtl, PERIOD_N, TF_DIV, type CandleStyle, type IndexControl, type OverlayKey, type SubKey, type TfKey } from './chartState.svelte';
	import { loadDraws, saveDraws, type SavedDraw } from './drawStore';
	import { publishView } from './seriesBus';
	import { registerWorkOverlays, MEASURE_NAME, TEXT_NAME } from './avwapOverlay';
	import { registerVolumeProfile, VP_INDICATOR } from './volumeProfile';
	import { registerCmpIndicator, CMP_INDICATOR, type CmpExtend } from './compareOverlay';
	import { downloadSnapshot } from './snapshot';
	import { downloadCsv } from '../../scan/csvExport';
	import { priceBarsToRows, priceCsvFilename, PRICE_CSV_COLUMNS, type PriceBar } from './priceCsv';
	import { IND_DEFS } from './indicatorParams';
	import ChartMenus from './ChartMenus.svelte';
	import ChartRibbon from './ChartRibbon.svelte';
	import DrawToolbar from './DrawToolbar.svelte';
	import BtChip from './BtChip.svelte';

	interface Props {
		candles: Candle[]; // 초기(현재+직전 연도)
		code: string;
		name?: string;
		lang: Lang;
		events?: { date: string; label: string; url?: string; kind?: 'report' | 'capital' | 'disclosure' }[];
		// 공시 레일(02 §4) · 날짜 그룹별 그날 공시 전부(items). 캔들 고가 텍스트 아님 = x축 라벨 아래 전용 dot 레일.
		// 호버=그날 공시 전 항목 툴팁, 클릭=우측 정기/비정기 공시목록 그 날짜로(원문 링크 아님).
		disclosures?: { date: string; items: { title: string; rceptNo: string; url: string; kind: 'regular' | 'nonreg' | 'news'; category: string }[] }[];
		valBand?: { lo: number; mid: number; hi: number } | null;
		peers?: { code: string; name: string }[]; // 동종업계 · 종목비교(VS) 후보
		// 전체화면 심볼 점프 · 검색은 엔진(suggest), 전환은 onPick (터미널 pick 관통)
		suggest?: (q: string, n: number) => { code: string; name: string; industry: string }[];
		onPick?: (code: string) => void;
		onSrc?: (line: string) => void; // 출처(공공누리)를 차트 하단 대신 패널 헤더에 표기하도록 부모로 끌어올림(econ/adj 반응 유지)
		onCoMovers?: (rows: CoMover[]) => void;
		// 백테스트 결과 상향 · 엔진은 PriceChart 소유, 결과(pf+candleTs)를 CenterStack 으로 올려 하단 BacktestReport 가 렌더.
		onBtResult?: (pf: PortfolioBtResult | null, candleTs: string[], fullRef: BtFullRef | null) => void;
		// 차트 주체(subject) · 'price'=회사 주가(기본) · 'index'=KR gov/US FRED 지수(01). CenterStack-local 소유(ctl 미상향).
		subject?: 'price' | 'index';
		// US 지수(FRED 종가전용) = 라인 강제 + 고저 파생지표 degenerate. KR 지수·주가는 false (01 §3.6).
		indexLine?: boolean;
		// 주가/지수 토글 + 지수 picker 번들 · ChartMenus(컨트롤 바)로 패스스루(PriceChart 자체는 미사용).
		indexCtl?: IndexControl;
		// 차트 상태 SSOT · CenterStack 소유(상단 macro 마퀴가 econ 토글 공유, 04 §5). PriceChart 가 new 하지 않고 받는다.
		ctl: ChartCtl;
	}
	let { candles, code, name = '', lang, events, disclosures = [], valBand, peers = [], suggest, onPick, onSrc, onCoMovers, onBtResult, subject = 'price', indexLine = false, indexCtl, ctl }: Props = $props();
	const rt = useDartLabRuntime();
	const browser = typeof window !== 'undefined'; // $app/environment 결합 제거 (4a-3)
	let el: HTMLDivElement | null = $state(null);
	let chart = $state<any>(null);
	let btPf = $state<PortfolioBtResult | null>(null); // 다전략 결과(N≤3 + 조합)
	let btCandleTs = $state<string[]>([]); // 백테스트 캔들 t(YYYYMMDD) · equity 정렬(BacktestReport 슬라이스)
	let btFullRef = $state<BtFullRef | null>(null); // 커스텀 구간 시 전체기간 대조(G3 체리피킹 가드) · 비커스텀이면 null
	// 결과를 CenterStack 으로 상향 · 하단 BacktestReport 가 렌더(보고서 모드). 다이얼로그 폐기.
	$effect(() => { onBtResult?.(btPf, btCandleTs, btFullRef); });
	// 차트→보고서 역 hover-sync · 포커스 전략 거래 진입일 ts(YYYYMMDD) 집합. crosshair 구독이 읽어 ctl.btCrosshairTs 설정(거래봉 위일 때만).
	const tradeEntrySet = $derived.by<Set<string>>(() => {
		const set = new Set<string>();
		const slot = btPf?.slots[Math.min(ctl.btFocus, (btPf?.slots.length ?? 1) - 1)];
		for (const tr of slot?.result.trades ?? []) set.add(tr.entryT);
		return set;
	});
	const tsToYmd = (ms: number): string => { const d = new Date(ms); return `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}${String(d.getUTCDate()).padStart(2, '0')}`; };
	// 보고서 거래행 클릭 → ctl.btHoverBar 설정 → 차트 해당 진입봉으로 스크롤(다이얼로그 onFocusBar 대체).
	$effect(() => {
		const t = ctl.btHoverBar;
		if (!t || !chart) return;
		try { chart.scrollToTimestamp(Date.UTC(+t.slice(0, 4), +t.slice(4, 6) - 1, +t.slice(6, 8)), 300); } catch { /* */ }
	});
	// 종목↔거시 동행(상관) · "어떤 거시가 이 종목과 같이 움직였나"(04 §5, 인과 아님). 회사전환 시 캔들 기준 재계산.
	let coMovers = $state<CoMover[]>([]);
	// 종목↔국내 시장지수 동행(베타) · 거시와 별도 행(지수 상관은 거의 항상 최상위라 섞으면 거시 발견을 가림).
	let marketCoMovers = $state<{ id: string; name: string; corr: number; n: number }[]>([]);
	$effect(() => {
		if (!browser) return;
		const cs = candles;
		if (subject === 'index' || !cs || cs.length < 14) { coMovers = []; marketCoMovers = []; onCoMovers?.([]); return; }
		let alive = true;
		(async () => {
			// 거시 시리즈는 srcCache(파일 1회 로드) 공유라 N개 getSeries 도 저렴. yoy 정의 시 변환된 시리즈로 동행 측정(오버레이와 일치).
			const series = await Promise.all(MACRO_SERIES.map(async (d) => ({ id: d.id, points: (await rt.macro.getSeries(d.id)) ?? [] })));
			if (!alive) return;
			coMovers = rankCoMovers(cs, series.filter((s) => s.points.length));
			onCoMovers?.(coMovers);
			// 시장지수 동행 · 모듈 캐시(회사 무관) 1회 로드. 코스피/코스닥 종가 vs 종목 월수익률.
			const mkt = await loadMarketIndexSeries(rt.index);
			if (!alive) return;
			const mc = rankCoMovers(cs, mkt.map((m) => ({ id: m.ref.code, points: m.points })).filter((s) => s.points.length));
			marketCoMovers = mc.map((c) => ({ ...c, name: MARKET_INDEX_REFS.find((r) => r.code === c.id)?.name ?? c.id }));
		})();
		return () => { alive = false; };
	});
	// ⛔ 불변식: chart.applyNewData 는 reapply() 단일 지점 (bumpDataRev 동행). pushTick 은 제외.
	// dataRev++ 직접 사용 금지 · $effect 안 증감은 읽기+쓰기라 self-dep 무한루프(effect_update_depth_exceeded).
	let dataRev = $state(0);
	let dataRevSeq = 0;
	const bumpDataRev = () => (dataRev = ++dataRevSeq);
	let econOn = false; // ECON indicator 생성 여부 (비반응)
	let econToken = 0; // stale async 가드
	let cmpOn = false; // 종목비교(CMP) indicator 생성 여부 (비반응)
	let cmpToken = 0;

	let kc: any = null;
	const subPanes = new Map<SubKey, string>();
	const mainOn = new Set<OverlayKey>();
	let vpOn = false; // 매물대 indicator 생성 여부 (비반응)
	const appliedParams: Record<string, number[]> = {}; // indParams diff 스냅샷 (비반응)
	let bandIds: string[] = [];
	let eventIds: string[] = [];
	let refIds: string[] = [];
	// 드로잉 · drawMap = 완성 드로잉 id→직렬화 (localStorage 영속 SSOT). pending = 진행중(ESC 취소 대상).
	const drawMap = new Map<string, SavedDraw>();
	let pendingDrawId: string | null = null;
	let selectedDrawId: string | null = null;
	// load-more 상태 (비반응 · 콜백이 읽음). oldestYear↔newestYear = 현재 로드된 이력 범위.
	// viewLen = 현재 tf 로 차트에 적용된 봉 수 (주/월 집계 후 길이 · applySpacing 기준).
	const hist = { code: '', oldestYear: 9999, newestYear: 0, loading: false, viewLen: 0 };
	let appliedTf: TfKey = 'D'; // tf effect 의 mount 중복 재적용 차단용 비반응 스냅샷
	let appliedStyle: CandleStyle = ctl.candleStyle; // HA ↔ 비HA 전환만 데이터 재적용 (스냅샷 가드)
	// 바 리플레이 · replayCutT = 현재 리플레이 봉 라벨(YYYYMMDD, 비반응). displaySeries 가 이 날짜까지
	// 절단해 BT·기준선이 "그 시점까지 데이터만으로" 재계산되는 정직한 리플레이를 만든다.
	let replayCutT: string | null = null;
	let appliedReplay = { on: false, idx: -1 }; // replay effect 중복 재적용 차단 스냅샷

	const toMs = (t: string) => Date.UTC(+t.slice(0, 4), +t.slice(4, 6) - 1, +t.slice(6, 8));
	// x축 날짜 라벨을 한국식 간단 표기로 압축 · 라이브러리 기본(YYYY-MM·MM-DD·YYYY)을 YY.MM·MM.DD·YYYY 로.
	// registerXAxis 가 이미 계산된 ticks 의 text 만 치환(틱 산출·간격 로직은 라이브러리 그대로 · 회귀 0).
	function compactAxisText(s: string): string {
		let m: RegExpExecArray | null;
		if ((m = /^(\d{2})(\d{2})-(\d{2})-(\d{2})/.exec(s))) return `${m[2]}.${m[3]}`; // YYYY-MM-DD(앵커) → YY.MM
		if ((m = /^(\d{2})(\d{2})-(\d{2})$/.exec(s))) return `${m[2]}.${m[3]}`; // YYYY-MM → YY.MM
		if (/^\d{2}-\d{2}$/.test(s)) return s.replace('-', '.'); // MM-DD → MM.DD
		return s; // YYYY · HH:mm 등 그대로
	}
	// turnover 는 억 단위 · {turnover} 플레이스홀더가 콤마만 붙이고 축약을 안 해 원 단위면
	// "446,546,135,655" 생짜 노출 (TVAL 페인·매물대 가중치도 동일 단위 공유, 상대값이라 무영향)
	const toK = (c: Candle) => ({ timestamp: toMs(c.t), open: c.o, high: c.h, low: c.l, close: c.c, volume: c.v, turnover: c.tv != null ? c.tv / 1e8 : undefined });

	// 공시 레일(02 §4) · disclosures(날짜 그룹) 각 날짜를 convertToPixel 로 x 픽셀화해 x축 날짜라벨 "아래" 전용 띠에 dot 배치.
	// 캔들 고가 텍스트 annotation(폭주·가격 차폐, §2.2 금지) 폐기. 레일 띠 = 캔버스가 끝나는 chartWrap 하단 padding 영역
	// (terminal.css .chartWrap padding-bottom · 출처 자리를 레일 lane 으로 전용). 좌표/폭은 el(캔버스) geometry 기준이라
	// 일반·전체화면(좌 58·하 22 padding) 모두 정렬. pan/zoom·resize 는 onScroll/onZoom·ResizeObserver 로 재계산.
	// 좌표 실패/범위 밖은 graceful skip(렌더 0·crash 0).
	type RailItem = { title: string; rceptNo: string; url: string; kind: 'regular' | 'nonreg' | 'news'; category: string };
	type RailDot = { x: number; date: string; items: RailItem[] };
	// 이벤트 레일 카테고리별 건수(전체 disclosures 기준 · 드롭다운 필터에 카운트 표기·0 카테고리 숨김)
	const railCatCounts = $derived.by<Record<string, number>>(() => {
		const c: Record<string, number> = {};
		for (const d of disclosures) for (const it of d.items) c[it.category] = (c[it.category] ?? 0) + 1;
		return c;
	});
	let railBox = $state<{ left: number; top: number; width: number; canvasTop: number } | null>(null);
	let railDots = $state<RailDot[]>([]);
	let hoverRail = $state<{ x: number; date: string; items: RailItem[] } | null>(null); // 호버 = 그날 공시 전부 툴팁(일자 헤더 포함)
	const ymdDash = (d: string) => `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`; // YYYYMMDD → YYYY-MM-DD
	function recomputeRail() {
		const c = chart;
		if (!c || !el) { railDots = []; railBox = null; return; }
		// 레일 띠 = 캔버스 바로 아래(canvas bottom → chartWrap 하단). offsetLeft/Top 이 전체화면 padding 을 자동 반영.
		// canvasTop = 캔버스 상단 · dot 호버 시 그 날짜 세로 가이드선을 캔버스 전 높이로 그릴 때 사용.
		railBox = { left: el.offsetLeft, top: el.offsetTop + el.offsetHeight, width: el.offsetWidth, canvasTop: el.offsetTop };
		if (!disclosures.length) { railDots = []; return; }
		const w = el.offsetWidth;
		const off = ctl.railCatsOff;
		const out: RailDot[] = [];
		for (const d of disclosures) {
			if (!/^\d{8}$/.test(d.date)) continue;
			// 이벤트 레일 카테고리 필터 · 끈 카테고리 항목 제외. 남은 항목 0 이면 dot 자체 숨김(개수·툴팁도 필터 반영).
			const items = off.length ? d.items.filter((it) => !off.includes(it.category)) : d.items;
			if (!items.length) continue;
			let x: number | undefined;
			try {
				const px = c.convertToPixel({ timestamp: toMs(d.date), value: 0 }, { paneId: 'candle_pane' });
				x = Array.isArray(px) ? px[0]?.x : px?.x;
			} catch { continue; }
			if (typeof x !== 'number' || !Number.isFinite(x) || x < -4 || x > w + 4) continue;
			out.push({ x, date: d.date, items });
		}
		railDots = out;
		if (hoverRail && !out.length) hoverRail = null;
	}
	// 데이터/기간/봉주기/disclosures/전체화면 변경 시 재계산 (rAF = 차트 렌더 후 좌표 안정).
	$effect(() => {
		void dataRev;
		void ctl.period;
		void ctl.tf;
		void ctl.full;
		void ctl.railCatsOff;
		void disclosures;
		if (browser) requestAnimationFrame(recomputeRail);
	});
	// 캔버스 크기 변화(전체화면 토글·창 리사이즈·페인 경계 드래그·툴바 줄바꿈) → 차트 캔버스 resize + 레일 geometry·dot x 재정렬.
	// klinecharts 는 컨테이너 크기를 자동 추적하지 않아(전체화면 토글이 c.resize() 를 명시 호출하는 이유) host(el) 가
	// flex:1 로 커질 때 캔버스가 따라오지 않는다 · 같은 observer 에서 chart.resize() 동행해 작았다→커졌을 때 안 커지는 회귀 차단.
	$effect(() => {
		if (!browser || !el) return;
		const ro = new ResizeObserver(() =>
			requestAnimationFrame(() => {
				try { chart?.resize(); } catch { /* */ }
				recomputeRail();
			})
		);
		ro.observe(el);
		return () => ro.disconnect();
	});
	// 출처(공공누리)를 차트 하단 캡션 대신 패널 헤더로 · econ/수정주가/HA 변화에 반응(srcText 가 ctl 읽음).
	$effect(() => {
		onSrc?.(srcText());
	});
	// 리본 Row1 정보 · 표시 시계열(리플레이 절단·수정주가 반영) 기준이라 리플레이 중에도 정직.
	// dataRev = reapply 동행 신호 (displaySeries 내부 untrack 읽기를 대신 깨운다).
	const ribbonInfo = $derived.by<{ last: number; prev: number | null; date: string; hi: number; lo: number } | null>(() => {
		void dataRev;
		if (!candles.length) return null;
		const s = displaySeries();
		if (!s.length) {
			const n = candles.length;
			return { last: candles[n - 1].c, prev: n >= 2 ? candles[n - 2].c : null, date: candles[n - 1].t, hi: candles[n - 1].h, lo: candles[n - 1].l };
		}
		const lastK = s[s.length - 1];
		const win = s.slice(-252);
		let hi = -Infinity;
		let lo = Infinity;
		for (const k of win) {
			if (k.h > hi) hi = k.h;
			if (k.l < lo) lo = k.l;
		}
		return { last: lastK.c, prev: s.length >= 2 ? s[s.length - 2].c : null, date: lastK.t, hi, lo };
	});
	// 상태 피드백 1줄 · 과거 백필 진행 동작을 리본에 노출 (침묵 로딩 = 버그처럼 보임 방지)
	let notice = $state<string | null>(null);
	// 전체화면 오버레이 2종 · 심볼 점프 팔레트(⌘K·/) + 단축키 도움말(?)
	let jumpOpen = $state(false);
	let jumpQ = $state('');
	let jumpIdx = $state(0);
	let jumpInput = $state<HTMLInputElement | null>(null);
	const jumpList = $derived(jumpOpen && suggest ? suggest(jumpQ, 8) : []);
	let helpOpen = $state(false);
	function jumpTo(c: string) {
		jumpOpen = false;
		jumpQ = '';
		jumpIdx = 0;
		onPick?.(c);
	}

	// 캔들 툴팁 · 한국어 압축형 + 등락률({change} 내장 placeholder, 전일종가 대비 자동색).
	// 배열은 wholesale 교체(라이브러리 명시 특례) · 기본 6줄을 우리 줄로 완전 대체.
	const tooltipCustom = (lg: Lang) =>
		lg === 'en'
			? [
					{ title: 'O', value: '{open}' }, { title: 'H', value: '{high}' }, { title: 'L', value: '{low}' },
					{ title: 'C', value: '{close}' }, { title: 'Vol', value: '{volume}' }, { title: 'TVal(100M)', value: '{turnover}' }, { title: 'Chg', value: '{change}' }
				]
			: [
					{ title: '시', value: '{open}' }, { title: '고', value: '{high}' }, { title: '저', value: '{low}' },
					{ title: '종', value: '{close}' }, { title: '량', value: '{volume}' }, { title: '대금(억)', value: '{turnover}' }, { title: '등락', value: '{change}' }
				];
	// 'ha'(하이킨아시)는 데이터 변환(reapply) · klinecharts 캔들 타입으로는 candle_solid 로 그린다.
	const kcCandleType = (t: CandleStyle) => (t === 'ha' ? 'candle_solid' : t);
	// US 지수(종가전용) = 사용자 candleStyle 무시 'area'(라인) 강제. ctl.candleStyle 영속값 불변(2차 오염 0, 01 §3.6).
	const effectiveCandleType = $derived(indexLine ? 'area' : kcCandleType(ctl.candleStyle));
	// US 종가전용 degenerate 지표(고저 부재 → flat/0) · chip 비활성 + 이미 켜진 페인 능동 제거(01 §4.2).
	const degenerateSubs = $derived(
		indexLine ? new Set<SubKey>(['KDJ', 'CCI', 'WR', 'DMI', 'BRAR', 'AO', 'CR', 'VOL', 'TVAL', 'OBV', 'PVT', 'EMV', 'VR', 'AVP']) : new Set<SubKey>()
	);
	const degenerateOverlays = $derived(indexLine ? new Set<OverlayKey>(['ICHI']) : new Set<OverlayKey>());
	// 차트 캔버스 활자 · 터미널 본체와 동일 스택. 기본 'Helvetica Neue' 는 한글이 없어 거래량
	// 축의 만·억 이 시스템 폰트(맑은 고딕)로 폴백돼 숫자와 다른 활자·다른 덩치로 렌더됐다.
	// 숫자 = JetBrains Mono(터미널 .mono 와 동일), 한글 = Pretendard 폴백으로 전 페인 통일.
	const CHART_FONT = "'JetBrains Mono', 'Pretendard Variable', ui-monospace, monospace";
	const themeStyles = () => ({
		grid: { horizontal: { color: 'rgba(48,58,78,0.55)' }, vertical: { color: 'rgba(38,46,62,0.3)' } },
		candle: {
			type: effectiveCandleType,
			bar: { upColor: '#34d399', downColor: '#f0616f', noChangeColor: '#8b919e', upBorderColor: '#34d399', downBorderColor: '#f0616f', noChangeBorderColor: '#8b919e', upWickColor: '#5eead4', downWickColor: '#fb7185', noChangeWickColor: '#8b919e' },
			area: { lineColor: '#5b9bf0', lineSize: 1.4, backgroundColor: [{ offset: 0, color: 'rgba(91,155,240,0.22)' }, { offset: 1, color: 'rgba(91,155,240,0.01)' }] },
			priceMark: { high: { color: '#8b919e', textFamily: CHART_FONT }, low: { color: '#8b919e', textFamily: CHART_FONT }, last: { upColor: '#34d399', downColor: '#f0616f', noChangeColor: '#8b919e', text: { color: '#0b0e14', family: CHART_FONT } } },
			tooltip: { offsetTop: 4, custom: tooltipCustom(lang), text: { color: '#cfd3dc', size: 11, family: CHART_FONT }, rect: { color: 'rgba(14,17,23,0.85)', borderColor: '#222b3a' } }
		},
		indicator: { tooltip: { text: { color: '#8b919e', size: 10, family: CHART_FONT } } },
		xAxis: { axisLine: { color: '#222b3a' }, tickLine: { color: '#222b3a' }, tickText: { color: '#8b919e', size: 10, family: CHART_FONT } },
		yAxis: { type: ctl.yMode, axisLine: { color: '#222b3a' }, tickLine: { color: '#222b3a' }, tickText: { color: '#8b919e', size: 10, family: CHART_FONT } },
		separator: { color: '#222b3a', fill: true, activeBackgroundColor: 'rgba(var(--amber-rgb),0.1)' },
		crosshair: { horizontal: { line: { color: 'rgba(255,255,255,0.6)' }, text: { backgroundColor: '#ff3f6f', family: CHART_FONT } }, vertical: { line: { color: 'rgba(255,255,255,0.6)' }, text: { backgroundColor: '#ff3f6f', family: CHART_FONT } } }
	});

	// 보조 페인 높이 · 컨테이너 비례(16%) 적응. 전체화면 진입 시 78px 고정 납작 페인 방지.
	function subPaneHeight(): number {
		const h = el?.clientHeight || 480;
		return Math.max(72, Math.min(240, Math.round(h * 0.16)));
	}

	// ── 차트 인스턴스 생성 (mount 1 회, el 기준) ──
	$effect(() => {
		const node = el;
		if (!browser || !node) return;
		let disposed = false;
		let local: any = null;
		(async () => {
			const mod: any = await import('klinecharts');
			if (disposed || !node) return;
			kc = mod;
			registerBtIndicators(mod);
			registerEconIndicator(mod);
			registerExtraIndicators(mod);
			registerWorkOverlays(mod);
			registerVolumeProfile(mod);
			registerCmpIndicator(mod);
			// x축 날짜 라벨 간단화 · 기본 축('default')의 createTicks 가 받는 defaultTicks 의 text 만 YY.MM 으로 재포맷.
			// 패턴 미일치(HH:mm 등)는 그대로 통과(타 차트 무해). init 전 등록해야 차트가 픽업. 재등록은 idempotent.
			try {
				mod.registerXAxis({
					name: 'default',
					createTicks: ({ defaultTicks }: { defaultTicks: { coord: number; value: number | string; text: string }[] }) =>
						defaultTicks.map((t) => ({ ...t, text: compactAxisText(t.text) }))
				});
			} catch { /* registerXAxis 미지원 빌드 · 기본 라벨 유지 */ }
			local = mod.init(node, { styles: themeStyles() });
			if (!local) return;
			local.setPriceVolumePrecision(0, 0);
			// 미래(데이터 없는) 우측 영역 0 · 차트는 반드시 마지막 봉까지만. 옛 12px 여백이
			// 줌아웃 시 ~3봉의 미래 축으로 보이던 것 제거 (EOD 차트에 미래 축은 무의미).
			local.setOffsetRightDistance(0);
			try { local.setMaxOffsetRightDistance(0); } catch { /* 구버전 무시 */ }
			// 캔들 페인 상단 여백 축소 · 기본 top gap(~0.2=20%)은 옛 absolute 버튼이 덮던 자리.
			// 버튼이 그래프 위 행으로 빠진 뒤 그 띠가 빈 공간으로 노출돼 "위에 안 그린다"는 회귀가 됐다.
			// 봉이 위로 차오르고 레전드(시/고/저/MA) 텍스트는 그 위에 겹쳐 그려진다(TradingView 식·밀도↑).
			try { local.setPaneOptions({ id: 'candle_pane', gap: { top: 0.06, bottom: 0.06 } }); } catch { /* 구버전 무시 */ }
			// 공시 레일 · pan/zoom 시 dot x 재정렬 (rAF 디바운스). 미지원 버전은 데이터 effect 재계산만.
			try {
				local.subscribeAction('onScroll', () => requestAnimationFrame(recomputeRail));
				local.subscribeAction('onZoom', () => requestAnimationFrame(recomputeRail));
				// 역 hover-sync · crosshair 가 거래 진입봉 위면 보고서 그 행 하이라이트(차트↔표 루프 완성). 거래봉 아니면 null(변경 시만 설정).
				local.subscribeAction('onCrosshairChange', (data: any) => {
					const ms = data?.kLineData?.timestamp ?? data?.timestamp;
					const ymd = typeof ms === 'number' ? tsToYmd(ms) : null;
					const next = ymd && tradeEntrySet.has(ymd) ? ymd : null;
					if (ctl.btCrosshairTs !== next) ctl.btCrosshairTs = next;
				});
			} catch { /* 구버전 무시 */ }
			// timestamp 는 Date.UTC 자정 · timezone 미설정 시 XAxis 라벨이 브라우저 로컬 TZ 로 풀려
			// 미주 사용자에게 하루 전 날짜로 표시되는 조용한 오류. 명시 고정.
			try { local.setTimezone('UTC'); } catch { /* */ }
			// 일봉 날짜 포맷 · 기본 'YYYY-MM-DD HH:mm' 하드코딩이 일봉에 09:00 같은 무의미 시각 노출.
			// Tooltip(0)·Crosshair(1) 만 날짜로, XAxis 등은 라이브러리 기본 유지.
			const fmtYmd = (ts: number) => {
				const d = new Date(ts);
				const p = (n: number) => String(n).padStart(2, '0');
				return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())}`;
			};
			// 큰 수 표기 · 라이브러리 기본 K/M/B(서양식) 대신 만·억·조. 거래량(주)·거래대금(원)
			// 축 라벨·툴팁 공통. 자릿수 규칙 고정: 조·억 = 소수 2자리, 만 = 정수, 만 미만 = 정수 콤마.
			const fmtBigKr = (value: string | number): string => {
				const v = Number(value);
				if (!Number.isFinite(v)) return String(value);
				const a = Math.abs(v);
				if (a >= 1e12) return (v / 1e12).toFixed(2) + '조';
				if (a >= 1e8) return (v / 1e8).toFixed(2) + '억';
				if (a >= 1e4) return Math.round(v / 1e4).toLocaleString() + '만';
				return Math.round(v).toLocaleString();
			};
			try {
				local.setCustomApi({
					formatDate: (dtf: unknown, ts: number, format: string, type: number) => {
						if (type === 0 || type === 1) return fmtYmd(ts);
						try { return mod.utils.formatDate(dtf, ts, format); } catch { return fmtYmd(ts); }
					},
					formatBigNumber: fmtBigKr
				});
			} catch { /* setCustomApi 미지원 빌드 · 기본 포맷 유지 */ }
			// 전체 이력 lazy 로드 · 좌측(forward) 도달 시 더 오래된 연도 prepend.
			// 주/월봉은 부분연도 prepend 가 버킷 경계를 깨므로 tf effect 가 전체 백필 후 재적용 (여기선 무시).
			local.setLoadDataCallback((p: any) => {
				const done = (rows: any[], more: boolean) => { try { p.callback(rows, more); } catch { /* */ } };
				// ⚠ untrack 필수 · klinecharts 는 applyNewData 안에서 본 콜백을 동기 호출(backward)한다.
				// 여기 상태 읽기가 reapply 를 부른 effect(회사전환 등)의 의존이 되면 유령 재실행 루프.
				const s = untrack(() => ({ replayOn: ctl.replay.on, tf: ctl.tf, subj: subject }));
				if (s.subj === 'index') return done([], false); // 지수 = series() 전이력 단발 로드 · 좌측 백필 없음(01 §6.6)
				if (s.replayOn) return done([], false); // 리플레이 · 절단 시계열에 과거 prepend 금지
				if (s.tf !== 'D') return done([], false);
				if (p.type !== 'forward' || hist.loading) return done([], hist.oldestYear - 1 >= KRX_MIN_YEAR);
				const next = hist.oldestYear - 1;
				if (next < KRX_MIN_YEAR) return done([], false);
				hist.loading = true;
				rt.price.older(hist.code, next)
					.then((older) => {
						hist.oldestYear = next;
						hist.loading = false;
						let rows = older;
						// 수정주가 ON · prepend 분도 전체 체이닝 재계산의 선두 슬라이스로 보정
						// (원본 그대로 붙이면 분할 이전 연도가 보정 스케일과 어긋난 절벽을 만든다)
						if (ctl.adj && older.length) {
							const adj = adjustCandles(rt.price.loaded(hist.code));
							if (adj.length >= older.length) rows = adj.slice(0, older.length);
						}
						done(rows.map(toK), next - 1 >= KRX_MIN_YEAR);
					})
					.catch(() => { hist.loading = false; done([], false); });
			});
			chart = local;
		})();
		return () => {
			disposed = true;
			if (local && kc) { try { kc.dispose(local); } catch { /* */ } }
			subPanes.clear();
			mainOn.clear();
			econOn = false;
			vpOn = false;
			cmpOn = false;
			for (const k of Object.keys(appliedParams)) delete appliedParams[k];
			bandIds = [];
			eventIds = [];
			refIds = [];
			drawMap.clear();
			pendingDrawId = null;
			selectedDrawId = null;
			if (chart === local) chart = null;
		};
	});

	// 전체 표시 시계열 = 원본 일봉 → (수정주가 보정). reapply 내부 전용 (리플레이 절단 이전 원본).
	function fullSeries(): Candle[] {
		const all = rt.price.loaded(hist.code);
		const base = all.length ? all : candles; // 캐시 미시드 방어 · prop 직접 적용
		if (!base.length) return base;
		return untrack(() => ctl.adj) ? adjustCandles(base) : base;
	}

	// 표시 시계열 (BT·기준선·이벤트 마커 공용) · 리플레이 중엔 현재 봉 날짜까지 절단.
	// 절단 덕에 dataRev 의존 effect(BT·52주 기준선)가 그 시점까지 데이터만으로 정직하게 재계산된다.
	function displaySeries(): Candle[] {
		const all = fullSeries();
		if (replayCutT == null) return all;
		let end = all.length;
		while (end > 0 && all[end - 1].t > replayCutT) end--;
		return all.slice(0, end);
	}

	// 로드된 전체 이력을 현재 tf 시점(일=원본, 주/월/분기/년=집계)으로 재적용 · applyNewData 단일 지점.
	// 리플레이 ON 이면 idx 봉까지 절단, 하이킨아시면 적용 직전 변환(버스·BT 는 원본 가격 유지).
	function reapply(c: any) {
		const tfv = untrack(() => ctl.tf);
		const base = fullSeries();
		if (!base.length) return;
		// 가용 데이터 범위 publish · 검증 구간 날짜 입력 bound·기본 전체창(StrategyDock). 동일값 가드로 재실행 루프 0.
		const loT = base[0].t, hiT = base[base.length - 1].t;
		if (ctl.dataFromT !== loT) ctl.dataFromT = loT;
		if (ctl.dataToT !== hiT) ctl.dataToT = hiT;
		let view = tfv === 'D' ? base : aggregateCandles(base, tfv);
		hist.viewLen = view.length; // 전체 길이 (리플레이 절단 전 · applySpacing·replay len 기준)
		// ⚠ untrack 은 콜백 안 읽기만 보호 · proxy 를 꺼내 밖에서 .on 읽으면 호출 effect 에 의존이 생긴다
		const rp = untrack(() => ({ on: ctl.replay.on, idx: ctl.replay.idx }));
		if (rp.on) {
			view = view.slice(0, Math.min(rp.idx, view.length - 1) + 1);
			replayCutT = view[view.length - 1].t;
		} else {
			replayCutT = null;
		}
		publishView(view, toMs); // AVWAP·측정룰러가 구독하는 표시 시계열 버스 (원본 가격)
		const out = !indexLine && untrack(() => ctl.candleStyle) === 'ha' ? heikinAshi(view) : view;
		c.applyNewData(out.map(toK), !rp.on && tfv === 'D' && hist.oldestYear - 1 >= KRX_MIN_YEAR);
		bumpDataRev();
	}

	// 리플레이를 reapply 없이 종료 · 직후 자체 reapply 하는 effect(회사전환·tf·adj)용 (이중 재적용 방지).
	function exitReplaySilently() {
		untrack(() => {
			if (!ctl.replay.on) return;
			ctl.replayExit();
			appliedReplay = { on: false, idx: ctl.replay.idx };
		});
	}

	// ── 데이터 적용 (회사전환 = applyNewData, dispose 안 함 = 영속) ──
	$effect(() => {
		const cs = candles;
		const c = chart;
		if (!c || !cs || cs.length === 0) return;
		hist.code = code;
		hist.oldestYear = +cs[0].t.slice(0, 4);
		hist.newestYear = +cs[cs.length - 1].t.slice(0, 4);
		hist.loading = false;
		exitReplaySilently(); // 회사 전환 · 이전 회사 시점 리플레이는 무의미
		reapply(c);
		bandIds.forEach((id) => c.removeOverlay(id));
		eventIds.forEach((id) => c.removeOverlay(id));
		refIds.forEach((id) => c.removeOverlay(id));
		try { c.removeOverlay({ groupId: 'draw' }); } catch { /* */ }
		bandIds = [];
		eventIds = [];
		refIds = [];
		drawMap.clear();
		pendingDrawId = null;
		selectedDrawId = null;
		restoreDraws(c); // 회사별 저장 드로잉 복원 (drawCount 동기화 포함)
		untrack(() => ctl.clearCompares()); // 이전 회사 기준 종목비교 해제
		// untrack · applyPeriodFull 의 ctl.period 읽기가 본 effect 의존이 되면 기간 클릭마다
		// 회사전환 전체(재적용+드로잉 삭제)가 재실행되고, viewLen 갱신 전 이중 tf 상향(W→M)까지 일으킨다.
		untrack(() => applyPeriodFull(c));
		// 주/월봉 유지 상태로 회사 전환 · 집계 정합 위해 전체 백필 (gov 전이력 회사는 no-op)
		if (untrack(() => ctl.tf) !== 'D') void backfillTo(c, KRX_MIN_YEAR);
	});

	// 가시 봉 수 재배치 · 현재 tf 적용 후 봉 수(viewLen) 기준. klinecharts BarSpace 하한 = 1px:
	// 미달이면 한 단계 굵은 봉으로 자동 상향 (일→주→월, HTS 관행. MAX 일봉 ~4천개 = 물리적 표시 불가).
	function applySpacing(c: any) {
		const tfv = untrack(() => ctl.tf);
		const len = hist.viewLen || candles.length || 1;
		const w = el?.clientWidth || 800;
		const btActive = untrack(() => ctl.btReportMode || ctl.btOn);
		// 커스텀 검증 구간(일봉 전용) · 구간 봉수로 barSpace + toT 우측 정렬(엔진 슬라이싱과 차트 줌 시각 일치).
		if (btActive && tfv === 'D' && untrack(() => ctl.btCustomWin)) {
			const base = fullSeries();
			const fromT = untrack(() => ctl.btWinFrom) as string;
			const toT = untrack(() => ctl.btWinTo) as string;
			let fi = 0; while (fi < base.length && base[fi].t < fromT) fi++;
			let ti = base.length - 1; while (ti > 0 && base[ti].t > toT) ti--;
			if (ti >= fi && base[ti]) {
				const nC = Math.max(2, ti - fi + 1);
				try { c.setBarSpace(Math.max(0.12, Math.min(30, w / nC))); c.scrollToTimestamp(toMs(base[ti].t)); } catch { /* */ }
				return;
			}
		}
		const N = Math.min(Math.ceil((PERIOD_N[ctl.period] ?? len) / TF_DIV[tfv]), len);
		const space = w / Math.max(1, N);
		// 봉 주기는 사용자가 고른 그대로 유지한다 · 긴 기간에서 일/주봉이 1px 미만이 되어도 자동 상향(일→주→월)
		// 하지 않는다(HTS·TradingView 관행: tf = 집계 선택일 뿐, 과거는 드래그/스크롤로 이동). 1px 미만이면 최근
		// 구간만 화면에 들어오고 나머지는 좌측으로 스크롤된다.
		// 일반 1px 하한(그 이하는 좌측 스크롤). 백테스트는 0.12px 까지 허용해 선택 구간 전체를 한 화면에(에쿼티/밴드 ts 정합).
		const floor = btActive ? 0.12 : 1;
		try { c.setBarSpace(Math.max(floor, Math.min(30, space))); c.scrollToRealTime(0); } catch { /* */ }
	}

	// 목표 연도까지 능동 백필 → (변경 시) 전체 재적용 + 재배치. 기간 점프·주/월봉 전환 공용.
	async function backfillTo(c: any, target: number) {
		const code0 = hist.code;
		if (!code0) return;
		let changed = false;
		while (hist.oldestYear > Math.max(target, KRX_MIN_YEAR) && !hist.loading) {
			const y = hist.oldestYear - 1;
			hist.loading = true;
			notice = T(`과거 시세 불러오는 중 … ${y}`, `loading history … ${y}`); // 진행 중 상시 · 완료 시 해제
			try { await rt.price.older(code0, y); } catch { hist.loading = false; break; }
			hist.loading = false;
			if (hist.code !== code0 || chart !== c) { notice = null; return; } // 회사 전환·차트 교체 → 중단
			hist.oldestYear = y;
			changed = true;
		}
		notice = null;
		if (changed && chart === c && hist.code === code0) {
			reapply(c);
			applySpacing(c);
		}
	}

	// 기간(특히 3Y/MAX)·줌아웃 시 필요한 과거연도까지 백필.
	const yearsForPeriod = (p: string): number => (p === 'MAX' ? 999 : Math.ceil((PERIOD_N[p] ?? 252) / 252) + 1);
	function applyPeriodFull(c: any) {
		applySpacing(c);
		const target = ctl.btCustomWin && ctl.btWinFrom
			? Math.max(KRX_MIN_YEAR, +ctl.btWinFrom.slice(0, 4) - 1) // 커스텀 시작연도까지 백필(워밍업 여유 −1)
			: ctl.period === 'MAX' ? KRX_MIN_YEAR : Math.max(KRX_MIN_YEAR, hist.newestYear - yearsForPeriod(ctl.period) + 1);
		void backfillTo(c, target);
	}

	// ── 봉 주기(일/주/월/분기/년) 전환 → 전체 백필 후 집계 재적용. ──
	// ⛔ BT 전략을 여기서 지우지 않는다(과거: clearBtAll). 백테스트 숫자는 항상 일봉(displaySeries)으로 정확히 계산되고,
	//   주/월봉에선 캔버스 마커·에쿼티만 숨긴다(bt effect 의 isDaily 게이트). 일봉 복귀 시 그대로 복원 · 데이터 손실 0.
	$effect(() => {
		const tfv = ctl.tf;
		const c = chart;
		if (!c || !candles.length) return;
		if (tfv === appliedTf) return;
		appliedTf = tfv;
		exitReplaySilently(); // 봉 주기 전환 · 리플레이 idx 좌표계가 깨지므로 자동 종료
		const code0 = hist.code;
		(async () => {
			if (tfv !== 'D') await backfillTo(c, KRX_MIN_YEAR);
			if (chart !== c || hist.code !== code0) return;
			reapply(c);
			applySpacing(c);
		})();
	});

	// ── 백테스트 = 일봉 고정(무조건). 진입 시 tf→D 강제(이전 tf 기억)·종료 시 복원. tf 토글은 ChartMenus/Ribbon 에서 비활성. ──
	let btPrevTf: TfKey | null = null;
	$effect(() => {
		const open = ctl.btReportMode;
		untrack(() => {
			if (open) {
				if (ctl.tf !== 'D') { if (btPrevTf == null) btPrevTf = ctl.tf; ctl.tf = 'D'; }
			} else if (btPrevTf != null) {
				ctl.tf = btPrevTf;
				btPrevTf = null;
			}
		});
	});

	// ── 백테스트 진입(또는 백테스트 중 회사 전환) = 검증 구간 기본 전체기간. 전이력 백필 후 [최초, 최신] 날짜창을 1회 설정(이후 사용자 편집 보존). ──
	// dataFromT/dataToT(백필마다 publish) 변화에 반응 = 경합 안전: 다른 백필 진행 중이면 그 reapply 가 effect 를 재실행시켜 끝까지 추적.
	let btDefaultedFor = '';
	$effect(() => {
		const open = ctl.btReportMode;
		const cd = code;
		void candles; void ctl.dataFromT; void ctl.dataToT; // 데이터 로드·백필 진행마다 재평가
		const c = chart;
		if (!open || !c || btDefaultedFor === cd) return;
		untrack(() => {
			const code0 = hist.code;
			if (!code0 || code0 !== cd || !fullSeries().length) return; // 데이터 준비 전 · candles/range effect 로 재시도
			// 아직 최초연도(KRX_MIN_YEAR)까지 안 내려왔으면 전이력 백필(주가만 · 지수 series 는 단발 전이력 로드). 진행 중이면 그쪽 reapply 가 dataFromT 갱신→재진입.
			if (subject !== 'index' && hist.oldestYear > KRX_MIN_YEAR) {
				if (!hist.loading) void backfillTo(c, KRX_MIN_YEAR);
				return;
			}
			const all = fullSeries();
			if (!all.length) return;
			btDefaultedFor = cd; // 전이력 확보 후 1회만
			ctl.setCustomWin(all[0].t, all[all.length - 1].t);
		});
	});

	// ── 수정주가 토글 → 재적용 (mount·회사전환 중복 적용은 스냅샷 가드) ──
	let appliedAdj = true;
	$effect(() => {
		const a = ctl.adj;
		const c = chart;
		if (!c || !candles.length) return;
		if (a === appliedAdj) return;
		appliedAdj = a;
		exitReplaySilently(); // 보정 전환 · 절단 기준 가격이 달라지므로 자동 종료
		reapply(c);
	});

	// ── 바 리플레이 · on/idx 변경 → 절단 재적용 (dataRev 동행으로 BT·기준선 자동 추종) ──
	$effect(() => {
		const on = ctl.replay.on;
		const idx = ctl.replay.idx;
		const c = chart;
		if (!c || !candles.length) return;
		if (on === appliedReplay.on && idx === appliedReplay.idx) return;
		appliedReplay = { on, idx };
		reapply(c);
	});

	// 자동재생 · replayMs(400/150ms 2단) 간격 한 봉 전진. 끝 봉 도달 시 replayStep 이 playing 을 끄면 cleanup.
	$effect(() => {
		if (!ctl.replay.on || !ctl.replay.playing) return;
		const t = setInterval(() => ctl.replayStep(), ctl.replayMs);
		return () => clearInterval(t);
	});

	// 리플레이 진입 · 시작점 = 현재 기간 윈도 시작(최소 30봉 워밍업), 현재 tf 봉 수로 환산.
	function enterReplay() {
		if (!chart || !hist.viewLen) return;
		const n = Math.ceil((PERIOD_N[ctl.period] ?? 252) / TF_DIV[ctl.tf]);
		const idx = Math.min(Math.max(30, hist.viewLen - n), hist.viewLen - 1);
		ctl.replay = { on: true, idx, playing: false, start: idx, len: hist.viewLen };
	}

	// ── 매물대 토글 → VPVR indicator 생성/제거 (candle_pane, figures:[] = y축 무왜곡) ──
	$effect(() => {
		const on = ctl.showVP && subject !== 'index'; // 매물대 = 종목 호가 멘탈모델 전용 · 지수 무의미(01 §4.2)
		const c = chart;
		if (!c) return;
		if (on && !vpOn) {
			vpOn = !!c.createIndicator({ name: VP_INDICATOR }, true, { id: 'candle_pane' });
		} else if (!on && vpOn) {
			try { c.removeIndicator('candle_pane', VP_INDICATOR); } catch { /* */ }
			vpOn = false;
		}
	});

	// 메인 오버레이 reconcile (다중 · candle_pane 스택). ICHI 활성 시 선행스팬용 우측 여백 확보.
	$effect(() => {
		const dgn = degenerateOverlays; // US 지수 ICHI degenerate 배제(01 §4.2)
		const want = new Set(ctl.overlays.filter((k) => !dgn.has(k)));
		const c = chart;
		if (!c) return;
		for (const k of [...mainOn]) if (!want.has(k)) { c.removeIndicator('candle_pane', k); mainOn.delete(k); delete appliedParams[k]; }
		want.forEach((k) => {
			if (mainOn.has(k)) return;
			// 커스텀 없으면 IND_DEFS 기본 명시 전달 · RSI 14 등 전문가 표준 교정값 적용
			const cp = ctl.indParams[k] ?? (IND_DEFS[k]?.defaults.length ? IND_DEFS[k].defaults : undefined);
			if (c.createIndicator(cp ? { name: k, calcParams: cp } : k, true, { id: 'candle_pane' })) {
				mainOn.add(k);
				if (cp) appliedParams[k] = cp;
			}
		});
		// 우측 여백은 항상 0 · 일목(ICHI) 구름 미래연장도 미래 축을 열지 않는다 (데이터 끝 = 차트 끝 불변).
		try { c.setOffsetRightDistance(0); } catch { /* */ }
	});

	// 보조지표 페인 reconcile
	$effect(() => {
		const dgn = degenerateSubs; // US 지수 degenerate 능동 배제 · chip 비활성만으론 이미 켜진 페인 잔존(01 §4.2 ★)
		const want = new Set(ctl.subs.filter((k) => !dgn.has(k)));
		const c = chart;
		if (!c) return;
		for (const [k, paneId] of [...subPanes]) if (!want.has(k)) { c.removeIndicator(paneId); subPanes.delete(k); delete appliedParams[k]; }
		want.forEach((k) => {
			if (subPanes.has(k)) return;
			const cp = ctl.indParams[k] ?? (IND_DEFS[k]?.defaults.length ? IND_DEFS[k].defaults : undefined);
			// 자릿수 통일 · 라이브러리 기본 precision 4(RSI 64.7436 류) 과잉. 수량 페인(VOL·TVAL·OBV·PVT)은
			// 정수 + 만·억 단위, 그 외 오실레이터는 소수 2자리 고정.
			const precision = k === 'VOL' || k === 'TVAL' || k === 'OBV' || k === 'PVT' ? 0 : 2;
			const id = c.createIndicator({ name: k, precision, ...(cp ? { calcParams: cp } : {}) }, false, { id: `pane_${k}`, height: subPaneHeight(), minHeight: 48, dragEnabled: true });
			if (id) {
				subPanes.set(k, id);
				if (cp) appliedParams[k] = cp;
			}
		});
	});

	// 지표 파라미터 적용 · appliedParams 스냅샷과 diff, 변경분만 overrideIndicator.
	// ⚠ override 에 minValue/maxValue 절대 전달 금지 (klinecharts 내부 오배선 · calcParams 만).
	$effect(() => {
		const ip = ctl.indParams;
		const c = chart;
		if (!c) return;
		const names = new Set([...Object.keys(ip), ...Object.keys(appliedParams)]);
		for (const k of names) {
			const next = ip[k] ?? IND_DEFS[k]?.defaults;
			const prev = appliedParams[k];
			if (!next || (prev && prev.length === next.length && prev.every((v, i) => v === next[i]))) continue;
			const paneId = mainOn.has(k as OverlayKey) ? 'candle_pane' : subPanes.get(k as SubKey);
			if (!paneId) continue;
			try { c.overrideIndicator({ name: k, calcParams: next }, paneId); } catch { /* */ }
			if (ip[k]) appliedParams[k] = next;
			else delete appliedParams[k];
			// ICHI 파라미터 변경도 우측 여백 불변(0) · 미래 축 금지 룰과 동일
		}
	});

	// 적정주가 밴드 → priceLine 오버레이 (토글)
	$effect(() => {
		const vb = valBand;
		const on = ctl.showBand;
		const c = chart;
		if (!c) return;
		bandIds.forEach((id) => c.removeOverlay(id));
		bandIds = [];
		if (on && vb && vb.hi > vb.lo) {
			const mk = (price: number, color: string) => c.createOverlay({ name: 'priceLine', points: [{ value: price }], lock: true, styles: { line: { color, style: 'dashed', size: 1 }, text: { color } } });
			bandIds = [mk(vb.hi, 'rgba(96,165,250,0.5)'), mk(vb.mid, 'rgba(96,165,250,0.85)'), mk(vb.lo, 'rgba(96,165,250,0.5)')].filter(Boolean) as string[];
		}
	});

	// 52주 고가·저가·전일종가 기준선 (HTS 관례 색: 고=적, 저=청, 전일=회) · 일봉 기준 산출.
	$effect(() => {
		const on = ctl.showRefs;
		void ctl.adj;
		void dataRev;
		const c = chart;
		if (!c) return;
		refIds.forEach((id) => c.removeOverlay(id));
		refIds = [];
		if (!on) return;
		const base = displaySeries();
		if (base.length < 2) return;
		const win = base.slice(-252);
		let hi = -Infinity;
		let lo = Infinity;
		for (const k of win) {
			if (k.h > hi) hi = k.h;
			if (k.l < lo) lo = k.l;
		}
		const prevC = base[base.length - 2].c;
		const mk = (price: number, color: string) => c.createOverlay({ name: 'priceLine', points: [{ value: price }], lock: true, styles: { line: { color, style: 'dashed', size: 1 }, text: { color } } });
		refIds = [mk(hi, 'rgba(240,97,111,0.65)'), mk(lo, 'rgba(96,165,250,0.65)'), mk(prevC, 'rgba(139,145,158,0.65)')].filter(Boolean) as string[];
	});

	// 실적·공시 시점 마커 → simpleAnnotation (토글, 가장 가까운 거래일 스냅).
	// 표시 시계열(수정주가 반영) 기준으로 고가 스냅 · 원본 기준이면 분할 이전 마커가 차트 밖으로 나간다.
	$effect(() => {
		const evs = events;
		const on = ctl.showEvents;
		void ctl.adj;
		const cs = candles.length ? displaySeries() : candles;
		const c = chart;
		if (!c || !cs.length) return;
		eventIds.forEach((id) => c.removeOverlay(id));
		eventIds = [];
		if (!on || !evs || !evs.length) return;
		const first = cs[0].t;
		const last = cs[cs.length - 1].t;
		const snap = (d: string) => { let best = cs[0]; let bd = Infinity; for (const k of cs) { const dd = Math.abs(Number(k.t) - Number(d)); if (dd < bd) { bd = dd; best = k; } } return best; };
		const ids: string[] = [];
		for (const ev of evs) {
			if (ev.date < first || ev.date > last) continue;
			const k = snap(ev.date);
			// 공시 시점 = dartlab 고유 강점. 비정기 material 공시(disclosure)는 cyan, 실적·증자(report·capital)는 orange.
			// url 보유 마커는 클릭 시 해당 DART 공시를 새 탭으로 · 가격차트가 곧 네비게이션 가능한 공시 타임라인.
			const disc = ev.kind === 'disclosure';
			const fg = disc ? '#22d3ee' : '#ff3f6f';
			const bg = disc ? 'rgba(34,211,238,0.12)' : 'rgba(var(--amber-rgb),0.12)';
			const bd = disc ? 'rgba(34,211,238,0.5)' : 'rgba(var(--amber-rgb),0.5)';
			const evUrl = ev.url;
			const id = c.createOverlay({
				name: 'simpleAnnotation',
				extendData: ev.label,
				points: [{ timestamp: toMs(k.t), value: k.h }],
				styles: { text: { color: fg, backgroundColor: bg, borderColor: bd } },
				onClick: evUrl
					? () => {
							window.open(evUrl, '_blank', 'noopener,noreferrer');
							return false;
						}
					: null
			});
			if (id) ids.push(id as string);
		}
		eventIds = ids;
	});

	// Y축 모드 / 캔들 스타일
	$effect(() => {
		const m = ctl.yMode;
		const c = chart;
		if (!c) return;
		try { c.setStyles({ yAxis: { type: m } }); } catch { /* */ }
	});
	$effect(() => {
		const t = ctl.candleStyle;
		const eff = effectiveCandleType; // indexLine(US 지수) → 'area' 강제 (ctl.candleStyle 영속값 불변)
		const lg = lang;
		const c = chart;
		if (!c) return;
		try { c.setStyles({ candle: { type: eff, tooltip: { custom: tooltipCustom(lg) } } }); } catch { /* */ }
		// HA ↔ 비HA 전환만 데이터 재변환 (스냅샷 가드). US 지수(indexLine)는 HA 무의미 → 재적용 스킵.
		if (!indexLine && t !== appliedStyle) {
			const wasHa = appliedStyle === 'ha';
			appliedStyle = t;
			if (wasHa || t === 'ha') reapply(c);
		}
	});

	// period·커스텀구간 변경 → 가시 봉 수 + 필요 시 과거 백필. 리플레이는 시작점 기준이 달라지므로 자동 종료.
	$effect(() => {
		void ctl.period;
		void ctl.btWinFrom; void ctl.btWinTo; // 커스텀 검증 구간 · 차트 줌·백필 동기
		const c = chart;
		if (!c || !candles.length) return;
		untrack(() => { if (ctl.replay.on) ctl.replayExit(); }); // 비silent · replay effect 가 전체 복원
		applyPeriodFull(c);
	});

	// ★펀더게이트(W2 간판②) · fundGate 조건 쓰는 룰 있을 때만 종목별 게이트 행 로드(비동기, 불필요 로드 회피).
	//   완료 시 btGateRows 갱신 → BT effect 재실행(반응). 종목 전환 시 재로드. 캐시는 data/fetch 코어가 공유.
	let btGateRows = $state<FundamentalGateRow[] | null>(null);
	let btGateCode = $state<string | null>(null);
	$effect(() => {
		const usesGate = ctl.btStrategies.some((s) => s.rule && ruleUsesGate(s.rule));
		if (!usesGate || subject === 'index') return;
		if (btGateCode === code) return; // 이미 로드된 종목
		btGateCode = code;
		loadGateRows(code)
			.then((rows) => { if (btGateCode === code) btGateRows = rows ?? []; })
			.catch(() => { if (btGateCode === code) btGateRows = []; });
	});

	// 백테스트 · 의존: 전략 슬롯 N(프리셋·파라미터·색·라벨)·포커스·비용(토글+bp)·기간·dataRev·게이트.
	$effect(() => {
		const c = chart;
		const slots = ctl.btStrategies; // 반응 의존 (배열 신참조마다 재실행)
		const focus = ctl.btFocus;
		const wc = ctl.btCosts;
		const bp = ctl.btCostsBp;
		void dataRev;
		void ctl.period;
		void ctl.btWinFrom; void ctl.btWinTo; // 커스텀 검증 구간 · 변경 시 재계산(엔진 입력 슬라이싱)
		const gateRows = btGateRows; // 반응 의존 · 게이트 로드 완료 시 재계산
		if (!c) return;
		// 지수 subject = 거래 대상 아님. 또한 종목별 백테스트 viz 는 '단일종목' 스코프 전용 ·
		// 시장(지수 타이밍)·유니버스 스코프에서 종목 결과를 그리면 '시장/유니버스'로 오도(정직: 칩·에쿼티도 비움).
		if (subject === 'index' || !slots.length || ctl.btScope !== 'single') {
			clearBt(c);
			btPf = null;
			btCandleTs = [];
			btFullRef = null;
			return;
		}
		void ctl.adj;
		const isDaily = ctl.tf === 'D'; // 주/월봉이면 캔버스 viz(마커·에쿼티) 숨김 · 일봉 ts 정렬 깨짐(숫자는 일봉으로 정확)
		const oos = ctl.btOosSplit;
		// 표시 시계열(수정주가 기본 ON)로 백테스트 · 원본이면 분할 절벽을 -98% 폭락으로 오인한다.
		let all = displaySeries();
		if (!all.length) return;
		let win: number;
		if (ctl.btCustomWin) {
			// 커스텀 구간 · from/to 인덱스 찾아 끝을 toIdx 로 절단(엔진 무수정: 신호 워밍업은 fromIdx 이전 전이력으로 자동 확보). win=구간 봉수.
			const fromT = ctl.btWinFrom as string;
			const toT = ctl.btWinTo as string;
			let fi = 0; while (fi < all.length && all[fi].t < fromT) fi++;
			let ti = all.length - 1; while (ti >= 0 && all[ti].t > toT) ti--;
			// 백필 진행 중(과거 연도 로드)이면 쓰레기 1봉 계산 대신 직전 결과 유지하고 대기(dataRev bump 시 재계산).
			if ((ti < 0 || all[0].t > fromT) && hist.loading) return;
			if (ti < 0 || fi >= all.length || ti < fi) { clearBt(c); btPf = null; btCandleTs = []; btFullRef = null; return; } // 구간이 데이터 범위 밖
			all = all.slice(0, ti + 1);
			win = ti - fi + 1;
		} else {
			win = Math.min(PERIOD_N[ctl.period] ?? all.length, all.length);
		}
		// 펀더게이트 PIT 시계열 · 게이트 룰 있을 때만(공시일 이후 봉 계단, look-ahead 0). 없으면 null(회귀 0).
		const usesGate = slots.some((s) => s.rule && ruleUsesGate(s.rule));
		const gate = usesGate ? buildGateSeries(all.map((cd) => cd.t), gateRows ?? []) : null;
		// 다전략(N≤3) + 동일가중 조합. look-ahead 차단은 displaySeries 절단이 N전략에 상속(01 §2.2).
		// extendData 신참조가 재계산 트리거(CMP 식). 슬롯별 spec.code 공통(단일종목).
		const stop = ctl.btStop.lossPct || ctl.btStop.gainPct ? { ...ctl.btStop } : null; // 손절/익절(S2) · 빈값=미적용
		const pf = runPortfolioBacktest(all, slots, { windowBars: win, withCosts: wc, costsBp: bp, oosSplit: oos, gate, stop, spec: { code, name, market: 'KR', dataSource: 'gov/prices', adjusted: ctl.adj } });
		btPf = pf;
		btCandleTs = all.map((cd) => cd.t); // equity 인덱스 정렬 · BacktestDialog 가 startIdx 오프셋으로 슬라이스
		// G3 체리피킹 대조 · 창이 전체의 *진부분집합*일 때만 같은 전략을 전체 기간에도 돌려 '이 구간 vs 전체' 병기(전체기간 선택=대조 무의미·자백 불필요).
		if (ctl.btWindowIsSubset) {
			const fullSer = displaySeries();
			const fullGate = usesGate ? buildGateSeries(fullSer.map((cd) => cd.t), gateRows ?? []) : null;
			// oosSplit:0 · 전체기간 대조는 in/out 분할 없는 순수 벤치(체리피킹 자백 기준선).
			const pfFull = runPortfolioBacktest(fullSer, slots, { windowBars: fullSer.length, withCosts: wc, costsBp: bp, oosSplit: 0, gate: fullGate, stop, spec: { code, name, market: 'KR', dataSource: 'gov/prices', adjusted: ctl.adj } });
			const fr = pfFull?.slots[Math.min(focus, (pfFull.slots.length || 1) - 1)]?.result ?? null;
			btFullRef = fr ? { retPct: fr.metrics.retPct, bhRetPct: fr.bh.retPct, cagrPct: fr.metrics.cagrPct, fromT: fullSer[fr.startIdx]?.t ?? '', toT: fullSer[fullSer.length - 1]?.t ?? '', bars: fr.equity.filter((v) => v != null).length } : null;
		} else {
			btFullRef = null;
		}
		// 펀더게이트 배경 틴트 · 포커스 전략의 fundGate 조건(임계값)으로 활성 구간 산출(공시일 이후 PIT 계단).
		let gateVis: { active: (0 | 1)[]; label: string } | null = null;
		if (gate && usesGate) {
			const frule = slots[Math.min(focus, slots.length - 1)]?.rule;
			const fc = frule ? [...frule.entry, ...frule.exit].find((cc) => cc.left === 'fundGate' && cc.right.kind === 'const') : null;
			if (fc && fc.right.kind === 'const') {
				const thr = fc.right.value;
				const active = gate.map((v): 0 | 1 => {
					if (v == null) return 0;
					const ok = fc.op === '>=' ? v >= thr : fc.op === '>' ? v > thr : fc.op === '<=' ? v <= thr : fc.op === '<' ? v < thr : false;
					return ok ? 1 : 0;
				});
				gateVis = { active, label: `Piotroski ${fc.op} ${thr}` };
			}
		}
		// 차트가 일봉일 때만 캔버스 viz · 주/월봉은 일봉 거래 ts 와 정렬 불가라 숨김(칩·보고서 숫자는 일봉 그대로 정확).
		const ext = isDaily ? buildBtExtend(pf, all, slots, focus, gateVis) : null;
		if (ext) applyBt(c, ext);
		else clearBt(c);
	});

	// 종목비교 오버레이 · 피어 회사파일 로드 → 수정주가 동일 보정 → CMP 생성/override.
	// 피어 보정 누락 = 피어 분할이 상대수익률을 왜곡하므로 본주와 같은 adj 정책 강제.
	$effect(() => {
		const list = ctl.compares;
		const adjOn = ctl.adj;
		const c = chart;
		if (!c) return;
		if (!list.length) {
			if (cmpOn) {
				try { c.removeIndicator('candle_pane', CMP_INDICATOR); } catch { /* */ }
				cmpOn = false;
			}
			return;
		}
		const token = ++cmpToken;
		const yr = new Date().getFullYear();
		Promise.all(list.map((p) => rt.price.initial(p.code, yr))).then((rs) => {
			if (token !== cmpToken || chart !== c) return;
			const loaded = list
				.map((p, i) => {
					const cs = rs[i]?.candles ?? [];
					return { code: p.code, name: p.name, candles: adjOn ? adjustCandles(cs) : cs };
				})
				.filter((p) => p.candles.length);
			const extendData: CmpExtend = { peers: loaded };
			if (cmpOn) c.overrideIndicator({ name: CMP_INDICATOR, extendData }, 'candle_pane');
			else cmpOn = !!c.createIndicator({ name: CMP_INDICATOR, extendData }, true, { id: 'candle_pane' });
			// 기간 수익률 미니표 (VS 팝오버) · 이미 로드한 피어 캔들 재사용, 추가 다운로드 0
			const mainAll = untrack(() => fullSeries());
			cmpRows = [
				{ name, code, r: CMP_RET_BARS.map((n) => retOf(mainAll.length ? mainAll : candles, n)) },
				...loaded.map((p) => ({ name: p.name, code: p.code, r: CMP_RET_BARS.map((n) => retOf(p.candles, n)) }))
			];
		});
	});
	// 본주+비교종목 기간 수익률 (1M/3M/6M/1Y) · VS 팝오버 미니표 데이터
	const CMP_RET_BARS = [21, 63, 132, 252];
	const retOf = (cs: Candle[], n: number): number | null =>
		cs.length > n && cs[cs.length - 1 - n].c ? (cs[cs.length - 1].c / cs[cs.length - 1 - n].c - 1) * 100 : null;
	let cmpRows = $state<{ name: string; code: string; r: (number | null)[] }[]>([]);
	$effect(() => {
		if (!ctl.compares.length) cmpRows = [];
	});

	// 경제지표 오버레이 · 선택 → 로드 → 생성/override (figures:[] = 캔들 y축 무왜곡, econOverlay.ts)
	$effect(() => {
		const ids = ctl.econ;
		const c = chart;
		const lg = lang;
		if (!c) return;
		if (!ids.length) {
			if (econOn) {
				try { c.removeIndicator('candle_pane', ECON_INDICATOR); } catch { /* */ }
				econOn = false;
			}
			return;
		}
		const token = ++econToken;
		(async () => {
			// 듀얼 소스 · id 가 'idx:' 면 시장지수(인덱스 포트), 아니면 거시(macro 포트). def 은 둘 다 econOverlay 가 동일 소비.
			const mkt = await loadMarketIndexSeries(rt.index);
			const resolved = await Promise.all(
				ids.map(async (id) => {
					if (id.startsWith('idx:')) {
						const m = mkt.find((x) => x.ref.code === id);
						return m ? { def: marketIndexDef(m.ref), points: m.points } : null;
					}
					const def = MACRO_SERIES.find((s) => s.id === id);
					return def ? { def, points: (await rt.macro.getSeries(id)) ?? [] } : null;
				})
			);
			if (token !== econToken || chart !== c) return; // 선택 변경·인스턴스 교체 → 폐기
			const series = resolved.filter((s): s is NonNullable<typeof s> => !!s && s.points.length > 0);
			const extendData: EconExtend = { lang: lg, series }; // 항상 새 참조 → setExtendData 재계산 보장
			if (econOn) c.overrideIndicator({ name: ECON_INDICATOR, extendData }, 'candle_pane');
			else econOn = !!c.createIndicator({ name: ECON_INDICATOR, extendData }, true, { id: 'candle_pane' });
		})();
	});

	// 전체화면 토글 → resize + 보조 페인 비례 재배분 + 전문가 단축키 레이어.
	// ESC 2단(진행중 드로잉 취소 → 닫기) · Delete 선택삭제 · ←/→ 스크롤(Shift=한 화면) ·
	// +/− 줌 · 1~6 기간 · D/W/M 봉주기 · 전체화면 한정 (일반 모드 = 페이지 스크롤 충돌).
	$effect(() => {
		if (!browser) return;
		const c = chart;
		void ctl.full;
		requestAnimationFrame(() => {
			try {
				c?.resize();
				const ph = subPaneHeight();
				for (const paneId of subPanes.values()) c?.setPaneOptions({ id: paneId, height: ph });
			} catch { /* */ }
		});
		if (!ctl.full) {
			// 전체화면 닫힘 · 리플레이 컨트롤(리본)이 사라지므로 동행 종료 (replay effect 가 전체 복원)
			untrack(() => { if (ctl.replay.on) ctl.replayExit(); });
			jumpOpen = false;
			helpOpen = false;
			// 일반 모드 · Shift+F 전체화면 진입 (그 외 단일 키는 페이지 스크롤·검색과 충돌하므로 추가 금지)
			const onKeyMini = (e: KeyboardEvent) => {
				const tgt = e.target as HTMLElement | null;
				if (tgt && (tgt.tagName === 'INPUT' || tgt.tagName === 'TEXTAREA' || tgt.isContentEditable)) return;
				if (e.shiftKey && (e.key === 'F' || e.key === 'f') && !e.metaKey && !e.ctrlKey && !e.altKey) {
					e.preventDefault();
					ctl.full = true;
				}
			};
			window.addEventListener('keydown', onKeyMini);
			return () => window.removeEventListener('keydown', onKeyMini);
		}
		const PERIOD_KEYS = ['1M', '3M', '6M', '1Y', '3Y', 'MAX'] as const;
		const onKey = (e: KeyboardEvent) => {
			const k = e.key;
			// 심볼 점프 · ⌘K·/ (TV 관행). input 가드보다 먼저: Terminal 전역 핸들러는 전체화면을
			// 감지해 양보한다 (보이지 않는 검색창 포커스 트랩 버그 수정 짝).
			if (((e.metaKey || e.ctrlKey) && k.toLowerCase() === 'k') || (k === '/' && !(e.target as HTMLElement | null)?.closest?.('input,textarea'))) {
				if (suggest && onPick) {
					e.preventDefault();
					jumpOpen = !jumpOpen;
					helpOpen = false;
					if (jumpOpen) requestAnimationFrame(() => jumpInput?.focus());
					return;
				}
			}
			const tgt = e.target as HTMLElement | null;
			if (tgt && (tgt.tagName === 'INPUT' || tgt.tagName === 'TEXTAREA' || tgt.isContentEditable)) return;
			if (k === 'Escape') {
				// 우선순위: 점프/도움말 닫기 → 진행중 드로잉 취소 → 리플레이 종료 → 전체화면 닫기
				if (jumpOpen || helpOpen) { jumpOpen = false; helpOpen = false; return; }
				if (cancelPendingDraw()) return;
				if (ctl.replay.on) { ctl.replayExit(); return; }
				ctl.full = false;
			} else if (k === '?') {
				helpOpen = !helpOpen;
				jumpOpen = false;
			} else if (k === ' ' && ctl.replay.on) {
				e.preventDefault(); // 리플레이 · 스페이스 = 재생/정지 (동영상 멘탈모델)
				ctl.replay.playing = !ctl.replay.playing;
			} else if (k === 'Delete' || k === 'Backspace') {
				removeDraw(selectedDrawId);
			} else if (k === 'ArrowLeft' || k === 'ArrowRight') {
				e.preventDefault();
				if (ctl.replay.on) { if (k === 'ArrowRight') ctl.replayStep(); else ctl.replayStepBack(); return; } // 리플레이 · →/← 한 봉 전·후진
				const bs = (() => { try { return c?.getBarSpace?.() ?? 8; } catch { return 8; } })();
				const w = el?.clientWidth || 800;
				const step = e.shiftKey ? w : bs * 8;
				try { c?.scrollByDistance(k === 'ArrowLeft' ? step : -step, 0); } catch { /* */ }
			} else if (k === '+' || k === '=') {
				try { c?.zoomAtCoordinate(1.15); } catch { /* */ }
			} else if (k === '-' || k === '_') {
				try { c?.zoomAtCoordinate(0.87); } catch { /* */ }
			} else if (k >= '1' && k <= '6' && !e.metaKey && !e.ctrlKey && !e.altKey) {
				ctl.period = PERIOD_KEYS[+k - 1];
			} else if ((k === 'd' || k === 'D') && !e.metaKey && !e.ctrlKey) {
				ctl.tf = 'D';
			} else if ((k === 'w' || k === 'W') && !e.metaKey && !e.ctrlKey) {
				ctl.tf = 'W';
			} else if ((k === 'm' || k === 'M') && !e.metaKey && !e.ctrlKey) {
				ctl.tf = 'M';
			} else if ((k === 'q' || k === 'Q') && !e.metaKey && !e.ctrlKey) {
				ctl.tf = 'Q';
			} else if ((k === 'y' || k === 'Y') && !e.metaKey && !e.ctrlKey) {
				ctl.tf = 'Y';
			} else if ((k === 'r' || k === 'R') && !e.metaKey && !e.ctrlKey) {
				if (ctl.replay.on) ctl.replayExit();
				else enterReplay(); // 리플레이 토글
			} else if ((k === 'a' || k === 'A') && !e.metaKey && !e.ctrlKey) {
				ctl.adj = !ctl.adj; // 수정주가
			} else if ((k === 'l' || k === 'L') && !e.metaKey && !e.ctrlKey) {
				ctl.yMode = ctl.yMode === 'log' ? 'normal' : 'log'; // 로그축
			} else if ((k === 'g' || k === 'G') && !e.metaKey && !e.ctrlKey) {
				ctl.showRefs = !ctl.showRefs; // 52주·전일 기준선
			} else if ((k === 'f' || k === 'F') && !e.metaKey && !e.ctrlKey && !e.shiftKey) {
				ctl.full = false; // 진입(Shift+F)과 대칭
			} else if ((k === 's' || k === 'S') && !e.metaKey && !e.ctrlKey) {
				snapshot();
			}
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});

	// ── 드로잉 · 완성 시점 카운트·우클릭/Delete 삭제·드래그 편집 재저장·회사별 localStorage 영속 ──
	const serializeDraw = (o: any): SavedDraw => ({
		name: o.name,
		points: (o.points ?? []).map((p: any) => ({ timestamp: p.timestamp, value: p.value })),
		...(typeof o.extendData === 'string' && o.extendData ? { text: o.extendData } : {})
	});
	function persistDraws() { saveDraws(hist.code, [...drawMap.values()]); }
	// 텍스트 주석 인라인 에디터 · 배치/더블클릭 시 점 위에 입력창. Enter 확정·Esc/빈값 취소(도형 제거).
	let textEdit = $state<{ id: string; x: number; y: number; value: string } | null>(null);
	function openTextEditor(o: any) {
		if (!chart || !o?.id) return;
		let x = 90;
		let y = 60;
		try {
			const p0 = o.points?.[0];
			const px = chart.convertToPixel({ timestamp: p0?.timestamp, value: p0?.value }, { paneId: 'candle_pane' });
			const p = Array.isArray(px) ? px[0] : px;
			if (p && Number.isFinite(p.x) && Number.isFinite(p.y)) { x = p.x; y = p.y; }
		} catch { /* 좌표 실패 · 기본 위치 */ }
		textEdit = { id: o.id, x, y, value: typeof o.extendData === 'string' ? o.extendData : '' };
	}
	function commitText(save: boolean) {
		const te = textEdit;
		textEdit = null;
		if (!te) return;
		const val = save ? te.value.trim() : '';
		if (!val) { removeDraw(te.id); return; }
		try { chart?.overrideOverlay({ id: te.id, extendData: val }); } catch { /* */ }
		const d = drawMap.get(te.id);
		if (d) { drawMap.set(te.id, { ...d, text: val }); persistDraws(); }
	}
	const focusOnMount = (el: HTMLInputElement) => { el.focus(); el.select(); };
	function drawOpts(toolName: string, points?: SavedDraw['points'], text?: string) {
		const ephemeral = toolName === MEASURE_NAME; // 측정룰러 · 영속 제외, 선택 해제 시 자동 제거
		return {
			name: toolName,
			groupId: 'draw',
			...(points ? { points } : {}),
			...(text ? { extendData: text } : {}),
			mode: ctl.magnet ? 'weak_magnet' : 'normal',
			onDrawEnd: (e: any) => {
				const o = e.overlay;
				if (!o?.id) return;
				if (pendingDrawId === o.id) pendingDrawId = null;
				if (ephemeral) return;
				drawMap.set(o.id, serializeDraw(o));
				ctl.drawCount = drawMap.size;
				persistDraws();
				// 텍스트 주석 · 배치 직후 인라인 입력 (연속 그리기 재시작 없음)
				if (toolName === TEXT_NAME && typeof o.extendData !== 'string') { setTimeout(() => openTextEditor(o), 0); return; }
				// 연속 그리기 · 같은 도구 즉시 재시작. setTimeout 0 = klinecharts 클릭 이벤트 재진입 회피.
				// 복원(points 사전 채움)은 onDrawEnd 미발화라 회사전환 시 유령 도구가 생기지 않는다.
				if (ctl.stayDraw) setTimeout(() => startDraw(toolName), 0);
			},
			onDoubleClick: (e: any) => {
				if (toolName === TEXT_NAME) { openTextEditor(e.overlay); return true; }
				return false;
			},
			onPressedMoveEnd: (e: any) => {
				const o = e.overlay;
				if (!o?.id || !drawMap.has(o.id)) return;
				drawMap.set(o.id, serializeDraw(o));
				persistDraws();
			},
			onSelected: (e: any) => { selectedDrawId = e.overlay?.id ?? null; },
			onDeselected: (e: any) => {
				if (selectedDrawId === e.overlay?.id) selectedDrawId = null;
				if (ephemeral && e.overlay?.id) { try { chart?.removeOverlay(e.overlay.id); } catch { /* */ } }
			},
			onRightClick: (e: any) => { removeDraw(e.overlay?.id); return true; }
		};
	}
	function removeDraw(id?: string | null) {
		if (!id) return;
		try { chart?.removeOverlay(id); } catch { /* */ }
		drawMap.delete(id);
		if (selectedDrawId === id) selectedDrawId = null;
		if (pendingDrawId === id) pendingDrawId = null;
		ctl.drawCount = drawMap.size;
		persistDraws();
	}
	function cancelPendingDraw(): boolean {
		if (!pendingDrawId) return false;
		try { chart?.removeOverlay(pendingDrawId); } catch { /* */ }
		pendingDrawId = null;
		return true;
	}
	function restoreDraws(c: any) {
		for (const d of loadDraws(hist.code)) {
			const id = c.createOverlay(drawOpts(d.name, d.points, d.text));
			if (id) drawMap.set(id as string, d);
		}
		ctl.drawCount = drawMap.size;
	}
	function startDraw(toolName: string) {
		try {
			cancelPendingDraw(); // 미완 도형 교체 · 유령 진행상태 방지
			const id = chart?.createOverlay(drawOpts(toolName));
			if (id) pendingDrawId = id as string;
		} catch { /* */ }
	}
	function clearDraw() {
		try { chart?.removeOverlay({ groupId: 'draw' }); } catch { /* */ }
		drawMap.clear();
		pendingDrawId = null;
		selectedDrawId = null;
		ctl.drawCount = 0;
		persistDraws();
	}
	// 차트 환경 설정 영속 · persist() 내부의 상태 읽기가 전부 의존이 되어 변경 시마다 저장
	$effect(() => {
		ctl.persist();
	});

	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);
	// 출처 표기 SSOT · DOM 캡션과 스냅샷 띠가 같은 문자열 (공공누리 출처표시 의무)
	const srcText = () =>
		T('출처: 금융위원회·한국거래소 (공공데이터포털)', 'Source: FSC · KRX (data.go.kr)') +
		(ctl.econ.length ? ' · ' + MACRO_ATTRIBUTION : '') +
		(ctl.adj ? T(' · 수정주가', ' · adjusted') : '') +
		(ctl.candleStyle === 'ha' ? ' · HA' : ''); // 하이킨아시 = 변형값 정직 고지
	function snapshot() {
		const ymd = candles.length ? candles[candles.length - 1].t : '';
		const date = ymd ? `${ymd.slice(0, 4)}-${ymd.slice(4, 6)}-${ymd.slice(6, 8)}` : '';
		void downloadSnapshot(chart, { fileTag: `${code}_${ymd}`, srcLine: `${name} ${code} · ${date} · ${srcText()}` }).catch(() => { /* 이미지 합성 실패 · 무해 */ });
	}
	// 가격 시계열 CSV(표) · terminal-data-download PRD. render 진실(chart.getDataList) 직렬화.
	//  index=출처(GOV) 불일치, HA=합성봉, 리플레이=절단 시계열 -> 비활성(버튼 미렌더). 이 3 게이트가 canCsv.
	const canCsv = $derived(subject !== 'index' && ctl.candleStyle !== 'ha' && !ctl.replay.on);
	function exportCsv() {
		if (!canCsv) return;
		let bars: PriceBar[] = [];
		try {
			bars = (chart?.getDataList?.() ?? []) as PriceBar[]; // candles prop 아님 = 백필 무성절단 방지(함정 1)
		} catch {
			bars = [];
		}
		if (!bars.length) return;
		const rows = priceBarsToRows(bars);
		downloadCsv(priceCsvFilename(code, rows, ctl.tf, ctl.adj), [...PRICE_CSV_COLUMNS] as string[], rows as unknown as Array<Record<string, unknown>>);
	}
	// 실시간 틱 (나중 가격 API 연결 시 호출) · 일봉 전용 (주/월 집계 봉에 일봉 append 방지)
	export function pushTick(c: Candle) { if (ctl.tf !== 'D') return; try { chart?.updateData(toK(c)); } catch { /* */ } }
</script>

<div class="chartWrap" class:full={ctl.full} role="img" aria-label="price chart" style={ctl.full ? '' : 'height:480px;min-height:360px;'}>
	{#if !ctl.full}
		<!-- 차트 컨트롤 바 · 그래프 위 전용 행(absolute 오버레이 아님, 밀도). 전체화면은 ChartRibbon. -->
		<ChartMenus {ctl} {lang} {subject} {indexLine} {indexCtl} {coMovers} {marketCoMovers} hasBand={!!valBand} {railCatCounts} onDraw={startDraw} onClearDraw={clearDraw} onSnapshot={snapshot} onCsv={canCsv ? exportCsv : undefined} />
	{/if}
	<div class="chartHost" bind:this={el}></div>

	{#if railBox && railDots.length}
		<!-- 공시 위치 레일(02 §4) · x축 날짜라벨 아래 전용 띠. left/top/width=캔버스 geometry(전체화면 padding 자동 반영).
		     호버=그날 공시 전부 툴팁, 클릭=우측 정기/비정기 공시목록 그 날짜로(focusDisclosure · 원문 링크 아님). -->
		<div class="discRail" style={`left:${railBox.left}px;top:${railBox.top}px;width:${railBox.width}px`} aria-label={T('공시 위치', 'disclosure markers')}>
			{#each railDots as d (d.date)}
				<button
					class="discDot"
					class:multi={d.items.length > 1}
					class:hasReg={d.items.some((i) => i.kind === 'regular')}
					class:hasNews={d.items.some((i) => i.kind === 'news')}
					style={`left:${d.x}px;opacity:${Math.min(0.4 + d.items.length * 0.12, 0.92)}`}
					aria-label={`${d.date.slice(0, 4)}-${d.date.slice(4, 6)}-${d.date.slice(6, 8)} ${T('공시', 'filings')} ${d.items.length}`}
					onmouseenter={() => (hoverRail = { x: d.x, date: d.date, items: d.items })}
					onmouseleave={() => (hoverRail = null)}
					onfocus={() => (hoverRail = { x: d.x, date: d.date, items: d.items })}
					onblur={() => (hoverRail = null)}
					onclick={() => focusDisclosure(d.date)}
				></button>
			{/each}
			{#if hoverRail}
				{@const ht = hoverRail}
				{@const half = Math.min(132, railBox.width / 2)}
				<div class="discTip mono" style={`left:${Math.min(Math.max(ht.x, half), railBox.width - half)}px`} role="tooltip">
					<div class="discTipHd"><b class="discTipDate">{ymdDash(ht.date)}</b> · {T('공시', 'filings')} {ht.items.length}{T('건', '')}</div>
					{#each ht.items.slice(0, 12) as it (it.rceptNo)}
						<div class="discTipRow">{#if it.kind === 'regular'}<span class="discTipTag">{T('정기', 'REG')}</span>{:else if it.kind === 'news'}<span class="discTipTag news">{T('뉴스', 'NEWS')}</span>{/if}{it.title}</div>
					{/each}
					{#if ht.items.length > 12}<div class="discTipMore">{T('외 ', '+')}{ht.items.length - 12}{T('건', '')}</div>{/if}
					<div class="discTipFoot">{T('클릭 → 우측 공시목록', 'click → filings list')}</div>
				</div>
			{/if}
		</div>
		{#if hoverRail}
			<!-- 그 공시일 세로 가이드선 · 캔버스 전 높이(차트 크로스헤어 결). dot↔캔들 x 일치 확인 + 위치 강조. -->
			<div class="discGuide" style={`left:${railBox.left + hoverRail.x}px;top:${railBox.canvasTop}px;height:${railBox.top - railBox.canvasTop}px`}></div>
		{/if}
	{/if}

	{#if textEdit}
		<input
			class="drawTextIn mono"
			style={`left:${Math.round(Math.max(4, textEdit.x - 80))}px; top:${Math.round(Math.max(4, textEdit.y - 38))}px`}
			bind:value={textEdit.value}
			use:focusOnMount
			placeholder={T('메모 입력 후 Enter', 'note + Enter')}
			maxlength="80"
			onkeydown={(e) => {
				e.stopPropagation();
				if (e.key === 'Enter' && !e.isComposing) commitText(true);
				else if (e.key === 'Escape') commitText(false);
			}}
			onblur={() => commitText(true)}
		/>
	{/if}

	{#if ctl.full}
		<ChartRibbon {ctl} {lang} {subject} {indexLine} hasBand={!!valBand} {name} {code} info={ribbonInfo} {notice} {peers} {cmpRows} {railCatCounts} canJump={!!(suggest && onPick)} onSnapshot={snapshot} onCsv={canCsv ? exportCsv : undefined} onReplay={enterReplay} onJump={() => { jumpOpen = true; helpOpen = false; requestAnimationFrame(() => jumpInput?.focus()); }} onHelp={() => { helpOpen = !helpOpen; jumpOpen = false; }} />
		<DrawToolbar {ctl} {lang} onDraw={startDraw} onClearDraw={clearDraw} />

		{#if jumpOpen}
			<!-- 심볼 점프 팔레트 (⌘K · /) · 전체화면을 떠나지 않는 종목 전환 -->
			<div class="chartJump" role="dialog" aria-label={T('종목 점프', 'symbol jump')}>
				<input
					class="cjInput mono"
					bind:this={jumpInput}
					bind:value={jumpQ}
					spellcheck={false}
					placeholder={T('종목코드 · 회사명 · Enter 전환', 'code or name · Enter to switch')}
					oninput={() => (jumpIdx = 0)}
					onkeydown={(e) => {
						e.stopPropagation();
						if (e.key === 'Escape') { jumpOpen = false; return; }
						if (!jumpList.length) return;
						if (e.key === 'ArrowDown') { e.preventDefault(); jumpIdx = (jumpIdx + 1) % jumpList.length; }
						else if (e.key === 'ArrowUp') { e.preventDefault(); jumpIdx = (jumpIdx - 1 + jumpList.length) % jumpList.length; }
						else if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); jumpTo(jumpList[Math.max(0, jumpIdx)].code); }
					}}
				/>
				{#if jumpList.length}
					<div class="cjList">
						{#each jumpList as s, i (s.code)}
							<button type="button" class={'cjRow' + (i === jumpIdx ? ' on' : '')} onmousedown={() => jumpTo(s.code)} onmouseenter={() => (jumpIdx = i)}>
								<b>{s.name}</b><span class="mono">{s.code}</span><i>{s.industry}</i>
							</button>
						{/each}
					</div>
				{:else if jumpQ.trim()}
					<div class="cjEmpty">{T('검색 결과 없음', 'no match')}</div>
				{/if}
			</div>
		{/if}

		{#if helpOpen}
			<!-- 단축키·숨은기능 도움말 (?) · 발견성: 만들어 둔 기능을 "존재하게" 만드는 1장 -->
			<div class="chartHelp" role="dialog" aria-label={T('단축키 도움말', 'shortcuts')}>
				<div class="chHd">{T('단축키 · 숨은 기능', 'SHORTCUTS & HIDDEN GEMS')}<button class="cbtn cIco" onclick={() => (helpOpen = false)} title="ESC">✕</button></div>
				<div class="chCols">
					<div>
						<div class="chLbl">{T('탐색', 'NAVIGATE')}</div>
						<div class="chRow"><kbd>⌘K</kbd><kbd>/</kbd><span>{T('종목 점프 (전체화면 유지)', 'symbol jump')}</span></div>
						<div class="chRow"><kbd>1</kbd>-<kbd>6</kbd><span>{T('기간 1M·3M·6M·1Y·3Y·MAX', 'period presets')}</span></div>
						<div class="chRow"><kbd>D</kbd><kbd>W</kbd><kbd>M</kbd><kbd>Q</kbd><kbd>Y</kbd><span>{T('봉 주기', 'timeframe')}</span></div>
						<div class="chRow"><kbd>←</kbd><kbd>→</kbd><span>{T('스크롤 · Shift=한 화면', 'scroll · Shift=page')}</span></div>
						<div class="chRow"><kbd>+</kbd><kbd>−</kbd><span>{T('줌', 'zoom')}</span></div>
						<div class="chRow"><kbd>F</kbd><kbd>ESC</kbd><span>{T('전체화면 닫기 (일반 모드 Shift+F 진입)', 'exit fullscreen (Shift+F to enter)')}</span></div>
					</div>
					<div>
						<div class="chLbl">{T('보기 토글', 'VIEW')}</div>
						<div class="chRow"><kbd>A</kbd><span>{T('수정주가', 'adjusted price')}</span></div>
						<div class="chRow"><kbd>L</kbd><span>{T('로그축', 'log axis')}</span></div>
						<div class="chRow"><kbd>G</kbd><span>{T('52주 고저·전일 기준선', '52w/prev refs')}</span></div>
						<div class="chRow"><kbd>S</kbd><span>{T('차트 PNG 저장 (출처 띠 포함)', 'save PNG')}</span></div>
						<div class="chLbl">{T('리플레이', 'REPLAY')}</div>
						<div class="chRow"><kbd>R</kbd><span>{T('리플레이 시작/종료', 'toggle replay')}</span></div>
						<div class="chRow"><kbd>Space</kbd><span>{T('재생/정지', 'play/pause')}</span></div>
						<div class="chRow"><kbd>→</kbd><kbd>←</kbd><span>{T('한 봉 전진/후진', 'step fwd/back')}</span></div>
					</div>
					<div>
						<div class="chLbl">{T('드로잉', 'DRAW')}</div>
						<div class="chRow"><kbd>{T('우클릭', 'R-click')}</kbd><span>{T('도형 삭제', 'delete shape')}</span></div>
						<div class="chRow"><kbd>Del</kbd><span>{T('선택 도형 삭제', 'delete selected')}</span></div>
						<div class="chRow"><kbd>{T('더블클릭', 'Dbl-click')}</kbd><span>{T('텍스트 주석 편집', 'edit text note')}</span></div>
						<div class="chLbl">{T('숨은 기능', 'HIDDEN')}</div>
						<div class="chRow"><span>{T('페인 경계 드래그 = 높이 조절', 'drag pane divider = resize')}</span></div>
						<div class="chRow"><span>{T('드로잉·지표·차트틀은 자동 저장', 'drawings/indicators auto-saved')}</span></div>
						<div class="chRow"><span>{T('차트 좌측 끝 = 과거 자동 로드(2010~)', 'scroll left = auto backfill')}</span></div>
					</div>
				</div>
			</div>
		{/if}
	{/if}

	<!-- 출처(공공누리)는 차트 하단 캡션이 아니라 패널 헤더로 · onSrc 콜백(srcText). 스냅샷 PNG 는 srcText 를 띠로 합성(SSOT 유지). -->

	<!-- 차트 위 요약 칩 · railBox geometry 로 가격 페인 좌상단(OHLC 레전드 아래). 전체 정직 푸터는 도크가 담당. -->
	{#if btPf && ctl.btStrategies.length && railBox}
		<BtChip pf={btPf} slots={ctl.btStrategies} focus={ctl.btFocus} {lang} left={railBox.left + 8} top={railBox.canvasTop + 52} onOpenReport={() => { ctl.btReportMode = true; ctl.btTearsheetOpen = true; }} />
	{/if}
</div>

<style>
	/* 공시 위치 레일 · x축 날짜라벨 "아래" 전용 띠(캔버스 하단 padding 영역). left/top/width 는 인라인(캔버스 geometry),
	   bottom:0 으로 띠 높이를 chartWrap 하단까지 채운다. dot 은 중립 슬레이트(축 furniture 처럼 · 알람색 아님). */
	.discRail {
		position: absolute;
		bottom: 0;
		pointer-events: none;
		z-index: 3;
	}
	.discDot {
		position: absolute;
		top: 50%;
		transform: translate(-50%, -50%);
		width: 6px;
		height: 6px;
		padding: 0;
		border: none;
		border-radius: 50%;
		background: #8b97ad; /* 건수=opacity(인라인) */
		cursor: pointer;
		pointer-events: auto;
		transition: transform 0.1s, background 0.1s;
	}
	.discDot.multi {
		width: 8px;
		height: 8px;
		background: #aeb9cc;
	}
	/* 정기보고서(사업/반기/분기) 포함 날짜 · 한눈에 찾도록 amber 링 (캔들 실적 마커와 같은 계열색) */
	.discDot.hasReg {
		box-shadow: 0 0 0 1.5px rgba(var(--amber-rgb), 0.7);
	}
	/* 뉴스 포함 날짜 · teal 배경(공시 회색과 구분). hasReg 와 조합 시 amber 링 + teal 점(공시·뉴스 공존 표시). */
	.discDot.hasNews {
		background: #2dd4bf;
	}
	.discDot:hover,
	.discDot:focus-visible {
		transform: translate(-50%, -50%) scale(1.5);
		background: #cfe0ff;
		outline: none;
	}
	/* 호버 툴팁 · 그날 공시 전부. 레일 위로 띄움(chartWrap overflow:hidden 안이라 위로는 안 잘림). pointer-events:none. */
	.discTip {
		position: absolute;
		bottom: calc(100% + 4px);
		transform: translateX(-50%);
		min-width: 180px;
		max-width: 264px;
		pointer-events: none;
		background: rgba(12, 16, 24, 0.96);
		border: 1px solid #2a3142;
		border-radius: 4px;
		padding: 5px 7px;
		z-index: 12;
		box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45);
	}
	.discTipHd {
		font-size: 9px;
		color: #8b919e;
		letter-spacing: 0.4px;
		margin-bottom: 3px;
	}
	.discTipDate {
		color: #e2e8f5;
		font-weight: 700;
		font-size: 10px;
	}
	.discTipRow {
		font-size: 10.5px;
		line-height: 1.45;
		color: #cfd3dc;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.discTipTag {
		display: inline-block;
		font-size: 8px;
		color: var(--amber);
		border: 1px solid rgba(var(--amber-rgb), 0.5);
		border-radius: 2px;
		padding: 0 3px;
		margin-right: 4px;
		vertical-align: 1px;
	}
	.discTipTag.news {
		color: #2dd4bf;
		border-color: rgba(45, 212, 191, 0.5);
	}
	.discTipMore {
		font-size: 9.5px;
		color: var(--dimmer);
		margin-top: 2px;
	}
	.discTipFoot {
		font-size: 9px;
		color: #5b8aa0;
		margin-top: 4px;
		border-top: 1px solid #1c2330;
		padding-top: 3px;
	}
	/* 공시일 세로 가이드선 · dot 호버 시 캔버스 전 높이. 차트 크로스헤어(amber)와 같은 결, 살짝 옅게. */
	.discGuide {
		position: absolute;
		width: 1px;
		pointer-events: none;
		background: rgba(174, 185, 204, 0.5);
		z-index: 4;
	}
</style>
