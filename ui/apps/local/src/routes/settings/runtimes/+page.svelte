<script lang="ts">
	import RuntimeCenter from '$lib/chat/RuntimeCenter.svelte';
	import '@dartlab/ui-surfaces/terminal/terminal.css';
</script>

<svelte:head><title>Agent Runtime Center · DartLab</title></svelte:head>

<main data-qa="runtime-settings">
	<RuntimeCenter />
</main>

<style>
	main { max-width: 48rem; margin: 0 auto; padding: 2rem 1.25rem; }
</style>
