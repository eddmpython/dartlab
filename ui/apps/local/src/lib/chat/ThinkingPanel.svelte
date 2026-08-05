<script lang="ts">
	// 추론 패널. 데스크탑 챗 앱 규범대로 사고는 본문 위가 아니라 도착한 자리에서 흐른다.
	// 흐르는 중(endedAt === null): 점 하나 + 끝부분 한 줄이 라이브로 지나간다.
	// 끝나면: "N초 동안 생각함" 한 줄로 접히고, 펼치면 전문이 그대로 남는다.
	// 라이브도 접힘도 한 줄 높이라 끝나는 순간 레이아웃이 흔들리지 않는다.
	import type { ThinkingPart } from '$lib/chat/chatStore.svelte';
	import { durationLabel } from '$lib/chat/toolLabels';

	let { part, qaId = null }: { part: ThinkingPart; qaId?: string | null } = $props();
	let open = $state(false);

	const live = $derived(part.endedAt === null);
	// 라이브 미리보기는 끝 220자만. 한 줄로 잘라 흐르는 느낌만 준다.
	const tail = $derived(part.text.length > 220 ? part.text.slice(-220) : part.text);
	const spent = $derived(durationLabel(part.endedAt === null ? null : part.endedAt - part.startedAt));
</script>

{#if live}
	<div class="think live" data-qa={qaId ?? undefined} role="status">
		<span class="pulse" aria-hidden="true"></span>
		<span class="label">생각 중</span>
		{#if tail}<span class="tail">{tail}</span>{/if}
	</div>
{:else if part.text}
	<div class="think" data-qa={qaId ?? undefined}>
		<button
			class="toggle"
			type="button"
			data-qa={qaId ? `${qaId}-toggle` : undefined}
			onclick={() => (open = !open)}
			aria-expanded={open}
		>
			<svg class="chev" class:open viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg>
			{spent ? `${spent} 동안 생각함` : '생각 과정'}
		</button>
		{#if open}
			<div class="full" data-qa={qaId ? `${qaId}-full` : undefined}>{part.text}</div>
		{/if}
	</div>
{/if}

<style>
	.think {
		font-size: 0.78rem;
		color: var(--dl-ink-mute, #6b7280);
	}
	.live {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		min-width: 0;
		line-height: 1.5;
	}
	.pulse {
		flex-shrink: 0;
		width: 0.5rem;
		height: 0.5rem;
		border-radius: 50%;
		background: var(--dl-info, #6ab0ff);
		animation: pulse 1.4s ease-in-out infinite;
	}
	@keyframes pulse {
		0%, 100% {
			opacity: 0.35;
			transform: scale(0.85);
		}
		50% {
			opacity: 1;
			transform: scale(1);
		}
	}
	.label {
		flex-shrink: 0;
		font-weight: 600;
		color: var(--dl-ink-dim, #9aa0aa);
	}
	/* 라이브 미리보기는 한 줄로 고정한다. 여러 줄로 자라면 접히는 순간 화면이 뛴다. */
	.tail {
		min-width: 0;
		flex: 1;
		opacity: 0.65;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.toggle {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.15rem 0.3rem;
		margin-left: -0.3rem;
		border: none;
		border-radius: 6px;
		background: none;
		color: var(--dl-ink-mute, #6b7280);
		font-size: 0.75rem;
		cursor: pointer;
	}
	.toggle:hover {
		color: var(--dl-ink-dim, #9aa0aa);
		background: var(--dl-bg-raised, #16171a);
	}
	.chev {
		transition: transform 0.15s ease;
	}
	.chev.open {
		transform: rotate(90deg);
	}
	.full {
		margin-top: 0.4rem;
		padding: 0.6rem 0.8rem;
		border-left: 2px solid var(--dl-line, #2a2c33);
		white-space: pre-wrap;
		word-break: break-word;
		line-height: 1.6;
		max-height: 22rem;
		overflow-y: auto;
		scrollbar-width: thin;
	}
</style>
