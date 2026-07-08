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
	const selected = $derived(Array.isArray(value) ? (value as string[]) : []);

	function toggleOption(opt: string) {
		const current = [...selected];
		const idx = current.indexOf(opt);
		if (idx >= 0) {
			current.splice(idx, 1);
		} else {
			current.push(opt);
		}
		onChange(current);
	}

	function isSelected(opt: string): boolean {
		return selected.includes(opt);
	}
</script>

<div class="multiselect-widget" class:full-width={fullWidth}>
	{#if label}
		<label class="widget-label">{label}</label>
	{/if}
	<div class="options-list">
		{#each options as opt}
			<button
				class="option-chip"
				class:selected={isSelected(opt)}
				onclick={() => toggleOption(opt)}
				type="button"
			>
				{opt}
			</button>
		{/each}
	</div>
	{#if selected.length > 0}
		<span class="selection-count">{selected.length} selected</span>
	{/if}
</div>

<style>
	.multiselect-widget {
		display: inline-flex;
		flex-direction: column;
		gap: 6px;
		min-width: 200px;
	}

	.multiselect-widget.full-width {
		width: 100%;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.options-list {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}

	.option-chip {
		padding: 4px 12px;
		border: 1px solid var(--nb-border);
		border-radius: 16px;
		background: var(--nb-card);
		color: var(--nb-text-secondary);
		font-size: 12px;
		cursor: pointer;
		transition: all 0.15s ease;
	}

	.option-chip:hover {
		border-color: var(--nb-pink);
		color: var(--nb-text);
	}

	.option-chip.selected {
		background: var(--nb-pink-subtle);
		border-color: var(--nb-pink);
		color: var(--nb-pink);
		font-weight: 500;
	}

	.selection-count {
		font-size: 11px;
		color: var(--nb-text-muted);
	}
</style>
