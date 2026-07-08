<script lang="ts">
	import CellOutput from './CellOutput.svelte';
	import type { NotebookCell } from '$lib/notebook/types';

	let {
		cell,
		index,
		canDelete,
		onrun,
		ondelete
	}: {
		cell: NotebookCell;
		index: number;
		canDelete: boolean;
		onrun: () => void;
		ondelete: () => void;
	} = $props();

	let editor = $state<HTMLTextAreaElement | null>(null);

	function autoGrow() {
		if (!editor) return;
		editor.style.height = 'auto';
		editor.style.height = `${Math.max(editor.scrollHeight, 40)}px`;
	}

	function onKeydown(e: KeyboardEvent) {
		if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
			e.preventDefault();
			onrun();
			return;
		}
		if (e.key === 'Tab') {
			e.preventDefault();
			const el = e.currentTarget as HTMLTextAreaElement;
			const start = el.selectionStart;
			const end = el.selectionEnd;
			cell.code = cell.code.slice(0, start) + '    ' + cell.code.slice(end);
			queueMicrotask(() => {
				el.selectionStart = el.selectionEnd = start + 4;
			});
		}
	}

	$effect(() => {
		// cell.code 변경 시 높이 재계산
		void cell.code;
		autoGrow();
	});
</script>

<div class="rounded-lg border border-dl-border bg-dl-bg-card">
	<div class="flex items-stretch gap-2 p-2">
		<div class="flex w-8 shrink-0 flex-col items-center gap-1 pt-1.5">
			<button
				onclick={onrun}
				disabled={cell.running}
				title="실행 (Ctrl+Enter)"
				class="flex h-7 w-7 items-center justify-center rounded text-dl-text-muted transition-colors hover:bg-dl-bg-dark hover:text-dl-primary disabled:cursor-wait disabled:opacity-50"
			>
				{#if cell.running}
					<span class="animate-spin text-sm">⟳</span>
				{:else}
					<span class="text-sm">▶</span>
				{/if}
			</button>
			<span class="font-mono text-[10px] text-dl-text-dim">[{cell.ran ? index + 1 : ' '}]</span>
		</div>

		<textarea
			bind:this={editor}
			bind:value={cell.code}
			oninput={autoGrow}
			onkeydown={onKeydown}
			spellcheck="false"
			rows="1"
			placeholder="python 코드. Ctrl+Enter 로 실행."
			class="flex-1 resize-none bg-transparent px-2 py-1.5 font-mono text-sm leading-relaxed text-dl-text outline-none placeholder:text-dl-text-dim"
		></textarea>

		{#if canDelete}
			<button
				onclick={ondelete}
				title="셀 삭제"
				class="h-7 w-7 shrink-0 rounded text-dl-text-dim transition-colors hover:bg-dl-bg-dark hover:text-red-400"
			>
				×
			</button>
		{/if}
	</div>

	{#if cell.ran || cell.running}
		<div class="border-t border-dl-border px-3 py-2.5">
			{#if cell.running && !cell.ran}
				<div class="text-xs text-dl-text-dim">실행 중...</div>
			{:else}
				<CellOutput stdout={cell.stdout} output={cell.output} />
			{/if}
		</div>
	{/if}
</div>
