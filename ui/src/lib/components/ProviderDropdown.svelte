<script>
	import { cn } from "$lib/utils.js";
	import { ChevronDown, Settings, Loader2, AlertCircle, Check } from "lucide-svelte";

	let { ui, onOpenSettings } = $props();
	let open = $state(false);

	let providerList = $derived.by(() => {
		const entries = Object.entries(ui.providers || {});
		return entries
			.filter(([, v]) => v.label)
			.map(([id, v]) => ({
				id,
				label: v.label || id,
				available: v.available === true,
				freeTier: v.freeTier || "",
			}))
			.sort((a, b) => (b.available ? 1 : 0) - (a.available ? 1 : 0));
	});

	function select(id) {
		ui.selectProvider(id);
		open = false;
	}

	function handleClickOutside(e) {
		if (!e.target.closest(".provider-dropdown")) open = false;
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="provider-dropdown relative" onclick={handleClickOutside}>
	<button
		class={cn(
			"flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] transition-colors",
			ui.statusLoading
				? "text-dl-text-dim"
				: !ui.activeProvider || !ui.providers[ui.activeProvider]?.available
					? "text-dl-primary-light bg-dl-primary/10 hover:bg-dl-primary/15"
					: "text-dl-text-muted hover:text-dl-text hover:bg-white/5"
		)}
		onclick={(e) => { e.stopPropagation(); open = !open; }}
	>
		{#if ui.statusLoading}
			<Loader2 size={12} class="animate-spin" />
			<span>확인 중...</span>
		{:else if !ui.activeProvider || !ui.providers[ui.activeProvider]?.available}
			<AlertCircle size={12} />
			<span>설정 필요</span>
		{:else}
			<span class="w-1.5 h-1.5 rounded-full bg-dl-success flex-shrink-0"></span>
			<span>{ui.providers[ui.activeProvider]?.label || ui.activeProvider}</span>
			{#if ui.activeModel}
				<span class="text-dl-text-dim">/</span>
				<span class="max-w-[80px] truncate">{ui.activeModel}</span>
			{/if}
		{/if}
		<ChevronDown size={10} class="transition-transform {open ? 'rotate-180' : ''}" />
	</button>

	{#if open}
		<div class="absolute right-0 top-full mt-1 w-56 rounded-lg border border-dl-border/50 bg-dl-bg-darker shadow-overlay z-50 py-1 overflow-hidden">
			{#each providerList as p}
				<button
					class={cn(
						"w-full flex items-center gap-2 px-3 py-2 text-left text-[12px] transition-colors hover:bg-white/5",
						p.id === ui.activeProvider ? "text-dl-text" : "text-dl-text-muted"
					)}
					onclick={(e) => { e.stopPropagation(); select(p.id); }}
				>
					{#if p.available}
						<span class="w-1.5 h-1.5 rounded-full bg-dl-success flex-shrink-0"></span>
					{:else}
						<span class="w-1.5 h-1.5 rounded-full bg-dl-text-dim/30 flex-shrink-0"></span>
					{/if}
					<span class="flex-1">{p.label}</span>
					{#if p.id === ui.activeProvider}
						<Check size={12} class="text-dl-success flex-shrink-0" />
					{/if}
				</button>
			{/each}
			<div class="border-t border-dl-border/30 mt-1 pt-1">
				<button
					class="w-full flex items-center gap-2 px-3 py-2 text-left text-[12px] text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
					onclick={(e) => { e.stopPropagation(); open = false; onOpenSettings?.(); }}
				>
					<Settings size={12} />
					<span>프로바이더 설정</span>
				</button>
			</div>
		</div>
	{/if}
</div>
