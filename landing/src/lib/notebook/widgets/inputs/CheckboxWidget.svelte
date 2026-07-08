<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const label = $derived((config.label as string) || '');

	function handleChange(e: Event) {
		onChange((e.target as HTMLInputElement).checked);
	}
</script>

<label class="checkbox-widget">
	<input
		type="checkbox"
		class="checkbox-input"
		checked={Boolean(value)}
		onchange={handleChange}
	/>
	{#if label}
		<span class="checkbox-label">{label}</span>
	{/if}
</label>

<style>
	.checkbox-widget {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		cursor: pointer;
		user-select: none;
	}

	.checkbox-input {
		width: 16px;
		height: 16px;
		accent-color: var(--nb-pink);
		cursor: pointer;
	}

	.checkbox-label {
		font-size: 13px;
		color: var(--nb-text);
	}
</style>
