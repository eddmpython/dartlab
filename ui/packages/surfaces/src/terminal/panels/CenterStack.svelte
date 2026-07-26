<script lang="ts">
	import { untrack } from 'svelte';
	import type { Candle, FinMode, FinScope, IndexRef, ProductIndexItem, TerminalFinanceBundle } from '@dartlab/ui-contracts';
	import { KR_INDEX_PRESETS } from '@dartlab/ui-contracts'; // 지수 기본값(코스피) · picker 칩은 ChartMenus 가 렌더
	import { useDartLabRuntime } from '@dartlab/ui-runtime';
	import type { Company, Lang, Tone, Num } from '../lib/types';
	import Panel from '../ui/Panel.svelte';
	import PriceChart from '../charts/PriceChart.svelte';
	import { ChartCtl, ECON_MAX, PERIOD_N } from '../charts/chartState.svelte'; // 차트 상태 SSOT · CenterStack 소유(상단 macro 마퀴가 econ 토글 공유)
	import type { CoMover } from '../lib/coMovement';
	import MiniFinChart from '../charts/MiniFinChart.svelte';
	import BacktestReport from '../charts/BacktestReport.svelte';
	import BacktestPreflight from '../charts/BacktestPreflight.svelte'; // 대기 상태 · void 대신 실행 전 프리플라이트(B&H 기준선·데이터품질·비용·체결모델)
	import { UniverseBacktester } from '../../scan'; // 유니버스 횡단면 백테스터(자급형) · 보고서 모드 universe 스코프 재호스팅
	import { backtestPreflight } from '../lib/backtest';
	import type { PortfolioBtResult, BtPreflight, BtFullRef } from '../lib/backtest';
	import FinFullscreen from './FinFullscreen.svelte';
	import GradeExplainDialog from './GradeExplainDialog.svelte';
	import { tx, txc, chgClass, sign, fmtNum, sparkPts as kpiSpark } from '../ui/helpers';
	import { fmtKRW, fmtMoney } from '../lib/engine';
	import { requestViewer } from '../lib/viewerEntry.svelte'; // 공시뷰어 전체화면 · 우측 ViewerOverlay 열기 신호
	import { finFullEntry } from '../lib/finFullEntry.svelte'; // 우측 레일 도시에 섹션 상세보기 → 재무 전체화면 특정 탭(people·shareholder) 열기 신호
	import { classifyFiling } from '../lib/eventRail'; // 비정기 공시 원문명 → DART 공시그룹 근사 분류(이벤트 레일 필터)
	import { watchlist } from '../lib/watchlist.svelte'; // 공시 워치 · 종목코드 왼쪽 ☆ 토글(좌측 패널과 공유)

	interface Props {
		co: Company;
		lang: Lang;
		ctl?: ChartCtl;
		// id 보유 항목(MACRO_SERIES 시계열)은 마퀴 클릭→차트 econ 오버레이. 파생 항목(국면·순풍 등 시계열 부재)은 id 없음 = 비클릭(04 §5).
		kpis?: { l: string; v: string; t: string; s?: number[]; id?: string }[];
		// 전체화면 심볼 점프 (PriceChart ⌘K·/) · 검색·전환은 터미널 엔진 관통
		suggest?: (q: string, n: number) => { code: string; name: string; industry: string }[];
		onPick?: (code: string) => void;
		onCoMovers?: (rows: CoMover[]) => void;
		// 카드뉴스(편집 캐러셀) · 셸이 보유 종목 집합 + 클릭 핸들러 주입. 보유 종목에 한해 회사 네비에 「카드뉴스」 노출(개별).
		cardsCodes?: Set<string>;
		onOpenCards?: (code: string) => void;
	}
	let { co, lang, ctl = new ChartCtl(), kpis = [], suggest, onPick, onCoMovers, cardsCodes, onOpenCards }: Props = $props();
	const rt = useDartLabRuntime();
	const localViewerHref = $derived(rt.viewer.urlForCompany(co.code));
	const localTerminalHref = $derived(`/analysis/${co.code}`);
	const tcls = (t: string) => (({ up: 'tUp', good: 'tGood', neutral: 'tNeu', warn: 'tWarn', down: 'tDn' }) as Record<string, string>)[t] || 'tNeu';
	// 등급 칩 상단 바 색 = 품질 tone(녹→청→회→앰버→적). 축 카테고리 무지개(GROUP_COLOR) 대체 · 색이 등급 *의미*를 가리키게.
	const toneCol = (t: string) => (({ up: 'var(--up)', good: 'var(--good)', neutral: 'var(--dim)', warn: 'var(--warn)', down: 'var(--dn)' }) as Record<string, string>)[t] || 'var(--dim)';
	let gradeOpen = $state(false); // 스캔등급 설명 다이얼로그
	// 차트 상태 · TerminalSurface 가 주입하면 Macro Lens 와 ECON 토글을 공유한다. 단독 사용 시 기본 인스턴스 생성.

	// 주가 캔들 (hyparquet 온디맨드) · 부팅 비차단, 회사 전환 시 재로드. 재무는 아래 별도 섹션.
	// 주가차트 컨트롤(기간·지표·드로잉·실적·밸류·로그·전체화면)은 PriceChart 인-차트 툴바로 이전.
	// ★소프트 스왑 · 전환 중 candles 를 비우지 않아 PriceChart(klinecharts 인스턴스·전체화면 상태)가
	// 언마운트되지 않는다 (전체화면 심볼 점프의 전제 + 깜빡임 제거, viewer soft-swap 동일 패턴).
	// chartCode 는 candles 와 *원자적으로* 갱신 · 전환 중 "새 code + 옛 candles" 불일치가 PriceChart
	// 데이터 effect(드로잉 복원·lazy 백필 키)에 새는 것을 차단.
	let candles = $state<Candle[] | null>(null);
	let chartCode = $state('');
	let chartName = $state('');
	let candleState = $state<'loading' | 'ready' | 'unavail'>('loading');
	// 차트 주체(subject, 01) · 'price'=회사 주가 / 'index'=KR gov·US FRED 지수. CenterStack-local 소유(ctl 미상향, §2.5).
	let subject = $state<'price' | 'index'>('price');
	let indexRef = $state<IndexRef | null>(null);
	const indexLine = $derived(subject === 'index' && indexRef?.market === 'US'); // US 지수=종가전용 라인(PriceChart 렌더 격리)
	let idxQuery = $state('');
	let idxResults = $state<IndexRef[]>([]);
	let idxCatalog = $state<IndexRef[]>([]); // 전체 지수 카탈로그(select 브라우징) · 세션 1회 로드
	rt.index.catalog().then((c) => (idxCatalog = c ?? []));
	let idxSearchToken = 0;
	function onIdxSearch() {
		const q = idxQuery.trim();
		if (!q) { idxResults = []; return; }
		const tk = ++idxSearchToken;
		void rt.index.search(q, 12).then((rs) => { if (tk === idxSearchToken) idxResults = rs ?? []; });
	}
	function pickIndex(r: IndexRef) {
		indexRef = r;
		subject = 'index';
		idxQuery = '';
		idxResults = [];
	}
	function setSubject(s: 'price' | 'index') {
		subject = s;
		if (s === 'index' && !indexRef) indexRef = KR_INDEX_PRESETS[0];
	}
	function searchIndex(q: string) {
		idxQuery = q;
		onIdxSearch();
	}
	// 컨트롤 번들 · 차트 컨트롤 바(ChartMenus)가 한 줄에서 주가/지수 토글·지수 picker 를 렌더하도록 내려보냄(idxBar 폐기).
	const indexCtl = $derived({ subject, indexRef, query: idxQuery, results: idxResults, catalog: idxCatalog, setSubject, pick: pickIndex, search: searchIndex });
	const onPickWrapped = $derived(onPick ? (c: string) => { subject = 'price'; onPick?.(c); } : undefined); // 심볼 점프 = 회사 → 주가 주체 복귀
	const priceYear = $derived(+co.price.asOf.slice(0, 4) || new Date().getFullYear());
	$effect(() => {
		const subj = subject;
		const iref = indexRef;
		const code = co.code;
		const nm = co.name.kr;
		const yr = priceYear;
		candleState = 'loading';
		let cancelled = false;
		// 주체 분기 · 'index'면 KR gov/US FRED 지수 시계열(rt.index.series), 그 외 회사 주가(rt.price.initial).
		// 소프트 스왑 동일: candles+chartCode+chartName 원자 갱신(PriceChart 인스턴스·전체화면 유지).
		if (subj === 'index' && iref) {
			rt.index.series(iref).then((cs) => {
				if (cancelled) return;
				candles = cs && cs.length ? cs : null;
				chartCode = iref.code;
				chartName = iref.name;
				candleState = cs && cs.length ? 'ready' : 'unavail';
			});
		} else {
			rt.price.initial(code, yr).then((r) => {
				if (cancelled) return;
				candles = r && r.candles.length ? r.candles : null;
				chartCode = code;
				chartName = nm;
				candleState = r && r.candles.length ? 'ready' : 'unavail';
			});
		}
		return () => {
			cancelled = true;
		};
	});

	// 회사 전환 = 그 회사 주가로 복귀 · 지수 주체는 center-local 이라 회사 바뀌면 해제(클릭한 회사가 안 보이는 혼동 차단).
	$effect(() => {
		void co.code; // 회사 전환 추적
		untrack(() => { subject = 'price'; }); // subject 읽기 의존 차단(자기루프 방지) · mount 시 'price' 재설정은 no-op
	});

	// 시장 스코프 디스커버리 · '시장(지수 타이밍)' 진입 시 차트를 지수 컨텍스트로 1회 자동 전환(어디서 지수를 고르나 헤매지 않게),
	// 단일종목/유니버스로 벗어나면 자동 진입분만 주가 복원. 전이(prev≠cur)에서만 · 시장 스코프 안의 수동 주가/지수 토글과 안 다툼.
	let btMktAuto = false;
	let btPrevScopeMkt = false;
	$effect(() => {
		const market = ctl.btReportMode && ctl.btScope === 'market';
		untrack(() => {
			if (market && !btPrevScopeMkt && subject !== 'index') { setSubject('index'); btMktAuto = true; }
			else if (!market && btPrevScopeMkt && btMktAuto) { subject = 'price'; btMktAuto = false; }
			btPrevScopeMkt = market;
		});
	});

	// 백테스트 결과 · PriceChart 가 onBtResult 로 올려줌(엔진은 PriceChart 소유). 보고서 모드에서 하단 BacktestReport 에 전달.
	let btPf = $state<PortfolioBtResult | null>(null);
	let btCandleTs = $state<string[]>([]);
	let btFullRef = $state<BtFullRef | null>(null); // 커스텀 구간 전체기간 대조(G3) · BacktestReport 가 '이 구간 vs 전체' 병기
	// 대기 프리플라이트 · 백테스트 모드(단일) + 결과 없음 + 캔들 일치일 때만. 백테스트와 같은 창(PERIOD_N[period]) 실현 B&H·데이터품질.
	const btPreflight = $derived.by<BtPreflight | null>(() => {
		if (!ctl.btReportMode || ctl.btScope !== 'single' || btPf || !candles || candles.length < 2 || chartCode !== co.code) return null;
		if (ctl.btCustomWin && ctl.btWinFrom && ctl.btWinTo) {
			// 커스텀 구간 · 끝을 toIdx 로 절단 + win=구간봉수 (백테스트와 동일 계약).
			let fi = 0; while (fi < candles.length && candles[fi].t < ctl.btWinFrom) fi++;
			let ti = candles.length - 1; while (ti > 0 && candles[ti].t > ctl.btWinTo) ti--;
			if (ti < fi) return null;
			return backtestPreflight(candles.slice(0, ti + 1), ti - fi + 1, ctl.btCostsBp);
		}
		const win = Math.min(PERIOD_N[ctl.period] ?? candles.length, candles.length);
		return backtestPreflight(candles, win, ctl.btCostsBp);
	});
	// 재무 카드 · dart/finance/{code}.parquet (HF hyparquet) 연간/분기/TTM, 온디맨드·회사별
	let finBundle = $state<TerminalFinanceBundle | null>(null);
	let finMode = $state<FinMode>('ttm'); // 그래프 기본 = TTM (추세) · 표는 분기 원값 (우측 패널·다이얼로그)
	let finScope = $state<FinScope | null>(null); // null = 자동(최신 데이터 범위). 연결/별도 토글 시 명시 범위.
	let finState = $state<'loading' | 'ready' | 'empty'>('loading');
	const finData = $derived(finBundle ? finBundle.views[finMode] ?? null : null);
	const finModeLabel: Record<FinMode, string> = { ttm: 'TTM', quarter: '분기', annual: '연간' };
	const finScopeLabel = (s: FinScope): string => (s === 'CFS' ? (lang === 'en' ? 'CONS' : '연결') : lang === 'en' ? 'SEP' : '별도');
	// 회사 전환 시 범위는 자동으로 (정의 순서상 아래 fetch effect 보다 먼저 · 같은 flush 에서 finScope=null 선반영)
	$effect(() => {
		void co.code;
		finScope = null;
	});
	$effect(() => {
		const code = co.code;
		const scope = finScope ?? undefined; // tracked → 연결/별도 토글 시 재조회
		finState = 'loading';
		finBundle = null;
		let cancelled = false;
		rt.finance.bundle(code, scope).then((b) => {
			if (cancelled) return;
			finBundle = b;
			finMode = b ? (b.views.ttm ? 'ttm' : b.defaultMode) : 'quarter'; // TTM 우선 · 분기 부족(신규상장 등)이면 defaultMode 폴백
			finState = b && b.modes.length ? 'ready' : 'empty';
		});
		return () => {
			cancelled = true;
		};
	});

	// 동종업계 · 주가차트 종목비교(VS) 후보 (map/companies relations, 회사별 캐시)
	let chartPeers = $state<{ code: string; name: string }[]>([]);
	$effect(() => {
		const code = co.code;
		let cancelled = false;
		chartPeers = [];
		rt.company.relations(code).then((r) => {
			if (cancelled) return;
			chartPeers = (r?.peers ?? []).filter((p) => p.stockCode && p.stockCode !== code).map((p) => ({ code: p.stockCode, name: p.corpName }));
		});
		return () => {
			cancelled = true;
		};
	});

	// 회사 주요제품 (corpList) · 헤더 빈 가운데 채움. 어댑터 캐시 공유(중복 다운로드 없음).
	let corpMeta = $state<Record<string, ProductIndexItem> | null>(null);
	rt.company.productIndex().then((m) => (corpMeta = m));
	const corpInfo = $derived(corpMeta?.[co.code] ?? null);
	const product = $derived(corpInfo?.product ?? '');
	// 재무제표 분석 전체화면 (FinFullscreen · 버틀러식 탭, ESC 닫기는 컴포넌트 내부)
	let finFull = $state(false);
	let finFullTab = $state('all'); // 진입 탭 · 종합 버튼=all, 우측 레일 상세보기=people·shareholder(아래 pulse 구독)
	// 우측 레일 도시에 섹션(인력·주주환원) 상세보기 신호 구독 · pulse 변할 때만 해당 탭으로 전체화면 연다.
	// seenFinFullPulse = 비반응 plain let · finFull/finFullTab 쓰기가 effect 를 재발화시키지 않음(viewerEntry 동일 패턴, 루프 없음).
	let seenFinFullPulse = finFullEntry.pulse;
	$effect(() => {
		const p = finFullEntry.pulse;
		if (p === seenFinFullPulse) return;
		seenFinFullPulse = p;
		finFullTab = finFullEntry.tab;
		finFull = true;
	});
	// 차트 출처(공공누리) · PriceChart 가 onSrc 로 올려줌(econ/수정주가/HA 반응). 차트 하단 대신 패널 헤더에 표기.
	let chartSrcLine = $state('');

	const p = $derived(co.price);
	const e = $derived(co.eco);
	// 헤더 가격 정합성 · prices 스냅샷(주배치, 지연 가능)보다 차트 캔들(gov EOD)이 최신이면 캔들 종가 SSOT.
	// 수익률·시총도 같은 기준으로 재계산(시총 = 스냅샷 주식수 × 최신 종가) · 헤더↔차트 불일치 제거.
	// 소프트 스왑 중(chartCode ≠ co.code)엔 옛 회사 캔들이므로 헤더 계산에서 제외 (스냅샷 폴백).
	const lastCandle = $derived(chartCode === co.code && candles && candles.length ? candles[candles.length - 1] : null);
	const dispLast = $derived(lastCandle ? lastCandle.c : p.last);
	const candleRet = (bars: number): number | null => {
		if (!candles || candles.length <= bars || !lastCandle) return null;
		const prev = candles[candles.length - 1 - bars].c;
		return prev ? (lastCandle.c / prev - 1) * 100 : null;
	};
	const dispRet1m = $derived(candleRet(22) ?? p.ret1m);
	const dispRet3m = $derived(candleRet(66) ?? p.ret3m);
	const dispRet1y = $derived(candleRet(252) ?? p.ret1y);
	const dispAsOf = $derived(lastCandle ? `${lastCandle.t.slice(0, 4)}-${lastCandle.t.slice(4, 6)}-${lastCandle.t.slice(6, 8)}` : p.asOf);
	const dispMktcap = $derived(lastCandle && p.last && p.mktcapRaw != null ? fmtMoney(p.mktcapRaw * (lastCandle.c / p.last), co.currency) : p.mktcap);
	const stats = $derived([
		{ l: '1M', v: dispRet1m == null ? '·' : sign(dispRet1m, 1) + '%', t: chgClass(dispRet1m) },
		{ l: '3M', v: dispRet3m == null ? '·' : sign(dispRet3m, 1) + '%', t: chgClass(dispRet3m) },
		{ l: '1Y', v: dispRet1y == null ? '·' : sign(dispRet1y, 0) + '%', t: chgClass(dispRet1y) },
		{ l: lang === 'en' ? 'MKT CAP' : '시가총액', v: dispMktcap, t: '' },
		{ l: lang === 'en' ? 'LISTED REV%' : '상장사매출비중', v: e.marketShare != null ? e.marketShare.toFixed(1) + '%' : '·', t: '' },
		{ l: lang === 'en' ? 'RANK' : '산업순위', v: e.industryRank != null ? e.industryRank + '/' + (e.industryPeerCount || '·') : '·', t: '' }
	]);
	const meta = $derived([
		{ l: lang === 'en' ? 'LISTED REV%' : '상장사매출비중', v: e.marketShare != null ? e.marketShare.toFixed(1) + '%' : '·' },
		{ l: lang === 'en' ? 'IND.RANK' : '산업순위', v: e.industryRank != null ? e.industryRank + '위/' + (e.industryPeerCount || '·') : '·' },
		{ l: lang === 'en' ? 'OWNER' : '대주주', v: e.holderPct != null ? e.holderPct.toFixed(1) + '%' : '·' },
		{ l: lang === 'en' ? 'EMP' : '임직원', v: e.empCount != null ? e.empCount.toLocaleString() + (lang === 'en' ? '' : '명') : '·' },
		{ l: 'ROE', v: e.roe != null ? e.roe.toFixed(1) + '%' : '·' },
		{ l: lang === 'en' ? 'OP MGN' : '영업이익률', v: e.opMargin != null ? e.opMargin.toFixed(1) + '%' : '·' }
	]);
	// 하단 분석 도구: DuPont ROE 분해. 렌즈의 텍스트 판단은 우측 스택이 담당한다.
	const fz = $derived(co.financials);
	const dp = $derived(fz.dupont); // {netMargin, assetTurn, equityMult, roe}
	const dpTone = $derived(dp.roe == null ? 'tNeu' : dp.roe >= 12 ? 'tUp' : dp.roe >= 6 ? 'tNeu' : 'tDn');
	const roeDriver = $derived.by<{ kr: string; en: string; tone: Tone } | null>(() => {
		const { netMargin, assetTurn, equityMult } = dp;
		if (netMargin == null || assetTurn == null || equityMult == null) return null;
		if (equityMult >= 2.5 && netMargin < 8) return { kr: '레버리지형', en: 'leverage-led', tone: 'warn' };
		if (netMargin >= 10) return { kr: '마진형', en: 'margin-led', tone: 'good' };
		if (assetTurn >= 1) return { kr: '회전형', en: 'turnover-led', tone: 'up' };
		return { kr: '균형형', en: 'balanced', tone: 'neutral' };
	});
	const dupontFactors = $derived([
		{ k: 'nm', label: lang === 'en' ? 'Net mgn' : '순이익률', disp: dp.netMargin != null ? dp.netMargin.toFixed(1) + '%' : '·', arr: fz.netMargin, col: '#34d399', op: '×' },
		{ k: 'at', label: lang === 'en' ? 'Asset turn' : '자산회전', disp: dp.assetTurn != null ? dp.assetTurn.toFixed(2) + '회' : '·', arr: fz.assetTurn, col: '#60a5fa', op: '×' },
		{ k: 'em', label: lang === 'en' ? 'Leverage' : '레버리지', disp: dp.equityMult != null ? dp.equityMult.toFixed(2) + '배' : '·', arr: fz.equityMult, col: (dp.equityMult ?? 0) >= 2.5 ? '#f0616f' : (dp.equityMult ?? 0) >= 2 ? '#fbbf24' : '#a78bfa', op: '=' },
		{ k: 'roe', label: 'ROE', disp: dp.roe != null ? dp.roe.toFixed(1) + '%' : '·', arr: fz.roe, col: '#34d399', op: '' }
	]);
	// 미니 스파크라인 path
	function spark(arr: Num[], w = 46, h = 13): string {
		const vals = arr.filter((x): x is number => x != null);
		if (vals.length < 2) return '';
		const lo = Math.min(...vals), hi = Math.max(...vals), rng = hi - lo || 1, n = arr.length;
		let d = '', pen = false;
		arr.forEach((val, i) => {
			if (val == null) { pen = false; return; }
			const x = n <= 1 ? w / 2 : (i / (n - 1)) * w;
			const y = h - ((val - lo) / rng) * h;
			d += `${pen ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)} `;
			pen = true;
		});
		return d.trim();
	}
	// 증자·감자 마커 · capitalChange 이벤트 (수정주가 자동 보정의 교차 검증 라벨).
	// 전환·행사(스톡옵션 등 수천 건)는 제외, 동일자 합산, |수량| 상위 40 상한 · 마커 폭주 방지.
	let capEvents = $state<{ date: string; label: string }[]>([]);
	$effect(() => {
		const code = co.code;
		let cancelled = false;
		capEvents = [];
		rt.report.capitalChanges(code).then((b) => {
			if (cancelled || !b) return;
			const byDate = new Map<string, { kind: string; qty: number }>();
			for (const ev of b.events) {
				if (ev.kind === 'conversion') continue;
				const d = ev.date.replace(/\D/g, '').slice(0, 8);
				if (d.length !== 8) continue;
				const key = `${d}|${ev.kind}`;
				const cur = byDate.get(key);
				if (cur) cur.qty += ev.qty;
				else byDate.set(key, { kind: ev.kind, qty: ev.qty });
			}
			const fmtQty = (q: number) => (Math.abs(q) >= 1e4 ? Math.round(Math.abs(q) / 1e4).toLocaleString() + '만주' : Math.abs(q).toLocaleString() + '주');
			capEvents = [...byDate.entries()]
				.sort((a, b2) => Math.abs(b2[1].qty) - Math.abs(a[1].qty))
				.slice(0, 40)
				.map(([key, v]) => ({ date: key.slice(0, 8), label: `${v.kind === 'paidIn' ? '유상증자' : '감자·소각'} ${fmtQty(v.qty)}` }));
		});
		return () => {
			cancelled = true;
		};
	});

	// 공시 이벤트 레일 (dartlab 고유 강점) · 정기보고서 url(접수일별) + 비정기 material 공시(날짜 그룹·클릭 시 DART).
	// 가격차트 마커가 곧 네비게이션 가능한 공시 타임라인. 같은 날 다수 공시는 1마커로 묶고 '외 N건' 표기(마커 폭주 방지).
	type RailItem = { title: string; rceptNo: string; url: string; kind: 'regular' | 'nonreg' | 'news'; category: string };
	let regularUrlByDate = $state<Record<string, string>>({});
	let disclosureEvents = $state<{ date: string; items: RailItem[] }[]>([]);
	$effect(() => {
		const code = co.code;
		let cancelled = false;
		regularUrlByDate = {};
		disclosureEvents = [];
		void Promise.all([rt.filing.regular(code), rt.filing.nonRegular(code), rt.news.forCompany(code)]).then(([reg, non, news]) => {
			if (cancelled) return;
			const rmap: Record<string, string> = {};
			for (const f of reg ?? []) if (f.rceptDate && f.url) rmap[f.rceptDate.replace(/\D/g, '').slice(0, 8)] = f.url;
			regularUrlByDate = rmap;
			// 레일 = 정기공시 + 비정기공시 통합 위치 타임라인. 날짜별로 그날 공시 전부 수집(호버 툴팁이 전부 나열, 클릭은 날짜로 우측 동기).
			const byDate = new Map<string, RailItem[]>();
			const add = (d8: string, item: RailItem) => {
				const cur = byDate.get(d8);
				if (cur) cur.push(item);
				else byDate.set(d8, [item]);
			};
			// 정기공시 · 사업/반기/분기보고서(그 분기 실적 공시). 캔들 실적 마커와 별개로 레일에도 = "공시 위치"의 완결성.
			for (const f of reg ?? []) {
				const d = (f.rceptDate ?? '').replace(/\D/g, '').slice(0, 8);
				if (d.length !== 8 || !f.url || !f.reportType?.trim()) continue;
				add(d, { title: f.reportType.trim() + (f.year ? ' ' + f.year : ''), rceptNo: f.rceptNo, url: f.url, kind: 'regular', category: 'regular' });
			}
			// 비정기(수시) 공시
			for (const f of non ?? []) {
				const d = (f.rceptDate ?? '').replace(/\D/g, '').slice(0, 8);
				if (d.length !== 8 || !f.url || !f.reportNm?.trim()) continue; // 빈 항목 방지(anti-clutter)
				add(d, { title: f.reportNm.trim(), rceptNo: f.rceptNo, url: f.url, kind: 'nonreg', category: classifyFiling(f.reportNm) });
			}
			// 종목 뉴스(네이버 헤드라인) · 공시 아닌 이벤트라 category='news'(레일 색·필터 구분). rceptNo 자리에 url(고유키).
			// 클릭 시 우측 '종목 뉴스' 패널 그 날짜 행 동기(focusDisclosure → newsWrap 스크롤). 원문은 패널에서 ↗.
			for (const n of news ?? []) {
				const d = (n.date ?? '').replace(/\D/g, '').slice(0, 8);
				if (d.length !== 8 || !n.title?.trim()) continue;
				add(d, { title: n.title.trim(), rceptNo: n.url || `news:${d}:${n.title}`, url: n.url, kind: 'news', category: 'news' });
			}
			// 전 기간 공시 날짜 전부 전달 · dot 폭주 방지는 PriceChart 의 "보이는 x 범위 밖 skip"이 담당. 전역 캡(옛 60) 제거: 줌아웃해도 옛 공시(예: 2015) dot 보존. 같은 날 다수는 1 dot + 툴팁 전체 나열.
			disclosureEvents = [...byDate.entries()]
				.sort((a, b) => (a[0] < b[0] ? 1 : -1))
				.map(([d, items]) => ({ date: d, items }));
		});
		return () => {
			cancelled = true;
		};
	});

	// 주가차트 재무 오버레이: 실적 발표 마커(보고서 접수일·클릭 시 DART) + 증자·감자 + 비정기 공시 레일 + 적정주가 밴드
	const priceEvents = $derived.by(() => {
		const src = finBundle?.views.quarter ?? finBundle?.views.ttm ?? finBundle?.views.annual;
		const filed = finBundle?.filedDates ?? {};
		type Ev = { date: string; label: string; url?: string; kind?: 'report' | 'capital' | 'disclosure' };
		const out: Ev[] = [];
		if (src) {
			const QEND: Record<string, string> = { '1': '0331', '2': '0630', '3': '0930', '4': '1231' };
			const urlFor = (d: string) => regularUrlByDate[d.replace(/\D/g, '').slice(0, 8)];
			for (const p of src.periods) {
				const mq = p.match(/^(\d{2})Q(\d)$/);
				if (mq) {
					const d = filed[`20${mq[1]}-${mq[2]}`] ?? '20' + mq[1] + QEND[mq[2]];
					out.push({ date: d, label: p, url: urlFor(d), kind: 'report' });
					continue;
				}
				const fy = p.match(/^FY(\d{2})$/);
				if (fy) {
					const d = filed[`20${fy[1]}-4`] ?? '20' + fy[1] + '1231';
					out.push({ date: d, label: p, url: urlFor(d), kind: 'report' });
				}
			}
		}
		const caps: Ev[] = capEvents.map((e) => ({ ...e, kind: 'capital' as const }));
		// ★공시(disclosure)는 캔들 고가 annotation 에서 제거 · 텍스트 폭주로 가격 차폐(PRD 02 §2.2/§11/§13 금지).
		// 실적(report)·증자(capital)만 캔들 위 유지(가격 옆 위치가 맞음). 공시는 하단 레일(DisclosureEventRail)로 분리.
		return [...out, ...caps];
	});
	const v = $derived(co.valuation);
	const priceValBand = $derived(
		v && v.fairLow != null && v.fairHigh != null && v.fairMid != null
			? { lo: v.fairLow, mid: v.fairMid, hi: v.fairHigh }
			: null
	);
	const valBand = $derived(
		v && v.fairMid != null
			? (() => {
					const lo = Math.min(v.fairLow || v.last, v.last) * 0.9;
					const hi = Math.max(v.fairHigh || v.last, v.last) * 1.1;
					const pos = (x: number) => Math.max(0, Math.min(100, ((x - lo) / (hi - lo)) * 100));
					return { lo, hi, pos };
				})()
			: null
	);
</script>

<!-- 경제·시장 KPI 티커 (종목/주가 라인 위, 좌우 흐름) · id 보유(시계열) 항목은 클릭→차트 econ 오버레이(04 §5).
     파생 항목(국면·순풍 등)은 시계열 부재 = 비클릭(허위 오버레이 금지·정직 분기). 안정키 = id/label+절반. -->
{#if kpis.length}
	<div class="kpiTicker"><div class="kpiTrack">
		{#each kpis.concat(kpis) as k, i (`${k.id ?? k.l}__${i < kpis.length ? 0 : 1}`)}
			{@const on = !!k.id && ctl.econ.includes(k.id)}
			{@const blocked = !!k.id && !on && ctl.econ.length >= ECON_MAX}
			{#if k.id}
				<button class="kpiItem kpiBtn" class:on disabled={blocked} title={blocked ? (lang === 'en' ? 'up to 3 economy series' : '경제지표는 동시 3개까지') : lang === 'en' ? 'overlay on chart' : '차트에 겹쳐보기'} onclick={() => { if (!k.id) return; ctl.toggleEcon(k.id); }}><i>{k.l}</i>{#if k.s && k.s.length > 1}<svg class={'kpiSpark ' + k.t} viewBox="0 0 34 11" preserveAspectRatio="none" aria-hidden="true"><polyline points={kpiSpark(k.s)} fill="none" stroke="currentColor" stroke-width="1.1" /></svg>{/if}<b class={k.t}>{k.v}</b></button>
			{:else}
				<span class="kpiItem"><i>{k.l}</i>{#if k.s && k.s.length > 1}<svg class={'kpiSpark ' + k.t} viewBox="0 0 34 11" preserveAspectRatio="none" aria-hidden="true"><polyline points={kpiSpark(k.s)} fill="none" stroke="currentColor" stroke-width="1.1" /></svg>{/if}<b class={k.t}>{k.v}</b></span>
			{/if}
		{/each}
	</div></div>
{/if}

<!-- SYMBOL HEADER -->
<div class="symHead">
	<div class="symId">
		<div class="symTop">
			<button class={'symWatch' + (watchlist.has(co.code) ? ' on' : '')} onclick={() => watchlist.toggle(co.code)} aria-pressed={watchlist.has(co.code)} title={watchlist.has(co.code) ? (lang === 'en' ? 'remove from disclosure watch' : '공시 워치에서 제거') : (lang === 'en' ? 'add to disclosure watch' : '공시 워치에 추가')}>{watchlist.has(co.code) ? '★' : '☆'}</button>
			<span class="symName">{co.name.kr}</span>
		</div>
		<div class="symCodeRow"><span class="symBadge kr">{co.marketLabel}</span><span class="symCode">{co.code}</span></div>
		<div class="symMeta">{tx(co.sector, lang)}{co.stage ? ' · ' + co.stage : ''}{co.role ? ' · ' + co.role : ''} · DART</div>
	</div>
	<!-- 중간 · 회사 기본정보 2줄(대표·결산월 / 상장일·본사) 위 / 주요제품 아래(좌), 회사 네비 세로 스택(우). 우측 가격정보와 ~3행 높이 정렬. -->
	<div class="symProd">
		<div class="symProdInfo">
			{#if corpInfo}
				<div class="symInfoRow">
					{#if corpInfo.ceo}<span class="sif"><i>{lang === 'en' ? 'CEO' : '대표'}</i><b>{corpInfo.ceo}</b></span>{/if}
					{#if corpInfo.fiscalMonth}<span class="sif"><i>{lang === 'en' ? 'FY END' : '결산월'}</i><b>{corpInfo.fiscalMonth}</b></span>{/if}
				</div>
				<div class="symInfoRow">
					{#if corpInfo.listedDate}<span class="sif"><i>{lang === 'en' ? 'LISTED' : '상장일'}</i><b class="mono">{corpInfo.listedDate}</b></span>{/if}
					{#if corpInfo.region}<span class="sif"><i>{lang === 'en' ? 'HQ' : '본사'}</i><b>{corpInfo.region}</b></span>{/if}
				</div>
			{/if}
			{#if product}
				<div class="symProdLine" title={product}><span class="symProdLbl">{lang === 'en' ? 'PRODUCTS' : '주요제품'}</span><span class="symProdV">{product}</span></div>
			{/if}
		</div>
		<!-- 회사 네비 세로 스택 · 터미널(로컬 임베드 한정) · 홈페이지 · 전자공시(DART 전체공시) · 공시뷰어(전체화면, 우측 ⤢ 동일) -->
		<nav class="symLinks">
			{#if localViewerHref}<a href={localTerminalHref}>{lang === 'en' ? 'terminal' : '터미널'}</a>{/if}
			{#if corpInfo?.homepage}<a href={corpInfo.homepage} target="_blank" rel="noopener">{lang === 'en' ? 'website ↗' : '홈페이지 ↗'}</a>{/if}
			{#if onOpenCards && cardsCodes?.has(co.code)}<button type="button" class="symCards" onclick={() => onOpenCards?.(co.code)} title={lang === 'en' ? 'Company card story · Instagram-style post' : '기업 카드뉴스 · 인스타그램형 포스트'}>{lang === 'en' ? 'cards ▦' : '카드뉴스 ▦'}</button>{/if}
			<a href={`https://dart.fss.or.kr/dsab001/main.do?autoSearch=true&textCrpNm=${encodeURIComponent(co.name.kr)}`} target="_blank" rel="noopener" title={lang === 'en' ? 'DART · company filings (auto-search by name)' : '전자공시(DART) · 회사별 공시 자동검색'}>{lang === 'en' ? 'DART ↗' : '전자공시 ↗'}</a>
			<button type="button" onclick={requestViewer} title={lang === 'en' ? 'disclosure viewer · fullscreen' : '공시뷰어 · 전체화면 (우측 정기공시 ⤢ 동일)'}>{lang === 'en' ? 'viewer ⤢' : '공시뷰어 ⤢'}</button>
		</nav>
	</div>
	<div class="symPrice">
		<span class="symLast mono">{fmtNum(dispLast)}</span>
		<span class={'symChg ' + chgClass(dispRet1m)}>{dispRet1m == null ? '' : sign(dispRet1m, 2) + '% · 1M'}</span>
	</div>
	<div class="symStats">
		{#each stats as s (s.l)}<div class="symStat"><span>{s.l}</span><b class={'mono ' + s.t}>{s.v}</b></div>{/each}
	</div>
</div>

<!-- GRADE STRIP · 백테스트 모드에선 숨김(비-백테스트 company 컨텍스트, 하단 보고서·프리플라이트 above-fold 확보). -->
{#if !ctl.btReportMode}
<Panel {lang} className="eAnalysis" prov="real" title={{ kr: '스캔 등급', en: 'SCAN GRADES' }} flush>
	{#snippet right()}<button class="finFullBtn" onclick={() => (gradeOpen = true)} title={lang === 'en' ? 'analysis detail' : '분석 내용'}>{lang === 'en' ? 'detail' : '상세보기'}</button>{/snippet}
	<div class="ecoMeta">{#each meta as m (m.l)}<div class="em"><span>{m.l}</span><b>{m.v}</b></div>{/each}</div>
	<div class="gradeStrip" style={`grid-template-columns:repeat(${co.grades.length || 1},minmax(0,1fr))`}>
		{#each co.grades as g (g.key)}
			<div class="gradeChip" style={`--gc:${toneCol(g.tone)}`} title={`${txc(g, lang)} · ${g.v}`}>
				<span class="gcLabel">{txc(g, lang)}</span>
				<span class={'gcVal ' + tcls(g.tone)}>{g.v}</span>
			</div>
		{/each}
	</div>
</Panel>
{/if}
{#if gradeOpen}<GradeExplainDialog {co} {lang} onClose={() => (gradeOpen = false)} />{/if}

<!-- 주가 캔들(일별 실데이터·멀티 보조지표) · 메인 히어로. 재무는 아래 전용 섹션. -->
<Panel {lang} className="eQuant" prov="real"
	title={{ kr: subject === 'index' ? '지수 차트' : '주가 차트', en: subject === 'index' ? 'INDEX CHART' : 'PRICE CHART' }}
	sub={subject === 'index'
		? (indexRef?.market === 'US' ? { kr: '미국 지수 · FRED (종가)', en: 'US index · FRED (close)' } : { kr: 'KR 지수 · 거래소 (EOD)', en: 'KR index · KRX (EOD)' })
		: (chartSrcLine ? { kr: chartSrcLine, en: chartSrcLine } : { kr: '공공데이터 일별 · EOD', en: 'gov daily · EOD' })} flush>
	{#snippet right()}<span class="eodBadge" title={lang === 'en' ? 'end-of-day daily data' : '일별 종가 기준(EOD)'}>EOD · {dispAsOf}</span>{/snippet}
	{#if candles && chartCode}
<!-- 소프트 스왑: 전환 중에도 직전 캔들로 마운트 유지 (code·name 은 candles 와 원자 갱신). 지수 주체면 회사 오버레이(공시·실적·밴드·피어) 비움. -->
		<PriceChart {ctl} {candles} code={chartCode} name={chartName} {lang} {subject} {indexLine} {indexCtl}
			events={subject === 'index' ? [] : priceEvents}
			disclosures={subject === 'index' ? [] : disclosureEvents}
			valBand={subject === 'index' ? null : priceValBand}
			peers={subject === 'index' ? [] : chartPeers}
			{suggest} onPick={onPickWrapped} onSrc={(s) => (chartSrcLine = s)} {onCoMovers}
				onBtResult={(pf, ts, fullRef) => { btPf = pf; btCandleTs = ts; btFullRef = fullRef; }} />
	{:else if candleState === 'loading'}
		<div class="chartLoad">{lang === 'en' ? (subject === 'index' ? 'loading index series …' : 'loading daily prices …') : (subject === 'index' ? '지수 시계열 불러오는 중 …' : '일별 시세 불러오는 중 …')}</div>
	{:else if subject === 'index'}
		<div class="chartLoad">{lang === 'en' ? 'index series unavailable.' : '지수 시계열을 불러올 수 없음.'}</div>
	{:else}
		<div class="chartLoad">{lang === 'en' ? 'daily chart unavailable here · snapshot only.' : '이 기기에서 일별 차트 불가 · 스냅샷만.'} 52W {fmtNum(co.price.lo52)}~{fmtNum(co.price.hi52)}</div>
	{/if}
</Panel>

<!-- ★백테스트 보고서 모드 · [백테스트] 시 하단(재무+판정+DuPont)을 보고서로 스왑(차트는 위에 고정·비파괴). 끄면 재무 복귀(finBundle 유지). -->
{#if ctl.btReportMode}
	{#if ctl.btScope === 'universe'}
		<Panel {lang} className="eAnalysis" prov="real" title={{ kr: '유니버스 백테스트', en: 'UNIVERSE BACKTEST' }} sub={{ kr: '횡단면 팩터 · 17년 상폐보존', en: 'cross-sectional · 17yr delisting-preserved' }} flush>
			<UniverseBacktester lang={lang === 'en' ? 'en' : 'ko'} onClose={() => { ctl.btReportMode = false; ctl.btDockOpen = false; }} onDrillDown={(c) => onPick?.(c)} />
		</Panel>
	{:else if ctl.btScope === 'market'}
		<!-- 시장(지수) 타이밍 · 지수 미선택 시 종목 결과를 '시장'으로 오도하지 않도록 명시 안내(정직: silent/오도 차단). -->
		<Panel {lang} className="eAnalysis" prov="derived" title={{ kr: '시장 백테스트', en: 'MARKET BACKTEST' }} sub={{ kr: '지수 타이밍', en: 'index timing' }} flush>
			<div class="storyEmpty">{subject === 'index'
				? (lang === 'en' ? 'Index selected. Index-timing backtest results are not rendered here yet · use the ‘Stock’ or ‘Universe’ scope for now.' : '지수가 선택되었습니다. 지수 타이밍 백테스트 결과는 아직 여기 표시되지 않습니다 · 지금은 ‘단일종목’ 또는 ‘유니버스’ 스코프를 이용하세요.')
				: (lang === 'en' ? 'Index timing · pick an index from the [INDEX] button on the chart bar above. For a per-stock backtest, switch the scope to ‘Stock’.' : '지수 타이밍 · 차트 상단의 [지수] 버튼에서 지수를 선택하세요. 종목별 백테스트는 스코프를 ‘단일종목’으로 바꾸세요.')}</div>
		</Panel>
	{:else if btPf}
		<BacktestReport pf={btPf} slots={ctl.btStrategies} focus={ctl.btFocus} period={ctl.period} withCosts={ctl.btCosts} adjusted={ctl.adj} candleTs={btCandleTs} scope={ctl.btScope} fullRef={btFullRef} {lang} tearsheetOpen={ctl.btTearsheetOpen} onToggleTearsheet={() => (ctl.btTearsheetOpen = !ctl.btTearsheetOpen)} hoverTs={ctl.btCrosshairTs} onFocus={(i) => ctl.setBtFocus(i)} onFocusBar={(t) => (ctl.btHoverBar = t)} onBack={() => { ctl.btReportMode = false; ctl.btDockOpen = false; ctl.clearBtAll(); }} />
	{:else}
		<!-- 대기 = void 금지. 실행 전 프리플라이트(이겨야 할 선·데이터품질·비용·체결모델) + 재무 small-multiples 유지(파괴적 교체 차단). -->
		<Panel {lang} className="eAnalysis" prov="derived" title={{ kr: '백테스트 준비', en: 'PREFLIGHT' }} sub={{ kr: '이 종목·이 창의 진실 · 실행 전', en: 'this symbol · this window' }} flush>
			{#if btPreflight}
				<BacktestPreflight pf={btPreflight} period={ctl.period} {lang} />
			{:else}
				<div class="storyEmpty">{lang === 'en' ? 'Loading price data …' : '시세 불러오는 중 …'}</div>
			{/if}
		</Panel>
		{#if finState === 'ready' && finData}
			<Panel {lang} className="eAnalysis" prov="real" title={{ kr: '재무제표 (참고)', en: 'FINANCIALS (context)' }} sub={{ kr: finModeLabel[finMode] + ' · ' + finData.periods.length + '기', en: finMode + ' · ' + finData.periods.length + 'p' }} flush>
				<div class="finGrid">
					{#each finData.cards as card (card.key)}
						<div class="finMini"><MiniFinChart {card} periods={finData.periods} /></div>
					{/each}
				</div>
			</Panel>
		{/if}
	{/if}
{:else}
<!-- 재무제표 분석 · dart/finance parquet 분기 TTM, 밀집 small-multiples.
     ui/web analysis.financial 의 핵심 카드 체계를 한 화면에 빽빽하게. -->
<Panel {lang} className="eAnalysis" prov="real" title={{ kr: '재무제표 분석', en: 'FINANCIALS' }}
	sub={finData ? { kr: finModeLabel[finMode] + ' · ' + finData.periods.length + '기 · ' + (co.currency === 'USD' ? 'USD' : '조 KRW'), en: finMode + ' · ' + finData.periods.length + 'p · ' + (co.currency === 'USD' ? 'USD' : 'KRW') } : { kr: co.currency === 'USD' ? 'edgar/financeStmt' : 'dart/finance', en: co.currency === 'USD' ? 'edgar/financeStmt' : 'dart/finance' }} flush>
	{#snippet right()}
		{#if finBundle && finBundle.availScopes.length > 1}
			<span class="segGroup mini">{#each finBundle.availScopes as s (s)}<button class={finBundle.scope === s ? 'seg on' : 'seg'} onclick={() => (finScope = s)} title={s === 'CFS' ? (lang === 'en' ? 'consolidated' : '연결재무제표') : (lang === 'en' ? 'separate' : '별도재무제표')}>{finScopeLabel(s)}</button>{/each}</span>
		{/if}
		{#if finBundle && finBundle.modes.length > 1}
			<span class="segGroup mini">{#each finBundle.modes as m (m)}<button class={finMode === m ? 'seg on' : 'seg'} onclick={() => (finMode = m)}>{lang === 'en' ? m.toUpperCase() : finModeLabel[m]}</button>{/each}</span>
		{/if}
		<button class="finFullBtn" onclick={() => { finFullTab = 'all'; finFull = true; }} title={lang === 'en' ? 'fullscreen analysis' : '전체화면 분석'} aria-label="fullscreen">{lang === 'en' ? 'detail' : '상세보기'}</button>
	{/snippet}
	{#if finState === 'ready' && finData}
		<div class="finGrid">
			{#each finData.cards as card (card.key)}
				<div class="finMini"><MiniFinChart {card} periods={finData.periods} /></div>
			{/each}
		</div>
	{:else if finState === 'loading'}
		<div class="chartLoad" style="height:110px">{lang === 'en' ? 'loading financials …' : '재무제표 불러오는 중 …'}</div>
	{:else}
		<div class="storyEmpty">{lang === 'en' ? 'No quarterly financials for this company.' : '분기 재무 데이터 없음.'}</div>
	{/if}
</Panel>
{#if finFull}
	<FinFullscreen {co} {lang} bundle={finBundle} mode={finMode} onMode={(m) => (finMode = m)} onScope={(s) => (finScope = s)} candles={chartCode === co.code ? candles : null} initialTab={finFullTab} onClose={() => (finFull = false)} />
{/if}

<div class="rowSplit">
	<!-- DUPONT ROE 분해 -->
	<Panel {lang} className="eValuation" prov="derived" title={{ kr: 'DuPont ROE 분해', en: 'DUPONT ROE' }} sub={{ kr: '순이익률 × 자산회전 × 레버리지', en: 'margin × turn × leverage' }} flush>
		{#snippet right()}<b class={'mono ' + dpTone}>{dp.roe != null ? dp.roe.toFixed(1) + '%' : '·'}</b>{/snippet}
		<div class="dupontRow">
			{#each dupontFactors as fct (fct.k)}
				<div class="dpCell">
					<span class="dpLbl">{fct.label}</span>
					<b class="dpVal mono" style={`color:${fct.col}`}>{fct.disp}</b>
					<svg class="dpSpark" viewBox="0 0 46 13" preserveAspectRatio="none" aria-hidden="true"><path d={spark(fct.arr)} fill="none" stroke={fct.col} stroke-width="1.2" /></svg>
				</div>
				{#if fct.op}<span class="dpOp">{fct.op}</span>{/if}
			{/each}
		</div>
		<div class="dpVerdict">
			{#if !roeDriver}{lang === 'en' ? 'Insufficient data for ROE decomposition.' : 'ROE 분해 데이터 부족.'}
			{:else if roeDriver.tone === 'warn'}{lang === 'en' ? `Leverage-led · equity multiplier ${dp.equityMult?.toFixed(1)}×, margin only ${dp.netMargin?.toFixed(1)}%. Returns lean on debt.` : `차입 의존 ROE · 자본승수 ${dp.equityMult?.toFixed(1)}배, 순이익률 ${dp.netMargin?.toFixed(1)}%. 레버리지가 수익률을 떠받침.`}
			{:else if roeDriver.tone === 'good'}{lang === 'en' ? `Margin-led · net margin ${dp.netMargin?.toFixed(1)}% drives returns. Durable quality.` : `마진형 ROE · 순이익률 ${dp.netMargin?.toFixed(1)}% 가 견인. 질 높은 수익률.`}
			{:else if roeDriver.tone === 'up'}{lang === 'en' ? `Turnover-led · asset turn ${dp.assetTurn?.toFixed(2)}× drives returns.` : `회전형 ROE · 자산회전 ${dp.assetTurn?.toFixed(2)}회 가 견인. 효율 중심.`}
			{:else}{lang === 'en' ? 'Balanced across margin, turnover and leverage.' : '마진·회전·레버리지가 고르게 기여하는 균형형 ROE.'}{/if}
		</div>
	</Panel>
	<!-- VALUATION -->
	{#if v}
		<Panel {lang} className="eValuation" prov="derived" title={{ kr: '밸류에이션 위치', en: 'VALUATION' }} sub={{ kr: '업종 중앙값 대비', en: 'vs peer median' }} flush>
			{#snippet right()}
				{@const cheap = v.upside != null && v.upside > 8}
				{@const rich = v.upside != null && v.upside < -8}
				<span class={cheap ? 'tUp' : rich ? 'tDn' : 'tNeu'}>{v.upside != null ? (v.upside >= 0 ? '+' : '') + v.upside.toFixed(0) + '%' : '·'}</span>
			{/snippet}
			<div class="valTop">
				<div class="valCell"><div class="vl">PER</div><div class={'vv ' + (v.per != null && v.perMed && v.per <= v.perMed ? 'tUp' : 'tDn')}>{v.per != null ? v.per.toFixed(1) + 'x' : '·'}</div><div class="vsub">{lang === 'en' ? 'peer med' : '업종중앙'} {v.perMed != null ? v.perMed.toFixed(1) + 'x' : '·'}</div></div>
				<div class="valCell"><div class="vl">PBR</div><div class={'vv ' + (v.pbr != null && v.pbrMed && v.pbr <= v.pbrMed ? 'tUp' : 'tDn')}>{v.pbr != null ? v.pbr.toFixed(2) + 'x' : '·'}</div><div class="vsub">{lang === 'en' ? 'peer med' : '업종중앙'} {v.pbrMed != null ? v.pbrMed.toFixed(2) + 'x' : '·'}</div></div>
			</div>
			{#if v.fairMid != null && valBand}
				<div class="fairBand">
					<div class="fairTrack">
						<div class="fairRange" style={`left:${valBand.pos(v.fairLow!)}%;width:${valBand.pos(v.fairHigh!) - valBand.pos(v.fairLow!)}%`}></div>
						<div class="fairNow" style={`left:${valBand.pos(v.last)}%`}></div>
					</div>
					<div class="fairLbl"><span>{fmtNum(Math.round(v.fairLow!))}</span><span class="tAmber">{lang === 'en' ? 'now ' : '현재 '}{fmtNum(v.last)}</span><span>{fmtNum(Math.round(v.fairHigh!))}</span></div>
				</div>
			{/if}
			<div class="valVerdict">
				{#if v.upside == null}{lang === 'en' ? 'Fair value n/a.' : '적정가 산출 불가.'}
				{:else if v.upside > 8}{lang === 'en' ? `Below peer multiples · ~+${v.upside.toFixed(0)}% to fair value.` : `업종 중앙값 대비 저평가 · 적정가까지 약 +${v.upside.toFixed(0)}% 여력.`}
				{:else if v.upside < -8}{lang === 'en' ? `Above peer median · ${Math.abs(v.upside).toFixed(0)}% rich.` : `업종 중앙값 대비 고평가 · 약 ${Math.abs(v.upside).toFixed(0)}% 비쌈.`}
				{:else}{lang === 'en' ? 'Roughly in line with peers.' : '업종 평균 수준의 밸류에이션.'}{/if}
			</div>
		</Panel>
	{:else}
		<Panel {lang} className="eValuation" prov="derived" title={{ kr: '밸류에이션', en: 'VALUATION' }} flush><div class="storyEmpty">{lang === 'en' ? 'Insufficient data.' : '데이터 부족.'}</div></Panel>
	{/if}
</div>
{/if}
