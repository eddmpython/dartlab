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
	const numValue = $derived(Number(value ?? start));

	function handleInput(e: Event) {
		const v = Number((e.target as HTMLInputElement).value);
		onChange(v);
	}
</script>

<div class="slider-widget" class:full-width={fullWidth}>
	{#if label}
		<label class="widget-label">{label}</label>
	{/if}
	<div class="slider-row">
		<input
			type="range"
			min={start}
			max={stop}
			step={step}
			value={numValue}
			oninput={handleInput}
			class="slider-input"
		/>
		<span class="slider-value">{numValue}</span>
	</div>
</div>

<style>
	.slider-widget {
		display: inline-flex;
		flex-direction: column;
		gap: 4px;
		min-width: 200px;
	}

	.slider-widget.full-width {
		width: 100%;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.slider-row {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.slider-input {
		flex: 1;
		height: 6px;
		-webkit-appearance: none;
		appearance: none;
		background: var(--nb-border);
		border-radius: 3px;
		outline: none;
		cursor: pointer;
	}

	.slider-input::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 16px;
		height: 16px;
		background: var(--nb-text);
		border-radius: 50%;
		cursor: pointer;
		transition: transform 0.1s ease;
	}

	.slider-input::-webkit-slider-thumb:hover {
		transform: scale(1.2);
	}

	.slider-input::-moz-range-thumb {
		width: 16px;
		height: 16px;
		background: var(--nb-text);
		border-radius: 50%;
		border: none;
		cursor: pointer;
	}

	.slider-value {
		font-family: var(--dl-font-mono);
		font-size: 13px;
		color: var(--nb-text);
		min-width: 40px;
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
</style>
