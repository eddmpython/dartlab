<!--
	플로팅 이모지 반응 — 우하단에 떠오르며 사라지는 애니메이션.
-->
<script>
	const { reactions = [] } = $props();
</script>

<div class="fixed bottom-16 right-4 pointer-events-none z-40 flex flex-col-reverse items-end gap-1">
	{#each reactions as r (r._id)}
		<div class="floating-emoji text-2xl animate-float-up">{r.emoji}</div>
	{/each}
</div>

<style>
	@keyframes float-up {
		0% { opacity: 1; transform: translateY(0) scale(1); }
		70% { opacity: 0.8; transform: translateY(-60px) scale(1.2); }
		100% { opacity: 0; transform: translateY(-100px) scale(0.8); }
	}
	.animate-float-up {
		animation: float-up 2.5s ease-out forwards;
	}
</style>
