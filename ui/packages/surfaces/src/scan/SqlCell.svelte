<script lang="ts">
	/**
	 * 단일 SQL 셀 · motherduck-style.
	 *
	 *   - CodeMirror 6 SQL editor (lang-sql + autocomplete + one-dark)
	 *   - ▶ Run 버튼 + ⌘Enter 단축키 (Shift+Enter = 실행 + 다음 셀)
	 *   - 결과 = TableView (정렬·검색·CSV)
	 *   - 셀 간 reference: 실행 시 `CREATE OR REPLACE TEMP VIEW cell_${id} AS ${sql}` 등록.
	 *     다음 셀이 `FROM cell_${id}` 참조 가능.
	 *   - 에러 marker (DuckDB LINE/COL 정보).
	 *
	 * READ-ONLY 안전장치는 Notebook 부모에서 처리.
	 */
	import { onMount } from 'svelte';
	import { Play, X, Pin, RotateCcw } from 'lucide-svelte';
	import TableView from './TableView.svelte';
	import { mountCodemirror } from './codemirror';
	import type { EditorView } from '@codemirror/view';
	import type { DartDb } from './duckSql';

	interface Props {
		id: string;
		code: string;
		db: DartDb | null;
		schemaTables?: Record<string, string[]>;
		onCodeChange: (id: string, code: string) => void;
		onDelete: (id: string) => void;
		onRunNext?: (id: string) => void;
	}

	let { id, code, db, schemaTables, onCodeChange, onDelete, onRunNext }: Props = $props();

	let editorEl: HTMLDivElement | undefined = $state(undefined);
	let view: EditorView | undefined = undefined;

	let result = $state<Array<Record<string, unknown>>>([]);
	let resultColumns = $state<string[]>([]);
	let error = $state<string | null>(null);
	let loading = $state(false);
	let elapsed = $state<number | null>(null);
	let cellViewRegistered = $state(false);

	const READONLY_RE = /^\s*(SELECT|WITH|SHOW|DESCRIBE|EXPLAIN|PRAGMA|CREATE\s+OR\s+REPLACE\s+TEMP\s+VIEW)\b/i;
	const DESTRUCTIVE_RE = /\b(DROP|DELETE|UPDATE|INSERT|ALTER|ATTACH|DETACH|COPY|TRUNCATE)\b/i;

	function isSafe(sql: string): { ok: boolean; reason?: string } {
		const trimmed = sql.trim();
		if (!trimmed) return { ok: false, reason: '빈 셀' };
		if (DESTRUCTIVE_RE.test(trimmed)) return { ok: false, reason: 'DROP/DELETE/UPDATE/INSERT/ALTER/ATTACH 차단' };
		if (!READONLY_RE.test(trimmed)) return { ok: false, reason: 'SELECT/WITH/SHOW/DESCRIBE/EXPLAIN/PRAGMA 로 시작' };
		return { ok: true };
	}

	async function runCell(mode: 'enter' | 'shift-enter' = 'enter') {
		if (!db) {
			error = 'db 가 아직 준비 안 됐습니다.';
			return;
		}
		const safe = isSafe(code);
		if (!safe.ok) {
			error = `⚠ ${safe.reason}`;
			result = [];
			resultColumns = [];
			return;
		}

		loading = true;
		error = null;
		const t0 = performance.now();

		try {
			// 1. user SQL 실행
			const rows = await Promise.race([
				db.query<Record<string, unknown>>(code),
				new Promise<never>((_, reject) =>
					setTimeout(() => reject(new Error('5초 timeout')), 5000)
				)
			]);
			result = rows.slice(0, 10000);
			resultColumns = result.length > 0 ? Object.keys(result[0]) : [];
			elapsed = performance.now() - t0;

			// 2. TEMP VIEW 등록 · 다른 셀이 cell_${id} 로 reference
			//    user SQL 자체가 SELECT 면 그대로 wrap, CREATE TEMP VIEW 면 skip.
			if (/^\s*SELECT|WITH/i.test(code)) {
				try {
					await db.query(`CREATE OR REPLACE TEMP VIEW cell_${id} AS ${code}`);
					cellViewRegistered = true;
				} catch {
					// VIEW 생성 실패 · 결과는 이미 받음. 다른 셀이 못 reference 만 함.
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
			result = [];
			resultColumns = [];
			elapsed = null;
		} finally {
			loading = false;
		}

		if (mode === 'shift-enter') onRunNext?.(id);
	}

	function clearResult() {
		result = [];
		resultColumns = [];
		error = null;
		elapsed = null;
	}

	onMount(() => {
		if (!editorEl) return;
		view = mountCodemirror({
			parent: editorEl,
			doc: code,
			onChange: (val) => onCodeChange(id, val),
			onRun: (mode) => void runCell(mode),
			schemaTables
		});
		return () => {
			view?.destroy();
		};
	});
</script>

<div class="cell sql-cell">
	<div class="cell-head">
		<button
			type="button"
			class="cell-run"
			onclick={() => runCell('enter')}
			disabled={loading || !db}
			title="⌘Enter / Ctrl+Enter / Shift+Enter (다음 셀)"
		>
			{#if loading}
				<span class="spinner"></span>
				<span>실행 중</span>
			{:else}
				<Play size={11} />
				<span>실행</span>
			{/if}
		</button>
		<span class="cell-id">cell_{id}</span>
		{#if cellViewRegistered}
			<span class="cell-badge" title="다음 셀에서 'FROM cell_{id}' 로 참조 가능">
				<Pin size={10} />
				<span>view</span>
			</span>
		{/if}
		<div class="cell-actions">
			{#if result.length > 0 || error}
				<button type="button" class="cell-icon-btn" onclick={clearResult} title="결과 지우기">
					<RotateCcw size={11} />
				</button>
			{/if}
			<button type="button" class="cell-icon-btn delete" onclick={() => onDelete(id)} title="셀 삭제">
				<X size={11} />
			</button>
		</div>
	</div>

	<div class="cell-editor" bind:this={editorEl}></div>

	{#if error}
		<div class="cell-error">⚠ {error}</div>
	{/if}

	{#if result.length > 0}
		<div class="cell-meta">
			{result.length.toLocaleString('ko-KR')} row · {resultColumns.length} cols
			{#if elapsed !== null}· {Math.round(elapsed)} ms{/if}
		</div>
		<div class="cell-result">
			<TableView
				title={`cell_${id}`}
				rows={result}
				csvFilename={`cell_${id}.csv`}
				emptyHint="결과 없음"
			/>
		</div>
	{/if}
</div>

<style>
	.cell {
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	.cell-head {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 6px 10px;
		background: #0a0e18;
		border-bottom: 1px solid #1e2433;
	}
	.cell-run {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 4px 12px;
		font-size: 11px;
		font-weight: 600;
		background: rgba(var(--amber-rgb), 0.1);
		border: 1px solid rgba(var(--amber-rgb), 0.4);
		border-radius: 4px;
		color: var(--amber);
		cursor: pointer;
		font-family: inherit;
	}
	.cell-run:hover:not(:disabled) {
		background: rgba(var(--amber-rgb), 0.18);
	}
	.cell-run:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.spinner {
		width: 10px;
		height: 10px;
		border: 1.5px solid currentColor;
		border-right-color: transparent;
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	.cell-id {
		font-family: monospace;
		font-size: 10px;
		color: #64748b;
	}
	.cell-badge {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-size: 9px;
		padding: 1px 5px;
		background: rgba(34, 197, 94, 0.1);
		border: 1px solid rgba(34, 197, 94, 0.3);
		border-radius: 3px;
		color: #22c55e;
		font-family: monospace;
	}
	.cell-icon-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
	.cell-actions {
		margin-left: auto;
		display: flex;
		gap: 4px;
	}
	.cell-icon-btn {
		background: transparent;
		border: none;
		color: #64748b;
		cursor: pointer;
		padding: 2px 6px;
		font-size: 11px;
		border-radius: 3px;
	}
	.cell-icon-btn:hover {
		color: #cbd5e1;
		background: rgba(255, 255, 255, 0.03);
	}
	.cell-icon-btn.delete:hover {
		color: #ef4444;
	}

	.cell-editor {
		min-height: 60px;
		max-height: 240px;
		overflow: auto;
	}
	.cell-editor :global(.cm-editor) {
		min-height: 60px;
	}
	.cell-editor :global(.cm-focused) {
		outline: none;
	}

	.cell-error {
		padding: 8px 12px;
		background: rgba(239, 68, 68, 0.08);
		color: #ef4444;
		font-size: 11px;
		font-family: 'JetBrains Mono', monospace;
		border-top: 1px solid rgba(239, 68, 68, 0.2);
	}
	.cell-meta {
		padding: 5px 12px;
		font-size: 10px;
		color: #64748b;
		font-family: monospace;
		background: #0a0e18;
		border-top: 1px solid #1e2433;
	}
	.cell-result {
		padding: 8px;
		min-height: 200px;
		max-height: 400px;
		display: flex;
	}
</style>
