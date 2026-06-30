<script lang="ts">
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { onMount } from 'svelte';

	let { data } = $props();

	const redirectMap: Record<string, string> = {
		'getting-started/installation': '/skills/start.installUv',
		'getting-started/quickstart': '/skills/start.quickStart',
		'getting-started/cli-maintenance': '/skills/operation.cliMaintenance',
		'getting-started/sections': '/skills/engines.company',
		tutorials: '/skills/runtime.notebooks',
		about: '/about',
		stability: '/skills/operation.stability',
		methodology: '/skills/operation.methodology'
	};

	const target = $derived(redirectMap[data.slug] ?? '/skills');
	const fullUrl = $derived(`${base}${target}`);

	onMount(() => {
		goto(fullUrl, { replaceState: true });
	});
</script>

<svelte:head>
	<title>Redirecting to {target} · DartLab</title>
	<meta name="robots" content="noindex" />
	<meta http-equiv="refresh" content="0;url={fullUrl}" />
	<link rel="canonical" href={fullUrl} />
</svelte:head>

<main class="redirect-page">
	<p>이 페이지는 <a href={fullUrl}>{target}</a> 으로 이동했습니다.</p>
</main>

<style>
	.redirect-page {
		min-height: 60vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 4rem 1rem;
		color: #94a3b8;
		font-size: 0.95rem;
	}

	.redirect-page a {
		color: var(--dl-accent);
		text-decoration: underline;
		margin: 0 0.25rem;
	}
</style>
