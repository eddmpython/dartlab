<script lang="ts">
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { onMount } from 'svelte';

	onMount(() => void goto(`${base}/chat`, { replaceState: true }));
</script>

<section aria-live="polite">
	<div class="spinner" aria-hidden="true"></div>
	<p>근거 기반 Ask를 여는 중입니다.</p>
	<a href={`${base}/chat`}>바로 열기</a>
</section>

<style>
	section {
		max-width: 720px;
		margin: 0 auto;
		padding: 3rem 1.5rem;
	}
	.spinner { width: 1.5rem; height: 1.5rem; border: 2px solid var(--dl-line, #2a2c33); border-top-color: var(--dl-accent, #ff5a36); border-radius: 50%; animation: spin .8s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }
	p {
		color: var(--dl-ink-dim, #9aa0aa);
		margin: 0 0 1.5rem;
	}
	a {
		padding: 0.6rem 1rem;
		border: 1px solid var(--dl-accent, #ff5a36);
		border-radius: 8px;
		background: transparent;
		color: var(--dl-accent, #ff5a36);
		text-decoration: none;
		font-family: var(--dl-font-mono, ui-monospace, monospace);
	}
	a:hover {
		background: var(--dl-accent, #ff5a36);
		color: #fff;
	}
</style>
