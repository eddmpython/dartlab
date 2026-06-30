<script lang="ts">
	/**
	 * Markdown 셀 · 가벼운 inline render.
	 *
	 * mdsvex 는 build-time 처리라 runtime 동적 변환에는 직접 사용 불가.
	 * 대신 매우 단순한 markdown subset (제목·목록·코드·강조·링크) 자체 변환.
	 * 셀 contents 는 사용자가 자기 메모.
	 */
	import { FileText, Eye, Pencil, X } from 'lucide-svelte';

	interface Props {
		id: string;
		code: string;
		onCodeChange: (id: string, code: string) => void;
		onDelete: (id: string) => void;
	}

	let { id, code, onCodeChange, onDelete }: Props = $props();
	let editing = $state(true);

	function escapeHtml(s: string): string {
		return s
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '&#39;');
	}

	function renderMd(src: string): string {
		const lines = src.split('\n');
		const out: string[] = [];
		let inList = false;
		let inCode = false;
		const codeLines: string[] = [];
		for (const line of lines) {
			if (line.startsWith('```')) {
				if (inCode) {
					out.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
					codeLines.length = 0;
					inCode = false;
				} else {
					inCode = true;
				}
				continue;
			}
			if (inCode) {
				codeLines.push(line);
				continue;
			}
			if (line.startsWith('### ')) {
				if (inList) {
					out.push('</ul>');
					inList = false;
				}
				out.push(`<h3>${escapeHtml(line.slice(4))}</h3>`);
			} else if (line.startsWith('## ')) {
				if (inList) {
					out.push('</ul>');
					inList = false;
				}
				out.push(`<h2>${escapeHtml(line.slice(3))}</h2>`);
			} else if (line.startsWith('# ')) {
				if (inList) {
					out.push('</ul>');
					inList = false;
				}
				out.push(`<h1>${escapeHtml(line.slice(2))}</h1>`);
			} else if (line.startsWith('- ') || line.startsWith('* ')) {
				if (!inList) {
					out.push('<ul>');
					inList = true;
				}
				out.push(`<li>${inlineMd(escapeHtml(line.slice(2)))}</li>`);
			} else if (line.trim() === '') {
				if (inList) {
					out.push('</ul>');
					inList = false;
				}
			} else {
				if (inList) {
					out.push('</ul>');
					inList = false;
				}
				out.push(`<p>${inlineMd(escapeHtml(line))}</p>`);
			}
		}
		if (inList) out.push('</ul>');
		if (inCode && codeLines.length > 0) {
			out.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
		}
		return out.join('\n');
	}

	function inlineMd(s: string): string {
		// **bold**, *italic*, `code`, [link](url)
		return s
			.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
			.replace(/\*([^*]+)\*/g, '<em>$1</em>')
			.replace(/`([^`]+)`/g, '<code>$1</code>')
			.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
	}

	let rendered = $derived(renderMd(code));
</script>

<div class="cell md-cell">
	<div class="cell-head">
		<span class="cell-id">
			<FileText size={11} />
			<span>markdown</span>
		</span>
		<div class="cell-actions">
			<button type="button" class="cell-icon-btn" onclick={() => (editing = !editing)} title="편집/미리보기 토글">
				{#if editing}
					<Eye size={11} />
				{:else}
					<Pencil size={11} />
				{/if}
			</button>
			<button type="button" class="cell-icon-btn delete" onclick={() => onDelete(id)} title="셀 삭제">
				<X size={11} />
			</button>
		</div>
	</div>

	{#if editing}
		<textarea
			class="md-textarea"
			value={code}
			oninput={(e) => onCodeChange(id, (e.target as HTMLTextAreaElement).value)}
			placeholder="# 제목&#10;**굵게** *기울이기* `code`&#10;- 목록"
			spellcheck={false}
			rows={4}
		></textarea>
	{:else}
		<div class="md-rendered">{@html rendered}</div>
	{/if}
</div>

<style>
	.cell {
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
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
	.cell-id {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		font-family: monospace;
		font-size: 10px;
		color: #64748b;
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

	.md-textarea {
		width: 100%;
		padding: 10px 14px;
		background: #050811;
		border: none;
		color: #cbd5e1;
		font-family: 'JetBrains Mono', monospace;
		font-size: 12px;
		line-height: 1.6;
		resize: vertical;
	}
	.md-textarea:focus {
		outline: none;
		background: #0a0e18;
	}

	.md-rendered {
		padding: 12px 16px;
		font-size: 13px;
		line-height: 1.6;
		color: #cbd5e1;
	}
	.md-rendered :global(h1) {
		font-size: 18px;
		font-weight: 700;
		color: #f1f5f9;
		margin: 8px 0 6px;
	}
	.md-rendered :global(h2) {
		font-size: 15px;
		font-weight: 600;
		color: #f1f5f9;
		margin: 8px 0 4px;
	}
	.md-rendered :global(h3) {
		font-size: 13px;
		font-weight: 600;
		color: #cbd5e1;
		margin: 6px 0 4px;
	}
	.md-rendered :global(p) {
		margin: 4px 0;
	}
	.md-rendered :global(ul) {
		margin: 4px 0 4px 20px;
	}
	.md-rendered :global(li) {
		margin: 2px 0;
	}
	.md-rendered :global(code) {
		font-family: 'JetBrains Mono', monospace;
		font-size: 11px;
		padding: 1px 5px;
		background: #1e2433;
		border-radius: 3px;
		color: var(--amber);
	}
	.md-rendered :global(pre) {
		background: #0a0e18;
		border: 1px solid #1e2433;
		border-radius: 4px;
		padding: 8px 12px;
		overflow-x: auto;
		font-size: 11px;
		font-family: 'JetBrains Mono', monospace;
	}
	.md-rendered :global(pre code) {
		background: transparent;
		padding: 0;
		color: #cbd5e1;
	}
	.md-rendered :global(a) {
		color: #60a5fa;
		text-decoration: none;
	}
	.md-rendered :global(a:hover) {
		text-decoration: underline;
	}
	.md-rendered :global(strong) {
		font-weight: 600;
		color: #f1f5f9;
	}
	.md-rendered :global(em) {
		font-style: italic;
		color: #cbd5e1;
	}
</style>
