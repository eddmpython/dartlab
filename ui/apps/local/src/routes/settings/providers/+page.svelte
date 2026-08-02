<script lang="ts">
	import RuntimeCenter from '$lib/chat/RuntimeCenter.svelte';
	import '@dartlab/ui-surfaces/terminal/terminal.css';
</script>

<svelte:head><title>Agent Runtime Center · DartLab</title></svelte:head>

<main>
	<p class="migration">Provider 설정은 Agent Runtime Center로 통합되었습니다.</p>
	<RuntimeCenter />
</main>

<style>
	main { max-width: 48rem; margin: 0 auto; padding: 2rem 1.25rem; }
	.migration { color: var(--dl-ink-dim, #9aa0aa); font-size: .82rem; }
</style>
