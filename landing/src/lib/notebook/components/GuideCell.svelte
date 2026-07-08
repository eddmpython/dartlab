<script lang="ts">
	import type { GuideData } from '../stores/notebookStore';

	interface Props {
		guide: GuideData;
		isActive: boolean;
	}

	let { guide, isActive }: Props = $props();

	let showHints = $state<boolean[]>([]);
	let showAnswer = $state(false);

	$effect(() => {
		showHints = guide.hints.map(() => false);
	});

	function toggleHint(idx: number) {
		showHints = showHints.map((v, i) => (i === idx ? !v : v));
	}

	function toggleAnswer() {
		showAnswer = !showAnswer;
	}
</script>

<div class="guide-cell" class:active={isActive}>
	<div class="guide-header">
		<span class="guide-icon">&#9881;</span>
		<span class="guide-label">Mission</span>
	</div>

	<div class="guide-mission">
		{guide.mission}
	</div>

	{#if guide.expectedOutput}
		<div class="expected-output">
			<span class="expected-label">Expected output:</span>
			<code>{guide.expectedOutput}</code>
		</div>
	{/if}

	<div class="guide-actions">
		{#each guide.hints as hint, idx}
			<button class="hint-btn" onclick={() => toggleHint(idx)}>
				{showHints[idx] ? 'Hide' : 'Show'} Hint {idx + 1}
			</button>
			{#if showHints[idx]}
				<div class="hint-content">{hint}</div>
			{/if}
		{/each}

		{#if guide.answer}
			<button class="answer-btn" onclick={toggleAnswer}>
				{showAnswer ? 'Hide Answer' : 'Show Answer'}
			</button>
			{#if showAnswer}
				<pre class="answer-content">{guide.answer}</pre>
			{/if}
		{/if}
	</div>
</div>

<style>
	.guide-cell {
		border: 1px solid var(--nb-pink-dim);
		border-radius: var(--radius-md);
		background: var(--nb-pink-subtle);
		transition: border-color 0.15s ease;
	}

	.guide-cell.active {
		border-color: var(--nb-pink);
	}

	.guide-header {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 16px;
		border-bottom: 1px solid var(--nb-pink-dim);
	}

	.guide-icon {
		font-size: 16px;
	}

	.guide-label {
		font-size: 12px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--nb-pink);
	}

	.guide-mission {
		padding: 12px 16px;
		color: var(--nb-text);
		line-height: 1.6;
		font-size: 14px;
	}

	.expected-output {
		padding: 0 16px 8px;
		font-size: 13px;
		color: var(--nb-text-secondary);
	}

	.expected-output code {
		background: var(--nb-code-bg);
		padding: 2px 6px;
		border-radius: 4px;
		color: var(--nb-success);
		font-size: 12px;
	}

	.expected-label {
		margin-right: 6px;
	}

	.guide-actions {
		padding: 8px 16px 12px;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.hint-btn,
	.answer-btn {
		align-self: flex-start;
		padding: 4px 12px;
		border: 1px solid var(--nb-border);
		border-radius: var(--radius-sm);
		background: var(--nb-card);
		color: var(--nb-text-secondary);
		font-size: 12px;
		cursor: pointer;
		transition: all 0.15s ease;
	}

	.hint-btn:hover,
	.answer-btn:hover {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.hint-content {
		padding: 8px 12px;
		background: var(--nb-card);
		border-radius: var(--radius-sm);
		color: var(--nb-text-secondary);
		font-size: 13px;
		line-height: 1.5;
	}

	.answer-content {
		padding: 12px;
		background: var(--nb-code-bg);
		border-radius: var(--radius-sm);
		color: var(--nb-text);
		font-family: 'Fira Code', 'Cascadia Code', monospace;
		font-size: 13px;
		line-height: 1.5;
		margin: 0;
		white-space: pre-wrap;
	}
</style>
