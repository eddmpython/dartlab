<script lang="ts">
	// dartlab 이야기 본문의 python 블록 위에 붙는 실행 막대.
	//
	// 코드 원본은 markdown 코드펜스 하나뿐이다. 이 컴포넌트는 그 위에 버튼만 얹고, 실행은
	// 노트북과 같은 pyodide 커널에서 한다. 한 페이지의 셀들이 커널 하나를 공유하므로 위 셀에서
	// 만든 `c` 를 아래 셀이 그대로 쓴다. 글 읽는 순서가 곧 실행 순서다.
	import { Play, Loader2, NotebookPen } from 'lucide-svelte';
	import { onMount } from 'svelte';
	import { runSnippet, prewarmEngine, prewarmData, takePrewarmedOutput, engineStatus } from '$lib/notebook/stores/executionStore';
	import type { CellOutput } from '$lib/notebook/engine/executionEngine';
	import OutputPanel from '$lib/notebook/components/OutputPanel.svelte';

	interface Props {
		code: string;
		/** 이 셀보다 위에 있는 본문 코드들. 커널이 아직 안 돌린 것만 먼저 흘린다. */
		prereq?: string[];
		/** 이 글을 노트북으로 가져간다. 첫 셀에만 붙인다(첫 셀 판별에도 쓴다). */
		onOpenNotebook?: () => void;
	}
	let { code, prereq = [], onOpenNotebook }: Props = $props();

	let output = $state<CellOutput | undefined>(undefined);
	let running = $state(false);

	// 클릭이 느린 두 원인을 진입 즉시 백그라운드로 없앤다.
	//   (1) 설치: pyodide + dartlab(21MB + polars) 12~20초. prewarmEngine 이 미리 끝낸다(멱등).
	//   (2) 데이터: 첫 셀이 여는 회사의 panel parquet(~12.8MB) fetch. 설치만 데워도 첫 클릭은 이 fetch
	//       때문에 여전히 느리다(실측 16초). 그래서 첫 셀은 설치가 끝난 뒤 자기 코드를 조용히 한 번
	//       실행해 데이터까지 커널 FS 에 올려 둔다. 그러면 사용자의 첫 클릭은 fetch 없이 실행만 한다.
	// dartlab 이야기는 독자 의도가 코드 실행이라 이 선제 다운로드가 정당하다(카테고리 한정).
	onMount(() => {
		const w = window as unknown as { requestIdleCallback?: (cb: (d?: unknown) => void) => void };
		const kick = async () => {
			await prewarmEngine();
			if (onOpenNotebook) await prewarmData(code); // 첫 셀만. 자기 데이터를 선제 캐시.
		};
		if (w.requestIdleCallback) w.requestIdleCallback(() => void kick());
		else setTimeout(() => void kick(), 1200);
	});

	/** 파이썬과 dartlab 을 내려받는 중일 때만 오래 걸린다고 말한다. 따뜻한 커널에는 거짓말이다. */
	let downloading = $derived(running && $engineStatus === 'loading');

	async function run() {
		// 프리페치가 읽는 동안 이 셀 결과를 미리 냈으면 fetch 도 계산도 없이 즉시 보여준다(체감 0초).
		const pre = takePrewarmedOutput(code);
		if (pre) {
			output = pre;
			return;
		}
		running = true;
		output = undefined;
		try {
			output = await runSnippet(code, prereq);
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
	{#if downloading}
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
