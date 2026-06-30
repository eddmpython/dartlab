<script lang="ts">
	/**
	 * 컬럼 헤더 hover 툴팁 · 메트릭 정의 + 단위 + 좋은 방향.
	 *
	 * Tooltip.svelte 가 "i" 버튼 + 툴팁 패턴인데, 컬럼 헤더는
	 * 헤더 셀 전체가 hover trigger 가 되어야 자연스러움. 그래서
	 * 별도 인라인 popover 로 구현.
	 */
	import type { MetricDef } from './types';

	interface Props {
		/** METRICS catalog 의 정의 · raw 테이블 컬럼처럼 catalog 에 없으면 undefined */
		metric?: MetricDef;
		/** metric 없을 때 사용할 컬럼명 fallback */
		fallbackKey?: string;
	}

	let { metric, fallbackKey }: Props = $props();

	let label = $derived(metric?.label ?? fallbackKey ?? '');
	let unit = $derived(metric?.unit);
	let definition = $derived(metric?.definition);
	let higherBetter = $derived(metric?.higherBetter);

	let open = $state(false);
	let dwellTimer: ReturnType<typeof setTimeout> | null = null;

	function show() {
		if (dwellTimer) clearTimeout(dwellTimer);
		dwellTimer = setTimeout(() => (open = true), 300);
	}
	function hide() {
		if (dwellTimer) clearTimeout(dwellTimer);
		open = false;
	}

	let directionLabel = $derived(
		higherBetter === true
			? '높을수록 좋음'
			: higherBetter === false
				? '낮을수록 좋음'
				: ''
	);
	let directionTone = $derived(
		higherBetter === true ? 'good' : higherBetter === false ? 'bad' : 'neutral'
	);
</script>

<span
	class="hdr"
	role="button"
	tabindex="0"
	aria-label={label}
	onmouseenter={show}
	onmouseleave={hide}
	onfocus={show}
	onblur={hide}
>
	<span class="hdr-label">{label}</span>
	{#if unit}
		<span class="hdr-unit">({unit})</span>
	{/if}
	{#if open && definition}
		<span class="bubble" role="tooltip">
			<span class="b-title">
				{label}
				{#if unit}<span class="b-unit">· {unit}</span>{/if}
			</span>
			<span class="b-def">{definition}</span>
			{#if directionLabel}
				<span class="b-dir tone-{directionTone}">{directionLabel}</span>
			{/if}
		</span>
	{/if}
</span>

<style>
	.hdr {
		display: inline-flex;
		align-items: baseline;
		gap: 4px;
		cursor: help;
		position: relative;
		font-weight: 600;
		font-size: 11px;
		color: #cbd5e1;
		letter-spacing: -0.01em;
		white-space: pre;
		line-height: 1.15;
	}
	.hdr-label {
		color: #f1f5f9;
	}
	.hdr-unit {
		color: #64748b;
		font-size: 10px;
		font-weight: 400;
	}
	.hdr:hover .hdr-label,
	.hdr:focus .hdr-label {
		color: var(--amber);
	}

	.bubble {
		position: absolute;
		top: calc(100% + 6px);
		left: 0;
		min-width: 220px;
		max-width: 320px;
		padding: 10px 12px;
		background: #0f172a;
		border: 1px solid #334155;
		border-radius: 6px;
		box-shadow: 0 12px 28px -10px rgba(0, 0, 0, 0.7);
		font-weight: 400;
		display: flex;
		flex-direction: column;
		gap: 6px;
		z-index: 100;
		animation: fadein 120ms ease-out;
		text-align: left;
		white-space: normal;
		text-transform: none;
		letter-spacing: 0;
	}
	.b-title {
		font-size: 12px;
		font-weight: 600;
		color: #f1f5f9;
	}
	.b-unit {
		font-weight: 400;
		color: #94a3b8;
	}
	.b-def {
		font-size: 11px;
		color: #cbd5e1;
		line-height: 1.5;
	}
	.b-dir {
		font-size: 10px;
		font-weight: 600;
		padding: 2px 6px;
		border-radius: 3px;
		align-self: flex-start;
	}
	.tone-good {
		background: rgba(34, 197, 94, 0.15);
		color: #22c55e;
	}
	.tone-bad {
		background: rgba(239, 68, 68, 0.15);
		color: #ef4444;
	}
	.tone-neutral {
		background: rgba(148, 163, 184, 0.15);
		color: #94a3b8;
	}

	@keyframes fadein {
		from {
			opacity: 0;
			transform: translateY(-4px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
