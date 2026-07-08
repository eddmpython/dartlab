<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const start = $derived(config.start != null ? Number(config.start) : undefined);
	const stop = $derived(config.stop != null ? Number(config.stop) : undefined);
	const step = $derived(Number(config.step ?? 1));
	const label = $derived((config.label as string) || '');
	const fullWidth = $derived(Boolean(config.full_width));

	function handleChange(e: Event) {
		const v = Number((e.target as HTMLInputElement).value);
		if (!isNaN(v)) onChange(v);
	}
</script>

<div class="number-widget" class:full-width={fullWidth}>
	{#if label}
		<label class="widget-label">{label}</label>
	{/if}
	<input
		type="number"
		class="number-input"
		value={Number(value ?? 0)}
		min={start}
		max={stop}
		step={step}
		onchange={handleChange}
	/>
</div>

<style>
	.number-widget {
		display: inline-flex;
		flex-direction: column;
		gap: 4px;
		min-width: 100px;
	}

	.number-widget.full-width {
		width: 100%;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.number-input {
		background: var(--nb-card);
		color: var(--nb-text);
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		padding: 6px 10px;
		font-size: 13px;
		font-family: var(--dl-font-mono);
		outline: none;
		width: 100px;
		transition: border-color 0.15s ease;
	}

	.number-input:focus {
		border-color: var(--nb-pink);
	}

	.number-input::-webkit-inner-spin-button,
	.number-input::-webkit-outer-spin-button {
		opacity: 1;
	}
</style>
