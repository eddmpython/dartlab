<script>
	import { GitCompareArrows, Eye, Filter } from "lucide-svelte";

	let { doc, viewMode = $bindable("unified"), onPeriodChange = null } = $props();

	let showPeriodPicker = $state(false);

	function selectBase(period) {
		showPeriodPicker = false;
		onPeriodChange?.(period, null);
	}
</script>

<div class="vw2-toolbar">
	<div class="vw2-toolbar-left">
		{#if doc.comparePeriod}
			<div class="vw2-period-badge">
				<GitCompareArrows size={12} />
				<span>{doc.basePeriod}</span>
				<span class="vw2-period-vs">vs</span>
				<span>{doc.comparePeriod}</span>
			</div>
		{:else}
			<div class="vw2-period-badge">
				<Eye size={12} />
				<span>{doc.basePeriod}</span>
			</div>
		{/if}

		{#if doc.availablePeriods?.length > 1}
			<div class="relative">
				<button class="vw2-period-btn" onclick={() => showPeriodPicker = !showPeriodPicker}>
					기간 변경
				</button>
				{#if showPeriodPicker}
					<div class="vw2-period-dropdown">
						{#each doc.availablePeriods as p}
							<button
								class="vw2-period-option {p === doc.basePeriod ? 'is-active' : ''}"
								onclick={() => selectBase(p)}
							>{p}</button>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<div class="vw2-toolbar-right">
		{#if doc.summary}
			{#if doc.summary.modifiedBlocks > 0}
				<span class="vw2-summary-badge vw2-badge-modified">수정 {doc.summary.modifiedBlocks}</span>
			{/if}
			{#if doc.summary.addedBlocks > 0}
				<span class="vw2-summary-badge vw2-badge-added">추가 {doc.summary.addedBlocks}</span>
			{/if}
			{#if doc.summary.removedBlocks > 0}
				<span class="vw2-summary-badge vw2-badge-removed">삭제 {doc.summary.removedBlocks}</span>
			{/if}
		{/if}
		<button
			class="vw2-mode-btn {viewMode === 'changesOnly' ? 'is-active' : ''}"
			onclick={() => viewMode = viewMode === "unified" ? "changesOnly" : "unified"}
			title="변경 사항만 보기"
		>
			<Filter size={13} />
		</button>
	</div>
</div>
