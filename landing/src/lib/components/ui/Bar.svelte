<script lang="ts">
	/** 수평 막대 · 비율 비교용 (peer · 백분위 등) */
	interface Props {
		value: number; // 0~1 또는 절대값
		max?: number; // 절대값 기준일 때 max
		tone?: 'brand' | 'good' | 'warn' | 'bad' | 'up' | 'down' | 'neutral';
		height?: number;
		marker?: number; // 비교 기준선 (예: 업종 평균)
	}

	let {
		value,
		max = 1,
		tone = 'brand',
		height = 6,
		marker
	}: Props = $props();

	const ratio = $derived(Math.max(0, Math.min(1, value / max)));
	const markerRatio = $derived(marker == null ? null : Math.max(0, Math.min(1, marker / max)));

	const fillColor: Record<string, string> = {
		brand: 'var(--dl-grad-heat)',
		good: 'var(--dl-good)',
		warn: 'var(--dl-warn)',
		bad: 'var(--dl-bad)',
		up: 'var(--dl-up)',
		down: 'var(--dl-down)',
		neutral: 'var(--dl-ink-mute)'
	};
</script>

<div class="bar" style="height: {height}px">
	<div class="bar-track"></div>
	<div class="bar-fill" style="width: {ratio * 100}%; background: {fillColor[tone]}"></div>
	{#if markerRatio != null}
		<div class="bar-marker" style="left: {markerRatio * 100}%"></div>
	{/if}
</div>

<style>
	.bar {
		position: relative;
		width: 100%;
		border-radius: 999px;
		overflow: hidden;
		background: rgba(255, 255, 255, 0.05);
	}
	.bar-track {
		position: absolute;
		inset: 0;
		background: rgba(255, 255, 255, 0.04);
	}
	.bar-fill {
		position: absolute;
		left: 0;
		top: 0;
		bottom: 0;
		border-radius: 999px;
		transition: width var(--dl-dur-state) var(--dl-ease);
	}
	.bar-marker {
		position: absolute;
		top: -2px;
		bottom: -2px;
		width: 2px;
		background: var(--dl-ink);
		opacity: 0.7;
		border-radius: 1px;
	}
</style>
