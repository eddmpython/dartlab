<script lang="ts">
	import { pctTone } from '@dartlab/ui-format/pct';

	/** 숫자 표시 · tabular-nums + 톤별 색 */
	interface Props {
		value: number | string | null | undefined;
		size?: 'sm' | 'md' | 'lg' | 'xl';
		tone?: 'auto' | 'up' | 'down' | 'flat' | 'good' | 'warn' | 'bad' | 'info' | 'ink';
		prefix?: string; // "₩", "+", "-"
		suffix?: string; // "%", "x", "조 원"
		align?: 'left' | 'right' | 'center';
	}

	let {
		value,
		size = 'md',
		tone = 'ink',
		prefix = '',
		suffix = '',
		align = 'right'
	}: Props = $props();

	const display = $derived(value == null || value === '' ? '·' : String(value));

	// auto tone: value 가 숫자면 부호로 결정
	const computedTone = $derived.by(() => {
		if (tone !== 'auto') return tone;
		const n = typeof value === 'number' ? value : parseFloat(String(value));
		return pctTone(n);
	});
</script>

<span
	class="num size-{size} tone-{computedTone}"
	style="text-align: {align};"
>
	{#if prefix}<span class="aff">{prefix}</span>{/if}{display}{#if suffix}<span class="aff">{suffix}</span>{/if}
</span>

<style>
	.num {
		display: inline-block;
		font-family: var(--dl-font-mono);
		font-feature-settings: 'tnum' 1;
		font-variant-numeric: tabular-nums;
		font-weight: 600;
		letter-spacing: -0.01em;
		line-height: 1.1;
	}
	.size-sm { font-size: 12px; }
	.size-md { font-size: 14px; }
	.size-lg { font-size: 20px; font-weight: 700; letter-spacing: -0.02em; }
	.size-xl { font-size: 36px; font-weight: 700; letter-spacing: -0.025em; }

	.tone-ink { color: var(--dl-ink-print); }
	.tone-up { color: var(--dl-up); }
	.tone-down { color: var(--dl-down); }
	.tone-flat { color: var(--dl-ink-mute); }
	.tone-good { color: var(--dl-good); }
	.tone-warn { color: var(--dl-warn); }
	.tone-bad { color: var(--dl-bad); }
	.tone-info { color: var(--dl-info); }
	.tone-unknown { color: var(--dl-ink-faint); }

	.aff {
		font-size: 0.7em;
		font-weight: 500;
		opacity: 0.7;
		margin: 0 1px;
	}
</style>
