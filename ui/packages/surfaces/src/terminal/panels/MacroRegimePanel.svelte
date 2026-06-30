<script lang="ts">
	// 거시 국면 · 좌측 최상단 글랜스. 한국 | 미국 세로 2분할로 두 시장 국면을 동시에.
	// 각 칸: 국면·확신도·성장/물가 방향·사분면·자산함의(빈 공간 없이 채움). 깊이·차트는 다이얼로그.
	import type { Lang } from '../lib/types';
	import type { RegimeQuadrantView, RegimeMarketView } from '../lib/macroLens';

	interface Props {
		regime: RegimeQuadrantView;
		lang: Lang;
	}
	let { regime, lang }: Props = $props();
	const T = (kr: string, en: string): string => (lang === 'en' ? en : kr);

	const kr = $derived(regime.markets.find((m) => m.market === 'KR') ?? null);
	const us = $derived(regime.markets.find((m) => m.market === 'US') ?? null);
	const cols = $derived(
		[
			{ m: kr, label: T('한국', 'KR') },
			{ m: us, label: T('미국', 'US') }
		].filter((c): c is { m: RegimeMarketView; label: string } => !!c.m)
	);

	function phaseTone(phase: string): string {
		const p = (phase || '').toLowerCase();
		if (/(expansion|recovery|확장|회복)/.test(p)) return 'tUp';
		if (/(contraction|crisis|수축|침체|위기)/.test(p)) return 'tDn';
		if (/(slowdown|둔화|보합)/.test(p)) return 'tWarn';
		return 'tNeu';
	}
	const arrow = (s: string): string => (/(ris|up|상승|확장|↑)/i.test(s) ? '↑' : /(fall|down|하락|둔화|↓)/i.test(s) ? '↓' : '→');
	const assetTone = (t: string): string => (t === 'ow' ? 'tUp' : t === 'uw' ? 'tDn' : 'tNeu');
	const assetArrow = (t: string): string => (t === 'ow' ? '↑' : t === 'uw' ? '↓' : '·');
</script>

{#if cols.length}
	<div class="mrSplit">
		{#each cols as c (c.label)}
			<div class="mrCol">
				<div class="mrColHd">{c.label}</div>
				<div class="mrColPhaseRow">
					<span class={'mrColPhase ' + phaseTone(c.m.phase)}>{c.m.phaseLabel || c.m.phase}</span>
					{#if c.m.confidence}<span class="mrColConf">{c.m.confidence}</span>{/if}
				</div>
				<div class="mrColDir">
					{#if c.m.growth}<span>{T('성장', 'G')} {arrow(c.m.growth)}</span>{/if}
					{#if c.m.inflation}<span>{T('물가', 'P')} {arrow(c.m.inflation)}</span>{/if}
				</div>
				{#if c.m.quadrantLabel}<div class="mrColQuad">{c.m.quadrantLabel}</div>{/if}
				{#if c.m.assets.length}
					<div class="mrColAssets">
						{#each c.m.assets as a (a.key)}
							<span class={assetTone(a.tone)}>{lang === 'en' ? a.labelEn : a.labelKr}{assetArrow(a.tone)}</span>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</div>
{:else}
	<div class="mrEmpty">{T('국면 데이터 미산출', 'no regime data')}</div>
{/if}
