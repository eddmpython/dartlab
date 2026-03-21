<!--
	KeyboardHelp — 키보드 단축키 도움말 모달. 카테고리별 그룹화 + 검색 필터.
-->
<script>
	import { X, Keyboard, Search } from "lucide-svelte";

	let { show = false, onClose = null } = $props();

	let filterText = $state("");

	const GROUPS = [
		{
			label: "탐색",
			shortcuts: [
				{ key: "1", desc: "Chat 탭" },
				{ key: "2", desc: "Viewer 탭" },
				{ key: "Ctrl+K", desc: "종목 검색 / 커맨드 팔레트" },
			],
		},
		{
			label: "채팅",
			shortcuts: [
				{ key: "Ctrl+N", desc: "새 대화" },
				{ key: "Enter", desc: "메시지 전송" },
				{ key: "Shift+Enter", desc: "줄바꿈" },
			],
		},
		{
			label: "뷰어",
			shortcuts: [
				{ key: "J / ↓", desc: "다음 topic" },
				{ key: "K / ↑", desc: "이전 topic" },
				{ key: "Ctrl+F", desc: "뷰어 내 검색" },
				{ key: "S", desc: "현재 topic AI 요약" },
				{ key: "B", desc: "북마크 토글" },
			],
		},
		{
			label: "일반",
			shortcuts: [
				{ key: "?", desc: "단축키 도움말" },
				{ key: "Esc", desc: "모달/검색 닫기" },
			],
		},
	];

	let filteredGroups = $derived.by(() => {
		if (!filterText.trim()) return GROUPS;
		const q = filterText.trim().toLowerCase();
		return GROUPS.map(g => ({
			...g,
			shortcuts: g.shortcuts.filter(s =>
				s.desc.toLowerCase().includes(q) || s.key.toLowerCase().includes(q)
			),
		})).filter(g => g.shortcuts.length > 0);
	});
</script>

{#if show}
	<!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
	<div
		class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
		onclick={onClose}
		role="dialog"
		aria-modal="true"
		aria-label="키보드 단축키"
	>
		<!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
		<div class="bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl w-96 max-w-[90vw] overflow-hidden" onclick={(e) => e.stopPropagation()}>
			<div class="flex items-center justify-between px-4 py-3 border-b border-dl-border/20">
				<div class="flex items-center gap-2 text-dl-text">
					<Keyboard size={16} />
					<span class="text-[13px] font-semibold">키보드 단축키</span>
				</div>
				<button class="p-1 rounded text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" onclick={onClose}>
					<X size={14} />
				</button>
			</div>

			<!-- 검색 -->
			<div class="flex items-center gap-2 px-4 py-2 border-b border-dl-border/10">
				<Search size={12} class="text-dl-text-dim" />
				<input
					type="text"
					bind:value={filterText}
					placeholder="단축키 검색..."
					class="flex-1 bg-transparent border-none outline-none text-[12px] text-dl-text placeholder:text-dl-text-dim"
				/>
			</div>

			<div class="px-4 py-3 space-y-4 max-h-[60vh] overflow-y-auto">
				{#each filteredGroups as group}
					<div>
						<div class="text-[10px] uppercase tracking-wider text-dl-text-dim mb-2">{group.label}</div>
						<div class="space-y-1.5">
							{#each group.shortcuts as s}
								<div class="flex items-center justify-between text-[12px]">
									<span class="text-dl-text-muted">{s.desc}</span>
									<kbd class="px-1.5 py-0.5 rounded bg-dl-bg-darker border border-dl-border/30 text-[11px] font-mono text-dl-text-dim min-w-[32px] text-center">{s.key}</kbd>
								</div>
							{/each}
						</div>
					</div>
				{/each}
				{#if filteredGroups.length === 0}
					<div class="text-[12px] text-dl-text-dim text-center py-4">일치하는 단축키가 없습니다</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
