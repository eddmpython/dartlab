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

	interface DictItem {
		key: string;
		widget: WidgetDescriptor;
	}

	const items = $derived.by((): DictItem[] => {
		const raw = config.items as Record<string, WidgetDescriptor> | undefined;
		if (!raw) return [];
		return Object.entries(raw).map(([key, widget]) => ({ key, widget }));
	});

	const dictValue = $derived(
		(typeof value === 'object' && value !== null && !Array.isArray(value))
			? value as Record<string, unknown>
			: {}
	);

	function handleItemChange(key: string, widget: WidgetDescriptor, newValue: unknown) {
		widget.value = newValue;
		onWidgetValueChange(widget.id, newValue);
		const updated = { ...dictValue, [key]: newValue };
		onChange(updated);
	}
</script>

<div class="dictionary-widget">
	{#if label}
		<div class="widget-label">{label}</div>
	{/if}
	<div class="dict-entries">
		{#each items as { key, widget } (key)}
			<div class="dict-entry">
				<span class="dict-key">{key}</span>
				<div class="dict-value">
					<WidgetRenderer descriptor={{
						...widget,
						value: dictValue[key] ?? widget.value
					}} />
				</div>
			</div>
		{/each}
	</div>
</div>

<style>
	.dictionary-widget {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.dict-entries {
		display: flex;
		flex-direction: column;
		gap: 6px;
		padding: 8px;
		border: 1px solid var(--nb-border);
		border-radius: 8px;
		background: var(--nb-card);
	}

	.dict-entry {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.dict-key {
		font-family: 'Fira Code', 'Cascadia Code', monospace;
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-pink);
		min-width: 60px;
		flex-shrink: 0;
	}

	.dict-value {
		flex: 1;
		min-width: 0;
	}
</style>
