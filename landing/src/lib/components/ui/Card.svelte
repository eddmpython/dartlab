<script lang="ts">
	import type { Snippet } from 'svelte';

	/** 기본 카드 · shadow 없이 1px border + raised bg */
	interface Props {
		title?: string;
		eyebrow?: string;
		interactive?: boolean;
		padded?: boolean;
		accent?: 'none' | 'red' | 'orange' | 'good' | 'warn' | 'bad' | 'info';
		children?: Snippet;
		header?: Snippet;
		foot?: Snippet;
	}

	let {
		title = '',
		eyebrow = '',
		interactive = false,
		padded = true,
		accent = 'none',
		children,
		header,
		foot
	}: Props = $props();

	const accentColor: Record<string, string> = {
		none: 'transparent',
		red: 'var(--dl-red)',
		orange: 'var(--dl-orange)',
		good: 'var(--dl-good)',
		warn: 'var(--dl-warn)',
		bad: 'var(--dl-bad)',
		info: 'var(--dl-info)'
	};
</script>

<article
	class="card"
	class:interactive
	class:padded
	style="--accent: {accentColor[accent]}"
>
	{#if accent !== 'none'}<span class="card-accent" aria-hidden="true"></span>{/if}

	{#if eyebrow || title || header}
		<header class="card-head">
			{#if eyebrow}<span class="card-eyebrow">{eyebrow}</span>{/if}
			{#if title}<h3 class="card-title">{title}</h3>{/if}
			{#if header}{@render header()}{/if}
		</header>
	{/if}

	{#if children}
		<div class="card-body">
			{@render children()}
		</div>
	{/if}

	{#if foot}
		<footer class="card-foot">
			{@render foot()}
		</footer>
	{/if}
</article>

<style>
	.card {
		position: relative;
		background: var(--dl-bg-raised);
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-lg);
		color: var(--dl-ink);
		transition:
			border-color var(--dl-dur-state) var(--dl-ease),
			background var(--dl-dur-state) var(--dl-ease);
		isolation: isolate;
	}
	.card.padded { padding: var(--dl-s-5); }
	.card.interactive { cursor: pointer; }
	.card.interactive:hover {
		border-color: var(--dl-line-strong);
		background: var(--dl-bg-overlay);
	}

	.card-accent {
		position: absolute;
		inset: 0 auto 0 0;
		width: 3px;
		background: var(--accent, transparent);
		border-radius: var(--dl-r-lg) 0 0 var(--dl-r-lg);
		opacity: 0.85;
	}

	.card-head {
		display: flex;
		flex-direction: column;
		gap: var(--dl-s-1);
		margin-bottom: var(--dl-s-3);
	}
	.card-eyebrow {
		font-family: var(--dl-font-mono);
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: var(--dl-ink-dim);
	}
	.card-title {
		font-family: var(--dl-font-ui);
		font-size: 16px;
		font-weight: 700;
		letter-spacing: -0.01em;
		color: var(--dl-ink-print);
		margin: 0;
	}

	.card-body { color: var(--dl-ink); }

	.card-foot {
		margin-top: var(--dl-s-4);
		padding-top: var(--dl-s-3);
		border-top: 1px solid var(--dl-line);
	}
</style>
