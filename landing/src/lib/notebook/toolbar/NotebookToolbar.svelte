<script lang="ts">
	import { base } from '$app/paths';
	import { tick } from 'svelte';
	import {
		Sun,
		Moon,
		Play,
		Download,
		FilePlus,
		Settings,
		AlignCenter,
		AlignJustify,
		Maximize,
		Zap,
		Upload,
		FileCode,
		FileSpreadsheet,
		Loader2
	} from 'lucide-svelte';
	import { themePref, toggleTheme } from '$lib/theme';
	// SNS·후원·브랜드테마 = dartlab 공통 SSOT(surfaces). 터미널·카드·랜딩 Header 와 동일 컨트롤 공유.
	import {
		DARTLAB_BRAND_LINKS,
		BrandSwitch,
		BrandSocial,
		SupportDialog,
		fetchGithubStars
	} from '@dartlab/ui-surfaces/terminal';
	import {
		notebook,
		resetNotebook,
		cellWidth,
		setCellWidth,
		loadNotebook,
		setTitle,
		setDescription
	} from '../stores/notebookStore';
	import {
		engineStatus,
		executeAllCells,
		destroyEngine,
		reactiveMode,
		setReactiveMode
	} from '../stores/executionStore';
	import {
		downloadNotebook,
		downloadAsMarimoFile,
		importMarimoNotebook,
		downloadAsJupyterFile,
		importJupyterNotebook,
		openFileDialog,
		readFileAsText
	} from '../utils/notebookFormat';

	interface Props {
		homeHref?: string;
	}

	let { homeHref = '/' }: Props = $props();

	const links = DARTLAB_BRAND_LINKS;
	let ghStars = $state<number | null>(null);
	fetchGithubStars(links.repo).then((n) => (ghStars = n));
	let supportOpen = $state(false);

	let showMenu = $state(false);
	let pathEditing = $state(false);
	let pathDraft = $state('');

	function handleRunAll() {
		executeAllCells($notebook.cells);
	}
	function handleExport() {
		downloadNotebook($notebook);
		showMenu = false;
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

	async function startPathEdit() {
		pathEditing = true;
		pathDraft = $notebook.title;
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
		if (val && val !== $notebook.title) {
			setTitle(val);
		}
	}
	function handlePathKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			(e.target as HTMLInputElement).blur();
		} else if (e.key === 'Escape') {
			pathEditing = false;
			pathDraft = $notebook.title;
		}
	}
</script>

<!-- 좌상단: dartlab 아바타 + 홈 (브랜드 = 홈 링크) -->
<a class="brand" href={homeHref} data-sveltekit-reload title="dartlab">
	<picture>
		<source srcset="{base}/avatar.webp" type="image/webp" />
		<img src="{base}/avatar.png" alt="dartlab" width="24" height="24" class="brand-avatar" />
	</picture>
	<span class="brand-word">dartlab <span class="brand-sub">notebook</span></span>
</a>

<!-- 상단 중앙: 노트북 제목(클릭 편집) -->
	<div class="filename-bar">
		{#if pathEditing}
			<input
				class="filepath-input editing"
				bind:value={pathDraft}
				onblur={commitPath}
				onkeydown={handlePathKeydown}
			/>
		{:else}
			<button class="filepath-display" onclick={startPathEdit} title="제목 편집">
				{$notebook.title || 'Untitled'}
			</button>
		{/if}
	</div>

<!-- 우상단: SNS(터미널 동일) + 노트북 설정 + 테마 -->
<div class="top-right">
	{#if $engineStatus === 'loading' || $engineStatus === 'executing' || $engineStatus === 'error'}
		<span class="status-badge {$engineStatus}">
			{#if $engineStatus === 'loading'}Loading Pyodide...{:else if $engineStatus === 'executing'}Running...{:else}Error{/if}
		</span>
	{/if}

	<button
		class="hdr-btn"
		onclick={toggleTheme}
		title={$themePref === 'light' ? '다크 모드로' : '라이트 모드로'}
		aria-label="테마 전환"
	>
		{#if $themePref === 'light'}<Moon size={15} />{:else}<Sun size={15} />{/if}
	</button>

	<div class="menu-wrap">
		<button
			class="hdr-btn"
			onclick={() => (showMenu = !showMenu)}
			title="노트북 설정"
			aria-label="노트북 설정"
		>
			<Settings size={15} />
		</button>
		{#if showMenu}
			<div class="dropdown-menu">
				<div class="dropdown-meta">
					<label class="meta-label" for="nb-title-input">제목</label>
					<input
						id="nb-title-input"
						class="meta-input"
						value={$notebook.title}
						oninput={(e) => setTitle((e.currentTarget as HTMLInputElement).value)}
						placeholder="제목 없음"
					/>
					<label class="meta-label" for="nb-desc-input">설명</label>
					<textarea
						id="nb-desc-input"
						class="meta-textarea"
						value={$notebook.description ?? ''}
						oninput={(e) => setDescription((e.currentTarget as HTMLTextAreaElement).value)}
						placeholder="짧은 설명 (허브 카드에 표시)"
						rows="2"
					></textarea>
				</div>
				<div class="dropdown-divider"></div>
				<button class="dropdown-item" onclick={handleNew}>
					<FilePlus size={14} /> 새 노트북
				</button>
				<button class="dropdown-item" onclick={handleExport}>
					<Download size={14} /> Export .json
				</button>
				<div class="dropdown-divider"></div>
				<button class="dropdown-item" onclick={handleImportMarimo}>
					<Upload size={14} /> Import marimo .py
				</button>
				<button class="dropdown-item" onclick={handleExportMarimo}>
					<FileCode size={14} /> Export marimo .py
				</button>
				<div class="dropdown-divider"></div>
				<button class="dropdown-item" onclick={handleImportJupyter}>
					<Upload size={14} /> Import Jupyter .ipynb
				</button>
				<button class="dropdown-item" onclick={handleExportJupyter}>
					<FileSpreadsheet size={14} /> Export Jupyter .ipynb
				</button>
			</div>
		{/if}
	</div>

	<BrandSocial {links} {ghStars} onSupport={() => (supportOpen = true)}>
		{#snippet leading()}<BrandSwitch />{/snippet}
	</BrandSocial>
</div>

<SupportDialog lang="kr" {links} {base} open={supportOpen} onClose={() => (supportOpen = false)} />

<!-- 좌하단: 셀 폭 토글 -->
	<div class="floating-controls bottom-left">
		<div class="width-toggle">
			<button
				class="width-btn"
				class:active={$cellWidth === 'compact'}
				onclick={() => setCellWidth('compact')}
				title="Compact"
				aria-label="Compact"><AlignCenter size={14} /></button
			>
			<button
				class="width-btn"
				class:active={$cellWidth === 'medium'}
				onclick={() => setCellWidth('medium')}
				title="Medium"
				aria-label="Medium"><AlignJustify size={14} /></button
			>
			<button
				class="width-btn"
				class:active={$cellWidth === 'full'}
				onclick={() => setCellWidth('full')}
				title="Full width"
				aria-label="Full"><Maximize size={14} /></button
			>
		</div>
	</div>

<!-- 우하단: 반응형 토글 + 모두 실행 -->
<div class="floating-controls bottom-right">
	<button
		class="float-btn"
		class:reactive-on={$reactiveMode}
		onclick={() => setReactiveMode(!$reactiveMode, true)}
		title={$reactiveMode ? '반응형 실행 중 · 눌러서 순차 실행으로 전환' : '순차 실행 중 · 눌러서 반응형 실행으로 전환'}
		aria-label={$reactiveMode ? '반응형 실행 켜짐' : '순차 실행 켜짐'}
	>
		<Zap size={16} />
	</button>
	<button
		class="float-btn accent"
		onclick={handleRunAll}
		title="모두 실행 (Ctrl+Shift+Enter)"
		aria-label="모두 실행"
		disabled={$engineStatus === 'executing'}
	>
		{#if $engineStatus === 'executing'}
			<Loader2 size={16} class="spin" />
		{:else}
			<Play size={16} />
		{/if}
	</button>
</div>

<style>
	/* 좌상단 브랜드 (아바타 + 홈) */
	.brand {
		position: fixed;
		top: 12px;
		left: 16px;
		z-index: 40;
		display: flex;
		align-items: center;
		gap: 8px;
		text-decoration: none;
		padding: 4px 8px;
		border-radius: var(--dl-r-md);
		transition: background 0.15s ease;
	}
	.brand:hover {
		background: var(--nb-card);
	}
	.brand-avatar {
		width: 24px;
		height: 24px;
		border-radius: 50%;
	}
	.brand-word {
		font-size: 14px;
		font-weight: 600;
		letter-spacing: -0.01em;
		color: var(--nb-text);
		white-space: nowrap;
	}
	.brand-sub {
		color: var(--nb-pink);
		font-weight: 600;
	}

	.filename-bar {
		position: fixed;
		top: 0;
		left: 50%;
		transform: translateX(-50%);
		z-index: 30;
		display: flex;
		align-items: center;
		padding: 18px 16px;
	}
	.filepath-display {
		border: none;
		background: transparent;
		color: var(--nb-text-muted);
		font-family: var(--dl-font-mono);
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
		font-family: var(--dl-font-mono);
		font-size: 12px;
		text-align: center;
		outline: none;
		width: 360px;
		padding: 4px 8px;
		border-radius: 6px;
		box-shadow: 0 0 0 1px var(--nb-pink);
	}

	/* 우상단 헤더 클러스터 */
	.top-right {
		position: fixed;
		top: 12px;
		right: 16px;
		z-index: 40;
		display: flex;
		align-items: center;
		gap: 4px;
	}
	.hdr-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		border: none;
		border-radius: var(--dl-r-md);
		background: transparent;
		color: var(--nb-text-muted);
		cursor: pointer;
		text-decoration: none;
		transition: all 0.15s ease;
	}
	.hdr-btn:hover {
		color: var(--nb-text);
		background: var(--nb-card);
	}
	.hdr-btn :global(.ic) {
		width: 15px;
		height: 15px;
	}

	.status-badge {
		font-size: 11px;
		font-weight: 600;
		padding: 2px 8px;
		border-radius: 10px;
		white-space: nowrap;
		margin-right: 4px;
	}
	.status-badge.loading,
	.status-badge.executing {
		color: var(--nb-pink);
		background: var(--nb-pink-subtle);
	}
	.status-badge.executing {
		animation: pulse-badge 1s ease-in-out infinite;
	}
	.status-badge.error {
		color: var(--nb-error);
		background: rgba(239, 68, 68, 0.1);
	}
	@keyframes pulse-badge {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}

	.menu-wrap {
		position: relative;
	}
	.dropdown-menu {
		position: absolute;
		top: 100%;
		right: 0;
		margin-top: 6px;
		background: var(--nb-card);
		border: 1px solid var(--nb-border);
		border-radius: 10px;
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
		padding: 4px;
		/* 제목·설명 입력이 한 줄에 충분히 들어가는 폭. 248px 에선 설명 textarea 가 답답했다.
		   좁은 화면에서는 뷰포트를 넘지 않도록 상한을 둔다. */
		min-width: 340px;
		max-width: calc(100vw - 24px);
		white-space: nowrap;
	}
	.dropdown-meta {
		display: flex;
		flex-direction: column;
		gap: 3px;
		padding: 8px 10px 6px;
		white-space: normal;
	}
	.meta-label {
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--dl-ink-dim);
	}
	.meta-label:not(:first-child) {
		margin-top: 4px;
	}
	.meta-input,
	.meta-textarea {
		width: 100%;
		padding: 5px 8px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-surface);
		color: var(--nb-text);
		font-size: 12.5px;
		font-family: var(--dl-font-ui);
		outline: none;
		box-sizing: border-box;
	}
	.meta-textarea {
		resize: vertical;
		line-height: 1.4;
	}
	.meta-input:focus,
	.meta-textarea:focus {
		border-color: var(--dl-accent);
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

	.floating-controls {
		position: fixed;
		z-index: 30;
		display: flex;
		gap: 6px;
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
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
	}
	.float-btn:hover {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
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
	}
	.float-btn.reactive-on {
		background: var(--nb-pink-subtle);
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.width-toggle {
		display: flex;
		align-items: center;
		background: var(--nb-card);
		border: 1px solid var(--nb-border);
		border-radius: 10px;
		padding: 2px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
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

	.float-btn :global(.spin) {
		animation: spin-nb 0.8s linear infinite;
	}
	@keyframes spin-nb {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	@media (max-width: 640px) {
		.brand-word {
			display: none;
		}
		.floating-controls.bottom-left {
			display: none;
		}
	}
</style>
