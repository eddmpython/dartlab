<!--
	Room 참여 다이얼로그 — 이름 입력 후 참여.
	localStorage에 이전 이름을 기억한다.
-->
<script>
	const { room, onClose } = $props();

	let name = $state(room.getSavedName() || "");
	let loading = $state(false);
	let error = $state("");

	async function handleJoin() {
		const trimmed = name.trim();
		if (!trimmed) { error = "이름을 입력하세요."; return; }
		if (trimmed.length > 30) { error = "이름은 30자 이하로 입력하세요."; return; }
		loading = true;
		error = "";
		try {
			await room.join(trimmed);
			onClose?.();
		} catch (err) {
			error = err.message || "참여 실패";
		} finally {
			loading = false;
		}
	}

	function handleKeydown(e) {
		if (e.key === "Enter" && !loading) handleJoin();
		if (e.key === "Escape") onClose?.();
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onkeydown={handleKeydown}>
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div class="bg-dl-bg-card border border-dl-border rounded-xl p-6 w-80 shadow-overlay" onclick={(e) => e.stopPropagation()}>
		<h2 class="text-lg font-semibold text-dl-text mb-1">협업 세션 참여</h2>
		<p class="text-sm text-dl-text-muted mb-4">
			Room ID: <span class="font-mono text-dl-accent">{room.roomId || "—"}</span>
		</p>

		<label class="block text-sm text-dl-text-muted mb-1.5">이름</label>
		<input
			type="text"
			class="w-full px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-dl-text text-sm
				focus:outline-none focus:ring-2 focus:ring-dl-ring placeholder:text-dl-text-dim"
			placeholder="표시될 이름 입력"
			maxlength="30"
			bind:value={name}
			autofocus
		/>

		{#if error}
			<p class="text-xs text-red-400 mt-1.5">{error}</p>
		{/if}

		<div class="flex gap-2 mt-4">
			<button
				class="flex-1 px-4 py-2 text-sm rounded-lg bg-dl-bg-darker border border-dl-border text-dl-text-muted
					hover:bg-dl-bg-card-hover transition-colors"
				onclick={() => onClose?.()}
				disabled={loading}
			>취소</button>
			<button
				class="flex-1 px-4 py-2 text-sm rounded-lg bg-dl-primary text-white font-medium
					hover:bg-dl-primary-dark transition-colors disabled:opacity-50"
				onclick={handleJoin}
				disabled={loading || !name.trim()}
			>{loading ? "참여 중..." : "참여"}</button>
		</div>
	</div>
</div>
