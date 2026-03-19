<!--
	KeyboardHelp — 키보드 단축키 도움말 모달.
-->
<script>
	import { X, Keyboard } from "lucide-svelte";

	let { show = false, onClose = null } = $props();

	const SHORTCUTS = [
		{ key: "?", desc: "단축키 도움말" },
		{ key: "1", desc: "Chat 탭" },
		{ key: "2", desc: "Viewer 탭" },
		{ key: "Ctrl+K", desc: "종목 검색" },
		{ key: "Ctrl+F", desc: "뷰어 내 검색" },
		{ key: "J / ↓", desc: "다음 topic" },
		{ key: "K / ↑", desc: "이전 topic" },
		{ key: "S", desc: "현재 topic AI 요약" },
		{ key: "B", desc: "북마크 토글" },
		{ key: "Esc", desc: "모달/검색 닫기" },
	];
</script>

{#if show}
	<!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
	<div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm" onclick={onClose}>
		<!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
		<div class="bg-dl-bg-card border border-dl-border/30 rounded-xl shadow-2xl w-80 max-w-[90vw] overflow-hidden" onclick={(e) => e.stopPropagation()}>
			<div class="flex items-center justify-between px-4 py-3 border-b border-dl-border/20">
				<div class="flex items-center gap-2 text-dl-text">
					<Keyboard size={16} />
					<span class="text-[13px] font-semibold">단축키</span>
				</div>
				<button class="p-1 rounded text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors" onclick={onClose}>
					<X size={14} />
				</button>
			</div>
			<div class="px-4 py-3 space-y-1.5">
				{#each SHORTCUTS as s}
					<div class="flex items-center justify-between text-[12px]">
						<span class="text-dl-text-muted">{s.desc}</span>
						<kbd class="px-1.5 py-0.5 rounded bg-dl-bg-darker border border-dl-border/30 text-[11px] font-mono text-dl-text-dim min-w-[32px] text-center">{s.key}</kbd>
					</div>
				{/each}
			</div>
		</div>
	</div>
{/if}
