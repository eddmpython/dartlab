<script lang="ts">
	import { FolderPlus, FilePlus, ChevronRight, ChevronDown, FileCode, FolderOpen, Folder, Trash2, RefreshCw, Upload, Copy, BookOpen, Pencil, Plus, Database, Loader2 } from 'lucide-svelte';
	import { onMount, tick } from 'svelte';
	import { listFiles, readFile, writeFile, mkdirFS, removeFileFS, renamePathFS, engineStatus, executionDoneCounter, loadNotebookFromFile, saveWorkspaceSnapshot, notebookFilePath, notebookPathVersion, destroyEngine } from '../../stores/executionStore';
	import type { FileEntry } from '../../engine/executionEngine';
	import { notebook, updateCellContent, activeCellId, loadNotebook, resetNotebook, setTitle, saveToServer } from '../../stores/notebookStore';

	let expandedDirs = $state<Set<string>>(new Set(['/workspace']));
	let treeData = $state<Map<string, FileEntry[]>>(new Map());
	let selectedFile = $state<string | null>(null);
	let fileContent = $state<string | null>(null);
	let engineReady = $state(false);
	let newItemParent = $state<string | null>(null);
	let newItemType = $state<'file' | 'dir' | null>(null);
	let newName = $state('');
	let renamingPath = $state<string | null>(null);
	let renameValue = $state('');

	interface WorkspaceEntry { id: string; title: string; cellCount: number; updatedAt: string; }
	let wsOpen = $state(true);
	let wsList = $state<WorkspaceEntry[]>([]);
	let wsLoading = $state(false);
	let wsNewName = $state('');
	let wsCreating = $state(false);
	let wsSearch = $state('');
	let wsDeleteConfirmId = $state<string | null>(null);
	let wsOpeningId = $state<string | null>(null);
	let wsTitleEditing = $state(false);
	let wsTitleDraft = $state('');

	const wsFiltered = $derived.by(() => {
		const base = wsList.filter((w) => !w.id.startsWith('study:'));
		return wsSearch.trim()
			? base.filter((w) => w.title.toLowerCase().includes(wsSearch.trim().toLowerCase()))
			: base;
	});

	let studyWsOpen = $state(true);
	let expandedStudyFolders = $state<Set<string>>(new Set());

	const studyTree = $derived.by(() => {
		const items = wsList.filter((w) => w.id.startsWith('study:'));
		const tree = new Map<string, WorkspaceEntry[]>();
		for (const item of items) {
			const path = item.id.replace('study:', '');
			const slashIdx = path.indexOf('/');
			const category = slashIdx > 0 ? path.substring(0, slashIdx) : path;
			if (!tree.has(category)) tree.set(category, []);
			tree.get(category)!.push(item);
		}
		return tree;
	});

	function toggleStudyFolder(cat: string) {
		const next = new Set(expandedStudyFolders);
		if (next.has(cat)) next.delete(cat);
		else next.add(cat);
		expandedStudyFolders = next;
	}

	function studyContentName(ws: WorkspaceEntry): string {
		const path = ws.id.replace('study:', '');
		const slashIdx = path.indexOf('/');
		return slashIdx > 0 ? path.substring(slashIdx + 1) : path;
	}

	async function loadWsList() {
		wsLoading = true;
		try {
			const res = await fetch('/api/notebook/list', { credentials: 'include' });
			if (res.ok) wsList = await res.json();
		} catch { /* silent */ } finally {
			wsLoading = false;
		}
	}

	async function openWs(id: string) {
		wsOpeningId = id;
		try {
			const res = await fetch(`/api/notebook/${encodeURIComponent(id)}`, { credentials: 'include' });
			if (!res.ok) return;
			const data = await res.json();
			if (data.error) return;
			destroyEngine();
			loadNotebook(data);
		} finally {
			wsOpeningId = null;
		}
	}

	async function createWs() {
		const name = wsNewName.trim() || 'Untitled';
		wsNewName = '';
		wsCreating = false;
		destroyEngine();
		resetNotebook();
		await tick();
		const nb = $notebook;
		const titled = { ...nb, title: name };
		const res = await fetch('/api/notebook/save', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			credentials: 'include',
			body: JSON.stringify(titled),
		});
		if (res.ok) await loadWsList();
	}

	function requestDeleteWs(id: string, e: MouseEvent) {
		e.stopPropagation();
		wsDeleteConfirmId = id;
	}

	async function confirmDeleteWs(id: string, e: MouseEvent) {
		e.stopPropagation();
		wsDeleteConfirmId = null;
		await fetch(`/api/notebook/${encodeURIComponent(id)}`, { method: 'DELETE', credentials: 'include' });
		wsList = wsList.filter((w) => w.id !== id);
	}

	function cancelDeleteWs(e?: MouseEvent) {
		e?.stopPropagation();
		wsDeleteConfirmId = null;
	}

	async function startTitleEdit(e: MouseEvent) {
		e.stopPropagation();
		wsTitleDraft = $notebook.title || '';
		wsTitleEditing = true;
		await tick();
		const input = document.querySelector('.ws-title-input') as HTMLInputElement;
		if (input) { input.focus(); input.select(); }
	}

	async function commitTitleEdit() {
		wsTitleEditing = false;
		const name = wsTitleDraft.trim();
		if (!name || name === $notebook.title) return;
		setTitle(name);
		await tick();
		await saveToServer();
		wsList = wsList.map((w) => w.id === $notebook.id ? { ...w, title: name } : w);
	}

	function cancelTitleEdit() {
		wsTitleEditing = false;
		wsTitleDraft = '';
	}

	function wsFormatDate(iso: string): string {
		if (!iso) return '';
		const d = new Date(iso);
		return d.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
	}

	const currentNotebookFile = $derived($notebookFilePath);

	let lastExecCount = 0;

	onMount(() => {
		loadWsList();
		const unsub1 = engineStatus.subscribe((s) => {
			const ready = s === 'ready' || s === 'executing';
			if (ready && !engineReady) {
				engineReady = true;
				loadDir('/workspace');
			}
			engineReady = ready;
		});
		const unsub2 = executionDoneCounter.subscribe((count) => {
			if (count > lastExecCount && engineReady) {
				lastExecCount = count;
				handleRefresh();
			}
			lastExecCount = count;
		});
		let lastPathVer = 0;
		const unsub3 = notebookPathVersion.subscribe((ver) => {
			if (ver > lastPathVer && engineReady) {
				lastPathVer = ver;
				handleRefresh();
			}
			lastPathVer = ver;
		});
		return () => { unsub1(); unsub2(); unsub3(); };
	});

	async function loadDir(path: string) {
		const items = await listFiles(path);
		const sorted = [...items].sort((a, b) => {
			if (a.isDir && !b.isDir) return -1;
			if (!a.isDir && b.isDir) return 1;
			return a.name.localeCompare(b.name);
		});
		treeData.set(path, sorted);
		treeData = new Map(treeData);
	}

	async function toggleDir(path: string) {
		if (expandedDirs.has(path)) {
			expandedDirs.delete(path);
			expandedDirs = new Set(expandedDirs);
		} else {
			expandedDirs.add(path);
			expandedDirs = new Set(expandedDirs);
			await loadDir(path);
		}
	}

	async function handleSelectFile(path: string) {
		if (path.endsWith('.py') && path !== currentNotebookFile) {
			await loadNotebookFromFile(path);
			selectedFile = null;
			fileContent = null;
			await handleRefresh();
			saveWorkspaceSnapshot();
			return;
		}
		selectedFile = path;
		fileContent = await readFile(path);
	}

	async function startRename(path: string, name: string) {
		renamingPath = path;
		renameValue = name;
		await tick();
		const input = document.querySelector('.rename-input') as HTMLInputElement;
		if (input) {
			input.focus();
			const dotIdx = name.lastIndexOf('.');
			input.setSelectionRange(0, dotIdx > 0 ? dotIdx : name.length);
		}
	}

	async function confirmRename() {
		const name = renameValue.trim();
		if (!name || !renamingPath) { cancelRename(); return; }
		const oldPath = renamingPath;
		const parent = oldPath.substring(0, oldPath.lastIndexOf('/')) || '/workspace';
		const newPath = parent + '/' + name;
		if (newPath === oldPath) { cancelRename(); return; }

		try {
			await renamePathFS(oldPath, newPath);
		} catch {
			cancelRename();
			return;
		}

		if (selectedFile === oldPath) {
			selectedFile = newPath;
			fileContent = await readFile(newPath);
		}
		if (expandedDirs.has(oldPath)) {
			expandedDirs.delete(oldPath);
			expandedDirs.add(newPath);
			expandedDirs = new Set(expandedDirs);
		}
		renamingPath = null;
		renameValue = '';
		await loadDir(parent);
		saveWorkspaceSnapshot();
	}

	function cancelRename() {
		renamingPath = null;
		renameValue = '';
	}

	async function startNewItem(type: 'file' | 'dir', parentPath: string) {
		newItemParent = parentPath;
		newItemType = type;
		newName = '';
		if (!expandedDirs.has(parentPath)) {
			expandedDirs.add(parentPath);
			expandedDirs = new Set(expandedDirs);
			await loadDir(parentPath);
		}
		await tick();
		const input = document.querySelector('.inline-input') as HTMLInputElement;
		if (input) input.focus();
	}

	async function confirmNewItem() {
		const name = newName.trim();
		if (!name || !newItemParent || !newItemType) return;
		const parent = newItemParent;
		const path = parent.endsWith('/') ? parent + name : parent + '/' + name;
		try {
			if (newItemType === 'file') {
				await writeFile(path, '');
			} else {
				await mkdirFS(path);
			}
		} catch {
			// creation failed
		}
		newItemParent = null;
		newItemType = null;
		newName = '';
		await loadDir(parent);
		saveWorkspaceSnapshot();
	}

	function cancelNewItem() {
		newItemParent = null;
		newItemType = null;
		newName = '';
	}

	async function handleDelete(path: string) {
		try {
			await removeFileFS(path);
		} catch {
			// deletion failed
		}
		if (selectedFile === path) {
			selectedFile = null;
			fileContent = null;
		}
		const parent = path.substring(0, path.lastIndexOf('/')) || '/workspace';
		await loadDir(parent);
		saveWorkspaceSnapshot();
	}

	async function handleUpload() {
		const input = document.createElement('input');
		input.type = 'file';
		input.multiple = true;
		input.onchange = async () => {
			if (!input.files) return;
			for (const file of input.files) {
				const text = await file.text();
				const path = '/workspace/' + file.name;
				await writeFile(path, text);
			}
			await loadDir('/workspace');
			saveWorkspaceSnapshot();
		};
		input.click();
	}

	function insertToCell(content: string) {
		const activeId = $activeCellId;
		if (!activeId) return;
		const cell = $notebook.cells.find((c) => c.id === activeId);
		if (!cell) return;
		const newContent = cell.content ? cell.content + '\n' + content : content;
		updateCellContent(activeId, newContent);
	}

	async function handleRefresh() {
		for (const path of expandedDirs) {
			await loadDir(path);
		}
	}
</script>

<div class="files-panel">
	<div class="ws-section">
		<div class="ws-section-header">
			<button class="ws-section-toggle" onclick={() => (wsOpen = !wsOpen)}>
				<Database size={12} />
				<span>Workspaces</span>
				{#if wsOpen}
					<ChevronDown size={11} class="ws-chevron" />
				{:else}
					<ChevronRight size={11} class="ws-chevron" />
				{/if}
			</button>
			{#if wsLoading}
				<Loader2 size={11} class="ws-spin" />
			{/if}
			<button class="ws-add-btn" onclick={() => { wsCreating = !wsCreating; wsOpen = true; }} title="New workspace" aria-label="New workspace">
				<Plus size={11} />
			</button>
		</div>

		{#if wsOpen}
			{#if wsCreating}
				<div class="ws-create-row">
					<input
						class="ws-create-input"
						placeholder="Workspace name..."
						bind:value={wsNewName}
						onkeydown={(e) => {
							if (e.key === 'Enter') createWs();
							if (e.key === 'Escape') { wsCreating = false; wsNewName = ''; }
						}}
					/>
					<button class="ws-create-confirm" onclick={createWs} aria-label="Create">✓</button>
				</div>
			{/if}
			{#if !wsLoading && wsList.length > 2}
				<div class="ws-search-row">
					<input
						class="ws-search-input"
						placeholder="Search..."
						bind:value={wsSearch}
					/>
					{#if wsSearch}
						<button class="ws-search-clear" onclick={() => (wsSearch = '')} aria-label="Clear search">✕</button>
					{/if}
				</div>
			{/if}
			{#if wsLoading}
				<div class="ws-empty">Loading...</div>
			{:else if wsList.length === 0}
				<div class="ws-empty">No workspaces saved</div>
			{:else if wsFiltered.length === 0}
				<div class="ws-empty">No results</div>
			{:else}
				{#each wsFiltered as ws (ws.id)}
					{@const isCurrent = $notebook.id === ws.id}
					{@const isOpening = wsOpeningId === ws.id}
					{@const displayTitle = isCurrent ? ($notebook.title || 'Untitled') : (ws.title || 'Untitled')}
					<div
						class="ws-item"
						class:ws-current={isCurrent}
						class:ws-opening={isOpening}
						onclick={() => !isCurrent && !wsOpeningId && openWs(ws.id)}
						role="button"
						tabindex="0"
						onkeydown={(e) => e.key === 'Enter' && !isCurrent && !wsOpeningId && openWs(ws.id)}
					>
						<div class="ws-item-info">
							{#if isCurrent && wsTitleEditing}
								<input
									class="ws-title-input"
									bind:value={wsTitleDraft}
									onblur={commitTitleEdit}
									onkeydown={(e) => {
										if (e.key === 'Enter') { e.preventDefault(); commitTitleEdit(); }
										if (e.key === 'Escape') cancelTitleEdit();
									}}
									onclick={(e) => e.stopPropagation()}
								/>
							{:else}
								<span class="ws-item-title">{displayTitle}</span>
							{/if}
							<span class="ws-item-meta">{ws.cellCount} cells · {wsFormatDate(ws.updatedAt)}</span>
						</div>
						{#if isOpening}
							<Loader2 size={11} class="ws-spin" />
						{:else if isCurrent}
							{#if !wsTitleEditing}
								<button class="ws-edit-btn" onclick={startTitleEdit} aria-label="Rename workspace">
									<Pencil size={10} />
								</button>
							{/if}
						{:else}
							<button class="ws-del-btn" onclick={(e) => requestDeleteWs(ws.id, e)} aria-label="Delete">✕</button>
						{/if}
					</div>
				{/each}
			{/if}
		{/if}
	</div>

	<div class="section-divider"></div>

	<div class="ws-section">
		<div class="ws-section-header">
			<button class="ws-section-toggle" onclick={() => (studyWsOpen = !studyWsOpen)}>
				<BookOpen size={12} />
				<span>Study</span>
				{#if studyWsOpen}
					<ChevronDown size={11} class="ws-chevron" />
				{:else}
					<ChevronRight size={11} class="ws-chevron" />
				{/if}
			</button>
		</div>

		{#if studyWsOpen}
			{#if wsLoading}
				<div class="ws-empty">Loading...</div>
			{:else if studyTree.size === 0}
				<div class="ws-empty">No study records</div>
			{:else}
				{#each [...studyTree.entries()] as [category, items]}
					<div class="study-folder">
						<button class="study-folder-btn" onclick={() => toggleStudyFolder(category)}>
							{#if expandedStudyFolders.has(category)}
								<ChevronDown size={11} />
								<FolderOpen size={12} class="study-folder-icon" />
							{:else}
								<ChevronRight size={11} />
								<Folder size={12} class="study-folder-icon" />
							{/if}
							<span class="study-folder-name">{category}</span>
							<span class="study-folder-count">{items.length}</span>
						</button>
						{#if expandedStudyFolders.has(category)}
							{#each items as ws (ws.id)}
								{@const isOpening = wsOpeningId === ws.id}
								<div
									class="ws-item study-ws-item"
									class:ws-opening={isOpening}
									onclick={() => !wsOpeningId && openWs(ws.id)}
									role="button"
									tabindex="0"
									onkeydown={(e) => e.key === 'Enter' && !wsOpeningId && openWs(ws.id)}
								>
									<div class="ws-item-info">
										<span class="ws-item-title">{studyContentName(ws)}</span>
										<span class="ws-item-meta">{ws.cellCount} cells · {wsFormatDate(ws.updatedAt)}</span>
									</div>
									{#if isOpening}
										<Loader2 size={11} class="ws-spin" />
									{/if}
								</div>
							{/each}
						{/if}
					</div>
				{/each}
			{/if}
		{/if}
	</div>

	<div class="section-divider"></div>

	{#if !engineReady}
		<div class="file-empty">Engine loading...</div>
	{:else}
		<div class="file-tree">
			{#snippet renderTree(path: string, depth: number)}
				{@const items = treeData.get(path) || []}
				{#if newItemParent === path}
					<div class="new-input-row" style="padding-left: {8 + depth * 14}px">
						{#if newItemType === 'dir'}
							<Folder size={13} class="tree-icon dir" />
						{:else}
							<FileCode size={13} class="tree-icon file" />
						{/if}
						<input
							class="inline-input"
							bind:value={newName}
							placeholder={newItemType === 'file' ? 'filename.py' : 'folder name'}
							onkeydown={(e) => {
								if (e.key === 'Enter') confirmNewItem();
								if (e.key === 'Escape') cancelNewItem();
							}}
							onblur={() => { if (!newName.trim()) cancelNewItem(); }}
						/>
					</div>
				{/if}
				{#each items as entry}
					{#if entry.isDir}
						<div class="tree-item-row">
							{#if renamingPath === entry.path}
								<div class="rename-row" style="padding-left: {8 + depth * 14}px">
									<Folder size={13} class="tree-icon dir" />
									<input
										class="rename-input"
										bind:value={renameValue}
										onkeydown={(e) => {
											if (e.key === 'Enter') confirmRename();
											if (e.key === 'Escape') cancelRename();
										}}
										onblur={() => confirmRename()}
									/>
								</div>
							{:else}
								<button
									class="tree-item"
									class:selected={selectedFile === entry.path}
									style="padding-left: {8 + depth * 14}px"
									onclick={() => toggleDir(entry.path)}
								>
									{#if expandedDirs.has(entry.path)}
										<ChevronDown size={12} class="tree-chevron" />
										<FolderOpen size={13} class="tree-icon dir" />
									{:else}
										<ChevronRight size={12} class="tree-chevron" />
										<Folder size={13} class="tree-icon dir" />
									{/if}
									<span class="tree-name">{entry.name}</span>
								</button>
								<div class="tree-inline-actions">
									<button
										class="tree-add"
										onclick={(e) => { e.stopPropagation(); startRename(entry.path, entry.name); }}
										title="Rename"
										aria-label="Rename folder"
									>
										<Pencil size={10} />
									</button>
									<button
										class="tree-add"
										onclick={(e) => { e.stopPropagation(); startNewItem('file', entry.path); }}
										title="New file"
										aria-label="New file in folder"
									>
										<FilePlus size={10} />
									</button>
									<button
										class="tree-add"
										onclick={(e) => { e.stopPropagation(); startNewItem('dir', entry.path); }}
										title="New folder"
										aria-label="New folder in folder"
									>
										<FolderPlus size={10} />
									</button>
									<button class="tree-delete" onclick={() => handleDelete(entry.path)} aria-label="Delete">
										<Trash2 size={11} />
									</button>
								</div>
							{/if}
						</div>
						{#if expandedDirs.has(entry.path)}
							{@render renderTree(entry.path, depth + 1)}
						{/if}
					{:else}
						{@const isCurrentNb = entry.path === currentNotebookFile}
						<div class="tree-item-row">
							{#if renamingPath === entry.path}
								<div class="rename-row" style="padding-left: {8 + depth * 14}px">
									{#if isCurrentNb}
										<BookOpen size={13} class="tree-icon notebook" />
									{:else}
										<FileCode size={13} class="tree-icon file" />
									{/if}
									<input
										class="rename-input"
										bind:value={renameValue}
										onkeydown={(e) => {
											if (e.key === 'Enter') confirmRename();
											if (e.key === 'Escape') cancelRename();
										}}
										onblur={() => confirmRename()}
									/>
								</div>
							{:else}
								<button
									class="tree-item"
									class:selected={selectedFile === entry.path}
									class:current-notebook={isCurrentNb}
									style="padding-left: {8 + depth * 14}px"
									onclick={() => handleSelectFile(entry.path)}
								>
									{#if isCurrentNb}
										<BookOpen size={13} class="tree-icon notebook" />
									{:else if entry.name.endsWith('.py')}
										<FileCode size={13} class="tree-icon py" />
									{:else}
										<FileCode size={13} class="tree-icon file" />
									{/if}
									<span class="tree-name">{entry.name}</span>
									{#if entry.size != null}
										<span class="tree-size">{entry.size > 1024 ? `${(entry.size / 1024).toFixed(1)}KB` : `${entry.size}B`}</span>
									{/if}
								</button>
								<div class="tree-inline-actions">
									{#if !isCurrentNb}
										<button
											class="tree-add"
											onclick={(e) => { e.stopPropagation(); startRename(entry.path, entry.name); }}
											title="Rename"
											aria-label="Rename"
										>
											<Pencil size={10} />
										</button>
										<button class="tree-delete" onclick={() => handleDelete(entry.path)} aria-label="Delete">
											<Trash2 size={11} />
										</button>
									{/if}
								</div>
							{/if}
						</div>
					{/if}
				{/each}
			{/snippet}

			<div class="tree-item-row root-row">
				<button
					class="tree-item root"
					onclick={() => toggleDir('/workspace')}
				>
					{#if expandedDirs.has('/workspace')}
						<ChevronDown size={12} class="tree-chevron" />
						<FolderOpen size={13} class="tree-icon dir" />
					{:else}
						<ChevronRight size={12} class="tree-chevron" />
						<Folder size={13} class="tree-icon dir" />
					{/if}
					<span class="tree-name">{($notebook.title || 'workspace')}</span>
				</button>
				<div class="tree-inline-actions root-actions">
					<button
						class="tree-add"
						onclick={(e) => { e.stopPropagation(); startNewItem('file', '/workspace'); }}
						title="New file"
						aria-label="New file"
					>
						<FilePlus size={11} />
					</button>
					<button
						class="tree-add"
						onclick={(e) => { e.stopPropagation(); startNewItem('dir', '/workspace'); }}
						title="New folder"
						aria-label="New folder"
					>
						<FolderPlus size={11} />
					</button>
					<button
						class="tree-add"
						onclick={(e) => { e.stopPropagation(); handleUpload(); }}
						title="Upload file"
						aria-label="Upload file"
					>
						<Upload size={11} />
					</button>
					<button
						class="tree-add"
						onclick={(e) => { e.stopPropagation(); handleRefresh(); }}
						title="Refresh"
						aria-label="Refresh"
					>
						<RefreshCw size={11} />
					</button>
				</div>
			</div>
			{#if expandedDirs.has('/workspace')}
				{@render renderTree('/workspace', 1)}
			{/if}
		</div>

		{#if selectedFile && fileContent !== null}
			<div class="file-preview">
				<div class="preview-header">
					<span class="preview-path">{selectedFile.replace('/workspace/', '')}</span>
					<button
						class="preview-action"
						onclick={() => { if (fileContent) insertToCell(fileContent); }}
						title="Insert to active cell"
						aria-label="Insert to cell"
					>
						<Copy size={12} />
					</button>
				</div>
				<pre class="preview-content">{fileContent}</pre>
			</div>
		{/if}
	{/if}
</div>

{#if wsDeleteConfirmId !== null}
	{@const targetWs = wsList.find((w) => w.id === wsDeleteConfirmId)}
	<div class="ws-dialog-backdrop" onclick={cancelDeleteWs} role="presentation">
		<div class="ws-dialog" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
			<p class="ws-dialog-title">Delete workspace?</p>
			<p class="ws-dialog-body">"{targetWs?.title || 'Untitled'}" will be permanently deleted. This cannot be undone.</p>
			<div class="ws-dialog-actions">
				<button class="ws-dialog-cancel" onclick={cancelDeleteWs}>Cancel</button>
				<button class="ws-dialog-confirm" onclick={(e) => wsDeleteConfirmId && confirmDeleteWs(wsDeleteConfirmId, e)}>Delete</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.files-panel {
		padding: 0;
		display: flex;
		flex-direction: column;
	}

	.section-divider {
		height: 1px;
		background: var(--nb-border);
		margin: 4px 0;
	}

	.ws-section {
		padding: 6px 8px 4px;
	}

	.ws-section-header {
		display: flex;
		align-items: center;
		margin-bottom: 2px;
	}

	:global(.ws-spin) {
		animation: ws-spin 0.8s linear infinite;
		color: var(--nb-text-muted);
		flex-shrink: 0;
	}

	@keyframes ws-spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.ws-opening {
		cursor: wait;
	}

	.ws-section-toggle {
		display: flex;
		align-items: center;
		gap: 4px;
		flex: 1;
		background: none;
		border: none;
		color: var(--nb-text-muted);
		font-size: 10px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		cursor: pointer;
		padding: 3px 0;
	}

	.ws-section-toggle:hover {
		color: var(--nb-text);
	}

	.ws-section-toggle :global(.ws-chevron) {
		margin-left: auto;
	}

	.ws-add-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 18px;
		height: 18px;
		border: none;
		border-radius: 3px;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.ws-add-btn:hover {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.ws-create-row {
		display: flex;
		gap: 4px;
		padding: 2px 0 4px;
	}

	.ws-create-input {
		flex: 1;
		padding: 3px 6px;
		background: var(--nb-card);
		border: 1px solid var(--nb-border);
		border-radius: 4px;
		font-size: 11px;
		color: var(--nb-text);
		outline: none;
	}

	.ws-create-confirm {
		background: var(--nb-surface);
		border: 1px solid var(--nb-border);
		border-radius: 4px;
		color: var(--nb-text);
		font-size: 11px;
		padding: 3px 6px;
		cursor: pointer;
	}

	.ws-empty {
		font-size: 11px;
		color: var(--nb-text-muted);
		padding: 4px 2px 6px;
	}

	.ws-item {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 4px 6px;
		border-radius: 5px;
		cursor: pointer;
		transition: background 0.1s ease;
	}

	.ws-item:not(.ws-current):hover {
		background: var(--nb-surface);
	}

	.ws-item.ws-current {
		background: var(--nb-card);
		border-left: 2px solid var(--nb-text-secondary);
		padding-left: 4px;
		cursor: default;
	}

	.ws-item-info {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 1px;
	}

	.ws-item-title {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.ws-current .ws-item-title {
		color: var(--nb-text);
		font-weight: 600;
	}

	.ws-title-input {
		flex: 1;
		width: 100%;
		padding: 0 2px;
		background: transparent;
		border: none;
		border-bottom: 1px solid var(--nb-border);
		border-radius: 0;
		font-size: 12px;
		font-weight: 600;
		color: var(--nb-text);
		outline: none;
		font-family: inherit;
	}

	.ws-item-meta {
		font-size: 10px;
		color: var(--nb-text-muted);
	}

	.ws-del-btn {
		background: none;
		border: none;
		color: var(--nb-text-muted);
		font-size: 10px;
		padding: 2px 4px;
		border-radius: 3px;
		cursor: pointer;
		flex-shrink: 0;
		line-height: 1;
		transition: all 0.1s ease;
	}

	.ws-del-btn:hover {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.ws-edit-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 20px;
		height: 20px;
		border: none;
		border-radius: 3px;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		flex-shrink: 0;
		transition: all 0.1s ease;
	}

	.ws-edit-btn:hover {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.ws-search-row {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 2px 0 4px;
		position: relative;
	}

	.ws-search-input {
		flex: 1;
		padding: 3px 22px 3px 6px;
		background: var(--nb-surface);
		border: 1px solid var(--nb-border);
		border-radius: 4px;
		font-size: 11px;
		color: var(--nb-text);
		outline: none;
		transition: border-color 0.1s ease;
	}

	.ws-search-input:focus {
		border-color: var(--nb-text-muted);
	}

	.ws-search-input::placeholder {
		color: var(--nb-text-muted);
	}

	.ws-search-clear {
		position: absolute;
		right: 4px;
		background: none;
		border: none;
		color: var(--nb-text-muted);
		font-size: 9px;
		cursor: pointer;
		padding: 2px 3px;
		border-radius: 3px;
		line-height: 1;
	}

	.ws-search-clear:hover {
		color: var(--nb-text);
	}

	.ws-dialog-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.35);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 9999;
	}

	.ws-dialog {
		background: var(--nb-card);
		border: 1px solid var(--nb-border);
		border-radius: 10px;
		padding: 20px;
		width: 260px;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.ws-dialog-title {
		font-size: 13px;
		font-weight: 600;
		color: var(--nb-text);
		margin: 0;
	}

	.ws-dialog-body {
		font-size: 12px;
		color: var(--nb-text-muted);
		margin: 0;
		line-height: 1.5;
	}

	.ws-dialog-actions {
		display: flex;
		gap: 6px;
		margin-top: 4px;
	}

	.ws-dialog-cancel {
		flex: 1;
		padding: 6px 0;
		background: var(--nb-surface);
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		color: var(--nb-text);
		font-size: 12px;
		cursor: pointer;
	}

	.ws-dialog-cancel:hover {
		background: var(--nb-card);
	}

	.ws-dialog-confirm {
		flex: 1;
		padding: 6px 0;
		background: var(--nb-surface);
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		color: var(--nb-text);
		font-size: 12px;
		font-weight: 600;
		cursor: pointer;
	}

	.ws-dialog-confirm:hover {
		background: var(--nb-border);
	}

	.new-input-row {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 2px 8px;
	}

	.new-input-row :global(.tree-icon.dir) {
		color: var(--nb-text-muted);
		flex-shrink: 0;
	}

	.new-input-row :global(.tree-icon.file) {
		color: var(--nb-text-muted);
		flex-shrink: 0;
	}

	.inline-input {
		flex: 1;
		min-width: 0;
		padding: 2px 6px;
		border: 1px solid var(--nb-border);
		border-radius: 4px;
		background: var(--nb-card);
		color: var(--nb-text);
		font-size: 12px;
		font-family: 'Fira Code', monospace;
		outline: none;
		box-sizing: border-box;
	}

	.inline-input::placeholder {
		color: var(--nb-text-muted);
	}

	.file-empty {
		padding: 16px 12px;
		text-align: center;
		color: var(--nb-text-muted);
		font-size: 12px;
	}

	.file-tree {
		display: flex;
		flex-direction: column;
		padding: 0 8px;
	}

	.tree-item-row {
		display: flex;
		align-items: center;
	}

	.tree-item-row:hover .tree-delete,
	.tree-item-row:hover .tree-add {
		opacity: 1;
	}

	.tree-item {
		display: flex;
		align-items: center;
		gap: 4px;
		width: 100%;
		padding: 3px 8px;
		border: none;
		border-radius: 4px;
		background: transparent;
		color: var(--nb-text);
		font-size: 12px;
		cursor: pointer;
		transition: background 0.1s ease;
		text-align: left;
		white-space: nowrap;
		overflow: hidden;
	}

	.tree-item:hover {
		background: var(--nb-surface);
	}

	.tree-item.selected {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.tree-item.root {
		font-weight: 600;
		padding-left: 4px;
	}

	.tree-item :global(.tree-chevron) {
		color: var(--nb-text-muted);
		flex-shrink: 0;
	}

	.tree-item :global(.tree-icon.dir) {
		color: var(--nb-text-secondary);
		flex-shrink: 0;
	}

	.tree-item :global(.tree-icon.file) {
		color: var(--nb-text-muted);
		flex-shrink: 0;
	}

	.tree-item :global(.tree-icon.py) {
		color: var(--nb-text-secondary);
		flex-shrink: 0;
	}

	.tree-item :global(.tree-icon.notebook) {
		color: var(--nb-text-secondary);
		flex-shrink: 0;
	}

	.tree-item.current-notebook {
		color: var(--nb-text);
		font-weight: 600;
	}

	.tree-item.current-notebook:hover {
		background: var(--nb-surface);
	}

	.rename-row {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 2px 8px;
		width: 100%;
	}

	.rename-row :global(.tree-icon.dir) {
		color: var(--nb-text-muted);
		flex-shrink: 0;
	}

	.rename-row :global(.tree-icon.file),
	.rename-row :global(.tree-icon.notebook) {
		flex-shrink: 0;
	}

	.rename-input {
		flex: 1;
		min-width: 0;
		padding: 2px 6px;
		border: 1px solid var(--nb-border);
		border-radius: 4px;
		background: var(--nb-card);
		color: var(--nb-text);
		font-size: 12px;
		font-family: 'Fira Code', monospace;
		outline: none;
		box-sizing: border-box;
	}

	.tree-name {
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.tree-size {
		font-size: 9px;
		color: var(--nb-text-muted);
		margin-left: auto;
		flex-shrink: 0;
	}

	.tree-inline-actions {
		display: flex;
		align-items: center;
		gap: 0;
		opacity: 0;
		transition: opacity 0.1s ease;
		flex-shrink: 0;
	}

	.tree-item-row:hover .tree-inline-actions {
		opacity: 1;
	}

	.root-row {
		padding-bottom: 2px;
	}

	.root-actions {
		margin-left: auto;
	}

	.tree-add {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 18px;
		height: 18px;
		border: none;
		border-radius: 3px;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		opacity: 0;
		transition: all 0.1s ease;
		flex-shrink: 0;
	}

	.tree-inline-actions .tree-add {
		opacity: 1;
	}

	.tree-add:hover {
		color: var(--nb-text);
		background: var(--nb-surface);
	}

	.tree-delete {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 20px;
		height: 20px;
		border: none;
		border-radius: 3px;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		opacity: 0;
		transition: all 0.1s ease;
		flex-shrink: 0;
	}

	.tree-delete:hover {
		color: var(--nb-text);
		background: var(--nb-surface);
	}

	.file-preview {
		margin-top: 8px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		overflow: hidden;
	}

	.preview-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 4px 8px;
		background: var(--nb-surface);
		border-bottom: 1px solid var(--nb-border);
	}

	.preview-path {
		font-size: 10px;
		font-family: 'Fira Code', monospace;
		color: var(--nb-text-muted);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.preview-action {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 22px;
		height: 22px;
		border: none;
		border-radius: 4px;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.1s ease;
		flex-shrink: 0;
	}

	.preview-action:hover {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.preview-content {
		font-size: 11px;
		font-family: 'Fira Code', monospace;
		color: var(--nb-text);
		padding: 8px;
		margin: 0;
		max-height: 200px;
		overflow-y: auto;
		white-space: pre-wrap;
		word-break: break-all;
		line-height: 1.5;
	}

	.preview-content::-webkit-scrollbar {
		width: 4px;
	}

	.preview-content::-webkit-scrollbar-thumb {
		background: var(--nb-border);
		border-radius: 2px;
	}

	.study-folder {
		display: flex;
		flex-direction: column;
	}

	.study-folder-btn {
		display: flex;
		align-items: center;
		gap: 4px;
		width: 100%;
		padding: 4px 6px;
		background: none;
		border: none;
		color: var(--nb-text);
		font-size: 12px;
		font-weight: 600;
		cursor: pointer;
		border-radius: 4px;
		transition: background 0.1s ease;
	}

	.study-folder-btn:hover {
		background: var(--nb-surface);
	}

	.study-folder-btn :global(.study-folder-icon) {
		color: var(--nb-text-secondary);
		flex-shrink: 0;
	}

	.study-folder-name {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.study-folder-count {
		margin-left: auto;
		font-size: 10px;
		color: var(--nb-text-muted);
		font-weight: 400;
		flex-shrink: 0;
	}

	.study-ws-item {
		padding-left: 22px;
	}
</style>
