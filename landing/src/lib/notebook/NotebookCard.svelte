<script lang="ts">
	import { ArrowUpRight, Trash2 } from 'lucide-svelte';

	interface Props {
		title: string;
		subtitle: string;
		metaLeft?: string;
		metaRight?: string;
		kind: 'example' | 'local';
		/** 카드 우상단 상태 배지. 레슨은 '이어하기' 를 띄운다. */
		badge?: string;
		/** 삭제·초기화 확인 문구. 레슨은 삭제가 아니라 '처음부터 다시' 다. */
		deletePrompt?: string;
		deleteLabel?: string;
		onopen: () => void;
		ondelete?: () => void;
	}

	let {
		title,
		subtitle,
		metaLeft = '',
		metaRight = '',
		kind,
		badge = '',
		deletePrompt = '삭제할까요?',
		deleteLabel = '삭제',
		onopen,
		ondelete
	}: Props = $props();
	let confirming = $state(false);
</script>

<div
	class="ncard {kind}"
	role="button"
	tabindex="0"
	onclick={onopen}
	onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && onopen()}
>
	<div class="ncard-head">
		<span class="ncard-kind">{kind === 'example' ? '레슨' : '내 노트북'}</span>
		{#if badge}<span class="ncard-badge">{badge}</span>{/if}
		<ArrowUpRight size={14} class="ncard-arrow" />
	</div>
	<h3 class="ncard-title">{title}</h3>
	<p class="ncard-sub">{subtitle}</p>
	<footer class="ncard-foot">
		<span class="ncard-meta">{metaLeft}</span>
		<span class="ncard-meta">{metaRight}</span>
	</footer>

	{#if ondelete}
		{#if confirming}
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="ncard-confirm" onclick={(e) => e.stopPropagation()}>
				<span>{deletePrompt}</span>
				<button class="cbtn" onclick={() => (confirming = false)}>취소</button>
				<button
					class="cbtn danger"
					onclick={() => {
						confirming = false;
						ondelete?.();
					}}>{deleteLabel}</button
				>
			</div>
		{:else}
			<button
				class="ncard-del"
				title={deleteLabel}
				aria-label={deleteLabel}
				onclick={(e) => {
					e.stopPropagation();
					confirming = true;
				}}><Trash2 size={13} /></button
			>
		{/if}
	{/if}
</div>

<style>
	.ncard {
		position: relative;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		min-height: 150px;
		padding: 1rem 1.1rem;
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-raised);
		cursor: pointer;
		outline: none;
		transition:
			border-color var(--dl-dur-hover) var(--dl-ease-soft),
			background var(--dl-dur-hover) var(--dl-ease-soft),
			transform var(--dl-dur-hover) var(--dl-ease-soft);
	}
	.ncard:hover,
	.ncard:focus-visible {
		background: var(--dl-bg-overlay);
		transform: translateY(-1px);
	}
	.ncard.local:hover {
		border-color: var(--dl-accent);
	}
	.ncard.example:hover {
		border-color: var(--dl-ink-mute);
	}

	.ncard-head {
		display: flex;
		align-items: center;
		gap: 0.45rem;
	}
	.ncard-kind {
		font-size: 0.66rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		font-weight: 700;
		color: var(--dl-ink-mute);
	}
	.ncard.local .ncard-kind {
		color: var(--dl-accent);
	}
	/* 이어하기 배지. 이미 시작한 레슨임을 카드에서 바로 알린다. */
	.ncard-badge {
		margin-left: 8px;
		padding: 1px 6px;
		border-radius: 3px;
		font-size: 0.62rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		color: var(--dl-accent);
		background: rgba(var(--dl-accent-rgb), 0.12);
	}
	.ncard :global(.ncard-arrow) {
		margin-left: auto;
		color: var(--dl-ink-faint);
	}
	.ncard:hover :global(.ncard-arrow) {
		color: var(--dl-accent);
	}

	.ncard-title {
		margin: 0;
		font-size: 1rem;
		line-height: 1.3;
		color: var(--dl-ink-print);
		font-weight: 600;
	}
	.ncard-sub {
		margin: 0;
		flex: 1;
		font-size: 0.83rem;
		line-height: 1.5;
		color: var(--dl-ink-mute);
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.ncard-foot {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		padding-top: 0.55rem;
		border-top: 1px solid var(--dl-line);
		margin-top: auto;
	}
	.ncard-meta {
		font-family: var(--dl-font-mono);
		font-size: 0.68rem;
		color: var(--dl-ink-dim);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.ncard-del {
		position: absolute;
		top: 10px;
		right: 34px;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border: none;
		border-radius: var(--dl-r-sm);
		background: transparent;
		color: var(--dl-ink-dim);
		cursor: pointer;
		opacity: 0;
		transition: all 0.12s ease;
	}
	.ncard:hover .ncard-del {
		opacity: 1;
	}
	.ncard-del:hover {
		background: var(--dl-bg-modal);
		color: var(--dl-bad);
	}

	.ncard-confirm {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-overlay);
		font-size: 0.85rem;
		color: var(--dl-ink);
	}
	.cbtn {
		padding: 4px 12px;
		border: 1px solid var(--dl-line-strong);
		border-radius: var(--dl-r-sm);
		background: var(--dl-bg-raised);
		color: var(--dl-ink-mute);
		font-size: 0.8rem;
		cursor: pointer;
		transition: all 0.12s ease;
	}
	.cbtn:hover {
		color: var(--dl-ink);
	}
	.cbtn.danger {
		border-color: var(--dl-bad);
		color: var(--dl-bad);
	}
	.cbtn.danger:hover {
		background: var(--dl-bad);
		color: #fff;
	}
</style>
