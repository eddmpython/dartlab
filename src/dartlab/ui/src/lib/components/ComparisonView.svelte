<script>
	import { fetchCompanyViewer } from "$lib/api.js";
	import DiffCompare from "./DiffCompare.svelte";

	let {
		stockCode = null,
		topics = [],
		periods = [],
	} = $props();

	let activeTopic = $state(null);
	let resolvedPeriods = $state([]);
	let loading = $state(false);
	let error = $state(null);

	function collectPeriods(viewerData) {
		const found = new Set();
		for (const block of viewerData?.blocks || []) {
			for (const period of block?.meta?.periods || []) {
				if (period) found.add(period);
			}
		}
		for (const entry of viewerData?.textDocument?.entries || []) {
			if (entry?.periodLabel) found.add(entry.periodLabel);
		}
		return [...found].sort().reverse();
	}

	async function ensurePeriods(topic) {
		if (!stockCode || !topic || (resolvedPeriods && resolvedPeriods.length >= 2)) return;
		loading = true;
		error = null;
		try {
			const viewerData = await fetchCompanyViewer(stockCode, topic);
			resolvedPeriods = collectPeriods(viewerData);
		} catch (e) {
			error = e.message;
		}
		loading = false;
	}

	$effect(() => {
		if (topics?.length && !topics.includes(activeTopic)) {
			activeTopic = topics[0];
		}
	});

	$effect(() => {
		resolvedPeriods = periods || [];
	});

	$effect(() => {
		if (activeTopic) ensurePeriods(activeTopic);
	});

	function topicButtonClass(topic) {
		return [
			"rounded-full border px-2 py-1 text-[10px] transition-colors",
			topic === activeTopic
				? "border-dl-accent/30 bg-dl-accent/10 text-dl-text"
				: "border-dl-border/20 text-dl-text-dim",
		].join(" ");
	}
</script>

<div class="rounded-xl border border-dl-border/20 bg-dl-surface-card overflow-hidden">
	<div class="flex flex-wrap items-center gap-2 px-4 py-3 border-b border-dl-border/15 bg-dl-bg-darker/40">
		<span class="text-[12px] font-semibold text-dl-text">기간 비교</span>
		{#if topics?.length > 1}
			<div class="flex flex-wrap gap-1 ml-auto">
				{#each topics as topic}
					<button
						class={topicButtonClass(topic)}
						onclick={() => { activeTopic = topic; resolvedPeriods = periods || []; }}
					>
						{topic}
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<div class="p-3">
		{#if !stockCode}
			<div class="text-[12px] text-dl-text-dim">비교할 회사를 먼저 선택하세요.</div>
		{:else if !activeTopic}
			<div class="text-[12px] text-dl-text-dim">비교할 topic이 없습니다.</div>
		{:else if error}
			<div class="text-[12px] text-red-400">{error}</div>
		{:else if loading && (!resolvedPeriods || resolvedPeriods.length < 2)}
			<div class="text-[12px] text-dl-text-dim">기간 목록을 불러오는 중...</div>
		{:else}
			<DiffCompare stockCode={stockCode} topic={activeTopic} periods={resolvedPeriods} />
		{/if}
	</div>
</div>
