<script lang="ts">
	import DOMPurify from 'dompurify';
	import DataFrameTable from './DataFrameTable.svelte';
	import type { NbOutput } from '$lib/notebook/types';

	let { stdout, output }: { stdout: string; output: NbOutput | null } = $props();

	const cleanHtml = (raw: string) => DOMPurify.sanitize(raw);
</script>

{#if stdout}
	<pre
		class="mb-2 overflow-x-auto whitespace-pre-wrap rounded bg-dl-bg-dark px-3 py-2 font-mono text-xs leading-relaxed text-dl-text-muted">{stdout}</pre>
{/if}

{#if output}
	{#if output.type === 'dataframe'}
		<DataFrameTable
			columns={output.columns}
			dtypes={output.dtypes}
			rows={output.rows}
			nrows={output.nrows}
			ncols={output.ncols}
			truncated={output.truncated}
		/>
	{:else if output.type === 'html'}
		<!-- eslint-disable-next-line svelte/no-at-html-tags -->
		<div class="nb-html overflow-x-auto text-sm text-dl-text-muted">{@html cleanHtml(output.data)}</div>
	{:else if output.type === 'repr'}
		<pre
			class="overflow-x-auto whitespace-pre-wrap rounded bg-dl-bg-dark px-3 py-2 font-mono text-xs leading-relaxed text-dl-text">{output.data}</pre>
	{:else if output.type === 'error'}
		<pre
			class="overflow-x-auto whitespace-pre-wrap rounded border border-red-500/40 bg-red-500/10 px-3 py-2 font-mono text-xs leading-relaxed text-red-400">{output.data}</pre>
	{/if}
{/if}
