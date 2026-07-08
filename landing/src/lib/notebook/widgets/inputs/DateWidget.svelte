<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const label = $derived((config.label as string) || '');
	const dateValue = $derived(String(value ?? ''));

	function handleChange(e: Event) {
		onChange((e.target as HTMLInputElement).value);
	}
</script>

<div class="date-widget">
	{#if label}
		<label class="widget-label">{label}</label>
	{/if}
	<input
		type="date"
		value={dateValue}
		onchange={handleChange}
		class="date-input"
	/>
</div>

<style>
	.date-widget {
		display: inline-flex;
		flex-direction: column;
		gap: 4px;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.date-input {
		padding: 6px 10px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-card);
		color: var(--nb-text);
		font-family: 'Fira Code', 'Cascadia Code', monospace;
		font-size: 13px;
		outline: none;
		transition: border-color 0.15s ease;
	}

	.date-input:focus {
		border-color: var(--nb-pink);
	}

	.date-input::-webkit-calendar-picker-indicator {
		filter: invert(0.5);
		cursor: pointer;
	}
</style>
