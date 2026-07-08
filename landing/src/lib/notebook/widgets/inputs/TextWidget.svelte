<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const label = $derived((config.label as string) || '');
	const placeholder = $derived((config.placeholder as string) || '');
	const fullWidth = $derived(Boolean(config.full_width));
	let debounceTimer: ReturnType<typeof setTimeout> | null = null;

	function handleInput(e: Event) {
		const v = (e.target as HTMLInputElement).value;
		if (debounceTimer) clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => onChange(v), 300);
	}
</script>

<div class="text-widget" class:full-width={fullWidth}>
	{#if label}
		<label class="widget-label">{label}</label>
	{/if}
	<input
		type="text"
		class="text-input"
		value={String(value ?? '')}
		placeholder={placeholder}
		oninput={handleInput}
	/>
</div>

<style>
	.text-widget {
		display: inline-flex;
		flex-direction: column;
		gap: 4px;
		min-width: 180px;
	}

	.text-widget.full-width {
		width: 100%;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.text-input {
		background: var(--nb-card);
		color: var(--nb-text);
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		padding: 6px 10px;
		font-size: 13px;
		font-family: 'Fira Code', 'Cascadia Code', monospace;
		outline: none;
		transition: border-color 0.15s ease;
	}

	.text-input:focus {
		border-color: var(--nb-pink);
	}
</style>
