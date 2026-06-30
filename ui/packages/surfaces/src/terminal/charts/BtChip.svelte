<script lang="ts">
	// 차트 위 백테스트 요약 칩 · 가격 페인 좌상단(OHLC 레전드 아래). 한 줄 헤드라인(도크 푸터와 동일 문법) +
	// 가장 심각한 active 경고 1개만 글리프로. equity 결과는 차트의 시계열 객체라 그 요약은 차트 chrome 에 둔다(배치법칙).
	// 클릭 = [백테스팅 상세] 다이얼로그. B&H 열위 시 dim(초록 축포 금지). 전체 정직 푸터는 도크가 담당(여긴 1줄+글리프).
	import type { PortfolioBtResult, StrategySlot, BtWarning } from '../lib/backtest';
	import type { Lang } from '../lib/types';

	interface Props {
		pf: PortfolioBtResult;
		slots: StrategySlot[];
		focus: number;
		lang: Lang;
		left: number; // 차트 페인 좌상단 x(px) · PriceChart railBox geometry
		top: number; // 차트 페인 상단 y(px) + 레전드 오프셋
		hide?: boolean; // 차트 드래그/줌 중 숨김
		onOpenReport: () => void;
	}
	let { pf, slots, focus, lang, left, top, hide = false, onOpenReport }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);
	const sgn = (v: number, d = 1) => (v >= 0 ? '+' : '') + v.toFixed(d);
	const cls = (v: number) => (v > 0 ? 'tUp' : v < 0 ? 'tDn' : 'tNeu');

	const bhRet = $derived(pf.slots[0]?.result.bh.retPct ?? 0);
	const focusId = $derived(slots[focus]?.id ?? slots[0]?.id);
	const focusSlot = $derived(pf.slots.find((s) => s.id === focusId) ?? pf.slots[0] ?? null);
	const focusMeta = $derived(slots.find((s) => s.id === focusId) ?? slots[focus] ?? slots[0]);
	const headRet = $derived(pf.combo ? pf.combo.metrics.retPct : focusSlot?.result.metrics.retPct ?? 0);
	// ★정직 패리티 · 보고서와 동일한 일화(증거 약함: 봉<60 또는 거래<5) 규칙. 차트가 헤드라인 surface 가 됐으니
	// 칩도 큰 초록 차단(NEVER-CLAIM): 약표본이면 수익·초과를 중립색으로(보고서 clsT 와 동일).
	const weakTier = $derived.by(() => {
		const r = focusSlot?.result;
		if (!r) return false;
		const nBars = r.equity.filter((v) => v != null).length;
		return nBars < 60 || r.metrics.tradeCount < 5;
	});
	const clsT = (v: number) => (weakTier ? 'tNeu' : cls(v));
	const headLabel = $derived(pf.combo ? T('조합', 'combo') : focusMeta?.label ?? '');
	const dotColor = $derived(pf.combo ? '#e879f9' : focusMeta?.color ?? '#8b919e');

	// 가장 심각한 active 경고 1개 · 우선순위 splitSuspect > shortRange > fewTrades > costsOff.
	const WARN_TOKEN: Record<BtWarning['kind'], { kr: string; en: string }> = {
		splitSuspect: { kr: '분할의심', en: 'split?' },
		shortRange: { kr: '기간부족', en: 'short' },
		fewTrades: { kr: '표본부족', en: 'few' },
		costsOff: { kr: '비용off', en: 'no cost' }
	};
	const PRIORITY: BtWarning['kind'][] = ['splitSuspect', 'shortRange', 'fewTrades', 'costsOff'];
	const topWarn = $derived.by(() => {
		const ws = focusSlot?.result.warnings ?? [];
		for (const k of PRIORITY) { const w = ws.find((x) => x.kind === k); if (w) return WARN_TOKEN[k]; }
		return null;
	});
</script>

{#if !hide}
	<button
		class="btChipOC"
		class:lag={headRet < bhRet}
		style={`left:${left}px;top:${top}px`}
		onclick={onOpenReport}
		title={T('백테스팅 상세 · 자산곡선·거래·낙폭·가정', 'backtest details')}
	>
		<i class="oc-dot" style={`background:${dotColor}`}></i>
		<b class={'oc-ret mono ' + clsT(headRet)}>{headLabel} {sgn(headRet)}%</b>
		<span class="oc-vs">vs {T('보유', 'B&H')}</span>
		<b class={'oc-bh mono ' + cls(bhRet)}>{sgn(bhRet)}%</b>
		<span class={'oc-xs mono ' + clsT(headRet - bhRet)}>{sgn(headRet - bhRet)}%p</span>
		{#if weakTier}<span class="oc-anec">{T('일화', 'anecdote')}</span>{/if}
		{#if topWarn}<span class="oc-warn">⚠ {T(topWarn.kr, topWarn.en)}</span>{/if}
		<span class="oc-more">{T('상세', 'details')} ▸</span>
	</button>
{/if}

<style>
	.btChipOC {
		position: absolute;
		z-index: 8;
		display: inline-flex;
		align-items: center;
		gap: 6px;
		background: rgba(10, 14, 21, 0.88);
		border: 1px solid var(--dl-line-strong, #2a3142);
		border-radius: 5px;
		padding: 3px 9px;
		cursor: pointer;
		font-family: inherit;
		backdrop-filter: blur(2px);
		max-width: calc(100% - 16px);
		white-space: nowrap;
		overflow: hidden;
	}
	.btChipOC:hover { border-color: #3a4456; }
	.btChipOC.lag { opacity: 0.9; }
	.oc-dot { width: 9px; height: 9px; border-radius: 2px; display: inline-block; flex: none; }
	.oc-ret { font-size: 16px; font-weight: 700; font-variant-numeric: tabular-nums; }
	.oc-vs { font-size: 10px; color: var(--dimmer, #5b6573); }
	.oc-bh { font-size: 12px; font-weight: 700; font-variant-numeric: tabular-nums; }
	.oc-xs { font-size: 12px; font-weight: 700; padding: 0 6px; border-radius: 8px; border: 1px solid var(--dl-line, #1b2130); font-variant-numeric: tabular-nums; }
	.oc-warn { font-size: 11px; color: var(--amber, var(--amber)); border: 1px solid rgba(var(--amber-rgb), 0.35); border-radius: 3px; padding: 0 5px; }
	/* 일화 태그 · 증거 약함(봉<60 또는 거래<5). 수익 중립색과 함께 "한 경로의 운"을 명시(NEVER-CLAIM). */
	.oc-anec { font-size: 10.5px; color: var(--dim, #8b94a3); border: 1px solid var(--dl-line, #1b2130); border-radius: 3px; padding: 0 5px; }
	.oc-more { font-size: 11px; color: var(--amber, var(--amber)); font-weight: 600; }
	.tUp { color: var(--up, #34d399); }
	.tDn { color: var(--dn, #f0616f); }
	.tNeu { color: #aeb6c2; }
</style>
