<!--
	Room 채팅 패널 — 인간 대 인간 채팅 + 빠른 이모지 반응.
-->
<script>
	import { Send } from "lucide-svelte";
	import MemberList from "./MemberList.svelte";
	import RoomAnalysisBanner from "./RoomAnalysisBanner.svelte";

	const { room, showMembers = true } = $props();

	let inputText = $state("");
	let chatContainer = $state(null);

	const QUICK_EMOJIS = ["👍", "🔥", "❤️", "💯", "🤔"];

	function handleSend() {
		if (!inputText.trim()) return;
		room.sendChat(inputText.trim());
		inputText = "";
	}

	function handleKeydown(e) {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	}

	function formatTime(ts) {
		const d = new Date(ts * 1000);
		return d.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
	}

	// 자동 스크롤
	$effect(() => {
		if (room.chatMessages.length && chatContainer) {
			requestAnimationFrame(() => {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			});
		}
	});
</script>

<div class="flex flex-col h-full bg-dl-bg-dark">
	{#if showMembers}
		<!-- 멤버 리스트 (상단) -->
		<div class="px-3 py-2 border-b border-dl-border/30">
			<div class="text-[10px] text-dl-text-dim mb-1.5 uppercase tracking-wider">참여자 ({room.members.length})</div>
			<MemberList members={room.members} myMemberId={room.memberId} />
		</div>
	{/if}

	<!-- AI 분석 배너 -->
	{#if room.analysisStream}
		<RoomAnalysisBanner stream={room.analysisStream} analyzing={room.analyzing} />
	{/if}

	<!-- 채팅 메시지 -->
	<div class="flex-1 overflow-y-auto px-3 py-2 space-y-1.5" bind:this={chatContainer}>
		{#if room.chatMessages.length === 0}
			<p class="text-sm text-dl-text-dim text-center mt-8">아직 메시지가 없습니다.</p>
		{/if}
		{#each room.chatMessages as msg (msg.timestamp)}
			{@const isMine = msg.memberId === room.memberId}
			<div class="flex {isMine ? 'justify-end' : 'justify-start'}">
				<div class="max-w-[80%] {isMine ? 'bg-dl-primary/15 border-dl-primary/20' : 'bg-dl-bg-card border-dl-border/30'} border rounded-lg px-3 py-1.5">
					{#if !isMine}
						<div class="text-[10px] text-dl-accent font-medium mb-0.5">{msg.name}</div>
					{/if}
					<div class="text-sm text-dl-text break-words">{msg.text}</div>
					<div class="text-[9px] text-dl-text-dim mt-0.5 text-right">{formatTime(msg.timestamp)}</div>
				</div>
			</div>
		{/each}
	</div>

	<!-- 빠른 이모지 -->
	<div class="flex items-center gap-1 px-3 py-1 border-t border-dl-border/20">
		{#each QUICK_EMOJIS as emoji}
			<button
				class="px-1.5 py-0.5 rounded hover:bg-dl-bg-card-hover transition-colors text-sm"
				onclick={() => room.sendReaction(emoji)}
			>{emoji}</button>
		{/each}
	</div>

	<!-- 입력 바 -->
	<div class="flex items-center gap-2 px-3 py-2 border-t border-dl-border/30 bg-dl-bg-darker/50">
		<input
			type="text"
			class="flex-1 px-3 py-1.5 rounded-lg bg-dl-bg-card border border-dl-border/50 text-sm text-dl-text
				placeholder:text-dl-text-dim focus:outline-none focus:ring-1 focus:ring-dl-ring"
			placeholder="메시지 입력..."
			maxlength="500"
			bind:value={inputText}
			onkeydown={handleKeydown}
		/>
		<button
			class="p-1.5 rounded-lg bg-dl-primary text-white hover:bg-dl-primary-dark transition-colors disabled:opacity-30"
			onclick={handleSend}
			disabled={!inputText.trim()}
		>
			<Send size={14} />
		</button>
	</div>
</div>
