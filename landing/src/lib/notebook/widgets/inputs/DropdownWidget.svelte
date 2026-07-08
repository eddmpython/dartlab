<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const options = $derived((config.options as string[]) || []);
	const label = $derived((config.label as string) || '');
	const fullWidth = $derived(Boolean(config.full_width));

	function handleChange(e: Event) {
		onChange((e.target as HTMLSelectElement).value);
	}
</script>

<div class="dropdown-widget" class:full-width={fullWidth}>
	{#if label}
		<label class="widget-label">{label}</label>
	{/if}
	<select class="dropdown-select" value={String(value ?? '')} onchange={handleChange}>
		{#each options as opt}
			<option value={opt} selected={String(value) === opt}>{opt}</option>
		{/each}
	</select>
</div>

<style>
	.dropdown-widget {
		display: inline-flex;
		flex-direction: column;
		gap: 4px;
		min-width: 140px;
	}

	.dropdown-widget.full-width {
		width: 100%;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.dropdown-select {
		background: var(--nb-card);
		color: var(--nb-text);
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		padding: 6px 10px;
		font-size: 13px;
		font-family: var(--dl-font-mono);
		outline: none;
		cursor: pointer;
		transition: border-color 0.15s ease;
	}

	.dropdown-select:focus {
		border-color: var(--nb-pink);
	}

	.dropdown-select:hover {
		border-color: var(--nb-text-muted);
	}
</style>
