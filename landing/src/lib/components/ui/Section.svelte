<script lang="ts">
	import type { Snippet } from 'svelte';
	import Eyebrow from './Eyebrow.svelte';

	/** 페이지 섹션 · eyebrow + title + subtitle + body */
	interface Props {
		eyebrow?: string;
		title?: string;
		subtitle?: string;
		number?: string; // "01", "02" 같은 NYT 스타일 섹션 번호
		id?: string;
		container?: 'wide' | 'article' | 'max' | 'none';
		children?: Snippet;
	}

	let {
		eyebrow = '',
		title = '',
		subtitle = '',
		number = '',
		id = '',
		container = 'wide',
		children
	}: Props = $props();

	const widthMap = {
		wide: 'var(--dl-w-wide)',
		article: 'var(--dl-w-article)',
		max: 'var(--dl-w-max)',
		none: 'none'
	};
</script>

<section class="section" {id} style="--section-w: {widthMap[container]}">
	<div class="section-inner">
		{#if number || eyebrow || title || subtitle}
			<header class="section-head">
				{#if number}
					<span class="section-num">{number}</span>
				{/if}
				{#if eyebrow}
					<Eyebrow text={eyebrow} />
				{/if}
				{#if title}
					<h2 class="section-title">{title}</h2>
				{/if}
				{#if subtitle}
					<p class="section-sub">{subtitle}</p>
				{/if}
			</header>
		{/if}

		{#if children}
			<div class="section-body">
				{@render children()}
			</div>
		{/if}
	</div>
</section>

<style>
	.section {
		padding-block: var(--dl-s-7);
	}
	.section-inner {
		max-width: var(--section-w);
		margin-inline: auto;
		padding-inline: var(--dl-s-6);
	}
	.section-head {
		display: flex;
		flex-direction: column;
		gap: var(--dl-s-2);
		margin-bottom: var(--dl-s-6);
	}
	.section-num {
		font-family: var(--dl-font-mono);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.18em;
		color: var(--dl-orange);
	}
	.section-title {
		font-family: var(--dl-font-ui);
		font-size: clamp(24px, 3vw, 32px);
		font-weight: 800;
		letter-spacing: -0.025em;
		line-height: 1.15;
		color: var(--dl-ink-print);
		margin: 0;
	}
	.section-sub {
		font-size: 14px;
		color: var(--dl-ink-mute);
		line-height: 1.65;
		max-width: var(--dl-w-article);
		margin: 0;
	}

	@media (max-width: 720px) {
		.section { padding-block: var(--dl-s-5); }
		.section-inner { padding-inline: var(--dl-s-4); }
	}
</style>
