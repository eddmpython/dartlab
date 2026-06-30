<script lang="ts">
	import type { Snippet } from 'svelte';

	/** "i" 버튼 + 툴팁 · CMoney 스타일. 지표 옆 용어 설명. */
	interface Props {
		label?: string; // 툴팁 텍스트 (간단)
		children?: Snippet; // 본문 (마크업 가능)
		ariaLabel?: string;
	}

	let { label = '', children, ariaLabel = '도움말' }: Props = $props();

	let open = $state(false);
	let timer: ReturnType<typeof setTimeout> | null = null;

	function show() {
		if (timer) clearTimeout(timer);
		open = true;
	}
	function hide() {
		timer = setTimeout(() => (open = false), 100);
	}
</script>

<span
	class="tip-wrap"
	role="button"
	tabindex="0"
	aria-label={ariaLabel}
	onmouseenter={show}
	onmouseleave={hide}
	onfocus={show}
	onblur={hide}
>
	<span class="tip-icon" aria-hidden="true">i</span>
	{#if open}
		<span class="tip-bubble">
			{#if children}
				{@render children()}
			{:else}
				{label}
			{/if}
		</span>
	{/if}
</span>

<style>
	.tip-wrap {
		position: relative;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 14px;
		height: 14px;
		margin-left: 4px;
		cursor: help;
		vertical-align: baseline;
	}
	.tip-icon {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		border: 1px solid var(--dl-line-strong);
		color: var(--dl-ink-dim);
		font-family: var(--dl-font-mono);
		font-size: 9px;
		font-weight: 600;
		display: grid;
		place-items: center;
		line-height: 1;
		font-style: italic;
		transition: color var(--dl-dur-hover) var(--dl-ease), border-color var(--dl-dur-hover) var(--dl-ease);
	}
	.tip-wrap:hover .tip-icon,
	.tip-wrap:focus .tip-icon {
		color: var(--dl-orange);
		border-color: var(--dl-orange);
	}

	.tip-bubble {
		position: absolute;
		bottom: calc(100% + 8px);
		left: 50%;
		transform: translateX(-50%);
		min-width: 180px;
		max-width: 280px;
		padding: var(--dl-s-2) var(--dl-s-3);
		background: var(--dl-bg-modal);
		border: 1px solid var(--dl-line-strong);
		border-radius: var(--dl-r-md);
		font-family: var(--dl-font-ui);
		font-size: 12px;
		font-weight: 400;
		line-height: 1.5;
		color: var(--dl-ink);
		text-align: left;
		white-space: normal;
		z-index: 100;
		box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.6);
		animation: tip-in 120ms var(--dl-ease);
	}
	.tip-bubble::after {
		content: '';
		position: absolute;
		top: 100%;
		left: 50%;
		transform: translateX(-50%);
		border: 5px solid transparent;
		border-top-color: var(--dl-bg-modal);
	}

	@keyframes tip-in {
		from { opacity: 0; transform: translate(-50%, 4px); }
		to { opacity: 1; transform: translate(-50%, 0); }
	}
</style>
