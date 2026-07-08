<script lang="ts">
	import { kernelStore, initKernel, runCell } from '$lib/notebook/kernel.svelte';
	import NotebookCell from './NotebookCell.svelte';
	import type { NotebookCell as Cell } from '$lib/notebook/types';

	let _cid = 0;
	const mkCell = (code = ''): Cell => ({
		id: `c${_cid++}`,
		code,
		running: false,
		stdout: '',
		output: null,
		ran: false
	});

	// 범용 시드 셀. 일반 파이썬, pandas 표, matplotlib 그래프.
	let cells = $state<Cell[]>([
		mkCell('print("Hello, notebook")\n21 * 2'),
		mkCell('import pandas as pd\npd.DataFrame({"n": [1, 2, 3, 4], "square": [1, 4, 9, 16]})'),
		mkCell(
			'import numpy as np\nimport matplotlib.pyplot as plt\n\nx = np.linspace(0, 2 * np.pi, 200)\nplt.plot(x, np.sin(x))\nplt.title("sin(x)")'
		)
	]);

	let runningAll = $state(false);
	const anyRunning = $derived(cells.some((c) => c.running) || runningAll);

	async function runOne(cell: Cell) {
		if (cell.running) return;
		cell.running = true;
		try {
			await initKernel();
			const res = await runCell(cell.code);
			cell.stdout = res.stdout;
			cell.output = res.output;
			cell.ran = true;
		} catch (e) {
			cell.stdout = '';
			cell.output = { type: 'error', data: e instanceof Error ? e.message : String(e) };
			cell.ran = true;
		} finally {
			cell.running = false;
		}
	}

	async function runAll() {
		if (runningAll) return;
		runningAll = true;
		try {
			for (const cell of cells) {
				await runOne(cell);
			}
		} finally {
			runningAll = false;
		}
	}

	function addCell() {
		cells = [...cells, mkCell('')];
	}

	function deleteCell(id: string) {
		cells = cells.filter((c) => c.id !== id);
	}
</script>

<div class="space-y-3">
	<!-- 툴바 -->
	<div
		class="flex flex-wrap items-center gap-3 rounded-lg border border-dl-border bg-dl-bg-card px-4 py-3"
	>
		{#if kernelStore.status === 'ready'}
			<span class="font-mono text-xs text-dl-text-dim">Python 커널 준비됨</span>
		{:else}
			<span class="text-sm text-dl-text-muted">브라우저 Python 커널</span>
		{/if}
		<div class="ml-auto flex items-center gap-2">
			<button
				onclick={runAll}
				disabled={anyRunning}
				class="rounded bg-dl-primary px-3.5 py-1.5 text-sm font-medium text-white transition-colors hover:bg-dl-primary-dark disabled:cursor-wait disabled:opacity-50"
			>
				{#if runningAll}실행 중...{:else}모두 실행{/if}
			</button>
			<button
				onclick={addCell}
				disabled={anyRunning}
				class="rounded border border-dl-border bg-dl-bg-dark px-3.5 py-1.5 text-sm text-dl-text-muted transition-colors hover:border-dl-primary hover:text-dl-primary disabled:opacity-50"
			>
				+ 셀
			</button>
		</div>
	</div>

	<!-- 부팅 진행 -->
	{#if kernelStore.status === 'loading'}
		<div class="rounded-lg border border-dl-border bg-dl-bg-card p-4">
			<div class="flex items-center gap-2 text-sm text-dl-primary">
				<span class="animate-spin">⟳</span>
				<span>{kernelStore.step || '초기화'}</span>
			</div>
			<p class="mt-2 text-xs text-dl-text-dim">
				첫 실행은 Pyodide 부팅으로 몇 초 걸립니다. 이후 셀은 즉시 실행됩니다.
			</p>
		</div>
	{/if}

	{#if kernelStore.status === 'error'}
		<div class="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-400">
			<div class="mb-1 font-medium">커널 초기화 실패</div>
			<div class="whitespace-pre-wrap text-xs">{kernelStore.errorMsg}</div>
		</div>
	{/if}

	<!-- 셀 -->
	{#each cells as cell, i (cell.id)}
		<NotebookCell
			{cell}
			index={i}
			canDelete={cells.length > 1}
			onrun={() => runOne(cell)}
			ondelete={() => deleteCell(cell.id)}
		/>
	{/each}
</div>
