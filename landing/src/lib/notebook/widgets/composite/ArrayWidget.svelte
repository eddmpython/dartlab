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

	const label = $derived((config.label as string) || '');
	const widgetItems = $derived((config.items as WidgetDescriptor[]) || []);

	const arrayValue = $derived(
		Array.isArray(value) ? (value as unknown[]) : widgetItems.map((w) => w.value)
	);

	function handleItemChange(idx: number, widget: WidgetDescriptor, newValue: unknown) {
		widget.value = newValue;
		onWidgetValueChange(widget.id, newValue);
		const updated = [...arrayValue];
		updated[idx] = newValue;
		onChange(updated);
	}
</script>

<div class="array-widget">
	{#if label}
		<div class="widget-label">{label}</div>
	{/if}
	<div class="array-items">
		{#each widgetItems as widget, idx (widget.id)}
			<div class="array-item">
				<span class="array-index">{idx}</span>
				<div class="array-value">
					<WidgetRenderer descriptor={{
						...widget,
						value: arrayValue[idx] ?? widget.value
					}} />
				</div>
			</div>
		{/each}
	</div>
</div>

<style>
	.array-widget {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.array-items {
		display: flex;
		flex-direction: column;
		gap: 6px;
		padding: 8px;
		border: 1px solid var(--nb-border);
		border-radius: 8px;
		background: var(--nb-card);
	}

	.array-item {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.array-index {
		font-family: 'Fira Code', 'Cascadia Code', monospace;
		font-size: 11px;
		color: var(--nb-text-muted);
		min-width: 20px;
		text-align: right;
		flex-shrink: 0;
	}

	.array-value {
		flex: 1;
		min-width: 0;
	}
</style>
