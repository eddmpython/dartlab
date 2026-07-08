<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const label = $derived((config.label as string) || 'Click');
	const kind = $derived((config.kind as string) || 'primary');
	const isRunButton = $derived(config.label === undefined && kind === 'primary');

	function handleClick() {
		const current = Number(value) || 0;
		onChange(current + 1);
	}
</script>

<button class="btn-widget btn-{kind}" onclick={handleClick} type="button">
	{label}
</button>

<style>
	.btn-widget {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 6px 16px;
		border-radius: 6px;
		font-size: 13px;
		font-weight: 500;
		border: 1px solid var(--nb-border);
		cursor: pointer;
		transition: all 0.15s ease;
		font-family: inherit;
	}

	.btn-primary {
		background: var(--nb-pink);
		color: white;
		border-color: var(--nb-pink);
	}

	.btn-primary:hover {
		opacity: 0.9;
	}

	.btn-secondary {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.btn-secondary:hover {
		background: var(--nb-border);
	}

	.btn-danger {
		background: var(--nb-error);
		color: white;
		border-color: var(--nb-error);
	}

	.btn-danger:hover {
		opacity: 0.9;
	}
</style>
