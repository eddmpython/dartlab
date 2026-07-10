<script lang="ts">
	// dartlab 이야기 본문의 python 블록 위에 붙는 실행 막대.
	//
	// 코드 원본은 markdown 코드펜스 하나뿐이다. 이 컴포넌트는 그 위에 버튼만 얹고, 실행은
	// 노트북과 같은 pyodide 커널에서 한다. 한 페이지의 셀들이 커널 하나를 공유하므로 위 셀에서
	// 만든 `c` 를 아래 셀이 그대로 쓴다. 글 읽는 순서가 곧 실행 순서다.
	import { Play, Loader2, NotebookPen } from 'lucide-svelte';
	import { runSnippet, prewarmEngine } from '$lib/notebook/stores/executionStore';
	import type { CellOutput } from '$lib/notebook/engine/executionEngine';
	import OutputPanel from '$lib/notebook/components/OutputPanel.svelte';

	interface Props {
		code: string;
		/** 이 글을 노트북으로 가져간다. 첫 셀에만 붙인다. */
		onOpenNotebook?: () => void;
	}
	let { code, onOpenNotebook }: Props = $props();

	let output = $state<CellOutput | undefined>(undefined);
	let running = $state(false);

	async function run() {
		running = true;
		output = undefined;
		try {
			output = await runSnippet(code);
		} finally {
			running = false;
		}
	}
</script>

<div class="rc-bar">
	<button class="rc-btn rc-run" onclick={run} onpointerenter={prewarmEngine} disabled={running}>
		{#if running}<Loader2 size={13} class="rc-spin" /> 실행 중{:else}<Play size={13} /> 실행{/if}
	</button>
	{#if onOpenNotebook}
		<button class="rc-btn" onclick={onOpenNotebook} onpointerenter={prewarmEngine}>
			<NotebookPen size={13} /> 노트북 생성하기
		</button>
	{/if}
	{#if running && !output}
		<span class="rc-note">처음 실행은 파이썬과 dartlab 을 내려받느라 20 초쯤 걸립니다.</span>
	{/if}
</div>

{#if output}
	<div class="rc-out"><OutputPanel {output} /></div>
{/if}

<style>
	.rc-bar {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-wrap: wrap;
		margin: -6px 0 10px;
	}
	.rc-btn {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 5px 11px;
		border: 1px solid var(--dl-line-strong);
		border-radius: var(--dl-r-sm);
		background: var(--dl-bg-raised);
		color: var(--dl-ink-mute);
		font-family: var(--dl-font-ui);
		font-size: 12.5px;
		cursor: pointer;
		transition: all 0.12s ease;
	}
	.rc-btn:hover:not(:disabled) {
		border-color: var(--dl-accent);
		color: var(--dl-accent);
	}
	.rc-btn:disabled {
		opacity: 0.6;
		cursor: default;
	}
	.rc-run {
		color: var(--dl-accent);
		border-color: rgba(var(--dl-accent-rgb), 0.45);
	}
	.rc-note {
		font-size: 12px;
		color: var(--dl-ink-mute);
	}
	.rc-bar :global(.rc-spin) {
		animation: rc-spin 0.9s linear infinite;
	}
	@keyframes rc-spin {
		to {
			transform: rotate(360deg);
		}
	}
	.rc-out {
		margin: -4px 0 18px;
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-sm);
		background: var(--dl-bg-base);
		overflow-x: auto;
	}
</style>
