<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { Sun, Moon, Play, Save, Download, FilePlus, Settings, AlignCenter, AlignJustify, Maximize, Zap, Cloud, UserRound, Upload, FileCode, FileSpreadsheet, Home, Rows3, Columns3, Loader2 } from 'lucide-svelte';
	import { notebook, resetNotebook, saveToServer, cellWidth, setCellWidth, loadNotebook, studyMode, studyLayout, setStudyLayout } from '../stores/notebookStore';
	import type { CellWidth, StudyLayout } from '../stores/notebookStore';
	import { engineStatus, executeAllCells, destroyEngine, reactiveMode, notebookFilePath, changeNotebookPath } from '../stores/executionStore';
	import { currentUser, checkAuth, authChecked } from '../stores/userStore';
	import { downloadNotebook, downloadAsMarimoFile, importMarimoNotebook, downloadAsJupyterFile, importJupyterNotebook, openFileDialog, readFileAsText } from '../utils/notebookFormat';

	const hasPracticeCells = $derived.by(() => {
		return $notebook.cells.some(
			(c) => (c.type === 'code' || c.type === 'guide') && !c.study
		);
	});

	interface Props {
		showHome?: boolean;
		homeHref?: string;
	}

	let { showHome = true, homeHref = '/' }: Props = $props();

	let isDark = $state(true);
	let showMenu = $state(false);
	let cloudSaving = $state(false);
	let cloudSaved = $state(false);
	let pathEditing = $state(false);
	let pathDraft = $state('');
	onMount(() => {
		const stored = localStorage.getItem('theme');
		isDark = stored ? stored === 'dark' : true;
		applyTheme();
		checkAuth();
	});

	function toggleTheme() {
		isDark = !isDark;
		applyTheme();
	}

	function applyTheme() {
		document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
		localStorage.setItem('theme', isDark ? 'dark' : 'light');
	}

	function handleRunAll() {
		executeAllCells($notebook.cells);
	}

	async function handleSave() {
		cloudSaving = true;
		cloudSaved = false;
		const result = await saveToServer();
		cloudSaving = false;
		if (result.ok) {
			cloudSaved = true;
			setTimeout(() => { cloudSaved = false; }, 2000);
		}
	}

	function handleExport() {
		downloadNotebook($notebook);
	}

	function handleExportMarimo() {
		downloadAsMarimoFile($notebook);
		showMenu = false;
	}

	async function handleImportMarimo() {
		showMenu = false;
		const file = await openFileDialog('.py');
		if (!file) return;
		const source = await readFileAsText(file);
		const nb = importMarimoNotebook(source, file.name);
		destroyEngine();
		loadNotebook(nb);
	}

	function handleExportJupyter() {
		downloadAsJupyterFile($notebook);
		showMenu = false;
	}

	async function handleImportJupyter() {
		showMenu = false;
		const file = await openFileDialog('.ipynb');
		if (!file) return;
		const source = await readFileAsText(file);
		const nb = importJupyterNotebook(source, file.name);
		destroyEngine();
		loadNotebook(nb);
	}

	function handleNew() {
		destroyEngine();
		resetNotebook();
		showMenu = false;
	}

	function handleLogin() {
		const currentPath = window.location.pathname;
		window.location.href = `/loginCallback?redirect=${encodeURIComponent(currentPath)}`;
	}

	async function startPathEdit() {
		pathEditing = true;
		pathDraft = $notebookFilePath;
		await tick();
		const input = document.querySelector('.filepath-input') as HTMLInputElement;
		if (input) {
			input.focus();
			input.select();
		}
	}

	function commitPath() {
		pathEditing = false;
		const val = pathDraft.trim();
		if (val && val !== $notebookFilePath) {
			changeNotebookPath(val);
		}
	}

	function handlePathKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			(e.target as HTMLInputElement).blur();
		} else if (e.key === 'Escape') {
			pathEditing = false;
			pathDraft = $notebookFilePath;
		}
	}
</script>

{#if !$studyMode}
<div class="filename-bar">
	{#if pathEditing}
		<input
			class="filepath-input editing"
			bind:value={pathDraft}
			onblur={commitPath}
			onkeydown={handlePathKeydown}
		/>
	{:else}
		<button class="filepath-display" onclick={startPathEdit} title="Click to edit path">
			{$notebookFilePath}
		</button>
	{/if}
</div>
{/if}

<div class="floating-controls top-right">
	{#if $engineStatus === 'loading' || $engineStatus === 'executing' || $engineStatus === 'error'}
		<div class="engine-status">
			{#if $engineStatus === 'loading'}
				<span class="status-badge loading">Loading Pyodide...</span>
			{:else if $engineStatus === 'executing'}
				<span class="status-badge running">Running...</span>
			{:else if $engineStatus === 'error'}
				<span class="status-badge error">Error</span>
			{/if}
		</div>
	{/if}
	{#if $studyMode && hasPracticeCells}
	<button
		class="float-btn layout-toggle"
		class:layout-active={$studyLayout === 'horizontal'}
		onclick={() => setStudyLayout($studyLayout === 'vertical' ? 'horizontal' : 'vertical')}
		title={$studyLayout === 'vertical' ? 'Switch to horizontal layout' : 'Switch to vertical layout'}
		aria-label="Toggle study layout"
	>
		{#if $studyLayout === 'vertical'}
			<Columns3 size={16} />
		{:else}
			<Rows3 size={16} />
		{/if}
	</button>
	{/if}
	{#if !$studyMode}
	<button class="float-btn" onclick={() => (showMenu = !showMenu)} title="Menu" aria-label="Menu">
		<Settings size={16} />
	</button>
	{/if}
	<button class="float-btn" onclick={toggleTheme} title={isDark ? 'Light mode' : 'Dark mode'} aria-label="Toggle theme">
		{#if isDark}
			<Sun size={16} />
		{:else}
			<Moon size={16} />
		{/if}
	</button>
	{#if showHome}
		<a class="float-btn home-btn" href={homeHref} data-sveltekit-reload title="Home" aria-label="Home">
			<Home size={16} />
		</a>
	{/if}

	{#if showMenu}
		<div class="dropdown-menu">
			<button class="dropdown-item" onclick={() => { handleNew(); }}>
				<FilePlus size={14} />
				New notebook
			</button>
			<button class="dropdown-item" onclick={() => { handleExport(); showMenu = false; }}>
				<Download size={14} />
				Export .json
			</button>
			<div class="dropdown-divider"></div>
			<button class="dropdown-item" onclick={handleImportMarimo}>
				<Upload size={14} />
				Import marimo .py
			</button>
			<button class="dropdown-item" onclick={handleExportMarimo}>
				<FileCode size={14} />
				Export marimo .py
			</button>
			<div class="dropdown-divider"></div>
			<button class="dropdown-item" onclick={handleImportJupyter}>
				<Upload size={14} />
				Import Jupyter .ipynb
			</button>
			<button class="dropdown-item" onclick={handleExportJupyter}>
				<FileSpreadsheet size={14} />
				Export Jupyter .ipynb
			</button>
		</div>
	{/if}
</div>

{#if !$studyMode}
<div class="floating-controls bottom-left">
	<div class="width-toggle">
		<button
			class="width-btn"
			class:active={$cellWidth === 'compact'}
			onclick={() => setCellWidth('compact')}
			title="Compact"
			aria-label="Compact"
		>
			<AlignCenter size={14} />
		</button>
		<button
			class="width-btn"
			class:active={$cellWidth === 'medium'}
			onclick={() => setCellWidth('medium')}
			title="Medium"
			aria-label="Medium"
		>
			<AlignJustify size={14} />
		</button>
		<button
			class="width-btn"
			class:active={$cellWidth === 'full'}
			onclick={() => setCellWidth('full')}
			title="Full width"
			aria-label="Full"
		>
			<Maximize size={14} />
		</button>
	</div>
</div>
{/if}

<div class="floating-controls bottom-right">
	{#if $authChecked}
		{#if $currentUser}
			<button
				class="float-btn user-btn"
				title={`${$currentUser.name} (${$currentUser.email})`}
				aria-label="User profile"
			>
				{#if $currentUser.picture}
					<img class="user-avatar" src={$currentUser.picture} alt="" referrerpolicy="no-referrer" />
				{:else}
					<UserRound size={16} />
				{/if}
			</button>
		{:else}
			<button
				class="float-btn login-btn"
				onclick={handleLogin}
				title="Login"
				aria-label="Login"
			>
				<UserRound size={16} />
			</button>
		{/if}
	{/if}
	{#if !$studyMode || hasPracticeCells}
	<button
		class="float-btn"
		class:reactive-on={$reactiveMode}
		onclick={() => reactiveMode.update((v) => !v)}
		title={$reactiveMode ? 'Reactive mode ON (click to disable)' : 'Reactive mode OFF (click to enable)'}
		aria-label="Toggle reactive mode"
	>
		<Zap size={16} />
	</button>
	<button class="float-btn accent" onclick={handleRunAll} title="Run all (Ctrl+Shift+Enter)" aria-label="Run all" disabled={$engineStatus === 'executing'}>
		{#if $engineStatus === 'executing'}
			<Loader2 size={16} class="spin" />
		{:else}
			<Play size={16} />
			<Play size={16} class="double-play" />
		{/if}
	</button>
	{/if}
	{#if !$studyMode}
	<button
		class="float-btn"
		class:cloud-saving={cloudSaving}
		class:cloud-saved={cloudSaved}
		onclick={handleSave}
		title={$currentUser ? 'Save to cloud (Ctrl+S)' : 'Save locally (Ctrl+S)'}
		aria-label="Save"
		disabled={cloudSaving}
	>
		{#if cloudSaving}
			<Loader2 size={16} class="spin" />
		{:else if $currentUser}
			<Cloud size={16} />
		{:else}
			<Save size={16} />
		{/if}
	</button>
	{/if}
	<a
		class="float-btn coffee-btn"
		href="https://www.buymeacoffee.com/eddmpython"
		target="_blank"
		rel="noopener"
		title="Buy me a coffee"
		aria-label="Buy me a coffee"
	>
		<img
			class="coffee-icon"
			src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAE60lEQVR4AcWXA5QrSRSGv6ruYGyubdu2bdu2bet4bdu2bXsnTiYTTLqrNrnLh355ft85caXvX3X/ul1XwX/Yb4kAawK7AqsAfYDLlOEBQ8DLwE3Ac2ouyoCg+C/4AHACsDPQwbQhDdwCnFcV8TuA4r/g1wGbAoqxUYAGwYDv1x4KaxEcDY5rUc5/Y7AEYYGHgANqIlQ1eBi4GDiE8aGgUFS8/2mEdz+J8N3PIeIph/yIxjegFEQjlo42w6wDFRadf5RlFyvR3+ODZUJcBRxdE7AByLJ0Mh7Ko4qTL+3k5gdacbRljlk8ejp9WpsNoZDFGBgpaNJZzVDCIZlxmG/OCteeGWO+uSpgCCIF7OwCuwYFR4HnK374JUR2WDPY6zHXrBVmn7lCR+t/AvIFza9/uCwwzyiLzjfKqZd38syrjcw3d5ZgJOauLrAyQVhoajZcdkqCNVco8sYHUX741eXDz8OURhXGKBQQDlkaGwzLLV5mvdUL1dVq4YvvwkwEK7tAPwHUZv/uhxGSGc1KSxfZYPURlBID4nlgrEIpWxUgIuRRS1lXu8+bH0R46/0oSy1cwtEE0V/1QIBVNDz0dBOHn9VNxVO4Tm2WVnJffch717UAeJ6iWFIMj2hyeU0yrUV8W4vhilPjbLhGIdALLgFYHx5+tklMd8bhSX6PuXz3U4jf4w7prEO+oCiXFSCzF9cvOLdhoNeT/3R3+OKFB59uZoNVCyg1KQIUMqNavmfu92RrrbhkCe0iYMEaeQhKywM0YEW8mLa3y+f7X1xKZUVD1E68ACxEw5alFylzwz0trLfbYG2G1YcnF63tgJYm2QUAkqLaTsjkNImUI3Xilz/cqhFD7Ll1jkjYEkSwBxTVXDo89kIjH38Z5uffZfllZqWSkqDWIiiFeCQatTRELN/8GJL8H7VXhm02zNPd6YOtJyBABA489UKjmGu9VQqSmmJZUf57G4JBKyM7oTFqUVqx27H9NDUYbrtyiJC2YAnEZUJYwIN7n2iWXG5U3Ya93QZBIeD0QHQViCwNWEaGbqdcSjL7TD4hFRB8YgUIGim9730aolCZlYb2fjBFcPoguhI0bgzhRUCFAUPht89J554Vr6ABM6UCFPR1ewznLcP+SnQNXA3GgG4E1cCYjDKcS8u9oa/bBwUwFQT0dvuUyppsNgsqCk4D46dEJpORMt3b6TMxaOphoafDxzeKVCoLlAhmhFQ6L+bsmmoCgM52g6MhnshLkEDMMIlEAddRdLb5YKfSCrS3GKIRiMULYHIEYrLEEuXqWCt1YKqloLmpVvksQ/EyeBkC8VLVMZ6MbW60U2kFgMaoob3NyMVtJUUA8lss4cvYhuhUXIFw2MrdLZ40VMoJApDf4ilkbCQ08SvgUQfXRQpLKgPlYrCAUvW3VEZJ4XJcJgZPA39MhEwRkMwoctnvA8qbRyH/I7m8kiKEZmL4wwVeAbanDnPM7DGUCPPc00+y08Cl6MZFQUUBA6aMKbzLm6+9QCobrh5Mckwkr9Q9lgsKfhty2efEHj75MsQqy4wy86DGdR0AKhWfn371eefjCCsvXeLykxO0tZp6HpBjeb3G5D8Ucsh44Kmm6o0pQiqj5Uzg++A40NVhWHWZIlusNyKHUixA/cZkgq1ZUItmPDmIYixYA0pDyLU4oaC2LLg1m+HN6Qxvz/8EPBxYA9rrfA8AAAAASUVORK5CYII="
			alt=""
		/>
	</a>
</div>

<style>
	.home-btn {
		text-decoration: none;
	}

	.engine-status {
		display: flex;
		align-items: center;
	}

	.filename-bar {
		position: fixed;
		top: 0;
		left: 50%;
		transform: translateX(-50%);
		z-index: 30;
		display: flex;
		align-items: center;
		gap: 0;
		padding: 18px 16px;
	}

	.filepath-display {
		border: none;
		background: transparent;
		color: var(--nb-text-muted);
		font-family: 'Fira Code', 'Cascadia Code', monospace;
		font-size: 12px;
		text-align: center;
		cursor: pointer;
		padding: 4px 8px;
		border-radius: 6px;
		transition: all 0.15s ease;
		max-width: 400px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.filepath-display:hover {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.filepath-input {
		border: none;
		background: var(--nb-card);
		color: var(--nb-text);
		font-family: 'Fira Code', 'Cascadia Code', monospace;
		font-size: 12px;
		text-align: center;
		outline: none;
		min-width: 200px;
		width: 360px;
		padding: 4px 8px;
		border-radius: 6px;
		box-shadow: 0 0 0 1px var(--nb-pink);
	}

	.status-badge {
		font-size: 11px;
		font-weight: 600;
		padding: 2px 8px;
		border-radius: 10px;
		white-space: nowrap;
	}

	.status-badge.loading {
		color: var(--nb-pink);
		background: var(--nb-pink-subtle);
	}

	.status-badge.running {
		color: var(--nb-pink);
		background: var(--nb-pink-subtle);
		animation: pulse-badge 1s ease-in-out infinite;
	}

	.status-badge.error {
		color: var(--nb-error);
		background: rgba(239, 68, 68, 0.1);
	}

	@keyframes pulse-badge {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.floating-controls {
		position: fixed;
		z-index: 30;
		display: flex;
		gap: 6px;
	}

	.floating-controls.top-right {
		top: 12px;
		right: 16px;
	}

	.floating-controls.bottom-right {
		bottom: 16px;
		right: 16px;
	}

	.floating-controls.bottom-left {
		bottom: 16px;
		left: 16px;
	}

	.float-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		border: 1px solid var(--nb-border);
		border-radius: 50%;
		background: var(--nb-card);
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.15s ease;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.float-btn:hover {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
	}

	.float-btn.accent {
		background: var(--nb-pink);
		border-color: var(--nb-pink);
		color: #fff;
	}

	.float-btn.accent:hover {
		background: var(--nb-pink-bright);
		border-color: var(--nb-pink-bright);
		color: #fff;
		box-shadow: 0 2px 16px var(--nb-pink-dim);
	}

	.float-btn.accent :global(.double-play) {
		margin-left: -10px;
	}

	.dropdown-menu {
		position: absolute;
		top: 100%;
		right: 0;
		margin-top: 6px;
		background: var(--nb-card);
		border: 1px solid var(--nb-border);
		border-radius: 10px;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
		padding: 4px;
		min-width: 200px;
		white-space: nowrap;
	}

	.dropdown-item {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
		padding: 8px 12px;
		border: none;
		border-radius: 6px;
		background: transparent;
		color: var(--nb-text-secondary);
		font-size: 13px;
		cursor: pointer;
		transition: all 0.1s ease;
	}

	.dropdown-item:hover {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.dropdown-divider {
		height: 1px;
		background: var(--nb-border);
		margin: 4px 8px;
	}

	.width-toggle {
		display: flex;
		align-items: center;
		background: var(--nb-card);
		border: 1px solid var(--nb-border);
		border-radius: 10px;
		padding: 2px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.width-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border: none;
		border-radius: 8px;
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		transition: all 0.15s ease;
	}

	.width-btn:hover {
		color: var(--nb-text);
	}

	.width-btn.active {
		background: var(--nb-pink-subtle);
		color: var(--nb-pink);
	}

	.float-btn.layout-active {
		background: var(--nb-pink-subtle);
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.float-btn.layout-active:hover {
		background: var(--nb-pink-dim);
		border-color: var(--nb-pink-bright);
		color: var(--nb-pink-bright);
	}

	.float-btn.reactive-on {
		background: rgba(250, 204, 21, 0.15);
		border-color: #facc15;
		color: #facc15;
	}

	.float-btn.reactive-on:hover {
		background: rgba(250, 204, 21, 0.25);
		border-color: #fbbf24;
		color: #fbbf24;
	}

	.user-btn {
		padding: 0;
		overflow: hidden;
	}

	.user-avatar {
		width: 100%;
		height: 100%;
		object-fit: cover;
		border-radius: 50%;
	}

	.login-btn {
		color: var(--nb-text-muted);
	}

	.login-btn:hover {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.float-btn.cloud-saving {
		color: var(--nb-pink);
	}

	.float-btn.cloud-saved {
		background: rgba(34, 197, 94, 0.15);
		border-color: #22c55e;
		color: #22c55e;
	}

	.float-btn :global(.spin-slow) {
		animation: spin-slow 1.5s linear infinite;
	}

	.float-btn :global(.spin) {
		animation: spin-slow 0.8s linear infinite;
	}

	@keyframes spin-slow {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.coffee-btn {
		text-decoration: none;
		padding: 0;
		overflow: hidden;
	}

	.coffee-icon {
		width: 20px;
		height: 20px;
		border-radius: 50%;
		filter: grayscale(100%) opacity(0.5);
		transition: filter 0.15s ease;
	}

	.coffee-btn:hover .coffee-icon {
		filter: grayscale(0%) opacity(1);
	}

	@media (max-width: 640px) {
		.layout-toggle {
			display: none !important;
		}

		.floating-controls.bottom-left {
			display: none !important;
		}
	}
</style>
