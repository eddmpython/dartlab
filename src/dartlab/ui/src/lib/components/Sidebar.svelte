<script>
	import { cn } from "$lib/utils.js";
	import { Button } from "$lib/components/ui/button/index.js";
	import { Plus, MessageSquare, Trash2, Search, FileText } from "lucide-svelte";

	let {
		conversations = [],
		activeId = null,
		open = true,
		version = "",
		onNewChat,
		onSelect,
		onDelete,
		onOpenSearch,
	} = $props();

	let searchQuery = $state("");

	function groupByDate(convs) {
		const today = new Date().setHours(0, 0, 0, 0);
		const yesterday = today - 86400000;
		const weekAgo = today - 7 * 86400000;

		const buckets = { "오늘": [], "어제": [], "이번 주": [], "이전": [] };

		for (const c of convs) {
			if (c.updatedAt >= today) buckets["오늘"].push(c);
			else if (c.updatedAt >= yesterday) buckets["어제"].push(c);
			else if (c.updatedAt >= weekAgo) buckets["이번 주"].push(c);
			else buckets["이전"].push(c);
		}

		const groups = [];
		for (const [label, items] of Object.entries(buckets)) {
			if (items.length > 0) groups.push({ label, items });
		}
		return groups;
	}

	let filteredConversations = $derived(
		searchQuery.trim()
			? conversations.filter(c =>
				c.title.toLowerCase().includes(searchQuery.toLowerCase())
			)
			: conversations
	);
	let groups = $derived(groupByDate(filteredConversations));
</script>

<aside class={cn(
	"surface-panel flex flex-col h-full bg-dl-bg-darker border-r border-dl-border transition-all duration-300 flex-shrink-0 overflow-hidden",
	open ? "w-[260px]" : "w-[52px]"
)}>
	{#if open}
		<div class="flex flex-col h-full min-w-[260px]">
			<!-- Brand -->
			<div class="border-b border-dl-border/40 px-4 pt-4 pb-3">
				<div class="flex items-center gap-2.5">
					<img src="/avatar.png" alt="DartLab" class="w-8 h-8 rounded-full shadow-sm" />
					<div>
						<div class="text-[15px] font-bold text-dl-text tracking-tight">DartLab</div>
						<div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Analysis Workspace</div>
					</div>
				</div>
			</div>

			<!-- New Chat -->
			<div class="p-3 pb-2">
				<Button variant="secondary" class="w-full justify-start gap-2" onclick={onNewChat}>
					<Plus size={16} />
					새 대화
				</Button>
			</div>

			<!-- Search -->
			{#if conversations.length > 3}
				<div class="px-3 pb-2">
					<div class="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-dl-bg-card/80 border border-dl-border/60">
						<Search size={12} class="text-dl-text-dim flex-shrink-0" />
						<input
							type="text"
							bind:value={searchQuery}
							placeholder="대화 검색..."
							class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"
						/>
					</div>
				</div>
			{/if}

			<!-- Conversation List -->
			<div class="flex-1 overflow-y-auto px-2 py-1 space-y-4">
				{#each groups as group}
					<div>
						<div class="px-2 py-1.5 text-[11px] font-medium text-dl-text-dim uppercase tracking-wider">
							{group.label}
						</div>
						{#each group.items as conv}
							<div
								class={cn(
									"w-full flex items-center gap-2 px-2 py-2 rounded-xl text-left text-[13px] transition-all duration-200 group",
									conv.id === activeId
										? "bg-dl-surface-card text-dl-text border border-dl-primary/30 shadow-sm shadow-black/15"
										: "text-dl-text-muted border border-transparent hover:bg-dl-bg-card/50 hover:text-dl-text hover:border-dl-border/60"
								)}
							>
								<button
									class="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-1 py-0.5 text-left"
									onclick={() => onSelect?.(conv.id)}
									aria-current={conv.id === activeId ? "true" : undefined}
								>
									<MessageSquare size={14} class="flex-shrink-0 opacity-50" />
									<span class="flex-1 truncate">{conv.title}</span>
								</button>
								<button
									class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-dl-bg-card-hover text-dl-text-dim hover:text-dl-primary transition-all"
									onclick={(e) => { e.stopPropagation(); onDelete?.(conv.id); }}
									aria-label={`${conv.title} 삭제`}
								>
									<Trash2 size={12} />
								</button>
							</div>
						{/each}
					</div>
				{/each}
			</div>

			{#if version}
				<div class="flex-shrink-0 px-4 py-2.5 border-t border-dl-border/40">
					<span class="text-[10px] text-dl-text-dim font-mono">v{version}</span>
				</div>
			{/if}
		</div>
	{:else}
		<!-- Collapsed: icon-only -->
		<div class="flex flex-col items-center h-full min-w-[52px] py-3 gap-2">
			<img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full shadow-sm mb-1" />
			<button
				class="p-2.5 rounded-lg text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card/50 transition-colors"
				onclick={onNewChat}
				title="새 대화"
			>
				<Plus size={18} />
			</button>

			<div class="flex-1 overflow-y-auto flex flex-col items-center gap-1 w-full px-1">
				{#each conversations.slice(0, 10) as conv}
					<button
						class={cn(
							"p-2 rounded-lg transition-colors w-full flex justify-center",
							conv.id === activeId
								? "bg-dl-bg-card text-dl-text"
								: "text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-card/50"
						)}
						onclick={() => onSelect?.(conv.id)}
						title={conv.title}
					>
						<MessageSquare size={16} />
					</button>
				{/each}
			</div>
		</div>
	{/if}
</aside>
