<script lang="ts">
	import { pyodideStore, initPyodide, runCell } from '$lib/stores/pyodide.svelte';
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

	// 시드 셀 - 현행 공개 계약 c.analysis. 오늘 브라우저 런타임에서 실데이터로 도는 finance 축.
	// 카탈로그 표 -> 실데이터 표 -> 전체 raw 페이로드 순.
	let cells = $state<Cell[]>([
		mkCell('c.analysis()'),
		mkCell(
			'import polars as pl\nhist = c.analysis("financial", "수익성")["marginTrend"]["history"]\npl.DataFrame(hist)'
		),
		mkCell('c.analysis("financial", "수익성")')
	]);

	let stockCode = $state('005930');
	let runningAll = $state(false);

	const stepLabels: Record<string, string> = {
		pyodide: 'Pyodide 엔진',
		packages: '패키지 로드',
		wheel: 'dartlab 설치',
		data: '데이터 다운로드',
		init: '초기화',
		done: '완료'
	};

	const anyRunning = $derived(cells.some((c) => c.running) || runningAll);

	async function runOne(cell: Cell) {
		if (cell.running) return;
		cell.running = true;
		try {
			await initPyodide(stockCode.trim() || '005930');
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
		<label class="flex items-center gap-2 text-sm text-dl-text-muted">
			종목
			<input
				type="text"
				bind:value={stockCode}
				disabled={anyRunning || pyodideStore.status === 'loading'}
				class="w-24 rounded border border-dl-border bg-dl-bg-dark px-2.5 py-1.5 font-mono text-sm text-dl-text outline-none focus:border-dl-primary disabled:opacity-50"
			/>
		</label>
		{#if pyodideStore.status === 'ready'}
			<span class="font-mono text-xs text-dl-text-dim">c = Company("{pyodideStore.currentStock}")</span>
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
	{#if pyodideStore.status === 'loading'}
		<div class="rounded-lg border border-dl-border bg-dl-bg-card p-4">
			<div class="mb-2 flex items-center gap-2 text-sm text-dl-primary">
				<span class="animate-spin">⟳</span>
				<span>{stepLabels[pyodideStore.step] || pyodideStore.step || '초기화'}</span>
				<span class="ml-auto text-dl-text-dim">{Math.round(pyodideStore.progress * 100)}%</span>
			</div>
			<div class="h-1 overflow-hidden rounded bg-dl-bg-dark">
				<div
					class="h-full bg-dl-primary transition-all"
					style:width="{pyodideStore.progress * 100}%"
				></div>
			</div>
			<p class="mt-2 text-xs text-dl-text-dim">
				첫 실행은 Pyodide 부팅 + dartlab 설치 + 데이터 다운로드로 8~12초 걸립니다. 이후 셀은 즉시 실행됩니다.
			</p>
		</div>
	{/if}

	{#if pyodideStore.status === 'error'}
		<div class="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-400">
			<div class="mb-1 font-medium">커널 초기화 실패</div>
			<div class="whitespace-pre-wrap text-xs">{pyodideStore.errorMsg}</div>
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
