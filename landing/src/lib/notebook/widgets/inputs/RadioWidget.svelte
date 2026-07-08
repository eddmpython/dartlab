<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const options = $derived((config.options as string[]) || []);
	const label = $derived((config.label as string) || '');
	const groupName = $derived(`radio-${Math.random().toString(36).slice(2, 8)}`);

	function handleChange(opt: string) {
		onChange(opt);
	}
</script>

<div class="radio-widget">
	{#if label}
		<div class="widget-label">{label}</div>
	{/if}
	<div class="radio-group">
		{#each options as opt}
			<label class="radio-option">
				<input
					type="radio"
					name={groupName}
					value={opt}
					checked={String(value) === opt}
					onchange={() => handleChange(opt)}
				/>
				<span class="radio-text">{opt}</span>
			</label>
		{/each}
	</div>
</div>

<style>
	.radio-widget {
		display: inline-flex;
		flex-direction: column;
		gap: 6px;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.radio-group {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.radio-option {
		display: flex;
		align-items: center;
		gap: 8px;
		cursor: pointer;
	}

	.radio-option input {
		accent-color: var(--nb-pink);
		cursor: pointer;
	}

	.radio-text {
		font-size: 13px;
		color: var(--nb-text);
	}
</style>
