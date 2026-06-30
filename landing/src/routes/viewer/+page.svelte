<script lang="ts">
	// /viewer 진입 · 마지막 본 종목(캐시) 또는 기본 삼성전자(005930)로 즉시 이동. 인덱스 UI 없음.
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';

	onMount(() => {
		let code = '005930';
		try {
			code = localStorage.getItem('dartlab:lastViewer') || '005930';
		} catch {
			/* localStorage 불가 → 기본 */
		}
		void goto(`${base}/viewer/company/${code}`, { replaceState: true });
	});
</script>

<svelte:head><title>공시 뷰어 · dartlab</title></svelte:head>

<div class="redirect">
	<picture>
		<source srcset="{base}/avatar-study.webp" type="image/webp" />
		<img class="redirect-avatar" src="{base}/avatar-study.png" alt="" width="72" height="72" />
	</picture>
	<div class="spinner"></div>
	<p>공시 뷰어 여는 중…</p>
</div>

<style>
	.redirect {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 14px;
		background: #050811;
		color: #94a3b8;
		font-size: 13px;
	}
	.redirect-avatar {
		border-radius: 50%;
		opacity: 0.95;
		filter: drop-shadow(0 4px 16px rgba(var(--dl-accent-rgb), 0.18));
	}
	.redirect p {
		margin: 0;
	}
	.spinner {
		width: 28px;
		height: 28px;
		border: 2px solid #1e2433;
		border-top-color: var(--dl-accent);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
