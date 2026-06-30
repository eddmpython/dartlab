<script lang="ts">
	/**
	 * SQL Notebook 컨테이너 · motherduck-style.
	 *
	 *   - 셀 list (SQL 또는 Markdown)
	 *   - 셀 add / delete / reorder
	 *   - Run all / Run above (위에서부터 순차)
	 *   - 셀 간 `cell_${id}` TEMP VIEW reference (각 SQL 셀에서 자체 등록)
	 *   - autocomplete schema = 8 prebuild 테이블 + cell_* (지난 셀 view)
	 *
	 * 저장·공유 (notebookStore.ts · notebookUrl.ts) 는 PR-ι 에서.
	 */
	import { onMount } from 'svelte';
	import { Notebook, Plus, Save, Share2, FolderOpen, FileText, Code, Pencil, Trash2 } from 'lucide-svelte';
	import SqlCell from './SqlCell.svelte';
	import MarkdownCell from './MarkdownCell.svelte';
	import {
		listNotebooks,
		saveNotebook,
		deleteNotebook,
		renameNotebook,
		type SavedNotebook,
		type NotebookCell
	} from './notebookStore';
	import { decodeNotebook, buildShareUrl } from './notebookUrl';
	import type { DartDb } from './duckSql';

	type Cell = NotebookCell;

	interface Props {
		db: DartDb | null;
		ecosystem: Array<Record<string, unknown>>;
	}

	let { db, ecosystem }: Props = $props();

	const STARTER: Cell[] = [
		{
			id: 'a1',
			type: 'md',
			code:
				'# SQL Notebook\n셀 단위 SQL · `▶ 실행` 또는 `⌘Enter`. `Shift+Enter` = 실행 + 다음 셀.\n\n각 SQL 셀이 `cell_${id}` 라는 TEMP VIEW 로 등록 → 다른 셀이 `FROM cell_a2` 로 참조 가능.\n\n사용 가능 테이블: `ecosystem`, `prices`, `valuation`, `changes`, `finance_lite`, `dividend`, `treasuryStock`, `executive`'
		},
		{
			id: 'a2',
			type: 'sql',
			code: `SELECT label, industryName, roe, opMargin, debtRatio
FROM ecosystem
WHERE roe IS NOT NULL
ORDER BY roe DESC
LIMIT 20`
		},
		{
			id: 'a3',
			type: 'sql',
			code: `SELECT industryName, COUNT(*) AS 회사수, AVG(roe) AS avg_roe
FROM cell_a2
GROUP BY industryName
ORDER BY avg_roe DESC`
		}
	];

	let cells = $state<Cell[]>([...STARTER]);
	let registeredTables = $state(false);
	let schemaTables = $state<Record<string, string[]>>({});
	let currentNbId = $state<string | null>(null);
	let currentNbName = $state<string>('새 노트북');
	let saved = $state<SavedNotebook[]>([]);
	let menuOpen = $state(false);
	let toast = $state<string | null>(null);

	function refreshSaved() {
		saved = listNotebooks();
	}

	function showToast(msg: string) {
		toast = msg;
		setTimeout(() => (toast = null), 1500);
	}

	function handleSave() {
		const name = window.prompt('노트북 이름', currentNbName);
		if (!name || !name.trim()) return;
		const nb = saveNotebook({
			id: currentNbId ?? undefined,
			name: name.trim(),
			cells: cells.slice()
		});
		currentNbId = nb.id;
		currentNbName = nb.name;
		refreshSaved();
		showToast('저장됨');
	}

	function handleLoad(nb: SavedNotebook) {
		cells = nb.cells.map((c) => ({ ...c }));
		currentNbId = nb.id;
		currentNbName = nb.name;
		menuOpen = false;
		showToast(`로드: ${nb.name}`);
	}

	function handleDelete(nb: SavedNotebook) {
		if (!window.confirm(`"${nb.name}" 삭제?`)) return;
		deleteNotebook(nb.id);
		if (currentNbId === nb.id) {
			currentNbId = null;
			currentNbName = '새 노트북';
		}
		refreshSaved();
	}

	function handleRename(nb: SavedNotebook) {
		const next = window.prompt('새 이름', nb.name);
		if (!next || !next.trim()) return;
		renameNotebook(nb.id, next.trim());
		if (currentNbId === nb.id) currentNbName = next.trim();
		refreshSaved();
	}

	function handleNew() {
		cells = [...STARTER];
		currentNbId = null;
		currentNbName = '새 노트북';
		menuOpen = false;
	}

	async function handleShare() {
		const url = buildShareUrl(cells, currentNbName);
		try {
			await navigator.clipboard.writeText(url);
			showToast('URL 복사됨');
		} catch {
			showToast('복사 실패');
		}
	}

	onMount(() => {
		refreshSaved();
		// URL ?nb= 진입 시 자동 로드
		if (typeof window !== 'undefined') {
			const url = new URL(window.location.href);
			const nbParam = url.searchParams.get('nb');
			if (nbParam) {
				const decoded = decodeNotebook(nbParam);
				if (decoded && decoded.cells.length > 0) {
					cells = decoded.cells;
					currentNbName = decoded.name ?? '공유 노트북';
				}
			}
		}
	});

	function genId(): string {
		// 짧은 timestamp + random
		return Date.now().toString(36).slice(-4) + Math.random().toString(36).slice(2, 5);
	}

	function addSqlCell(after?: string) {
		const newCell: Cell = { id: genId(), type: 'sql', code: '' };
		if (after) {
			const idx = cells.findIndex((c) => c.id === after);
			cells = [...cells.slice(0, idx + 1), newCell, ...cells.slice(idx + 1)];
		} else {
			cells = [...cells, newCell];
		}
	}

	function addMdCell(after?: string) {
		const newCell: Cell = { id: genId(), type: 'md', code: '' };
		if (after) {
			const idx = cells.findIndex((c) => c.id === after);
			cells = [...cells.slice(0, idx + 1), newCell, ...cells.slice(idx + 1)];
		} else {
			cells = [...cells, newCell];
		}
	}

	function deleteCell(id: string) {
		cells = cells.filter((c) => c.id !== id);
		// TEMP VIEW 정리
		if (db) {
			void db.query(`DROP VIEW IF EXISTS cell_${id}`).catch(() => {});
		}
	}

	function updateCode(id: string, code: string) {
		cells = cells.map((c) => (c.id === id ? { ...c, code } : c));
	}

	function runNext(id: string) {
		const idx = cells.findIndex((c) => c.id === id);
		const next = cells[idx + 1];
		if (next && next.type === 'sql') {
			// SqlCell 의 runCell 직접 trigger 어렵 · focus 만 넘김. 사용자가 ⌘Enter.
			// 단순화: 다음 셀이 SQL 이면 그 셀의 editor focus.
			const el = document.querySelector(`[data-cell-id="${next.id}"] .cm-editor`) as HTMLElement | null;
			el?.focus();
		} else if (!next) {
			addSqlCell(id);
		}
	}

	// ── parquet 등록 + autocomplete schema fed ──
	async function registerAllTables() {
		if (registeredTables || !db) return;
		try {
			// in-memory ecosystem
			await db.registerJson('ecosystem', ecosystem);
			// HF parquet views
			const lazy: Array<[string, string]> = [
				['prices', 'gov/prices/date/' + new Date().getFullYear() + '.parquet'],
				['valuation', 'dart/scan/valuation.parquet'],
				['changes', 'dart/scan/changes.parquet'],
				['finance_lite', 'dart/scan/finance-lite.parquet'],
				['dividend', 'dart/scan/report/dividend.parquet'],
				['treasuryStock', 'dart/scan/report/treasuryStock.parquet'],
				['executive', 'dart/scan/report/executive.parquet']
			];
			for (const [view, path] of lazy) {
				try {
					await db.registerHfParquet(view, path);
				} catch (err) {
					console.info(`[scan/notebook] ${view} skip`, err);
				}
			}
			// schema fed for autocomplete
			const cols = await db.query<{ table_name: string; column_name: string }>(`
				SELECT table_name, column_name
				FROM information_schema.columns
				WHERE table_schema = 'main'
			`);
			const m: Record<string, string[]> = {};
			for (const r of cols) {
				const t = String(r.table_name);
				if (!m[t]) m[t] = [];
				m[t].push(String(r.column_name));
			}
			schemaTables = m;
			registeredTables = true;
		} catch (err) {
			console.warn('[scan/notebook] registerAllTables 실패', err);
		}
	}

	$effect(() => {
		if (db && !registeredTables) void registerAllTables();
	});

	function moveCell(id: string, dir: 'up' | 'down') {
		const idx = cells.findIndex((c) => c.id === id);
		if (idx < 0) return;
		const target = dir === 'up' ? idx - 1 : idx + 1;
		if (target < 0 || target >= cells.length) return;
		const next = cells.slice();
		[next[idx], next[target]] = [next[target], next[idx]];
		cells = next;
	}
</script>

<div class="notebook">
	<header class="nb-head">
		<span class="nb-title">
			<Notebook size={14} />
			<span>{currentNbName}</span>
		</span>
		<span class="nb-sub">{cells.length} 셀 · {Object.keys(schemaTables).length} 테이블</span>
		<div class="nb-actions">
			<button type="button" class="nb-btn" onclick={() => addSqlCell()}>
				<Plus size={12} /><Code size={12} />
				<span>SQL</span>
			</button>
			<button type="button" class="nb-btn" onclick={() => addMdCell()}>
				<Plus size={12} /><FileText size={12} />
				<span>MD</span>
			</button>
			<button type="button" class="nb-btn" onclick={handleSave} title="LocalStorage 저장">
				<Save size={12} />
				<span>저장</span>
			</button>
			<button type="button" class="nb-btn" onclick={handleShare} title="?nb= URL 복사">
				<Share2 size={12} />
				<span>공유</span>
			</button>
			<div class="nb-menu-wrap">
				<button
					type="button"
					class="nb-btn"
					onclick={() => {
						menuOpen = !menuOpen;
						if (menuOpen) refreshSaved();
					}}
					aria-haspopup="menu"
				>
					<FolderOpen size={12} />
					<span>내 노트북 ({saved.length})</span>
				</button>
				{#if menuOpen}
					<div class="nb-menu" role="menu">
						<button type="button" class="nb-menu-new" onclick={handleNew}>
							<Plus size={12} /> 새 노트북
						</button>
						{#if saved.length === 0}
							<div class="nb-menu-empty">저장된 노트북 없음</div>
						{:else}
							<div class="nb-menu-divider"></div>
							{#each saved as nb (nb.id)}
								<div class="nb-menu-row" class:active={currentNbId === nb.id}>
									<button type="button" class="nb-menu-load" onclick={() => handleLoad(nb)}>
										<span class="nb-menu-name">{nb.name}</span>
										<span class="nb-menu-meta">{nb.cells.length} 셀</span>
									</button>
									<button type="button" class="nb-menu-icon" onclick={() => handleRename(nb)} title="이름 변경">
										<Pencil size={11} />
									</button>
									<button type="button" class="nb-menu-icon" onclick={() => handleDelete(nb)} title="삭제">
										<Trash2 size={11} />
									</button>
								</div>
							{/each}
						{/if}
					</div>
				{/if}
			</div>
		</div>
	</header>

	{#if toast}
		<div class="nb-toast">{toast}</div>
	{/if}

	<div class="nb-body">
		{#each cells as cell, i (cell.id)}
			<div class="cell-wrap" data-cell-id={cell.id}>
				<div class="cell-controls">
					<button type="button" class="cc-btn" onclick={() => moveCell(cell.id, 'up')} disabled={i === 0} title="위로">▲</button>
					<button type="button" class="cc-btn" onclick={() => moveCell(cell.id, 'down')} disabled={i === cells.length - 1} title="아래로">▼</button>
				</div>
				<div class="cell-body">
					{#if cell.type === 'sql'}
						<SqlCell
							id={cell.id}
							code={cell.code}
							{db}
							{schemaTables}
							onCodeChange={updateCode}
							onDelete={deleteCell}
							onRunNext={runNext}
						/>
					{:else}
						<MarkdownCell
							id={cell.id}
							code={cell.code}
							onCodeChange={updateCode}
							onDelete={deleteCell}
						/>
					{/if}
				</div>
				<div class="cell-after">
					<button type="button" class="add-here" onclick={() => addSqlCell(cell.id)} title="아래에 SQL 셀">+ SQL</button>
					<button type="button" class="add-here" onclick={() => addMdCell(cell.id)} title="아래에 Markdown 셀">+ MD</button>
				</div>
			</div>
		{/each}

		{#if cells.length === 0}
			<div class="empty">
				<button type="button" class="empty-btn" onclick={() => addSqlCell()}>+ 첫 SQL 셀</button>
			</div>
		{/if}
	</div>
</div>

<style>
	.notebook {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: 0;
		background: #0a0e18;
		border-radius: 6px;
		overflow: hidden;
	}
	.nb-head {
		display: flex;
		align-items: baseline;
		gap: 12px;
		padding: 10px 14px;
		background: #0f172a;
		border-bottom: 1px solid #1e2433;
		flex-shrink: 0;
	}
	.nb-title {
		font-size: 13px;
		font-weight: 700;
		color: #f1f5f9;
	}
	.nb-sub {
		font-size: 10px;
		color: #64748b;
		font-family: monospace;
		flex: 1;
	}
	.nb-actions {
		display: flex;
		gap: 6px;
	}
	.nb-btn {
		padding: 5px 10px;
		font-size: 11px;
		background: rgba(var(--amber-rgb), 0.08);
		border: 1px solid rgba(var(--amber-rgb), 0.3);
		border-radius: 3px;
		color: var(--amber);
		cursor: pointer;
		font-family: inherit;
	}
	.nb-btn:hover {
		background: rgba(var(--amber-rgb), 0.16);
	}

	.nb-menu-wrap {
		position: relative;
	}
	.nb-menu {
		position: absolute;
		top: calc(100% + 4px);
		right: 0;
		min-width: 280px;
		max-height: 400px;
		overflow-y: auto;
		background: #0f172a;
		border: 1px solid #334155;
		border-radius: 5px;
		box-shadow: 0 18px 32px -12px rgba(0, 0, 0, 0.7);
		z-index: 50;
		padding: 6px;
		display: flex;
		flex-direction: column;
		gap: 1px;
	}
	.nb-menu-new {
		padding: 6px 10px;
		font-size: 11px;
		background: rgba(var(--amber-rgb), 0.08);
		border: 1px solid rgba(var(--amber-rgb), 0.3);
		border-radius: 3px;
		color: var(--amber);
		cursor: pointer;
		font-family: inherit;
		text-align: left;
	}
	.nb-menu-new:hover {
		background: rgba(var(--amber-rgb), 0.16);
	}
	.nb-menu-empty {
		padding: 12px 10px;
		font-size: 10px;
		color: #475569;
		text-align: center;
	}
	.nb-menu-divider {
		height: 1px;
		background: #1e2433;
		margin: 4px 0;
	}
	.nb-menu-row {
		display: flex;
		align-items: stretch;
		gap: 1px;
		background: #050811;
		border-radius: 3px;
	}
	.nb-menu-row.active {
		background: rgba(var(--amber-rgb), 0.06);
	}
	.nb-menu-load {
		flex: 1;
		text-align: left;
		padding: 6px 10px;
		background: transparent;
		border: none;
		color: inherit;
		cursor: pointer;
		font-family: inherit;
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 8px;
	}
	.nb-menu-load:hover {
		background: rgba(255, 255, 255, 0.03);
	}
	.nb-menu-name {
		font-size: 11px;
		color: #f1f5f9;
		font-weight: 500;
	}
	.nb-menu-meta {
		font-size: 9px;
		color: #64748b;
		font-family: monospace;
	}
	.nb-menu-icon {
		background: transparent;
		border: none;
		color: #475569;
		cursor: pointer;
		padding: 0 8px;
		font-size: 11px;
	}
	.nb-menu-icon:hover {
		color: var(--amber);
	}

	.nb-toast {
		position: absolute;
		top: 50px;
		right: 14px;
		padding: 6px 12px;
		background: var(--amber);
		color: #0a0e18;
		border-radius: 4px;
		font-size: 11px;
		font-weight: 600;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
		z-index: 100;
	}

	.nb-body {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		padding: 12px;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.cell-wrap {
		display: grid;
		grid-template-columns: 32px 1fr;
		gap: 6px;
	}
	.cell-controls {
		display: flex;
		flex-direction: column;
		gap: 2px;
		padding-top: 8px;
	}
	.cc-btn {
		background: transparent;
		border: none;
		color: #475569;
		cursor: pointer;
		padding: 2px;
		font-size: 9px;
	}
	.cc-btn:hover:not(:disabled) {
		color: var(--amber);
	}
	.cc-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	.cell-body {
		min-width: 0;
	}
	.cell-after {
		grid-column: 2;
		display: flex;
		gap: 4px;
		padding: 4px 0;
		justify-content: center;
		opacity: 0;
		transition: opacity 0.15s;
	}
	.cell-wrap:hover .cell-after {
		opacity: 1;
	}
	.add-here {
		font-size: 10px;
		padding: 3px 10px;
		background: transparent;
		border: 1px dashed #1e2433;
		border-radius: 3px;
		color: #64748b;
		cursor: pointer;
		font-family: inherit;
	}
	.add-here:hover {
		border-color: var(--amber);
		color: var(--amber);
		border-style: solid;
	}

	.empty {
		display: flex;
		justify-content: center;
		padding: 40px;
	}
	.empty-btn {
		padding: 12px 24px;
		background: rgba(var(--amber-rgb), 0.1);
		border: 1px solid rgba(var(--amber-rgb), 0.4);
		border-radius: 6px;
		color: var(--amber);
		cursor: pointer;
		font-family: inherit;
		font-size: 13px;
		font-weight: 600;
	}
	.empty-btn:hover {
		background: rgba(var(--amber-rgb), 0.18);
	}
</style>
