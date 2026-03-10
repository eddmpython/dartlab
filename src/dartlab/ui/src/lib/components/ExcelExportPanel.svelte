<script>
	import { cn } from "$lib/utils.js";
	import { fetchExportModules, downloadExcel } from "$lib/api.js";
	import { FileSpreadsheet, Download, Loader2, X, CheckSquare, Square, ChevronDown, ChevronUp } from "lucide-svelte";

	let { stockCode = null, corpName = "", onClose } = $props();

	let modules = $state([]);
	let selected = $state(new Set());
	let loading = $state(false);
	let downloading = $state(false);
	let error = $state("");
	let expanded = $state(false);

	const FINANCE_GROUP = new Set(["IS", "BS", "CF", "ratios"]);

	let financeModules = $derived(modules.filter(m => FINANCE_GROUP.has(m.name)));
	let otherModules = $derived(modules.filter(m => !FINANCE_GROUP.has(m.name)));
	let allSelected = $derived(selected.size === modules.length && modules.length > 0);

	$effect(() => {
		if (stockCode) loadModules();
	});

	async function loadModules() {
		loading = true;
		error = "";
		try {
			const data = await fetchExportModules(stockCode);
			modules = data.modules || [];
			selected = new Set(modules.map(m => m.name));
		} catch (e) {
			error = e.message;
		}
		loading = false;
	}

	function toggle(name) {
		const next = new Set(selected);
		if (next.has(name)) next.delete(name);
		else next.add(name);
		selected = next;
	}

	function toggleAll() {
		if (allSelected) {
			selected = new Set();
		} else {
			selected = new Set(modules.map(m => m.name));
		}
	}

	function toggleGroup(group) {
		const names = group.map(m => m.name);
		const allIn = names.every(n => selected.has(n));
		const next = new Set(selected);
		if (allIn) {
			for (const n of names) next.delete(n);
		} else {
			for (const n of names) next.add(n);
		}
		selected = next;
	}

	async function handleDownload() {
		if (selected.size === 0 || downloading) return;
		downloading = true;
		error = "";
		try {
			const mods = allSelected ? null : [...selected];
			await downloadExcel(stockCode, mods);
		} catch (e) {
			error = e.message;
		}
		downloading = false;
	}
</script>

<div class="rounded-xl border border-dl-border bg-dl-bg-card/60 backdrop-blur-sm overflow-hidden animate-fadeIn">
	<!-- Header -->
	<div class="flex items-center justify-between px-4 py-3 border-b border-dl-border/50">
		<div class="flex items-center gap-2">
			<FileSpreadsheet size={16} class="text-dl-success" />
			<span class="text-[13px] font-medium text-dl-text">Excel 내보내기</span>
			{#if corpName}
				<span class="text-[11px] text-dl-text-dim">— {corpName}</span>
			{/if}
		</div>
		<div class="flex items-center gap-1.5">
			<button
				class="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-dl-success/15 text-dl-success text-[11px] font-medium hover:bg-dl-success/25 transition-colors disabled:opacity-40"
				onclick={handleDownload}
				disabled={selected.size === 0 || downloading || loading}
			>
				{#if downloading}
					<Loader2 size={12} class="animate-spin" />
					다운로드 중
				{:else}
					<Download size={12} />
					다운로드 ({selected.size})
				{/if}
			</button>
			{#if onClose}
				<button
					class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
					onclick={onClose}
				>
					<X size={16} />
				</button>
			{/if}
		</div>
	</div>

	<!-- Content -->
	<div class="px-4 py-3">
		{#if loading}
			<div class="flex items-center gap-2 py-4 justify-center text-[12px] text-dl-text-dim">
				<Loader2 size={14} class="animate-spin" />
				모듈 목록 로드 중...
			</div>
		{:else if error}
			<div class="text-[12px] text-dl-primary-light py-2">{error}</div>
		{:else if modules.length > 0}
			<!-- Select all -->
			<div class="flex items-center justify-between mb-2">
				<button
					class="flex items-center gap-1.5 text-[11px] text-dl-text-muted hover:text-dl-text transition-colors"
					onclick={toggleAll}
				>
					{#if allSelected}
						<CheckSquare size={13} class="text-dl-success" />
					{:else}
						<Square size={13} />
					{/if}
					전체 선택
				</button>
				<button
					class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"
					onclick={() => expanded = !expanded}
				>
					{expanded ? "접기" : "펼치기"}
					{#if expanded}
						<ChevronUp size={12} />
					{:else}
						<ChevronDown size={12} />
					{/if}
				</button>
			</div>

			<!-- Finance group -->
			{#if financeModules.length > 0}
				<div class="mb-2">
					<button
						class="text-[10px] text-dl-text-dim mb-1 hover:text-dl-text-muted transition-colors"
						onclick={() => toggleGroup(financeModules)}
					>
						재무제표
					</button>
					<div class="flex flex-wrap gap-1">
						{#each financeModules as m}
							<button
								class={cn(
									"px-2.5 py-1 rounded-lg text-[11px] border transition-all",
									selected.has(m.name)
										? "border-dl-success/40 bg-dl-success/10 text-dl-success"
										: "border-dl-border text-dl-text-dim hover:border-dl-border hover:text-dl-text-muted"
								)}
								onclick={() => toggle(m.name)}
							>
								{m.label}
							</button>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Other modules -->
			{#if otherModules.length > 0}
				<div>
					<button
						class="text-[10px] text-dl-text-dim mb-1 hover:text-dl-text-muted transition-colors"
						onclick={() => toggleGroup(otherModules)}
					>
						보고서/공시 ({otherModules.length})
					</button>
					{#if expanded}
						<div class="flex flex-wrap gap-1">
							{#each otherModules as m}
								<button
									class={cn(
										"px-2.5 py-1 rounded-lg text-[11px] border transition-all",
										selected.has(m.name)
											? "border-dl-success/40 bg-dl-success/10 text-dl-success"
											: "border-dl-border text-dl-text-dim hover:border-dl-border hover:text-dl-text-muted"
									)}
									onclick={() => toggle(m.name)}
								>
									{m.label}
								</button>
							{/each}
						</div>
					{:else}
						<div class="flex flex-wrap gap-1">
							{#each otherModules.slice(0, 6) as m}
								<button
									class={cn(
										"px-2.5 py-1 rounded-lg text-[11px] border transition-all",
										selected.has(m.name)
											? "border-dl-success/40 bg-dl-success/10 text-dl-success"
											: "border-dl-border text-dl-text-dim hover:border-dl-border hover:text-dl-text-muted"
									)}
									onclick={() => toggle(m.name)}
								>
									{m.label}
								</button>
							{/each}
							{#if otherModules.length > 6}
								<button
									class="px-2 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-text-muted transition-colors"
									onclick={() => expanded = true}
								>
									+{otherModules.length - 6}개 더
								</button>
							{/if}
						</div>
					{/if}
				</div>
			{/if}
		{:else}
			<div class="text-[12px] text-dl-text-dim py-2">내보낼 수 있는 데이터가 없습니다</div>
		{/if}
	</div>
</div>
