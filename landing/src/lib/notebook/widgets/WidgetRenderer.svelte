<script lang="ts">
	import type { WidgetDescriptor } from './WidgetBridge';
	import { onWidgetValueChange } from './WidgetBridge';
	import SliderWidget from './inputs/SliderWidget.svelte';
	import DropdownWidget from './inputs/DropdownWidget.svelte';
	import TextWidget from './inputs/TextWidget.svelte';
	import TextAreaWidget from './inputs/TextAreaWidget.svelte';
	import NumberWidget from './inputs/NumberWidget.svelte';
	import CheckboxWidget from './inputs/CheckboxWidget.svelte';
	import SwitchWidget from './inputs/SwitchWidget.svelte';
	import RadioWidget from './inputs/RadioWidget.svelte';
	import ButtonWidget from './inputs/ButtonWidget.svelte';
	import DateWidget from './inputs/DateWidget.svelte';
	import MultiselectWidget from './inputs/MultiselectWidget.svelte';
	import RangeSliderWidget from './inputs/RangeSliderWidget.svelte';
	import FileWidget from './inputs/FileWidget.svelte';
	import CodeEditorWidget from './inputs/CodeEditorWidget.svelte';
	import FormWidget from './composite/FormWidget.svelte';
	import DictionaryWidget from './composite/DictionaryWidget.svelte';
	import ArrayWidget from './composite/ArrayWidget.svelte';
	import BatchWidget from './composite/BatchWidget.svelte';
	import TableWidget from './data/TableWidget.svelte';

	interface Props {
		descriptor: WidgetDescriptor;
	}

	let { descriptor }: Props = $props();
	let localValue = $state<unknown>(undefined);
	let hasLocalOverride = $state(false);
	const currentValue = $derived(hasLocalOverride ? localValue : descriptor.value);

	$effect(() => {
		hasLocalOverride = false;
	});

	function handleChange(newValue: unknown) {
		localValue = newValue;
		hasLocalOverride = true;
		onWidgetValueChange(descriptor.id, newValue);
	}
</script>

<div class="widget-container" data-widget-type={descriptor.type}>
	{#if descriptor.type === 'slider'}
		<SliderWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'dropdown'}
		<DropdownWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'text'}
		<TextWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'text_area'}
		<TextAreaWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'number'}
		<NumberWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'checkbox'}
		<CheckboxWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'switch'}
		<SwitchWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'radio'}
		<RadioWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'button' || descriptor.type === 'run_button'}
		<ButtonWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'date'}
		<DateWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'multiselect'}
		<MultiselectWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'range_slider'}
		<RangeSliderWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'file'}
		<FileWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'code_editor'}
		<CodeEditorWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'table'}
		<TableWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'form'}
		<FormWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'dictionary'}
		<DictionaryWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'array'}
		<ArrayWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else if descriptor.type === 'batch'}
		<BatchWidget config={descriptor.config} value={currentValue} onChange={handleChange} />
	{:else}
		<div class="widget-unknown">Unknown widget: {descriptor.type}</div>
	{/if}
</div>

<style>
	.widget-container {
		display: inline-flex;
		align-items: center;
		vertical-align: middle;
	}

	.widget-unknown {
		color: var(--nb-text-muted);
		font-size: 12px;
		font-style: italic;
		padding: 4px 8px;
		border: 1px dashed var(--nb-border);
		border-radius: 4px;
	}
</style>
