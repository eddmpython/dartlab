<!--
	DiffCompare — 기간간 텍스트 비교 뷰.
	두 기간의 공시 텍스트를 좌우 또는 상하로 비교 표시.
	추가/삭제/유지를 컬러로 구분.
-->
<script>
	import { fetchCompanyTopicDiff } from "$lib/api.js";
	import { ArrowLeftRight, Loader2, X, Plus, Minus, Equal } from "lucide-svelte";

	let {
		stockCode = null,
		topic = null,
		periods = [],      // 사용 가능한 기간 목록
		onClose = null,
	} = $props();

	let fromPeriod = $state(null);
	let toPeriod = $state(null);
	let diffData = $state(null);
	let diffLoading = $state(false);
	let diffError = $state(null);

	// 기본값: 최신 2기간
	$effect(() => {
		if (periods.length >= 2 && !fromPeriod && !toPeriod) {
			toPeriod = periods[0];    // 최신
			fromPeriod = periods[1];  // 직전
		}
	});

	async function loadDiff() {
		if (!stockCode || !topic || !fromPeriod || !toPeriod) return;
		diffLoading = true;
		diffError = null;
		try {
			const res = await fetchCompanyTopicDiff(stockCode, topic, fromPeriod, toPeriod);
			diffData = res;
		} catch (e) {
			diffError = e.message;
		}
		diffLoading = false;
	}

	$effect(() => {
		if (fromPeriod && toPeriod && fromPeriod !== toPeriod) {
			loadDiff();
		}
	});

	function periodLabel(p) {
		if (!p) return "";
		const m = String(p).match(/^(\d{4})(Q([1-4]))?$/);
		if (!m) return p;
		return m[3] ? `'${m[1].slice(2)}.${m[3]}Q` : `'${m[1].slice(2)}`;
	}

	let stats = $derived.by(() => {
		if (!diffData?.diff) return { added: 0, removed: 0, same: 0 };
		let added = 0, removed = 0, same = 0;
		for (const chunk of diffData.diff) {
			const count = chunk.paragraphs?.length || 1;
			if (chunk.kind === "added") added += count;
			else if (chunk.kind === "removed") removed += count;
			else same += count;
		}
		return { added, removed, same };
	});
</script>

<div class="rounded-xl border border-dl-border/20 bg-dl-surface-card overflow-hidden">
	<!-- Header -->
	<div class="flex items-center gap-2 px-4 py-2 border-b border-dl-border/15 bg-dl-bg-darker/50">
		<ArrowLeftRight size={14} class="text-dl-accent" />
		<span class="text-[12px] font-semibold text-dl-text">기간 비교</span>

		<!-- Period selectors -->
		<div class="flex items-center gap-1 ml-auto">
			<select
				class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"
				bind:value={fromPeriod}
			>
				{#each periods as p}
					<option value={p} disabled={p === toPeriod}>{periodLabel(p)}</option>
				{/each}
			</select>
			<span class="text-[11px] text-dl-text-dim">→</span>
			<select
				class="px-2 py-0.5 rounded bg-dl-bg-darker border border-dl-border/20 text-[11px] text-dl-text outline-none"
				bind:value={toPeriod}
			>
				{#each periods as p}
					<option value={p} disabled={p === fromPeriod}>{periodLabel(p)}</option>
				{/each}
			</select>
			{#if onClose}
				<button class="p-1 ml-1 text-dl-text-dim hover:text-dl-text" onclick={onClose}>
					<X size={12} />
				</button>
			{/if}
		</div>
	</div>

	<!-- Stats bar -->
	{#if diffData && !diffLoading}
		<div class="flex items-center gap-3 px-4 py-1.5 border-b border-dl-border/10 text-[10px]">
			{#if stats.added > 0}
				<span class="flex items-center gap-1 text-emerald-400">
					<Plus size={10} />
					<span>추가 {stats.added}</span>
				</span>
			{/if}
			{#if stats.removed > 0}
				<span class="flex items-center gap-1 text-red-400">
					<Minus size={10} />
					<span>삭제 {stats.removed}</span>
				</span>
			{/if}
			{#if stats.same > 0}
				<span class="flex items-center gap-1 text-dl-text-dim">
					<Equal size={10} />
					<span>유지 {stats.same}</span>
				</span>
			{/if}
		</div>
	{/if}

	<!-- Content -->
	<div class="max-h-[60vh] overflow-y-auto px-4 py-3">
		{#if diffLoading}
			<div class="flex items-center justify-center py-8 gap-2">
				<Loader2 size={14} class="animate-spin text-dl-text-dim" />
				<span class="text-[12px] text-dl-text-dim">비교 로딩 중...</span>
			</div>
		{:else if diffError}
			<div class="text-[12px] text-red-400 py-4">{diffError}</div>
		{:else if diffData?.diff}
			<div class="space-y-0.5">
				{#each diffData.diff as chunk}
					{#each chunk.paragraphs || [chunk.text || ""] as para}
						{@const text = String(para || "").trim()}
						{#if text}
							{#if chunk.kind === "added"}
								<div class="pl-3 py-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-dl-text/85 text-[13px] leading-[1.8] rounded-r">
									<span class="text-emerald-500/60 text-[10px] mr-1">+</span>{text}
								</div>
							{:else if chunk.kind === "removed"}
								<div class="pl-3 py-1 border-l-2 border-red-400 bg-red-500/5 text-dl-text/40 text-[13px] leading-[1.8] rounded-r line-through decoration-red-400/30">
									<span class="text-red-400/60 text-[10px] mr-1">-</span>{text}
								</div>
							{:else}
								<p class="text-[13px] leading-[1.8] text-dl-text/70 py-0.5">{text}</p>
							{/if}
						{/if}
					{/each}
				{/each}
			</div>
		{:else}
			<div class="text-[12px] text-dl-text-dim text-center py-4">비교할 기간을 선택하세요</div>
		{/if}
	</div>
</div>
