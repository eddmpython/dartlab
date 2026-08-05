<script lang="ts">
	/**
	 * 분석 과정 추적. 데스크탑 챗 앱 규범대로 한 줄로 접어 두고 펼칠 때만 보인다.
	 *
	 * 예전에는 도구 호출마다 전체 폭 테두리 카드를 쌓아 15회 호출이 15개 박스가 됐다.
	 * 본문보다 과정이 화면을 지배해 읽을 수 없었다. 여기서는 진행 중에만 현재 단계를
	 * 한 줄로 보이고, 끝나면 "분석 15단계" 한 줄로 접는다.
	 */
	import type { ChatActivity, ToolBlock } from '$lib/chat/chatStore.svelte';
	import ToolCard from '$lib/chat/ToolCard.svelte';

	let {
		tools = [],
		activities = [],
		streaming = false
	}: {
		tools?: ToolBlock[];
		activities?: ChatActivity[];
		streaming?: boolean;
	} = $props();

	let open = $state(false);

	const TOOL_LABELS: Record<string, string> = {
		RunPython: '코드 실행',
		EngineCall: '엔진 호출',
		ReadSkill: '스킬 조회',
		GetSkillBody: '스킬 본문',
		ReadCapability: 'API 조회',
		WebSearch: '웹 검색',
		Read: '파일 인용',
		SaveArtifact: '산출물 저장',
		CompileVisual: '차트 생성',
		CompileFinancialDashboard: '재무 대시보드',
		PeerCompareN: '동종사 비교',
		DCFValuation: 'DCF 가치평가',
		SensitivityAnalysis: '민감도 분석',
		ScenarioCompareN: '시나리오 비교',
		ScenarioOverlay: '시나리오 오버레이',
		CreditScorecard: '신용 스코어카드',
		RegressionForecast: '회귀 예측',
		SearchPastSessions: '과거 세션 검색'
	};

	const total = $derived(tools.length);
	const running = $derived(tools.find((tool) => tool.status === 'running'));
	const failed = $derived(tools.some((tool) => tool.status === 'error'));
	const current = $derived(running ?? tools.at(-1));
	const currentLabel = $derived(current ? (TOOL_LABELS[current.name] ?? current.name) : '');

	// 같은 도구가 연달아 호출되면 묶어서 센다. EngineCall 이 9번이면 한 줄에 "엔진 호출 9".
	const grouped = $derived.by(() => {
		const out: Array<{ name: string; label: string; count: number }> = [];
		for (const tool of tools) {
			const label = TOOL_LABELS[tool.name] ?? tool.name;
			const last = out.at(-1);
			if (last && last.name === tool.name) last.count += 1;
			else out.push({ name: tool.name, label, count: 1 });
		}
		return out;
	});
</script>

<!-- 도구를 하나도 못 쓴 실패에서 "분석 0단계" 는 정보가 아니라 소음이다. -->
{#if streaming || total}
	<div class="trail" data-qa="step-trail">
		{#if streaming}
			<div class="live" role="status">
				<span class="spin" aria-hidden="true"></span>
				<span class="now">{currentLabel || '분석을 시작합니다'}</span>
				{#if total > 1}<span class="count">{total}단계</span>{/if}
			</div>
		{:else}
			<button type="button" class="toggle" onclick={() => (open = !open)} aria-expanded={open}>
				<svg class:rot={open} viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg>
				<span>분석 {total}단계</span>
				{#if failed}<em>일부 실패</em>{/if}
				<span class="summary">{grouped.slice(0, 3).map((g) => (g.count > 1 ? `${g.label} ${g.count}` : g.label)).join(' · ')}{grouped.length > 3 ? ' …' : ''}</span>
			</button>
		{/if}

		{#if open && !streaming}
			<div class="detail">
				{#each tools as tool (tool.id)}
					<ToolCard {tool} />
				{/each}
				{#if activities.length}
					<ul class="acts">
						{#each activities as activity (activity.id)}
							<li class:err={activity.status === 'error'}>{activity.summary}</li>
						{/each}
					</ul>
				{/if}
			</div>
		{/if}
	</div>
{/if}

<style>
	.trail { margin: .1rem 0 .55rem; }
	.live,
	.toggle {
		display: flex;
		align-items: center;
		gap: .45rem;
		width: 100%;
		padding: .25rem 0;
		border: 0;
		background: none;
		color: var(--dl-ink-mute, #6b7280);
		font-size: .78rem;
		text-align: left;
	}
	.toggle { cursor: pointer; }
	.toggle:hover { color: var(--dl-ink-dim, #9aa0aa); }
	.toggle svg { flex: none; transition: transform .15s ease; }
	.toggle svg.rot { transform: rotate(90deg); }
	.summary {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: color-mix(in srgb, var(--dl-ink-mute, #6b7280) 75%, transparent);
	}
	.toggle em { font-style: normal; color: #d6b870; }
	.now { color: var(--dl-ink-dim, #9aa0aa); }
	.count { color: color-mix(in srgb, var(--dl-ink-mute, #6b7280) 75%, transparent); }
	.spin {
		flex: none;
		width: .7rem;
		height: .7rem;
		border: 1.5px solid color-mix(in srgb, currentColor 25%, transparent);
		border-top-color: currentColor;
		border-radius: 50%;
		animation: spin .7s linear infinite;
	}
	@keyframes spin { to { transform: rotate(360deg); } }
	.detail { display: grid; gap: .3rem; margin-top: .35rem; }
	.acts { margin: .1rem 0 0; padding-left: 1rem; color: var(--dl-ink-mute, #6b7280); font-size: .74rem; line-height: 1.6; }
	.acts .err { color: #ff8c8c; }
</style>
