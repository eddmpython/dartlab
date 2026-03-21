<!--
	Room 상단 바 (데스크톱) — 룸 상태 + 멤버 아바타 + 채팅/퇴장 버튼.
-->
<script>
	import { Users, MessageCircle, LogOut } from "lucide-svelte";
	import MemberList from "./MemberList.svelte";

	const { room, onToggleChat, onLeave } = $props();
</script>

{#if room.joined}
	<div class="flex items-center gap-3 h-8 px-3 bg-dl-bg-card/80 border-b border-dl-border/30 text-xs shrink-0">
		<!-- 룸 상태 -->
		<div class="flex items-center gap-1.5">
			<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
			<span class="text-dl-text-muted">Room</span>
			<span class="font-mono text-dl-text-dim text-[10px]">{room.roomId?.slice(0, 8) || ""}</span>
		</div>

		<!-- 멤버 -->
		<div class="flex items-center gap-1.5">
			<Users size={12} class="text-dl-text-dim" />
			<MemberList members={room.members} myMemberId={room.memberId} compact={true} />
		</div>

		<div class="flex-1"></div>

		<!-- 채팅 토글 -->
		<button
			class="flex items-center gap-1 px-2 py-1 rounded text-dl-text-muted hover:text-dl-text hover:bg-dl-bg-card-hover transition-colors relative"
			onclick={onToggleChat}
		>
			<MessageCircle size={13} />
			<span>Chat</span>
			{#if room.unreadCount > 0}
				<span class="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-dl-primary text-white text-[8px] flex items-center justify-center font-bold">
					{room.unreadCount > 9 ? "9+" : room.unreadCount}
				</span>
			{/if}
		</button>

		<!-- 퇴장 -->
		<button
			class="flex items-center gap-1 px-2 py-1 rounded text-dl-text-dim hover:text-red-400 hover:bg-red-400/10 transition-colors"
			onclick={onLeave}
			title="룸 퇴장"
		>
			<LogOut size={13} />
		</button>
	</div>
{/if}
