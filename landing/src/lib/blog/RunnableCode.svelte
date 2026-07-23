<script lang="ts">
	// dartlab 이야기 본문의 Python 코드펜스를 편집 가능한 노트북 셀로 보여 준다.
	// 글의 코드펜스가 원본이고, 편집값은 현재 페이지의 커널에서만 실행한다.
	import { ExternalLink, Loader2, Play, RotateCcw } from 'lucide-svelte';
	import {
		runSnippet,
		prewarmEngine,
		engineStatus
	} from '$lib/notebook/stores/executionStore';
	import type { CellOutput } from '$lib/notebook/engine/executionEngine';
	import CodeCell from '$lib/notebook/components/CodeCell.svelte';
	import OutputPanel from '$lib/notebook/components/OutputPanel.svelte';

	interface Props {
		code: string;
		/** 현재 셀보다 위에 있는 편집값을 실행 시점에 읽는다. */
		getPrereq?: () => string[];
		/** 페이지가 관리하는 셀 값도 함께 갱신한다. */
		onCodeChange?: (code: string) => void;
		/** 글 전체를 노트북 편집 화면에서 연다. 첫 셀에만 붙인다. */
		onOpenNotebook?: () => void;
	}

	let { code, getPrereq = () => [], onCodeChange, onOpenNotebook }: Props = $props();
	// svelte-ignore state_referenced_locally
	let editableCode = $state(code);
	let output = $state<CellOutput | undefined>(undefined);
	let running = $state(false);
	let active = $state(false);

	const dirty = $derived(editableCode !== code);
	const downloading = $derived(running && $engineStatus === 'loading');

	function updateCode(value: string) {
		editableCode = value;
		output = undefined;
		onCodeChange?.(value);
	}

	function resetCode() {
		updateCode(code);
	}

	async function run() {
		if (running) return;
		running = true;
		output = undefined;
		try {
			output = await runSnippet(editableCode, getPrereq());
		} finally {
			running = false;
		}
	}
</script>

<section
	class="blog-cell"
	data-testid="blog-notebook-cell"
	onfocusin={() => (active = true)}
	onfocusout={() => (active = false)}
>
	<header class="blog-cell-header">
		<div class="blog-cell-kind">
			<span class="blog-cell-dot"></span>
			<span>Python 셀</span>
			<span class="blog-cell-hint">직접 수정하고 실행할 수 있습니다</span>
		</div>
		<div class="blog-cell-actions">
			{#if dirty}
				<button class="blog-cell-action" onclick={resetCode} aria-label="원본 코드로 되돌리기">
					<RotateCcw size={13} /> 원본
				</button>
			{/if}
			{#if onOpenNotebook}
				<button class="blog-cell-action" onclick={onOpenNotebook} onpointerenter={prewarmEngine}>
					<ExternalLink size={13} /> 전체 화면
				</button>
			{/if}
		</div>
	</header>

	<div class="blog-cell-body">
		<button
			class="blog-cell-run"
			data-testid="blog-cell-run"
			onclick={run}
			onpointerenter={prewarmEngine}
			disabled={running}
			aria-label={running ? 'Python 셀 실행 중' : 'Python 셀 실행'}
		>
			{#if running}
				<Loader2 size={15} class="blog-cell-spin" />
			{:else}
				<Play size={15} />
			{/if}
		</button>
		<div class="blog-cell-editor">
			<CodeCell
				content={editableCode}
				isActive={active}
				isRunning={running}
				onContentChange={updateCode}
				onRun={run}
				onRunAndMove={run}
			/>
		</div>
	</div>

	{#if downloading}
		<p class="blog-cell-note">처음 실행할 때는 파이썬과 dartlab을 내려받느라 잠시 걸립니다.</p>
	{/if}

	{#if output}
		<div class="blog-cell-output" data-testid="blog-cell-output">
			<OutputPanel {output} />
		</div>
	{/if}
</section>

<style>
	.blog-cell {
		--nb-bg: var(--dl-bg-deep);
		--nb-surface: var(--dl-bg-base);
		--nb-card: var(--dl-bg-raised);
		--nb-border: var(--dl-line-strong);
		--nb-text: var(--dl-ink);
		--nb-text-secondary: var(--dl-ink-mute);
		--nb-text-muted: var(--dl-ink-dim);
		--nb-success: var(--dl-good);
		--nb-error: var(--dl-bad);

		margin: 1.25rem 0 1.75rem;
		border: 1px solid var(--nb-border);
		border-radius: 12px;
		background: var(--nb-card);
		box-shadow: 0 16px 34px rgba(3, 5, 9, 0.18);
		overflow: hidden;
		transition: border-color 0.15s ease, box-shadow 0.15s ease;
	}

	.blog-cell:focus-within {
		border-color: rgba(var(--dl-accent-rgb), 0.55);
		box-shadow: 0 18px 38px rgba(3, 5, 9, 0.24), 0 0 0 1px rgba(var(--dl-accent-rgb), 0.08);
	}

	.blog-cell-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		min-height: 34px;
		padding: 5px 9px 5px 12px;
		border-bottom: 1px solid var(--nb-border);
		background: color-mix(in srgb, var(--nb-card) 88%, var(--dl-bg-base));
		font-family: var(--dl-font-ui);
	}

	.blog-cell-kind,
	.blog-cell-actions,
	.blog-cell-action {
		display: flex;
		align-items: center;
	}

	.blog-cell-kind {
		gap: 7px;
		color: var(--nb-text-secondary);
		font-size: 11.5px;
		font-weight: 650;
	}

	.blog-cell-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--dl-accent);
		box-shadow: 0 0 0 3px rgba(var(--dl-accent-rgb), 0.12);
	}

	.blog-cell-hint {
		color: var(--nb-text-muted);
		font-weight: 450;
	}

	.blog-cell-actions {
		gap: 4px;
	}

	.blog-cell-action {
		gap: 5px;
		padding: 4px 7px;
		border: 0;
		border-radius: 6px;
		background: transparent;
		color: var(--nb-text-muted);
		font-family: var(--dl-font-ui);
		font-size: 11.5px;
		cursor: pointer;
	}

	.blog-cell-action:hover {
		background: rgba(var(--dl-accent-rgb), 0.09);
		color: var(--dl-accent);
	}

	.blog-cell-body {
		display: grid;
		grid-template-columns: 42px minmax(0, 1fr);
		min-height: 68px;
		background: var(--nb-surface);
	}

	.blog-cell-run {
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding: 14px 0 0;
		border: 0;
		border-right: 1px solid var(--nb-border);
		background: color-mix(in srgb, var(--nb-card) 88%, transparent);
		color: var(--dl-accent);
		cursor: pointer;
	}

	.blog-cell-run:hover:not(:disabled) {
		background: rgba(var(--dl-accent-rgb), 0.09);
	}

	.blog-cell-run:disabled {
		cursor: default;
		opacity: 0.75;
	}

	.blog-cell-editor {
		min-width: 0;
		padding: 3px 0;
	}

	.blog-cell-note {
		margin: 0;
		padding: 7px 12px;
		border-top: 1px solid var(--nb-border);
		color: var(--nb-text-muted);
		font-family: var(--dl-font-ui);
		font-size: 11.5px;
	}

	.blog-cell-output {
		border-top: 1px solid var(--nb-border);
		background: var(--nb-bg);
		overflow-x: auto;
	}

	.blog-cell-output :global(.output-panel) {
		border-top: 0;
	}

	.blog-cell :global(.blog-cell-spin) {
		animation: blog-cell-spin 0.9s linear infinite;
	}

	@keyframes blog-cell-spin {
		to {
			transform: rotate(360deg);
		}
	}

	@media (max-width: 640px) {
		.blog-cell-hint {
			display: none;
		}

		.blog-cell-action {
			font-size: 0;
		}

		.blog-cell-action :global(svg) {
			width: 15px;
			height: 15px;
		}

		.blog-cell-body {
			grid-template-columns: 36px minmax(0, 1fr);
		}
	}
</style>
