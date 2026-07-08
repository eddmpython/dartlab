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
	import GithubIcon from '$lib/components/GithubIcon.svelte';
	// SNS·브랜드테마 = dartlab 공통 SSOT(surfaces). 터미널·랜딩 Header 와 동일 컨트롤 공유.
	import { DARTLAB_BRAND_LINKS, BrandSwitch } from '@dartlab/ui-surfaces/terminal';
	import {
		notebook,
		resetNotebook,
		cellWidth,
		setCellWidth,
		loadNotebook,
		setTitle,
		studyMode
	} from '../stores/notebookStore';
	import {
		engineStatus,
		executeAllCells,
		destroyEngine,
		reactiveMode
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
			<button class="filepath-display" onclick={startPathEdit} title="제목 편집">
				{$notebook.title || 'Untitled'}
			</button>
		{/if}
	</div>
{/if}

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

	<BrandSwitch />

	<a class="hdr-btn" href={DARTLAB_BRAND_LINKS.repo} target="_blank" rel="noopener" title="GitHub">
		<GithubIcon class="ic" />
	</a>
	<a
		class="hdr-btn sns-lg"
		href={DARTLAB_BRAND_LINKS.youtube}
		target="_blank"
		rel="noopener"
		title="YouTube"
	>
		<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true">
			<path
				d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"
			/>
		</svg>
	</a>
	<a
		class="hdr-btn sns-lg"
		href={DARTLAB_BRAND_LINKS.threads}
		target="_blank"
		rel="noopener"
		title="Threads"
	>
		<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true">
			<path
				d="M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.472 12.01v-.017c.03-3.579.879-6.43 2.525-8.482C5.845 1.205 8.6.024 12.18 0h.014c2.746.02 5.043.725 6.826 2.098 1.677 1.29 2.858 3.13 3.509 5.467l-2.04.569c-1.104-3.96-3.898-5.984-8.304-6.015-2.91.022-5.11.936-6.54 2.717C4.307 6.504 3.616 8.914 3.589 12c.027 3.086.718 5.496 2.057 7.164 1.43 1.783 3.631 2.698 6.54 2.717 2.623-.02 4.358-.631 5.8-2.045 1.647-1.613 1.618-3.593 1.09-4.798-.31-.71-.873-1.3-1.634-1.75-.192 1.352-.622 2.446-1.284 3.272-.886 1.102-2.14 1.704-3.73 1.79-1.202.065-2.361-.218-3.259-.801-1.063-.689-1.685-1.74-1.752-2.964-.065-1.19.408-2.285 1.33-3.082.88-.76 2.119-1.207 3.583-1.291a13.853 13.853 0 0 1 3.02.142c-.126-.742-.375-1.332-.75-1.757-.513-.586-1.308-.883-2.359-.89h-.029c-.844 0-1.992.232-2.721 1.32L7.734 7.847c.98-1.454 2.568-2.256 4.478-2.256h.044c3.194.02 5.097 1.975 5.287 5.388.108.046.216.094.321.142 1.49.7 2.58 1.761 3.154 3.07.797 1.82.871 4.79-1.548 7.158-1.85 1.81-4.094 2.628-7.277 2.65Z"
			/>
		</svg>
	</a>
	<a
		class="hdr-btn sns-lg"
		href={DARTLAB_BRAND_LINKS.instagram}
		target="_blank"
		rel="noopener"
		title="Instagram"
	>
		<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true">
			<path
				d="M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 1.381.164.422.36 1.057.413 2.227.057 1.266.07 1.646.07 4.85s-.015 3.585-.074 4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.413-1.274.057-1.649.07-4.859.07-3.211 0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.165-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 0-3.196.016-3.586.061-4.861.061-1.17.255-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06zm0 3.678c-3.405 0-6.162 2.76-6.162 6.162 0 3.405 2.76 6.162 6.162 6.162 3.405 0 6.162-2.76 6.162-6.162 0-3.405-2.76-6.162-6.162-6.162zM12 16c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm7.846-10.405c0 .795-.646 1.44-1.44 1.44-.795 0-1.44-.646-1.44-1.44 0-.794.646-1.439 1.44-1.439.793-.001 1.44.645 1.44 1.439z"
			/>
		</svg>
	</a>
</div>

<!-- 좌하단: 셀 폭 토글 -->
{#if !$studyMode}
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
{/if}

<!-- 우하단: 반응형 토글 + 모두 실행 -->
<div class="floating-controls bottom-right">
	<button
		class="float-btn"
		class:reactive-on={$reactiveMode}
		onclick={() => reactiveMode.update((v) => !v)}
		title={$reactiveMode ? '반응형 실행 ON' : '반응형 실행 OFF'}
		aria-label="반응형 실행 토글"
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
		.brand-word,
		.sns-lg {
			display: none;
		}
		.floating-controls.bottom-left {
			display: none;
		}
	}
</style>
