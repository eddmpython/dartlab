<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const label = $derived((config.label as string) || '');
	let checked = $derived(Boolean(value));

	function toggle() {
		onChange(!checked);
	}
</script>

<label class="switch-widget">
	<button class="switch-track" class:on={checked} onclick={toggle} type="button" role="switch" aria-checked={checked} aria-label={label || 'Toggle'}>
		<span class="switch-thumb" class:on={checked}></span>
	</button>
	{#if label}
		<span class="switch-label">{label}</span>
	{/if}
</label>

<style>
	.switch-widget {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		cursor: pointer;
	}

	.switch-track {
		position: relative;
		width: 36px;
		height: 20px;
		background: var(--nb-border);
		border-radius: 10px;
		border: none;
		cursor: pointer;
		transition: background 0.2s ease;
		padding: 0;
	}

	.switch-track.on {
		background: var(--nb-pink);
	}

	.switch-thumb {
		position: absolute;
		top: 2px;
		left: 2px;
		width: 16px;
		height: 16px;
		background: white;
		border-radius: 50%;
		transition: transform 0.2s ease;
	}

	.switch-thumb.on {
		transform: translateX(16px);
	}

	.switch-label {
		font-size: 13px;
		color: var(--nb-text);
	}
</style>
