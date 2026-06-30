<script lang="ts">
	// 백테스트 결과 + 정직 푸터(SSOT) · 전략 도크 하단 sticky. 다전략(N≤3): 조합 헤드라인 + 전략별 미니행(클릭=포커스).
	// BacktestStrip 에서 추출 · 차트 하단 absolute 오버레이가 아니라 도크 footer(normal flow). 닫기는 도크 헤더가 담당.
	// 정직(04): 3단 심각도 · Tier1 명세 스탬프(상존) · Tier2 구조한계(N≥2 사후선택) · Tier3 active 경고(amber, 발동시만).
	// 11px floor. 전략 열위 시 dim(초록 축포 금지). 상세 전부는 [백테스팅 상세] → BacktestDialog.
	import type { PortfolioBtResult, StrategySlot, BtWarning } from '../lib/backtest';
	import { GOV_ATTRIBUTION } from '@dartlab/ui-contracts';
	import type { Lang } from '../lib/types';

	interface Props {
		pf: PortfolioBtResult;
		slots: StrategySlot[]; // 전체 슬롯(메타) · pf.slots 는 워밍업 통과분만이라 id 매칭
		focus: number;
		withCosts: boolean;
		adjusted: boolean;
		lang: Lang;
		onFocus: (i: number) => void;
		onOpenReport: () => void;
	}
	let { pf, slots, focus, withCosts, adjusted, lang, onFocus, onOpenReport }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);
	let methodOpen = $state(false); // ⓘ 방법론 · 가정 원장 on-demand (Bloomberg 패턴)
	const sgn = (v: number, d = 1) => (v >= 0 ? '+' : '') + v.toFixed(d);
	const cls = (v: number) => (v > 0 ? 'tUp' : v < 0 ? 'tDn' : 'tNeu');
	const fmtDate = (t: string) => `${t.slice(2, 4)}.${t.slice(4, 6)}.${t.slice(6, 8)}`;

	const multi = $derived(pf.slots.length >= 2);
	const bhRet = $derived(pf.slots[0]?.result.bh.retPct ?? 0);
	const focusId = $derived(slots[focus]?.id ?? slots[0]?.id);
	const focusRes = $derived(pf.slots.find((s) => s.id === focusId)?.result ?? pf.slots[0]?.result ?? null);
	const headRet = $derived(pf.combo ? pf.combo.metrics.retPct : focusRes?.metrics.retPct ?? 0);
	const headLabel = $derived(pf.combo ? T('조합', 'combo') : slots.find((s) => s.id === focusId)?.label ?? '');
	const comboMddNums = $derived.by(() => {
		if (!pf.combo || !pf.slots.length) return null;
		const worst = Math.min(...pf.slots.map((s) => s.result.metrics.mddPct));
		return { combo: pf.combo.metrics.mddPct, worst, better: pf.combo.metrics.mddPct > worst };
	});
	const comboMddBetter = $derived(comboMddNums?.better ?? false);
	const metaOf = (id: string) => slots.find((s) => s.id === id);
	const idxOf = (id: string) => slots.findIndex((s) => s.id === id);
	const WARN_LABEL: Record<BtWarning['kind'], { kr: string; en: string }> = {
		fewTrades: { kr: '표본 부족', en: 'few trades' },
		shortRange: { kr: '기간 부족 · 참고용', en: 'short range' },
		splitSuspect: { kr: '분할 의심 · 구간 무효', en: 'split suspect' },
		costsOff: { kr: '비용 미포함', en: 'costs off' }
	};
</script>

<div class="btFooter" class:btLag={headRet < bhRet}>
	<div class="btHead">
		<b class={'btRet mono ' + cls(headRet)}>{headLabel} {sgn(headRet)}%</b>
		<span class="btVs">vs</span>
		<b class={'btRet mono ' + cls(bhRet)}>{T('보유', 'B&H')} {sgn(bhRet)}%</b>
		<span class={'btExcess mono ' + cls(headRet - bhRet)}>{sgn(headRet - bhRet)}%p</span>
		<button class="btMore" onclick={onOpenReport} title={T('자산곡선·거래·낙폭·가정 보기', 'detailed view')}>{T('백테스팅 상세', 'details')} ▸</button>
	</div>

	<!-- 전략별 미니행 · 색칩 + 라벨 + 수익률(입력 순서, 승자 정렬·강조 금지). 클릭 = 포커스(마커·리포트 전환). -->
	<div class="btChips">
		{#each pf.slots as s (s.id)}
			{@const meta = metaOf(s.id)}
			<button class="btChip" class:on={s.id === focusId} onclick={() => onFocus(idxOf(s.id))} title={T('이 전략에 포커스 (마커·상세)', 'focus this strategy')}>
				<i class="btSw" style={`background:${meta?.color ?? '#8b919e'}`}></i>
				<span class="btChipLbl">{meta?.label ?? s.id}</span>
				<b class={'mono ' + cls(s.result.metrics.retPct)}>{sgn(s.result.metrics.retPct)}%</b>
			</button>
		{/each}
	</div>

	<!-- ★정직 Tier3 (active 경고, amber·트리거 시만) + Tier2 (사후선택/분산, N≥2 상존). -->
	{#if (focusRes?.warnings ?? []).length || multi}
		<div class="btTier btTierFlags">
			{#each focusRes?.warnings ?? [] as w (w.kind)}
				<span class="btWarnChip" title={w.date ?? ''}>⚠ {T(WARN_LABEL[w.kind].kr, WARN_LABEL[w.kind].en)}{w.date ? ' ' + fmtDate(w.date) : ''}</span>
			{/each}
			{#if multi}
				<button class="btFlagChip" onclick={() => (methodOpen = !methodOpen)} title={T('여러 전략을 같은 데이터로 비교 = 사후선택 편향(위 곡선이 미래 최고 아님) · 단일종목 조합 = 타이밍 분산이지 자산 분산 아님', 'comparing strategies on the same data = selection bias · single-stock combo = timing, not asset diversification')}>{T('사후선택·타이밍분산', 'selection · timing')}{#if comboMddBetter && comboMddNums} · <b class="btDiv">{T('분산효과 낙폭', 'divers. DD')} {Math.abs(comboMddNums.combo).toFixed(0)}%&lt;{Math.abs(comboMddNums.worst).toFixed(0)}%</b>{/if} ⓘ</button>
			{/if}
		</div>
	{/if}
	<!-- Tier1 명세 스탬프(상존·닫기불가) · 방법론은 capability(경고 아님). -->
	<div class="btTier btTierSpec">
		<span class="btStamp">{T('체결 t+1 시가', 'fill t+1 open')}</span>
		<span class="btStamp">{withCosts ? T('비용 반영', 'costs on') : T('비용 미포함', 'costs off')}</span>
		<span class="btStamp">{adjusted ? T('배당미반영·수정주가', 'div excl·adj') : T('배당미반영·무수정주가', 'div excl·unadj')}</span>
		<span class="btStamp">{T('단일구간', 'single window')}</span>
		{#if focusRes?.runSpec}<span class="btStamp">{T('기준일', 'as of')} {fmtDate(focusRes.runSpec.dataAsOf)}</span>{/if}
		<button class="btMethod" class:on={methodOpen} onclick={() => (methodOpen = !methodOpen)} title={T('방법론·가정 펼치기', 'methodology')}>ⓘ {T('방법론', 'method')}</button>
	</div>
	{#if methodOpen}
		<div class="btLedger">
			{#if multi}<div>{T('· 여러 전략 같은 데이터 비교 = 사후선택 편향 · 단일종목 조합 = 타이밍 분산이지 자산 분산 아님 · 조합 = 동일가중 보유합성(리밸런싱 없음)', '· comparing strategies on same data = selection bias · single-stock combo = timing not asset diversification · combo = equal-weight, no rebalancing')}</div>{/if}
			<div>{T('· 신호 t일 종가 → t+1일 시가 체결 · 미래참조 구조적 차단', '· signal close(t) → fill open(t+1) · look-ahead structurally blocked')}</div>
			<div>{T('· 거래정지·갭 봉(v=0/o=0) = 체결 이연 (감사 카운터로 노출)', '· halted/gap bars (v=0/o=0) = fill deferred (audit counter)')}</div>
			<div>{T('· 배당 미반영 + 무수정주가 기본 → B&H를 보수적으로 깎음(전략이 상대적 유리) · 상존 편향', '· dividends excluded + unadjusted price haircut B&H · persistent bias favoring strategy')}</div>
			<div>{T('· 단일구간 in-sample · 과거 가정 노출형 시뮬레이션 · 미래 수익 보장 없음 · 추천 아님', '· single-window in-sample · assumption-exposed historical simulation · no guarantee · not advice')}</div>
			<div class="btAttrLine">{GOV_ATTRIBUTION}</div>
		</div>
	{/if}
</div>

<style>
	/* 도크 하단 결과+정직 푸터 · normal flow(도크가 sticky 처리). 11px floor 유지. */
	.btFooter { padding: 6px 7px 5px; font-size: 11.5px; border-top: 1px solid var(--dl-line-strong, #2a3142); background: rgba(10, 14, 21, 0.6); }
	.btFooter.btLag { opacity: 0.92; }
	.btHead { display: flex; align-items: baseline; gap: 7px; flex-wrap: wrap; }
	.btRet { font-size: 15px; font-weight: 700; font-variant-numeric: tabular-nums; }
	.btVs { color: var(--dimmer); font-size: 10px; }
	.btExcess { font-size: 12px; font-weight: 700; padding: 1px 6px; border-radius: 8px; border: 1px solid var(--dl-line, #1b2130); font-variant-numeric: tabular-nums; }
	.btMore { margin-left: auto; background: rgba(var(--amber-rgb), 0.1); border: 1px solid rgba(var(--amber-rgb), 0.45); color: var(--amber, var(--amber)); font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 3px; cursor: pointer; font-family: inherit; }
	.btMore:hover { background: rgba(var(--amber-rgb), 0.2); }
	.btChips { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
	.btChip { display: inline-flex; align-items: center; gap: 5px; background: none; border: 1px solid var(--dl-line, #1b2130); border-radius: 12px; padding: 1px 8px 1px 5px; cursor: pointer; font-family: inherit; font-size: 11px; color: #aeb6c2; }
	.btChip:hover { border-color: #3a4456; }
	.btChip.on { border-color: #3a4456; background: rgba(255, 255, 255, 0.04); }
	.btSw { width: 9px; height: 9px; border-radius: 2px; display: inline-block; }
	.btChipLbl { color: var(--dl-ink, #c8cfdb); }
	.btChip b { font-size: 11px; font-variant-numeric: tabular-nums; }
	.btTier { margin-top: 4px; line-height: 1.5; font-size: 11px; }
	.btTierFlags { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
	.btWarnChip { font-size: 11px; color: var(--amber, var(--amber)); border: 1px solid rgba(var(--amber-rgb), 0.35); border-radius: 3px; padding: 0 6px; }
	.btFlagChip { font-size: 11px; color: #8b94a3; background: none; border: 1px solid var(--dl-line, #1b2130); border-radius: 3px; padding: 1px 7px; cursor: pointer; font-family: inherit; }
	.btFlagChip:hover { color: #aeb6c2; border-color: #3a4456; }
	.btDiv { font-weight: 600; font-style: normal; color: #aeb6c2; }
	.btTierSpec { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; color: var(--dimmer); }
	.btStamp { color: #8b94a3; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--dl-line, #1b2130); border-radius: 3px; padding: 0 6px; letter-spacing: 0.01em; }
	.btMethod { font-size: 11px; background: none; border: 1px solid var(--dl-line-strong, #2a3142); color: #aeb6c2; border-radius: 3px; padding: 0 7px; cursor: pointer; font-family: inherit; }
	.btMethod:hover, .btMethod.on { color: var(--dl-ink, #c8cfdb); border-color: #3a4456; }
	.btLedger { margin-top: 4px; padding: 6px 8px; background: rgba(255, 255, 255, 0.02); border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; font-size: 11px; color: #8b94a3; line-height: 1.6; }
	.btAttrLine { color: #5b6573; font-size: 10px; margin-top: 2px; }
	.tUp { color: var(--up, #34d399); }
	.tDn { color: var(--dn, #f0616f); }
	.tNeu { color: #aeb6c2; }
</style>
