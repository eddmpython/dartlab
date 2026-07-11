<script lang="ts">
	// 마크다운셀은 사용자 입력(untrusted)이라 반드시 정화해 렌더한다. 옛 코드는 marked.parse 를
	// sanitize 없이 {@html} 로 흘려 공유 노트북 임포트 시 stored-XSS 구멍이었다.
	import { renderRichMarkdown } from '../markdown/richMarkdown';

	interface Props {
		content: string;
		isActive: boolean;
		isEditing: boolean;
		onContentChange: (content: string) => void;
		onStartEdit: () => void;
		onStopEdit: () => void;
		onShiftEnter: () => void;
	}

	let { content, isActive, isEditing, onContentChange, onStartEdit, onStopEdit, onShiftEnter }: Props = $props();

	let textareaEl: HTMLTextAreaElement | null = null;

	const renderedHtml = $derived(renderRichMarkdown(content || '*Empty markdown cell*'));

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onStopEdit();
		}
		if (e.shiftKey && e.key === 'Enter') {
			e.preventDefault();
			onStopEdit();
			onShiftEnter();
		}
	}

	function handleInput(e: Event) {
		const target = e.target as HTMLTextAreaElement;
		onContentChange(target.value);
		autoResize(target);
	}

	function autoResize(el: HTMLTextAreaElement) {
		el.style.height = 'auto';
		el.style.height = el.scrollHeight + 'px';
	}

	$effect(() => {
		if (isEditing && textareaEl) {
			textareaEl.focus();
			autoResize(textareaEl);
		}
	});
</script>

<div
	class="markdown-cell"
	class:active={isActive}
>
	{#if isEditing}
		<textarea
			bind:this={textareaEl}
			value={content}
			oninput={handleInput}
			onkeydown={handleKeydown}
			onblur={onStopEdit}
			class="markdown-editor"
			placeholder="Enter markdown..."
		></textarea>
	{:else}
		<div
			class="markdown-preview"
			ondblclick={onStartEdit}
			role="textbox"
			tabindex="0"
			onkeydown={(e) => e.key === 'Enter' && onStartEdit()}
		>
			{@html renderedHtml}
		</div>
	{/if}
</div>

<style>
	.markdown-cell {
		transition: border-color 0.15s ease;
	}

	.markdown-preview {
		padding: 12px 16px;
		color: var(--nb-text);
		cursor: text;
		min-height: 32px;
		line-height: 1.7;
	}

	.markdown-preview :global(h1) {
		font-size: 1.5rem;
		font-weight: 700;
		margin-bottom: 0.5rem;
		color: var(--nb-text);
	}

	.markdown-preview :global(h2) {
		font-size: 1.25rem;
		font-weight: 600;
		margin-bottom: 0.4rem;
		color: var(--nb-text);
	}

	.markdown-preview :global(h3) {
		font-size: 1.1rem;
		font-weight: 600;
		margin-bottom: 0.3rem;
		color: var(--nb-text);
	}

	.markdown-preview :global(p) {
		margin-bottom: 0.5rem;
	}

	.markdown-preview :global(code) {
		background: var(--nb-code-bg);
		padding: 2px 6px;
		border-radius: 4px;
		font-size: 0.875rem;
		color: var(--nb-pink);
	}

	.markdown-preview :global(pre code) {
		display: block;
		padding: 12px;
		overflow-x: auto;
		color: var(--nb-text);
	}

	.markdown-preview :global(blockquote) {
		border-left: 3px solid var(--nb-pink);
		padding-left: 12px;
		color: var(--nb-text-secondary);
		margin: 8px 0;
	}

	.markdown-preview :global(ul),
	.markdown-preview :global(ol) {
		padding-left: 1.5rem;
		margin-bottom: 0.5rem;
	}

	.markdown-preview :global(table) {
		width: 100%;
		border-collapse: collapse;
		margin: 8px 0;
	}

	.markdown-preview :global(th),
	.markdown-preview :global(td) {
		border: 1px solid var(--nb-border);
		padding: 6px 12px;
		text-align: left;
	}

	.markdown-preview :global(th) {
		background: var(--nb-surface);
		font-weight: 600;
	}

	/* 임베드: 유튜브 16:9 반응형, 영상, 반응형 이미지. 블로그 아티클과 같은 결. */
	.markdown-preview :global(.rm-embed) {
		margin: 12px 0;
		border-radius: 8px;
		overflow: hidden;
	}
	.markdown-preview :global(.rm-youtube) {
		position: relative;
		width: 100%;
		aspect-ratio: 16 / 9;
		background: #000;
	}
	.markdown-preview :global(.rm-youtube iframe) {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		border: 0;
	}
	.markdown-preview :global(.rm-video video) {
		width: 100%;
		display: block;
		border-radius: 8px;
	}
	.markdown-preview :global(.rm-figure) {
		margin: 12px 0;
	}
	.markdown-preview :global(.rm-img) {
		max-width: 100%;
		height: auto;
		border-radius: 8px;
		display: block;
	}
	.markdown-preview :global(.rm-figure figcaption) {
		font-size: 0.8rem;
		color: var(--nb-text-secondary);
		margin-top: 4px;
		text-align: center;
	}
	.markdown-preview :global(.rm-embed-err) {
		color: var(--nb-pink);
		font-size: 0.85rem;
	}

	.markdown-editor {
		width: 100%;
		min-height: 80px;
		padding: 12px 16px;
		background: var(--nb-surface);
		border: none;
		color: var(--nb-text);
		font-family: var(--dl-font-mono);
		font-size: 14px;
		line-height: 1.6;
		resize: none;
		outline: none;
	}
</style>
