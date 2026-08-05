<script lang="ts">
	// 연속으로 실행된 도구 묶음. 무거운 질문에서 도구가 14~56 회 돌면 화면이 그만큼의 줄이
	// 되고 본문이 밀려난다. 사용자는 보통 "무엇을 몇 번 했나" 만 알면 되고, 특정 호출을
	// 확인할 때만 파고든다. 그래서 집계 한 줄로 접고 펼치면 개별 카드가 그대로 나온다.
	//
	// 근거 제품이라 기본값은 펼침이다. 과정을 감추는 쪽을 기본으로 두지 않는다.
	// 묶음이 길어질 때만 접어서 본문 가독을 지킨다.
	import type { ToolPart } from '$lib/chat/chatStore.svelte';
	import { toolLabel } from '$lib/chat/toolLabels';
	import ToolCard from '$lib/chat/ToolCard.svelte';

	let {
		tools,
		qaId = null,
		liveToolId = null
	}: { tools: ToolPart[]; qaId?: string | null; liveToolId?: string | null } = $props();

	let open = $state(false);

	// 이름별로 몇 번 돌았는지. 순서는 처음 등장한 순서를 지킨다.
	const tally = $derived.by(() => {
		const counts = new Map<string, number>();
		for (const tool of tools) {
			const label = toolLabel(tool.name);
			counts.set(label, (counts.get(label) ?? 0) + 1);
		}
		return [...counts.entries()].map(([label, count]) => ({ label, count }));
	});
	const summary = $derived(tally.map((item) => `${item.label} ${item.count}`).join(' · '));
	const failed = $derived(tools.filter((tool) => tool.status === 'error').length);
	const running = $derived(tools.some((tool) => tool.status === 'running'));
	const totalMs = $derived(
		tools.reduce((sum, tool) => sum + (typeof tool.durationMs === 'number' ? tool.durationMs : 0), 0)
	);
	const elapsed = $derived(totalMs >= 1000 ? `${Math.round(totalMs / 1000)}초` : '');
</script>

<div class="run" data-qa={qaId ?? undefined}>
	<button
		class="head"
		type="button"
		data-qa={qaId ? `${qaId}-toggle` : undefined}
		onclick={() => (open = !open)}
		aria-expanded={open}
	>
		<span class="ico" class:spin={running} aria-hidden="true">
			{#if running}
				<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
			{:else}
				<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
			{/if}
		</span>
		<span class="count">{tools.length}단계</span>
		<span class="sum">{summary}</span>
		<span class="sp"></span>
		{#if failed}<span class="bad">실패 {failed}</span>{/if}
		{#if elapsed}<span class="dur">{elapsed}</span>{/if}
		<svg class="chev" class:open viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
	</button>

	{#if open}
		<div class="items" data-qa={qaId ? `${qaId}-items` : undefined}>
			{#each tools as tool (tool.id)}
				<ToolCard {tool} live={tool.id === liveToolId} />
			{/each}
		</div>
	{/if}
</div>

<style>
	/* 개별 도구 카드와 같은 왼쪽 가이드선 규범. 묶음이라고 박스를 두르면 다시 소음이 된다. */
	.run {
		border-left: 1px solid var(--dl-line, #2a2c33);
	}
	.head {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		width: 100%;
		padding: 0.22rem 0.55rem;
		border: none;
		border-radius: 6px;
		background: none;
		color: var(--dl-ink-mute, #6b7280);
		font-size: 0.76rem;
		text-align: left;
		cursor: pointer;
	}
	.head:hover {
		background: color-mix(in srgb, var(--dl-bg-raised, #16171a) 70%, transparent);
	}
	.ico {
		display: inline-flex;
		flex-shrink: 0;
		color: var(--dl-good, #34d399);
	}
	.ico.spin {
		color: var(--dl-info, #6ab0ff);
		animation: spin 0.9s linear infinite;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	.count {
		font-weight: 600;
		color: var(--dl-ink, #e7e7ea);
		flex-shrink: 0;
		font-variant-numeric: tabular-nums;
	}
	.sum {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		min-width: 0;
	}
	.sp {
		flex: 1;
	}
	.bad {
		flex-shrink: 0;
		color: var(--dl-bad, #ef4444);
	}
	.dur {
		flex-shrink: 0;
		font-variant-numeric: tabular-nums;
		color: color-mix(in srgb, var(--dl-ink-mute, #6b7280) 70%, transparent);
	}
	.chev {
		flex-shrink: 0;
		transition: transform 0.15s ease;
	}
	.chev.open {
		transform: rotate(180deg);
	}
	.items {
		display: flex;
		flex-direction: column;
		gap: 0;
		padding-left: 0.55rem;
	}
</style>
