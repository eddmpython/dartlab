<script lang="ts">
	import type { CellOutput } from '../stores/notebookStore';
	import DataFrameTable from './DataFrameTable.svelte';
	import WidgetRenderer from '../widgets/WidgetRenderer.svelte';
	import type { WidgetDescriptor } from '../widgets/WidgetBridge';
	import { extractWidgetsFromHtml } from '../widgets/WidgetBridge';

	interface Props {
		output?: CellOutput;
		expectedOutput?: string;
		multiDefVars?: string[];
	}

	let { output, expectedOutput, multiDefVars = [] }: Props = $props();

	const isCorrect = $derived(
		expectedOutput && output ? output.data.trim() === expectedOutput.trim() : null
	);

	const imgStdout = $derived.by(() => {
		if (!output || output.type !== 'image') return '';
		const sep = '__STDOUT_END__\n';
		const idx = output.data.indexOf(sep);
		return idx !== -1 ? output.data.slice(0, idx) : '';
	});

	const imgSrc = $derived.by(() => {
		if (!output || output.type !== 'image') return '';
		const sep = '__STDOUT_END__\n';
		const idx = output.data.indexOf(sep);
		return idx !== -1 ? output.data.slice(idx + sep.length) : output.data;
	});

	const dfParsed = $derived.by(() => {
		if (!output || output.type !== 'dataframe') return null;
		try {
			let jsonStr = output.data;
			let stdout = '';
			const sep = '__STDOUT_END__\n';
			const sepIdx = output.data.indexOf(sep);
			if (sepIdx !== -1) {
				stdout = output.data.slice(0, sepIdx);
				jsonStr = output.data.slice(sepIdx + sep.length);
			}
			return { data: JSON.parse(jsonStr), stdout };
		} catch {
			return null;
		}
	});

	const widgetParsed = $derived.by(() => {
		if (!output || output.type !== 'widget') return null;
		try {
			let jsonStr = output.data;
			let stdout = '';
			const sep = '__STDOUT_END__\n';
			const sepIdx = output.data.indexOf(sep);
			if (sepIdx !== -1) {
				stdout = output.data.slice(0, sepIdx);
				jsonStr = output.data.slice(sepIdx + sep.length);
			}
			const parsed = JSON.parse(jsonStr);
			if (parsed.type === 'html_composite' && parsed.html) {
				const { cleanHtml, widgetDescriptors } = extractWidgetsFromHtml(parsed.html);
				return { mode: 'html_composite' as const, html: cleanHtml, widgets: widgetDescriptors, stdout };
			}
			return { mode: 'single' as const, descriptor: parsed as WidgetDescriptor, stdout };
		} catch {
			return null;
		}
	});
</script>

{#if multiDefVars.length > 0 || (output && (output.data || output.type === 'error'))}
	<div class="output-panel" class:error={output?.type === 'error'}>
		{#if multiDefVars.length > 0}
			<div class="multidef-banner">
				<span class="multidef-icon">⚠</span>
				<span>Multiple definitions: <strong>{multiDefVars.join(', ')}</strong> — 같은 변수를 여러 셀에서 정의할 수 없습니다.</span>
			</div>
		{/if}
		{#if output && output.type === 'widget' && widgetParsed}
			{#if widgetParsed.stdout}
				<pre class="output-content">{widgetParsed.stdout}</pre>
			{/if}
			{#if widgetParsed.mode === 'single'}
				<div class="widget-output">
					<WidgetRenderer descriptor={widgetParsed.descriptor} />
				</div>
			{:else if widgetParsed.mode === 'html_composite'}
				<div class="widget-html-output">
					{@html widgetParsed.html}
					{#each [...widgetParsed.widgets.values()] as wd (wd.id)}
						<WidgetRenderer descriptor={wd} />
					{/each}
				</div>
			{/if}
		{:else if output && output.type === 'dataframe' && dfParsed}
			<DataFrameTable data={dfParsed.data} stdout={dfParsed.stdout || undefined} />
		{:else if output && output.type === 'image'}
			{#if imgStdout}
				<pre class="output-content">{imgStdout}</pre>
			{/if}
			<img class="output-image" src={imgSrc} alt="Chart output" />
		{:else if output && output.type === 'html'}
			<div class="output-html">{@html output.data}</div>
		{:else if output}
			<pre class="output-content">{output.data}</pre>
		{/if}
		{#if isCorrect === true}
			<span class="validation correct">Correct</span>
		{:else if isCorrect === false}
			<span class="validation incorrect">Try again</span>
		{/if}
	</div>
{/if}

<style>
	.output-panel {
		border-top: 1px solid var(--nb-border);
		padding: 10px 14px;
		position: relative;
	}

	.output-panel.error {
		background: rgba(239, 68, 68, 0.04);
	}

	.multidef-banner {
		display: flex;
		align-items: flex-start;
		gap: 7px;
		padding: 7px 10px;
		margin-bottom: 8px;
		background: rgba(234, 179, 8, 0.07);
		border: 1px solid rgba(234, 179, 8, 0.3);
		border-radius: 6px;
		font-size: 12px;
		color: var(--nb-text-secondary);
		line-height: 1.5;
	}

	.multidef-icon {
		flex-shrink: 0;
		font-size: 13px;
		margin-top: 1px;
	}

	.output-content {
		margin: 0;
		font-family: 'Fira Code', 'Cascadia Code', monospace;
		font-size: 13px;
		line-height: 1.5;
		color: var(--nb-text);
		white-space: pre-wrap;
		word-break: break-word;
		overflow-x: auto;
	}

	.error .output-content {
		color: var(--nb-error);
	}

	.output-image {
		max-width: 100%;
		height: auto;
		border-radius: 4px;
		display: block;
	}

	.output-html {
		overflow-x: auto;
	}

	.widget-output {
		padding: 4px 0;
	}

	.widget-html-output {
		overflow-x: auto;
	}

	.widget-html-output :global(.chani-widget-slot) {
		display: inline-block;
		vertical-align: middle;
	}

	.validation {
		position: absolute;
		top: 8px;
		right: 12px;
		font-size: 11px;
		font-weight: 600;
		padding: 2px 8px;
		border-radius: 10px;
	}

	.validation.correct {
		background: rgba(34, 197, 94, 0.1);
		color: var(--nb-success);
	}

	.validation.incorrect {
		background: rgba(239, 68, 68, 0.1);
		color: var(--nb-error);
	}
</style>
