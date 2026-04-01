<!--
	Room 멤버 목록 — 색상 아바타 + 이름 + role 뱃지.
-->
<script>
	const { members = [], myMemberId = null, compact = false } = $props();

	const COLORS = [
		"#ea4647", "#3b82f6", "#10b981", "#f59e0b",
		"#8b5cf6", "#ec4899", "#06b6d4", "#84cc16",
		"#f97316", "#6366f1",
	];

	function avatarColor(name) {
		let hash = 0;
		for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) | 0;
		return COLORS[Math.abs(hash) % COLORS.length];
	}

	function initial(name) {
		return name.charAt(0).toUpperCase();
	}
</script>

{#if compact}
	<!-- 가로 배열 (RoomBar용) -->
	<div class="flex items-center gap-1">
		{#each members.slice(0, 5) as m (m.memberId)}
			<div
				class="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white
					ring-1 ring-dl-bg-dark {m.memberId === myMemberId ? 'ring-2 ring-dl-accent' : ''}"
				style="background: {avatarColor(m.name)}"
				title={m.name + (m.role === 'host' ? ' (호스트)' : '')}
			>{initial(m.name)}</div>
		{/each}
		{#if members.length > 5}
			<span class="text-[10px] text-dl-text-muted ml-0.5">+{members.length - 5}</span>
		{/if}
	</div>
{:else}
	<!-- 세로 리스트 -->
	<div class="space-y-1">
		{#each members as m (m.memberId)}
			<div class="flex items-center gap-2 px-2 py-1.5 rounded-lg {m.memberId === myMemberId ? 'bg-dl-surface-active' : ''}">
				<div
					class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
					style="background: {avatarColor(m.name)}"
				>{initial(m.name)}</div>
				<span class="text-sm text-dl-text truncate flex-1">{m.name}</span>
				{#if m.role === "host"}
					<span class="text-[10px] px-1.5 py-0.5 rounded bg-dl-accent/20 text-dl-accent font-medium">호스트</span>
				{/if}
				{#if m.memberId === myMemberId}
					<span class="text-[10px] text-dl-text-dim">(나)</span>
				{/if}
			</div>
		{/each}
	</div>
{/if}
