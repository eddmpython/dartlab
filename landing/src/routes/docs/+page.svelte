<script lang="ts">
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { onMount } from 'svelte';

	onMount(() => {
		goto(`${base}/skills`, { replaceState: true });
	});
</script>

<svelte:head>
	<title>DartLab Docs · Skills</title>
	<meta name="description" content="DartLab의 공식 문서와 절차 진입점은 Skill OS입니다." />
	<meta http-equiv="refresh" content="0;url={base}/skills" />
</svelte:head>
