<script lang="ts">
	import WidgetRenderer from '../WidgetRenderer.svelte';
	import type { WidgetDescriptor } from '../WidgetBridge';
	import { onWidgetValueChange } from '../WidgetBridge';

	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const label = $derived((config.label as string) || 'Submit');
	const bordered = $derived(config.bordered !== false);
	const innerWidget = $derived(config.inner as WidgetDescriptor | null);
	let submitted = $state(false);

	function handleSubmit() {
		if (!innerWidget) return;
		submitted = true;
		onChange(innerWidget.value);
		setTimeout(() => { submitted = false; }, 1500);
	}

	function handleInnerChange(newValue: unknown) {
		if (!innerWidget) return;
		innerWidget.value = newValue;
		onWidgetValueChange(innerWidget.id, newValue);
	}
</script>

<div class="form-widget" class:bordered>
	{#if innerWidget}
		<div class="form-inner">
			<WidgetRenderer descriptor={{
				...innerWidget,
				value: innerWidget.value
			}} />
		</div>
	{/if}
	<button
		class="form-submit-btn"
		class:submitted
		onclick={handleSubmit}
		type="button"
	>
		{submitted ? 'Submitted' : label}
	</button>
</div>

<style>
	.form-widget {
		display: inline-flex;
		flex-direction: column;
		gap: 8px;
	}

	.form-widget.bordered {
		padding: 12px;
		border: 1px solid var(--nb-border);
		border-radius: 8px;
		background: var(--nb-card);
	}

	.form-inner {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.form-submit-btn {
		align-self: flex-start;
		padding: 6px 16px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-pink);
		color: #fff;
		font-size: 12px;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.15s ease;
	}

	.form-submit-btn:hover {
		opacity: 0.85;
	}

	.form-submit-btn.submitted {
		background: var(--nb-success, #22c55e);
		border-color: var(--nb-success, #22c55e);
	}
</style>
