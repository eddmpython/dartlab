<script lang="ts">
	import { marketForCode } from '../lib/dartUrl';
	import {
		financeAvailability,
		loadFinanceStatement,
		loadSceMatrix,
		type FinanceAvailability
	} from '../lib/finance/financeQuery';
	import {
		FREQ_BY_KIND,
		FREQ_LABELS,
		KIND_LABELS,
		SCOPE_LABELS,
		UNIT_DIVISORS,
		UNIT_LABELS,
		type FinanceFreq,
		type FinanceKind,
		type FinanceScope,
		type FinanceStatement,
		type FinanceUnit,
		type SceMatrixData
	} from '../lib/finance/types';
	import FinanceTable from './FinanceTable.svelte';
	import SceMatrix from './SceMatrix.svelte';

	let {
		code,
		corpName = '',
		showHeader = true,
		frameless = false
	}: {
		code: string;
		corpName?: string;
		showHeader?: boolean;
		frameless?: boolean;
	} = $props();

	const KINDS: FinanceKind[] = ['IS', 'BS', 'CF', 'CIS', 'SCE'];
	const UNITS: FinanceUnit[] = ['원', '백만', '억'];
	// avail probe 실패(파케이 404 등) 시에도 로드는 진행시켜 정직한 에러 메시지를 띄운다 · null 고정 = 영구 스피너 회귀.
	const AVAIL_FALLBACK: FinanceAvailability = { scopes: ['CFS', 'OFS'], byScope: { CFS: KINDS, OFS: KINDS } };

	let kind = $state<FinanceKind>('IS');
	let freq = $state<FinanceFreq>('quarter'); // 기본 분기 · 표는 최신 보고 원값 우선 (연간·누적은 토글)
	let scope = $state<FinanceScope>('CFS'); // 연결 우선 · availableScopes(CFS 우선 정렬) 미포함 시에만 첫 가용범위로
	let unit = $state<FinanceUnit>('백만');
	let avail = $state<FinanceAvailability | null>(null);
	let statement = $state<FinanceStatement | null>(null);
	let sceData = $state<SceMatrixData | null>(null);
	let scePeriod = $state('');
	let loading = $state(false);
	let errorMsg = $state<string | null>(null);

	const divisor = $derived(UNIT_DIVISORS[unit]);
	const market = $derived(marketForCode(code));
	const displayName = $derived(corpName || code);
	const availableScopes = $derived<FinanceScope[]>(avail?.scopes.length ? avail.scopes : ['CFS', 'OFS']);
	const availableKinds = $derived<FinanceKind[]>(avail ? (avail.byScope[scope] ?? []) : KINDS);
	const isEmpty = $derived(kind !== 'SCE' && statement != null && statement.rows.length === 0);
	const sceEmpty = $derived(kind === 'SCE' && sceData != null && sceData.periods.length === 0);

	const displayTabs = $derived.by(() => {
		const has = new Set(availableKinds);
		const tabs: { label: string; kind: FinanceKind }[] = [];
		if (has.has('IS')) tabs.push({ label: '손익계산서', kind: 'IS' });
		else if (has.has('CIS')) tabs.push({ label: '손익계산서', kind: 'CIS' });
		if (has.has('BS')) tabs.push({ label: '재무상태표', kind: 'BS' });
		if (has.has('CF')) tabs.push({ label: '현금흐름표', kind: 'CF' });
		if (has.has('IS') && has.has('CIS')) tabs.push({ label: '포괄손익', kind: 'CIS' });
		if (has.has('SCE')) tabs.push({ label: '자본변동표', kind: 'SCE' });
		return tabs;
	});

	function firstTabKind(a: FinanceKind[]): FinanceKind {
		const has = new Set(a);
		if (has.has('IS')) return 'IS';
		if (has.has('CIS')) return 'CIS';
		return a[0] ?? 'BS';
	}

	function pickKind(k: FinanceKind) {
		kind = k;
		if (!FREQ_BY_KIND[k].includes(freq)) freq = FREQ_BY_KIND[k][0];
	}

	function usOrDeviceMsg(m: string): string {
		return m === 'US'
			? 'EDGAR 정량재무제표는 준비 중입니다.'
			: '정량재무제표를 불러올 수 없습니다.';
	}

	let lastAvailKey = '';
	$effect(() => {
		const m = market;
		const c = code;
		const key = `${m}:${c}`;
		if (key === lastAvailKey) return;
		lastAvailKey = key;
		avail = null;
		statement = null;
		sceData = null;
		errorMsg = null;
		void financeAvailability(c, m)
			.then((a) => {
				if (code === c) avail = a;
			})
			.catch(() => {
				if (code === c) avail = AVAIL_FALLBACK;
			});
	});

	$effect(() => {
		if (!avail) return;
		if (!availableScopes.includes(scope)) {
			scope = availableScopes[0]; // 연결 우선(availableScopes CFS 우선) · 연결 없을 때만 별도
			return;
		}
		if (!availableKinds.includes(kind)) pickKind(firstTabKind(availableKinds));
	});

	let lastLoadKey = '';
	$effect(() => {
		const m = market;
		const c = code;
		const k = kind;
		const f = freq;
		const s = scope;
		// 가용성 확정 전엔 로드 보류 · 기본 kind(IS)로 헛로드하면 단일 포괄손익(CIS) 회사에서
		// 빈 IS 결과가 CIS 라벨로 잠깐 렌더되는 깜빡임 + 이중로드가 생긴다. avail 도착 시 kind 교정 후 1회 로드.
		if (!avail) return;
		const key = `${m}:${c}:${k}:${f}:${s}`;
		if (key === lastLoadKey) return;
		lastLoadKey = key;
		loading = true;
		errorMsg = null;
		statement = null;
		sceData = null;
		if (k === 'SCE') {
			loadSceMatrix(c, m, s)
				.then((data) => {
					if (code !== c) return;
					sceData = data;
					if (data && data.periods.length) {
						if (!data.periods.includes(scePeriod)) scePeriod = data.periods[0];
					} else {
						errorMsg = data === null ? usOrDeviceMsg(m) : '자본변동표 데이터가 없습니다.';
					}
				})
				.catch((e) => {
					if (code === c) errorMsg = `로드 실패: ${e instanceof Error ? e.message : String(e)}`;
				})
				.finally(() => {
					if (code === c) loading = false;
				});
			return;
		}
		loadFinanceStatement(c, m, k, f, s)
			.then((st) => {
				if (code !== c) return;
				statement = st;
				if (st === null) errorMsg = usOrDeviceMsg(m);
			})
			.catch((e) => {
				if (code === c) errorMsg = `로드 실패: ${e instanceof Error ? e.message : String(e)}`;
			})
			.finally(() => {
				if (code === c) loading = false;
			});
	});
</script>

<section class="finance-pane" class:frameless aria-label="재무제표 분석">
	{#if showHeader}
		<header class="fp-head">
			<div class="fp-title">
				<strong>{displayName}</strong>
				<span>{code}</span>
				<em>정량재무제표</em>
			</div>
			<div class="fp-meta">
				<span>{KIND_LABELS[kind]}</span>
				<span>{SCOPE_LABELS[scope]}</span>
				<span>단위 {UNIT_LABELS[unit]}</span>
			</div>
		</header>
	{/if}

	<div class="controls">
		<div class="tabs">
			{#each displayTabs as t (t.label)}
				<button type="button" class="tab" class:active={kind === t.kind} onclick={() => pickKind(t.kind)} title={t.label}>{t.label}</button>
			{/each}
		</div>
		<div class="segs">
			{#if kind === 'SCE'}
				<div class="seg" title="기간">
					{#each (sceData?.periods ?? []).slice(0, 8) as p (p)}
						<button type="button" class="seg-btn" class:active={scePeriod === p} onclick={() => (scePeriod = p)}>{p}</button>
					{/each}
				</div>
			{:else}
				<div class="seg" title="빈도">
					{#each FREQ_BY_KIND[kind] as f (f)}
						<button type="button" class="seg-btn" class:active={freq === f} onclick={() => (freq = f)}>{FREQ_LABELS[f]}</button>
					{/each}
				</div>
			{/if}
			{#if availableScopes.length > 1}
				<div class="seg" title="범위">
					{#each availableScopes as s (s)}
						<button type="button" class="seg-btn" class:active={scope === s} onclick={() => (scope = s)}>{SCOPE_LABELS[s]}</button>
					{/each}
				</div>
			{/if}
			<div class="seg" title="단위">
				{#each UNITS as u (u)}
					<button type="button" class="seg-btn" class:active={unit === u} onclick={() => (unit = u)}>{u}</button>
				{/each}
			</div>
		</div>
	</div>

	<div class="body">
		{#if loading || !avail}
			<div class="state"><div class="spinner"></div></div>
		{:else if errorMsg}
			<div class="state"><p>{errorMsg}</p></div>
		{:else if kind === 'SCE'}
			{#if sceEmpty || !sceData || !scePeriod}
				<div class="state"><p>이 회사는 자본변동표({SCOPE_LABELS[scope]}) 데이터가 없습니다.</p></div>
			{:else}
				<SceMatrix data={sceData} period={scePeriod} {divisor} />
			{/if}
		{:else if isEmpty}
			<div class="state"><p>이 회사는 {KIND_LABELS[kind]}({FREQ_LABELS[freq]}·{SCOPE_LABELS[scope]}) 정량 데이터가 없습니다.</p></div>
		{:else if statement}
			<FinanceTable {statement} {divisor} />
		{/if}
	</div>
</section>

<style>
	/* --fin-* 토큰: 미정의 시 fallback = 기존 viewer 값 (픽셀 무변화).
	   터미널은 .dlTermFinSkin 래퍼가 terminal.css 토큰으로 오버라이드. */
	.finance-pane {
		height: 100%;
		min-height: 0;
		display: flex;
		flex-direction: column;
		background: var(--fin-bg, #050811);
		color: var(--fin-txt, #f1f5f9);
		border: 1px solid var(--fin-bd, #1e2433);
		border-radius: var(--fin-radius-lg, 8px);
		overflow: hidden;
		font-family: var(--fin-font, inherit);
	}
	.finance-pane.frameless {
		border: 0;
		border-radius: 0;
	}
	.fp-head {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 8px 10px;
		border-bottom: 1px solid var(--fin-bd, #1e2433);
	}
	.fp-title,
	.fp-meta {
		display: flex;
		align-items: baseline;
		gap: 8px;
		min-width: 0;
	}
	.fp-title strong {
		font-size: 14px;
		font-weight: 800;
		white-space: nowrap;
	}
	.fp-title span {
		color: #94a3b8;
		font-family: monospace;
		font-size: 11px;
	}
	.fp-title em {
		color: #cbd5e1;
		font-size: 12px;
		font-style: normal;
	}
	.fp-title em::before {
		content: '·';
		margin-right: 6px;
		color: #64748b;
	}
	.fp-meta {
		flex-shrink: 0;
		color: #cbd5e1;
		font-size: 11px;
	}
	.fp-meta span + span::before {
		content: '·';
		margin-right: 8px;
		color: #64748b;
	}
	.controls {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 10px;
		padding: 8px 10px;
		border-bottom: 1px solid var(--fin-bd, #1e2433);
	}
	.tabs,
	.segs {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		flex-wrap: wrap;
	}
	.tab {
		padding: 5px 10px;
		border: 1px solid transparent;
		border-radius: var(--fin-radius, 6px);
		background: transparent;
		color: var(--fin-dim, #cbd5e1);
		font: inherit;
		font-size: 12px;
		cursor: pointer;
	}
	.tab:hover {
		color: #e2e8f0;
	}
	.tab.active {
		background: rgba(var(--amber-rgb), 0.12);
		border-color: rgba(var(--amber-rgb), 0.5);
		color: var(--amber);
		font-weight: 600;
	}
	.seg {
		display: inline-flex;
		gap: 2px;
		padding: 2px;
		border: 1px solid var(--fin-bd, #1e2433);
		border-radius: var(--fin-radius, 6px);
	}
	.seg-btn {
		padding: 3px 8px;
		border: none;
		border-radius: var(--fin-radius, 4px);
		background: transparent;
		color: var(--fin-dim, #cbd5e1);
		font: inherit;
		font-size: 11px;
		cursor: pointer;
	}
	.seg-btn:hover {
		color: #e2e8f0;
	}
	.seg-btn.active {
		background: rgba(var(--amber-rgb), 0.14);
		color: var(--amber);
		font-weight: 600;
	}
	.body {
		flex: 1 1 auto;
		min-height: 0;
		overflow: hidden;
	}
	.state {
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 12px;
		color: var(--fin-dim, #cbd5e1);
		text-align: center;
	}
	.state p {
		margin: 0;
		font-size: 13px;
	}
	.spinner {
		width: 26px;
		height: 26px;
		border: 2px solid var(--fin-bd, #1e2433);
		border-top-color: var(--amber);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	@media (max-width: 760px) {
		.fp-head {
			align-items: flex-start;
			flex-direction: column;
		}
		.controls {
			align-items: flex-start;
			flex-direction: column;
		}
	}
</style>
