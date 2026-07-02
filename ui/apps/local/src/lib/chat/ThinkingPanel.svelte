<script lang="ts">
	// 추론 패널. reasoning 모델의 사고 흐름을 답변과 분리해 표시 (Claude/ChatGPT 벤치마크).
	// 진행중(active): "생각 중" 라벨 + 사고 텍스트 끝부분이 흐릿하게 라이브로 흐른다.
	// 완료: "추론 과정" 한 줄로 접힘, 클릭 시 전체 펼침. 테두리 없는 ghost 스타일 (chrome 최소).
	let { thinking, active }: { thinking: string; active: boolean } = $props();
	let open = $state(false);

	// 진행중 라이브 프리뷰는 끝 220자만 (스크롤 없이 흐르는 느낌).
	const tail = $derived(thinking.length > 220 ? thinking.slice(-220) : thinking);
</script>

{#if active}
	<div class="think live">
		<span class="pulse"></span>
		<div class="livebody">
			<span class="label">생각 중</span>
			{#if tail}<span class="tail">{tail}</span>{/if}
		</div>
	</div>
{:else if thinking}
	<div class="think">
		<button class="toggle" onclick={() => (open = !open)} aria-expanded={open}>
			<svg class="chev" class:open viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6" /></svg>
			추론 과정
		</button>
		{#if open}
			<div class="full">{thinking}</div>
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
		align-items: flex-start;
		gap: 0.5rem;
	}
	.pulse {
		flex-shrink: 0;
		width: 0.5rem;
		height: 0.5rem;
		margin-top: 0.3rem;
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
	.livebody {
		min-width: 0;
		line-height: 1.5;
	}
	.label {
		font-weight: 600;
		color: var(--dl-ink-dim, #9aa0aa);
		margin-right: 0.5rem;
	}
	.tail {
		opacity: 0.65;
		word-break: break-word;
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
