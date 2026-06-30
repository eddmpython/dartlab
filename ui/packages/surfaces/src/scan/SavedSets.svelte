<script lang="ts">
	/**
	 * 헤더 드롭다운 · 내 컬럼셋 list + 저장 + 공유 URL 복사.
	 */
	import {
		listColumnSets,
		saveColumnSet,
		removeColumnSet,
		renameColumnSet
	} from './workspace';
	import type { SavedColumnSet, FilterCond, SortKey } from './types';

	interface Props {
		cols: string[];
		conds: FilterCond[];
		sorts: SortKey[];
		shareUrl: string;
		onLoad: (set: SavedColumnSet) => void;
	}

	let { cols, conds, sorts, shareUrl, onLoad }: Props = $props();

	let open = $state(false);
	let sets = $state<SavedColumnSet[]>([]);
	let saveName = $state('');
	let toast = $state<string | null>(null);

	function refresh() {
		sets = listColumnSets();
	}

	function toggle() {
		open = !open;
		if (open) refresh();
	}

	function close() {
		open = false;
		saveName = '';
	}

	function handleSave() {
		const name = saveName.trim();
		if (!name) return;
		saveColumnSet({
			name,
			cols: cols.slice(),
			conds: conds.slice(),
			sort: sorts.slice()
		});
		saveName = '';
		refresh();
		showToast('저장됨');
	}

	function handleLoad(s: SavedColumnSet) {
		onLoad(s);
		close();
	}

	function handleRemove(e: MouseEvent, id: string) {
		e.stopPropagation();
		removeColumnSet(id);
		refresh();
	}

	function handleRename(e: MouseEvent, s: SavedColumnSet) {
		e.stopPropagation();
		const next = window.prompt('새 이름', s.name);
		if (next && next.trim()) {
			renameColumnSet(s.id, next.trim());
			refresh();
		}
	}

	async function copyShareUrl() {
		try {
			await navigator.clipboard.writeText(shareUrl);
			showToast('URL 복사됨');
		} catch {
			showToast('복사 실패');
		}
	}

	function showToast(msg: string) {
		toast = msg;
		setTimeout(() => (toast = null), 1500);
	}

	function backdropClick(e: MouseEvent) {
		if (!(e.target as HTMLElement).closest('.savedsets-wrap')) close();
	}

	$effect(() => {
		if (open) {
			window.addEventListener('click', backdropClick);
			return () => window.removeEventListener('click', backdropClick);
		}
	});
</script>

<div class="savedsets-wrap">
	<button type="button" class="ss-btn" onclick={toggle} aria-haspopup="menu" aria-expanded={open}>
		<span>내 컬럼셋</span>
		<span class="caret">▾</span>
	</button>

	{#if open}
		<div class="ss-menu" role="menu">
			<div class="ss-section">
				<div class="ss-label">현재 상태 저장</div>
				<div class="ss-save">
					<input
						type="text"
						bind:value={saveName}
						placeholder="이름 (예: 우량주 하이ROE)"
						class="ss-input"
						onkeydown={(e) => e.key === 'Enter' && handleSave()}
					/>
					<button type="button" class="ss-save-btn" onclick={handleSave} disabled={!saveName.trim()}>
						저장
					</button>
				</div>
			</div>

			<div class="ss-divider"></div>

			<div class="ss-section">
				<div class="ss-label">URL 공유</div>
				<button type="button" class="ss-share" onclick={copyShareUrl}>
					🔗 현재 상태 URL 복사
				</button>
			</div>

			<div class="ss-divider"></div>

			<div class="ss-section">
				<div class="ss-label">저장된 컬럼셋 ({sets.length}/12)</div>
				{#if sets.length === 0}
					<div class="ss-empty">저장된 컬럼셋 없음</div>
				{:else}
					<ul class="ss-list">
						{#each sets as s (s.id)}
							<li class="ss-item">
								<button type="button" class="ss-load" onclick={() => handleLoad(s)}>
									<div class="ss-name">{s.name}</div>
									<div class="ss-meta">
										{s.cols.length} 컬럼 · {s.conds.length} 조건
									</div>
								</button>
								<button
									type="button"
									class="ss-icon"
									onclick={(e) => handleRename(e, s)}
									title="이름 변경"
									aria-label="이름 변경"
								>
									✎
								</button>
								<button
									type="button"
									class="ss-icon"
									onclick={(e) => handleRemove(e, s.id)}
									title="삭제"
									aria-label="삭제"
								>
									✕
								</button>
							</li>
						{/each}
					</ul>
				{/if}
			</div>

			{#if toast}
				<div class="ss-toast">{toast}</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.savedsets-wrap {
		position: relative;
	}
	.ss-btn {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		height: 32px;
		padding: 0 12px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 5px;
		color: #cbd5e1;
		font-size: 12px;
		cursor: pointer;
		line-height: 1;
		font-family: inherit;
	}
	.ss-btn:hover {
		border-color: #334155;
		color: #f1f5f9;
	}
	.caret {
		font-size: 9px;
		color: #64748b;
	}

	.ss-menu {
		position: absolute;
		right: 0;
		top: calc(100% + 6px);
		width: 280px;
		max-height: 480px;
		overflow-y: auto;
		background: #0f172a;
		border: 1px solid #334155;
		border-radius: 6px;
		box-shadow: 0 18px 32px -12px rgba(0, 0, 0, 0.7);
		z-index: 100;
		font-size: 11px;
	}
	.ss-section {
		padding: 10px 12px;
	}
	.ss-label {
		font-size: 10px;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 6px;
	}
	.ss-save {
		display: flex;
		gap: 4px;
	}
	.ss-input {
		flex: 1;
		padding: 5px 8px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 3px;
		color: #f1f5f9;
		font-family: inherit;
		font-size: 11px;
	}
	.ss-save-btn {
		padding: 5px 10px;
		background: rgba(var(--amber-rgb), 0.1);
		border: 1px solid rgba(var(--amber-rgb), 0.4);
		border-radius: 3px;
		color: var(--amber);
		font-size: 11px;
		font-weight: 500;
		cursor: pointer;
		font-family: inherit;
	}
	.ss-save-btn:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}
	.ss-share {
		width: 100%;
		padding: 6px 10px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 3px;
		color: #cbd5e1;
		font-size: 11px;
		cursor: pointer;
		text-align: left;
		font-family: inherit;
	}
	.ss-share:hover {
		border-color: #334155;
		color: var(--amber);
	}
	.ss-divider {
		height: 1px;
		background: #1e2433;
	}
	.ss-empty {
		font-size: 10px;
		color: #475569;
		padding: 8px 0;
	}
	.ss-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.ss-item {
		display: flex;
		align-items: stretch;
		gap: 2px;
		background: #050811;
		border-radius: 3px;
	}
	.ss-load {
		flex: 1;
		text-align: left;
		background: transparent;
		border: none;
		padding: 6px 8px;
		color: inherit;
		cursor: pointer;
		font-family: inherit;
	}
	.ss-load:hover {
		background: rgba(var(--amber-rgb), 0.06);
	}
	.ss-name {
		font-weight: 500;
		color: #f1f5f9;
		font-size: 11px;
	}
	.ss-meta {
		font-size: 9px;
		color: #64748b;
		font-family: monospace;
	}
	.ss-icon {
		background: transparent;
		border: none;
		color: #475569;
		cursor: pointer;
		padding: 0 6px;
		font-size: 11px;
	}
	.ss-icon:hover {
		color: var(--amber);
	}

	.ss-toast {
		position: absolute;
		bottom: -32px;
		right: 0;
		padding: 6px 12px;
		background: var(--amber);
		color: #0a0e18;
		border-radius: 4px;
		font-size: 11px;
		font-weight: 600;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	}
</style>
