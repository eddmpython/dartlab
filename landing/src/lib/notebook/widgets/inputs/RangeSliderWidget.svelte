<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const start = $derived(Number(config.start ?? 0));
	const stop = $derived(Number(config.stop ?? 100));
	const step = $derived(Number(config.step ?? 1));
	const label = $derived((config.label as string) || '');
	const fullWidth = $derived(Boolean(config.full_width));

	const rangeValue = $derived(
		Array.isArray(value) && value.length === 2
			? [Number(value[0]), Number(value[1])]
			: [start, stop]
	);

	function handleMinInput(e: Event) {
		const v = Number((e.target as HTMLInputElement).value);
		const newMin = Math.min(v, rangeValue[1]);
		onChange([newMin, rangeValue[1]]);
	}

	function handleMaxInput(e: Event) {
		const v = Number((e.target as HTMLInputElement).value);
		const newMax = Math.max(v, rangeValue[0]);
		onChange([rangeValue[0], newMax]);
	}
</script>

<div class="range-slider-widget" class:full-width={fullWidth}>
	{#if label}
		<label class="widget-label">{label}</label>
	{/if}
	<div class="range-row">
		<input
			type="range"
			min={start}
			max={stop}
			step={step}
			value={rangeValue[0]}
			oninput={handleMinInput}
			class="range-input"
		/>
		<input
			type="range"
			min={start}
			max={stop}
			step={step}
			value={rangeValue[1]}
			oninput={handleMaxInput}
			class="range-input"
		/>
	</div>
	<div class="range-values">
		<span class="range-val">{rangeValue[0]}</span>
		<span class="range-sep">&ndash;</span>
		<span class="range-val">{rangeValue[1]}</span>
	</div>
</div>

<style>
	.range-slider-widget {
		display: inline-flex;
		flex-direction: column;
		gap: 4px;
		min-width: 200px;
	}

	.range-slider-widget.full-width {
		width: 100%;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.range-row {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.range-input {
		flex: 1;
		height: 6px;
		-webkit-appearance: none;
		appearance: none;
		background: var(--nb-border);
		border-radius: 3px;
		outline: none;
		cursor: pointer;
	}

	.range-input::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 14px;
		height: 14px;
		background: var(--nb-text);
		border-radius: 50%;
		cursor: pointer;
	}

	.range-input::-moz-range-thumb {
		width: 14px;
		height: 14px;
		background: var(--nb-text);
		border-radius: 50%;
		border: none;
		cursor: pointer;
	}

	.range-values {
		display: flex;
		align-items: center;
		gap: 6px;
		justify-content: center;
	}

	.range-val {
		font-family: 'Fira Code', 'Cascadia Code', monospace;
		font-size: 12px;
		color: var(--nb-text);
		font-variant-numeric: tabular-nums;
	}

	.range-sep {
		color: var(--nb-text-muted);
		font-size: 12px;
	}
</style>
