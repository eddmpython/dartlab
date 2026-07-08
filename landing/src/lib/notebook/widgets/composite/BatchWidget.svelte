<script lang="ts">
	import WidgetRenderer from '../WidgetRenderer.svelte';
	import type { WidgetDescriptor } from '../WidgetBridge';
	import { onWidgetValueChange } from '../WidgetBridge';
	import { extractWidgetsFromHtml } from '../WidgetBridge';

	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const rawHtml = $derived((config.html as string) || '');
	const widgetMap = $derived((config.widgets as Record<string, WidgetDescriptor>) || {});

	const batchValue = $derived(
		(typeof value === 'object' && value !== null && !Array.isArray(value))
			? value as Record<string, unknown>
			: {}
	);

	const parsed = $derived.by(() => {
		if (!rawHtml) return { cleanHtml: '', widgetDescriptors: new Map<string, WidgetDescriptor>() };
		return extractWidgetsFromHtml(rawHtml);
	});

	const allWidgets = $derived.by(() => {
		const result = new Map<string, WidgetDescriptor>();
		for (const [id, wd] of parsed.widgetDescriptors) {
			result.set(id, wd);
		}
		for (const [key, wd] of Object.entries(widgetMap)) {
			if (!result.has(wd.id)) {
				result.set(wd.id, wd);
			}
		}
		return result;
	});
</script>

<div class="batch-widget">
	{#if parsed.cleanHtml}
		<div class="batch-html">
			{@html parsed.cleanHtml}
		</div>
	{/if}
	{#if allWidgets.size > 0}
		<div class="batch-widgets">
			{#each [...allWidgets.values()] as wd (wd.id)}
				<WidgetRenderer descriptor={{
					...wd,
					value: batchValue[wd.id] ?? wd.value
				}} />
			{/each}
		</div>
	{/if}
</div>

<style>
	.batch-widget {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.batch-html {
		font-size: 13px;
		line-height: 1.5;
		color: var(--nb-text);
	}

	.batch-html :global(.chani-widget-slot) {
		display: inline-block;
		vertical-align: middle;
	}

	.batch-widgets {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		align-items: center;
	}
</style>
