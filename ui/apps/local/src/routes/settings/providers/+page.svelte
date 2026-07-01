<script lang="ts">
	import { base } from '$app/paths';
	import ProviderSettings from '$lib/chat/ProviderSettings.svelte';
</script>

<svelte:head>
	<title>공급자 설정 · dartlab local</title>
</svelte:head>

<section>
	<a class="back" href={`${base}/chat`}>← 챗</a>
	<h1>AI 공급자</h1>
	<p>분석에 사용할 공급자를 선택하고 로그인하세요. 챗 답변(LLM)의 전제입니다.</p>
	<ProviderSettings />
</section>

<style>
	section {
		max-width: 720px;
		margin: 0 auto;
		padding: 3rem 1.5rem;
	}
	.back {
		color: var(--dl-ink-dim, #9aa0aa);
		text-decoration: none;
		font-size: 0.85rem;
	}
	h1 {
		font-size: 1.5rem;
		margin: 1rem 0 0.4rem;
	}
	p {
		color: var(--dl-ink-dim, #9aa0aa);
		font-size: 0.9rem;
		margin: 0 0 1.5rem;
	}
</style>
