<script lang="ts">
	import type { StudyData } from '../stores/notebookStore';
	import { notebook } from '../stores/notebookStore';

	interface Props {
		study: StudyData;
		isActive: boolean;
	}

	let { study, isActive }: Props = $props();

	const block = $derived(study.block);
	const isIntro = $derived(study.blockType === 'intro');
	const isSectionDivider = $derived(study.blockType === 'sectionDivider');
	const isFooter = $derived(study.blockType === 'footer');
	const isShowcase = $derived($notebook.metadata?.layout === 'showcase');
	const introPoints = $derived(asArray(block.points));
	const introPrerequisites = $derived(asArray(block.prerequisites));
	const footerItems = $derived(asArray(block.items));

	function asArray(value: unknown): unknown[] {
		return Array.isArray(value) ? value : [];
	}

	function text(value: unknown): string {
		return typeof value === 'string' ? value : '';
	}

	function objectText(value: unknown, key: string): string {
		if (!value || typeof value !== 'object') return '';
		const raw = (value as Record<string, unknown>)[key];
		return text(raw);
	}

	function blockText(key: string): string {
		return text(block[key]);
	}
</script>

<div class="study-cell" class:active={isActive}>
	{#if isIntro}
		<div class="intro">
			<div class="intro-inner">
				{#if block.emoji}
					<span class="intro-emoji">{blockText('emoji')}</span>
				{/if}
				<h1 class="intro-title">
					{blockText('title') || blockText('seoTitle') || blockText('metaTitle')}
				</h1>
				{#if block.goal}
					<p class="intro-goal">{blockText('goal')}</p>
				{/if}
				{#if block.description}
					<p class="intro-desc">{blockText('description')}</p>
				{/if}
				{#if introPoints.length}
					<div class="intro-points">
						{#each introPoints as point}
							<span class="intro-point">
								{typeof point === 'string' ? point : `${objectText(point, 'emoji')} ${objectText(point, 'title')}`.trim()}
							</span>
						{/each}
					</div>
				{/if}
				{#if introPrerequisites.length}
					<div class="intro-prereqs">
						<span class="intro-prereqs-label">Prerequisites</span>
						<div class="intro-prereqs-links">
							{#each introPrerequisites as prereq}
								<a href={objectText(prereq, 'url')} class="intro-prereq-link" data-sveltekit-reload>
									{objectText(prereq, 'text')}
								</a>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</div>
	{:else if isSectionDivider}
		<div class="section-divider" class:showcase-divider={isShowcase}>
			{#if !isShowcase}
				<span class="section-badge">{(study.sectionIndex ?? 0) + 1}</span>
			{/if}
			<div class="section-text">
				<h2 class="section-title">
					{#if block.emoji}
						<span>{blockText('emoji')}</span>
					{/if}
					{blockText('title')}
				</h2>
				{#if block.subtitle}
					<p class="section-subtitle">{blockText('subtitle')}</p>
				{/if}
			</div>
		</div>
	{:else if isFooter}
		<div class="footer-section">
			<h2 class="footer-title">{blockText('title')}</h2>
			{#if block.description}
				<p class="footer-desc">{blockText('description')}</p>
			{/if}
			{#if footerItems.length}
				<ul class="footer-list">
					{#each footerItems as item}
						<li>
							{#if typeof item === 'string'}
								{item}
							{:else}
								<a href={objectText(item, 'studyUrl')}>{objectText(item, 'study')}</a>
							{/if}
						</li>
					{/each}
				</ul>
			{/if}
			{#if block.code}
				<pre class="footer-code"><code>{blockText('code')}</code></pre>
			{/if}
			{#if block.tip}
				<p class="footer-tip">{blockText('tip')}</p>
			{/if}
		</div>
	{:else}
		<div class="generic-block">
			{#if block.title}
				<h3>{blockText('title')}</h3>
			{/if}
			{#if block.description}
				<p>{blockText('description')}</p>
			{:else}
				<pre>{JSON.stringify({ ...block, type: study.blockType }, null, 2)}</pre>
			{/if}
		</div>
	{/if}
</div>

<style>
	.study-cell {
		--color-text: var(--nb-text);
		--color-text-secondary: var(--nb-text-secondary);
		--color-text-muted: var(--nb-text-muted);
		--color-border: var(--nb-border);
		--color-surface: var(--nb-surface);
		--color-surface-glass: var(--nb-surface);
		--color-code-bg: var(--nb-code-bg);
		--color-bg: var(--nb-bg);
		--color-card: var(--nb-card);
		--color-card-hover: var(--nb-surface);
		--color-accent-text: var(--nb-pink);
		--color-accent-active: var(--nb-pink-bright);
		--color-code-text: var(--nb-code-text, #e4e4e7);
		--color-warning: #f59e0b;
		--radius-sm: 4px;
		--radius-md: 8px;
		--radius-lg: 10px;
		--radius-xl: 12px;
		--radius-full: 9999px;
		padding: 4px 0;
	}

	.study-cell.active {
		outline: none;
	}

	.intro {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		gap: 0.75rem;
		padding: 2rem 0 1.5rem;
	}

	.intro-inner {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		gap: 0.75rem;
	}

	.intro-emoji {
		font-size: 2.5rem;
	}

	.intro-title {
		color: var(--nb-text);
		font-size: 1.75rem;
		font-weight: 700;
		margin: 0;
		line-height: 1.3;
	}

	.intro-goal {
		color: var(--nb-text-secondary);
		font-size: 1rem;
		margin: 0;
		line-height: 1.6;
	}

	.intro-desc {
		color: var(--nb-text-muted);
		font-size: 0.9375rem;
		margin: 0;
		line-height: 1.7;
	}

	.intro-points {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		justify-content: center;
		margin-top: 0.25rem;
	}

	.intro-point {
		padding: 0.25rem 0.75rem;
		border: 1px solid var(--nb-border);
		border-radius: 9999px;
		font-size: 0.8125rem;
		color: var(--nb-text-muted);
	}

	.intro-prereqs {
		margin-top: 0.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
		align-items: center;
	}

	.intro-prereqs-label {
		font-size: 0.75rem;
		color: var(--nb-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.intro-prereqs-links {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
		justify-content: center;
	}

	.intro-prereq-link {
		color: var(--nb-text-secondary);
		font-size: 0.8125rem;
		text-decoration: underline;
	}

	.section-divider {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
	}

	.section-divider.showcase-divider {
		justify-content: center;
		padding: 0.5rem 1rem 0;
	}

	.showcase-divider .section-text {
		align-items: center;
		text-align: center;
	}

	.showcase-divider .section-title {
		font-size: 1.125rem;
		color: var(--nb-text-muted);
		font-weight: 500;
	}

	.showcase-divider .section-subtitle {
		font-size: 0.8125rem;
	}

	.section-badge {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 1.75rem;
		height: 1.75rem;
		border-radius: 9999px;
		background: var(--nb-text);
		color: var(--nb-bg);
		font-weight: 700;
		font-size: 0.8125rem;
		flex-shrink: 0;
	}

	.section-text {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}

	.section-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--nb-text);
		margin: 0;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.section-subtitle {
		font-size: 0.8125rem;
		color: var(--nb-text-muted);
		margin: 0;
	}

	.footer-section {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		padding: 1rem 0;
	}

	.footer-title {
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--nb-text);
		margin: 0;
	}

	.footer-desc {
		font-size: 0.9375rem;
		color: var(--nb-text-secondary);
		line-height: 1.6;
		margin: 0;
	}

	.footer-list {
		list-style: disc;
		padding-left: 1.25rem;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	.footer-list li {
		color: var(--nb-text-secondary);
		font-size: 0.9375rem;
		line-height: 1.5;
	}

	.footer-list a {
		color: var(--nb-pink);
		text-decoration: underline;
	}

	.footer-code {
		background: var(--nb-code-bg);
		padding: 1rem;
		border-radius: 8px;
		overflow-x: auto;
		margin: 0;
		font-size: 0.875rem;
		line-height: 1.7;
		color: var(--nb-code-text, #e4e4e7);
		font-family: 'Fira Code', 'Consolas', monospace;
	}

	.footer-code code {
		white-space: pre;
	}

	.footer-tip {
		font-size: 0.875rem;
		color: var(--nb-text-muted);
		margin: 0;
		padding: 0.75rem 1rem;
		background: var(--nb-surface);
		border: 1px solid var(--nb-border);
		border-radius: 10px;
	}

	.generic-block {
		padding: 0.75rem 1rem;
		color: var(--nb-text-secondary);
	}

	.generic-block h3 {
		margin: 0 0 0.5rem;
		color: var(--nb-text);
		font-size: 1rem;
	}

	.generic-block p {
		margin: 0;
		line-height: 1.6;
	}

	.generic-block pre {
		margin: 0;
		overflow-x: auto;
		white-space: pre-wrap;
		font-size: 0.8125rem;
		color: var(--nb-text-muted);
	}
</style>
