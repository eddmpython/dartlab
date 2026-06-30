<script lang="ts">
	// 전체화면 좌측 세로 그리기 툴바 (TradingView 좌측 툴바 멘탈모델) · 상시 노출 위젯.
	// 상태는 ChartCtl 공유, 도형 생성은 onDraw 콜백 (chartState "명령은 콜백" 규약).
	// 아이콘 = 모노크롬 인라인 SVG 단일 세트 (이모지 금지 · OS 컬러 렌더로 터미널 톤 파괴).
	import type { Lang } from '../lib/types';
	import { type ChartCtl, DRAW_TOOLS } from './chartState.svelte';

	interface Props {
		ctl: ChartCtl;
		lang: Lang;
		onDraw: (name: string) => void;
		onClearDraw: () => void;
	}
	let { ctl, lang, onDraw, onClearDraw }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);
	// 마지막 선택 도구 · 시각 피드백 (다음 클릭 도형). 영속 아님.
	let lastTool = $state<string | null>(null);

	const dot = (x: number, y: number) => `M${x - 1.1} ${y} a1.1 1.1 0 1 0 2.2 0 a1.1 1.1 0 1 0 -2.2 0`;
	const PATHS: Record<string, string[]> = {
		segment: ['M4 12 L12 4', dot(3.2, 12.8), dot(12.8, 3.2)],
		rayLine: ['M4.6 11.4 L14 2', dot(3.8, 12.2)],
		priceLine: ['M2 8 h12', dot(4.5, 8)],
		horizontalStraightLine: ['M2 8 h12'],
		verticalStraightLine: ['M8 2 v12'],
		fibonacciLine: ['M2 4.2 h12', 'M2 8 h7.5', 'M2 11.8 h12'],
		parallelStraightLine: ['M2 12 L11.5 3.5', 'M4.5 14 L14 5.5'],
		priceChannelLine: ['M2 11 L11 2.8', 'M5 13.2 L14 5', 'M6.2 9.4 L9.8 5.8'],
		anchoredVWAP: ['M8 2.4 a1.6 1.6 0 1 0 0.01 0', 'M8 5.6 V13.6', 'M3.6 10.4 a4.4 4.4 0 0 0 8.8 0', 'M5.9 7.4 h4.2'],
		positionTool: ['M3.5 3.2 h9 v4.4 h-9 z', 'M3.5 8.4 h9 v4.4 h-9 z'],
		MEASURE: ['M2.2 10.8 L10.8 2.2 L13.8 5.2 L5.2 13.8 Z', 'M5.4 7.6 l1.4 1.4', 'M7.6 5.4 l1.4 1.4', 'M9.8 3.2 l1.4 1.4'],
		TEXTNOTE: ['M3.5 3.2 h9', 'M8 3.2 v9.6', 'M6.2 12.8 h3.6'],
		MAGNET: ['M5.1 2.4 v4.9 a2.9 2.9 0 0 0 5.8 0 V2.4', 'M5.1 2.4 h2.3 v2.8', 'M10.9 2.4 h-2.3 v2.8'],
		STAY: ['M12.9 8 a4.9 4.9 0 1 1 -1.5 -3.5', 'M11.5 2.4 l0.4 2.3 -2.3 0.4'],
		TRASH: ['M3.4 4.6 h9.2', 'M6.3 4.6 V3.2 h3.4 v1.4', 'M4.7 4.6 l0.6 8.4 h5.4 l0.6 -8.4', 'M7 6.9 v3.9', 'M9 6.9 v3.9']
	};
</script>

{#snippet ic(name: string)}
	<svg viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
		{#each PATHS[name] ?? [] as d (d)}<path {d} />{/each}
	</svg>
{/snippet}

<div class="drawBar" role="toolbar" aria-label={T('그리기 도구', 'draw tools')}>
	{#each DRAW_TOOLS as d (d.name)}
		<button class={lastTool === d.name ? 'dbBtn on' : 'dbBtn'} title={T(d.kr, d.en)} onclick={() => { lastTool = d.name; onDraw(d.name); }}>{@render ic(d.name)}</button>
	{/each}
	<span class="dbDiv"></span>
	<button class={ctl.magnet ? 'dbBtn on' : 'dbBtn'} title={T('자석 스냅', 'magnet snap')} onclick={() => (ctl.magnet = !ctl.magnet)}>{@render ic('MAGNET')}</button>
	<button class={ctl.stayDraw ? 'dbBtn on' : 'dbBtn'} title={T('연속 그리기 · 완성 후 같은 도구 유지', 'stay in drawing mode')} onclick={() => (ctl.stayDraw = !ctl.stayDraw)}>{@render ic('STAY')}</button>
	<button class="dbBtn dbClear" disabled={!ctl.drawCount} title={T('그리기 전체 지우기', 'clear all drawings')} onclick={() => { lastTool = null; onClearDraw(); }}>{@render ic('TRASH')}{#if ctl.drawCount}<i class="dbCount">{ctl.drawCount}</i>{/if}</button>
</div>
