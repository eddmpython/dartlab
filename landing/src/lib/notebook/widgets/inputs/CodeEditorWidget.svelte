<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const label = $derived((config.label as string) || '');
	const language = $derived((config.language as string) || 'python');
	const placeholder = $derived((config.placeholder as string) || '');
	const minLines = $derived(Number(config.min_lines ?? 6));
	const maxLines = $derived(Number(config.max_lines ?? 20));
	const fullWidth = $derived(config.full_width !== false);

	const codeValue = $derived(String(value ?? ''));
	const lineCount = $derived(Math.max(minLines, Math.min(maxLines, (codeValue.match(/\n/g) || []).length + 2)));

	function handleInput(e: Event) {
		onChange((e.target as HTMLTextAreaElement).value);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Tab') {
			e.preventDefault();
			const ta = e.target as HTMLTextAreaElement;
			const start = ta.selectionStart;
			const end = ta.selectionEnd;
			const val = ta.value;
			ta.value = val.slice(0, start) + '    ' + val.slice(end);
			ta.selectionStart = ta.selectionEnd = start + 4;
			onChange(ta.value);
		}
	}
</script>

<div class="code-editor-widget" class:full-width={fullWidth}>
	{#if label}
		<div class="widget-header">
			<span class="widget-label">{label}</span>
			<span class="lang-tag">{language}</span>
		</div>
	{:else}
		<div class="widget-header">
			<span class="lang-tag">{language}</span>
		</div>
	{/if}
	<textarea
		class="code-textarea"
		rows={lineCount}
		value={codeValue}
		placeholder={placeholder}
		oninput={handleInput}
		onkeydown={handleKeydown}
		spellcheck="false"
		autocomplete="off"
		autocapitalize="off"
	></textarea>
</div>

<style>
	.code-editor-widget {
		display: inline-flex;
		flex-direction: column;
		gap: 4px;
		min-width: 300px;
	}

	.code-editor-widget.full-width {
		width: 100%;
	}

	.widget-header {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.lang-tag {
		font-size: 10px;
		padding: 1px 6px;
		border-radius: 4px;
		background: var(--nb-surface);
		color: var(--nb-text-muted);
		font-family: var(--dl-font-mono);
		text-transform: lowercase;
	}

	.code-textarea {
		width: 100%;
		padding: 10px 12px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-code-bg, #18181b);
		color: var(--nb-text);
		font-family: var(--dl-font-mono);
		font-size: 13px;
		line-height: 1.5;
		resize: vertical;
		outline: none;
		tab-size: 4;
		white-space: pre;
		overflow-wrap: normal;
		overflow-x: auto;
		transition: border-color 0.15s ease;
	}

	.code-textarea:focus {
		border-color: var(--nb-pink);
	}

	.code-textarea::placeholder {
		color: var(--nb-text-muted);
		opacity: 0.5;
	}
</style>
