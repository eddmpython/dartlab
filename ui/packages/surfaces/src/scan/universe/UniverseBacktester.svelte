<script lang="ts">
	// 유니버스 백테스터 · 전종목 크로스섹셔널 랭킹(17년 가격보존). terminal-strategy-lab 05 §6 킬러뷰.
	// "분위가 단조롭게 벌어지나"가 한 자에 + 폐지 양극단 밴드로 불확실성까지 정직. 단일종목 랩과 별도 객체.
	// 정직 가드 상존(U-G1~G8): 이중밴드·시도카운터·OOS 강제·이중벤치·근사라벨·추천아님.
	import { ensureDuckDb } from '../duckSql';
	import { loadUniversePanel, loadUniverseYmRange } from './load';
	import { runUniverse } from './engine';
	import { RANK_SIGNAL_LABEL } from './types';
	import type { RankSignalKey, UniverseBtResult, UniverseRow } from './types';

	interface Props {
		lang?: 'ko' | 'en';
		onClose?: () => void;
		onDrillDown?: (stockCode: string) => void; // Q행 클릭 → 단일종목 시간기계(단방향)
	}
	let { lang = 'ko', onClose, onDrillDown }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);

	let rows = $state<UniverseRow[] | null>(null);
	let loadState = $state<'idle' | 'loading' | 'ready' | 'error'>('idle');
	let errMsg = $state('');
	let ymRange = $state<{ min: string; max: string } | null>(null);

	// 컨트롤(P1 사전규칙 · 데이터 보기 전 결정). 시도 카운터(U-G7): 조합 바꿀 때마다 +1.
	let signal = $state<RankSignalKey>('mom12_1');
	let buckets = $state(5);
	let rebalance = $state<'M' | 'Q'>('Q');
	let liquidityPctile = $state(0.7); // 상위30% · 필수(penny 인공물 차단)
	let attempts = $state(0);

	// OOS 강제(끌 수 없음) · train 2010~2019 / test 2020~. 두 구간 동시 회계.
	const result = $derived.by<UniverseBtResult | null>(() => {
		if (!rows || rows.length === 0) return null;
		void signal;
		void buckets;
		void rebalance;
		void liquidityPctile;
		const from = ymRange?.min ?? '201001';
		const to = ymRange?.max ?? '202612';
		return runUniverse(rows, { rebalance, rankSignal: signal, buckets, liquidityPctile, windowFrom: from, windowTo: to });
	});

	async function load() {
		loadState = 'loading';
		try {
			const { db, error } = await ensureDuckDb();
			if (!db) {
				loadState = 'error';
				errMsg = error ?? T('데이터 엔진 미지원 브라우저', 'data engine unsupported');
				return;
			}
			ymRange = await loadUniverseYmRange(db);
			rows = await loadUniversePanel(db, ymRange?.min ?? '201001', ymRange?.max ?? '202612');
			loadState = 'ready';
		} catch (e) {
			loadState = 'error';
			errMsg = e instanceof Error ? e.message : String(e);
		}
	}
	$effect(() => {
		if (loadState === 'idle') load();
	});
	function bump() {
		attempts += 1;
	}

	// ── 시각화 헬퍼: 분위 NAV 공유 절대축(공통 lo/hi) SVG 폴리라인(계단) ──
	const W = 560;
	const H = 200;
	const PAD = { l: 6, r: 44, t: 8, b: 18 };
	function allNav(r: UniverseBtResult): number[] {
		const run = r.conservative; // 헤드라인=보수
		const vals: number[] = [...run.ewBench];
		for (let b = 1; b <= buckets; b++) vals.push(...(run.navByBucket[b] ?? []));
		return vals.filter((v) => Number.isFinite(v));
	}
	const bounds = $derived.by(() => {
		if (!result || result.status !== 'ok') return { lo: 100, hi: 100 };
		const v = allNav(result);
		return { lo: Math.min(100, ...v), hi: Math.max(100, ...v) };
	});
	function path(nav: number[]): string {
		const r = result;
		if (!r) return '';
		const n = nav.length;
		const { lo, hi } = bounds;
		const span = hi - lo || 1;
		const x = (i: number) => PAD.l + (i / Math.max(1, n - 1)) * (W - PAD.l - PAD.r);
		const y = (val: number) => PAD.t + (1 - (val - lo) / span) * (H - PAD.t - PAD.b);
		// 계단(직선보간 금지 · 월말만 평가 시각화, 05 §6)
		let d = '';
		for (let i = 0; i < n; i++) {
			if (!Number.isFinite(nav[i])) continue;
			d += i === 0 ? `M${x(i)},${y(nav[i])}` : ` H${x(i)} V${y(nav[i])}`;
		}
		return d;
	}
	const BUCKET_COLOR = ['#34d399', '#a3e635', '#fbbf24', '#ec4899', '#f0616f']; // 상위(녹)→하위(적), 중립
	const fmt = (v: number) => (v >= 0 ? '+' : '') + v.toFixed(0);
	const pct = (v: number) => (v >= 0 ? '+' : '') + v.toFixed(1) + '%';
</script>

<div class="ubWrap" role="dialog" aria-label={T('유니버스 백테스터', 'Universe backtester')}>
	<div class="ubHead">
		<b class="ubTtl">{T('유니버스 백테스터', 'Universe Backtester')}</b>
		<span class="ubSub">{T('전종목 크로스섹셔널 (폐지 포함·17년 가격보존)', 'cross-sectional · 17y price-preserved')}</span>
		<span class="ubApprox" title={T('월말 리샘플 근사 · 월중 손절·갭·정지 미반영(MDD 과소평가)', 'month-end resample approx')}
			>{T('월말 근사 ⓘ', 'month-end ⓘ')}</span>
		{#if onClose}<button class="ubX" onclick={onClose} aria-label="close">✕</button>{/if}
	</div>

	<div class="ubCtl">
		<select bind:value={signal} onchange={bump} class="ubSel" title={T('랭킹 신호', 'rank signal')}>
			{#each Object.entries(RANK_SIGNAL_LABEL) as [k, v] (k)}<option value={k}>{T(v.kr, v.en)}</option>{/each}
		</select>
		<span class="ubSeg">
			{#each [{ v: 'Q' as const, l: T('분기', 'Q') }, { v: 'M' as const, l: T('월', 'M') }] as o (o.v)}
				<button class={rebalance === o.v ? 'on' : ''} onclick={() => { rebalance = o.v; bump(); }}>{o.l}</button>
			{/each}
		</span>
		<span class="ubSeg">
			{#each [3, 5, 10] as b (b)}
				<button class={buckets === b ? 'on' : ''} onclick={() => { buckets = b; bump(); }}>{b}{T('분위', 'q')}</button>
			{/each}
		</span>
		<label class="ubLiq" title={T('유동성 컷 · 그 시점 거래대금 상위 (필수: penny 인공물 차단)', 'liquidity cut')}>
			{T('유동성 상위', 'liquid top')}
			<select bind:value={liquidityPctile} onchange={bump}>
				<option value={0.8}>20%</option><option value={0.7}>30%</option><option value={0.5}>50%</option>
			</select>
		</label>
		<span class="ubAttempts" title={T('탐색한 조합 수 = 자유도(많을수록 과적합 위험)', 'tried combos = degrees of freedom')}
			>{T('시도', 'tries')} {attempts}</span>
	</div>

	{#if loadState === 'loading'}
		<div class="ubMsg">{T('패널 로드 중… (최초 11.9MB)', 'loading panel… (11.9MB first time)')}</div>
	{:else if loadState === 'error'}
		<div class="ubMsg err">{T('로드 실패', 'load failed')}: {errMsg}</div>
	{:else if result && result.status === 'ok'}
		{@const r = result}
		{@const consTop = r.conservative.navByBucket[1] ?? []}
		{@const optTop = r.optimistic.navByBucket[1] ?? []}
		{@const ew = r.conservative.ewBench}
		<!-- ★NAV 분위 곡선 (공유 절대축·계단). 분위 끝만 라벨, 중간 dim. -->
		<svg class="ubSvg" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-label={T('분위 NAV', 'quantile NAV')}>
			<line x1={PAD.l} y1={H - PAD.b} x2={W - PAD.r} y2={H - PAD.b} class="ubAxis" />
			{#each Array.from({ length: buckets }, (_, i) => i + 1) as b (b)}
				{@const nav = r.conservative.navByBucket[b] ?? []}
				<path d={path(nav)} fill="none" stroke={BUCKET_COLOR[Math.min(4, Math.round(((b - 1) / Math.max(1, buckets - 1)) * 4))]} stroke-width={b === 1 || b === buckets ? 1.6 : 0.9} opacity={b === 1 || b === buckets ? 1 : 0.5} />
				{#if (b === 1 || b === buckets) && nav.length}
					<text x={W - PAD.r + 3} y={PAD.t + (1 - ((nav.at(-1) ?? 100) - bounds.lo) / (bounds.hi - bounds.lo || 1)) * (H - PAD.t - PAD.b)} class="ubLab">Q{b} {fmt((nav.at(-1) ?? 100) - 100)}</text>
				{/if}
			{/each}
			<path d={path(ew)} fill="none" stroke="#8b94a3" stroke-width="1.2" stroke-dasharray="3 2" />
			<text x={W - PAD.r + 3} y={PAD.t + (1 - ((ew.at(-1) ?? 100) - bounds.lo) / (bounds.hi - bounds.lo || 1)) * (H - PAD.t - PAD.b)} class="ubLab ew">EW {fmt((ew.at(-1) ?? 100) - 100)}</text>
		</svg>

		<div class="ubHeadline">
			{#if r.headlineSuppressed}
				<span class="ubBand">⚠ {T('폐지 의존 과다 · 단일 수치 무의미', 'too delisting-dependent · no single number')}</span>
			{:else}
				<b class="ubBig">Q1 {fmt((consTop.at(-1) ?? 100) - 100)}</b>
				<span class="ubBandSm">{T('밴드', 'band')} {fmt((consTop.at(-1) ?? 100) - 100)}~{fmt((optTop.at(-1) ?? 100) - 100)}</span>
			{/if}
			<span class="ubChip">{T('스프레드 Q1−Q', 'spread Q1−Q')}{buckets} {pct(r.conservative.metrics.spreadEndPct)}</span>
			<span class="ubChip">{T('턴오버', 'turnover')} {(r.conservative.metrics.avgTurnover * 100).toFixed(0)}%</span>
			<span class="ubChip">EW {fmt((ew.at(-1) ?? 100) - 100)}</span>
		</div>

		<!-- 정직 표면 상존(닫기불가) · U-G1·G3·G4·G7·G8 -->
		<div class="ubHonesty">
			<div>⚠ {T('단조성=눈으로(t-stat·IC 수치 아님) · 사후선택 1신호 · 표본=리밸', 'monotonicity by eye (not t-stat) · selection · sample=rebalances')} {r.rebalances.length}{T('회', '')}</div>
			<div>⚠ {T('동일가중=소형주 틸트(size 프리미엄 포함) · 폐지 밴드=unknown', 'equal-weight=small-cap tilt · band=unknown delist')} {r.nUnknownExits}{T('종목', '')}{#if r.nMergerExits > 0} · {T('합병 추정', 'merger~')} {r.nMergerExits}{T('=last-close 제외', '=excluded')}{/if}</div>
			<div class="ubFoot">{T('과거 [기간] 이 유니버스·규칙 회계 결과 · 월말 근사(MDD 과소평가) · 추천 아님 · 검증된 팩터 아님', 'historical accounting · month-end approx · not advice')}</div>
		</div>
	{:else if result}
		<div class="ubMsg">{T('표본 부족(리밸<4) · 윈도/신호 조정', 'insufficient sample')}</div>
	{/if}
</div>

<style>
	.ubWrap { background: var(--dl-bg-raised, #0e141f); border: 1px solid var(--dl-line, #1b2130); border-radius: 6px; padding: 10px 12px; color: var(--dl-ink, #c8cfdb); font-size: 12px; max-width: 620px; }
	.ubHead { display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px; }
	.ubTtl { font-size: 13px; font-weight: 700; }
	.ubSub { font-size: 11px; color: #8b94a3; }
	.ubApprox { font-size: 11px; color: #8b94a3; border: 1px solid var(--dl-line, #1b2130); border-radius: 3px; padding: 0 6px; }
	.ubX { margin-left: auto; background: none; border: none; color: #8b94a3; cursor: pointer; font-size: 14px; }
	.ubX:hover { color: var(--dl-ink, #c8cfdb); }
	.ubCtl { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-bottom: 8px; }
	.ubSel, .ubLiq select { background: var(--dl-bg-modal, #11161f); color: var(--dl-ink, #c8cfdb); border: 1px solid var(--dl-line, #1b2130); border-radius: 3px; padding: 2px 5px; font-family: inherit; font-size: 11px; }
	.ubSeg { display: inline-flex; border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; overflow: hidden; }
	.ubSeg button { background: none; border: none; color: #8b94a3; cursor: pointer; font-family: inherit; font-size: 11px; padding: 2px 8px; }
	.ubSeg button.on { background: rgba(255, 255, 255, 0.06); color: var(--dl-ink, #c8cfdb); }
	.ubLiq { font-size: 11px; color: #8b94a3; display: inline-flex; align-items: center; gap: 4px; }
	.ubAttempts { font-size: 11px; color: #8b94a3; margin-left: auto; }
	.ubMsg { padding: 24px; text-align: center; color: #8b94a3; font-size: 12px; }
	.ubMsg.err { color: var(--dn, #f0616f); }
	.ubSvg { display: block; width: 100%; height: 200px; background: rgba(8, 11, 18, 0.5); border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; }
	.ubAxis { stroke: #2a3142; stroke-width: 1; }
	.ubLab { font-size: 9px; fill: #aeb6c2; font-family: var(--dl-font-mono, monospace); }
	.ubLab.ew { fill: #8b94a3; }
	.ubHeadline { display: flex; align-items: baseline; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
	.ubBig { font-size: 17px; font-weight: 700; font-family: var(--dl-font-mono, monospace); }
	.ubBand { font-size: 12px; color: var(--amber, var(--amber)); }
	.ubBandSm { font-size: 11px; color: #8b94a3; }
	.ubChip { font-size: 11px; color: #aeb6c2; border: 1px solid var(--dl-line, #1b2130); border-radius: 10px; padding: 1px 8px; }
	.ubHonesty { margin-top: 8px; font-size: 11px; color: #8b94a3; line-height: 1.55; }
	.ubFoot { color: var(--dimmer, #6b7280); margin-top: 2px; }
</style>
