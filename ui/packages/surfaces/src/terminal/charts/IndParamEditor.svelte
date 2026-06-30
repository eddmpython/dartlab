<script lang="ts">
	// 지표 파라미터 generic 에디터 · IND_DEFS 카탈로그 기반, 29종 전부 한 컴포넌트.
	// 확인 버튼 없음(즉시 반영 = HTS 감각). 적용은 ChartCtl.setIndParams → PriceChart diff effect 가 overrideIndicator.
	import type { Lang } from '../lib/types';
	import type { ChartCtl } from './chartState.svelte';
	import { IND_DEFS } from './indicatorParams';

	interface Props {
		ctl: ChartCtl;
		lang: Lang;
		name: string;
		onRemove?: () => void; // 지표 제거 (호출측 toggleOverlay/toggleSub)
	}
	let { ctl, lang, name, onRemove }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);
	const def = $derived(IND_DEFS[name]);
	const cur = $derived(ctl.indParams[name] ?? def?.defaults ?? []);
	const paramDef = (i: number) => def.params[Math.min(i, def.params.length - 1)];

	function step(i: number, dir: 1 | -1) {
		const pd = paramDef(i);
		const next = cur.slice();
		next[i] = Math.max(pd.min, Math.min(pd.max, +(next[i] + dir * pd.step).toFixed(2)));
		// MACD 류 단기<장기 가드 (en 라벨 fast/slow 쌍 존재 시)
		const fi = def.params.findIndex((p) => p.en === 'fast');
		const si = def.params.findIndex((p) => p.en === 'slow');
		if (fi >= 0 && si >= 0 && next[fi] >= next[si]) return;
		ctl.setIndParams(name, next);
	}
	function removeLine(i: number) {
		if (cur.length <= 1) return;
		ctl.setIndParams(name, cur.filter((_, j) => j !== i));
	}
	function addLine() {
		if (cur.length >= 5) return; // 기본 라인 팔레트 5색 · 6번째부터 색 재사용이라 상한 5
		const pd = paramDef(cur.length);
		ctl.setIndParams(name, [...cur, Math.min(pd.max, Math.round(cur[cur.length - 1] * 2))]);
	}
</script>

{#if def}
	<div class="ipEditor">
		<div class="ctMenuLbl">{name}{def.hintKr ? ` (${def.hintKr})` : ''} {T('파라미터', 'params')}</div>
		{#each cur as v, i (i)}
			<div class="ctRow btParamRow">
				<span class="btParamLbl">{lang === 'en' ? paramDef(i).en : paramDef(i).kr}</span>
				<button class="mItem" onclick={() => step(i, -1)}>−</button>
				<b class="btParamVal mono">{v}</b>
				<button class="mItem" onclick={() => step(i, 1)}>+</button>
				{#if def.grow && cur.length > 1}<button class="mItem" title={T('라인 제거', 'remove line')} onclick={() => removeLine(i)}>×</button>{/if}
			</div>
		{/each}
		<div class="ctRow">
			{#if def.grow && cur.length < 5}<button class="mItem" onclick={addLine}>{T('＋ 라인 추가', '+ line')}</button>{/if}
			{#if name in ctl.indParams}<button class="mItem" onclick={() => ctl.resetIndParams(name)}>{T('기본값', 'reset')}</button>{/if}
			{#if onRemove}<button class="mItem mClear" onclick={onRemove}>{T('지표 제거', 'remove')}</button>{/if}
		</div>
	</div>
{/if}
