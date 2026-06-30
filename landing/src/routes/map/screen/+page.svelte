<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { page } from '$app/state';

	// /map/screen 은 v1 부터 /screener 로 통합 · base64 ?q= 쿼리 그대로 호환.
	onMount(() => {
		const q = page.url.searchParams.get('q');
		const next = q ? `${base}/scan?q=${q}` : `${base}/scan`;
		goto(next, { replaceState: true });
	});
</script>

<svelte:head>
	<title>스크리너로 이동 중… | dartlab</title>
	<meta name="robots" content="noindex" />
	<meta http-equiv="refresh" content="0; url={base}/scan" />
</svelte:head>

<main class="redirect">
	<p>
		스크리너가 <a href="{base}/scan">/screener</a> 로 이동했습니다. 자동 이동되지 않으면
		클릭해 주세요.
	</p>
</main>

<style>
	.redirect {
		max-width: 480px;
		margin: 80px auto;
		padding: 24px;
		text-align: center;
		font-size: 14px;
		color: #94a3b8;
	}
	.redirect a {
		color: #60a5fa;
		text-decoration: none;
	}
	.redirect a:hover {
		text-decoration: underline;
	}
</style>
