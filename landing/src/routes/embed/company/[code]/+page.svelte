<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { CompanyCard } from '@dartlab/ui-surfaces/map';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	// URL 파라미터 · ?theme=dark|light · ?brand=0|1 · ?h=auto (iframe 자동 리사이즈)
	let theme = $derived(page.url.searchParams.get('theme') || 'dark');
	let showBrand = $derived(page.url.searchParams.get('brand') !== '0');

	// iframe parent 에게 높이 알림 (postMessage)
	onMount(() => {
		const autoResize = page.url.searchParams.get('h') === 'auto';
		if (!autoResize) return;
		const send = () => {
			try {
				window.parent?.postMessage(
					{ type: 'dartlab.embed.resize', height: document.body.scrollHeight },
					'*'
				);
			} catch {
				/* noop */
			}
		};
		send();
		const ro = new ResizeObserver(() => send());
		ro.observe(document.body);
		return () => ro.disconnect();
	});
</script>

<svelte:head>
	<title>{(data as any).node?.label || (data as any).code} | dartlab 임베드</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<div class="embed-root" class:light={theme === 'light'}>
	{#if (data as any).node}
		<CompanyCard
			basePath={base}
			node={(data as any).node}
			detail={(data as any).detail}
			loading={false}
			industryStat={(data as any).industryStats?.[(data as any).node.industry]}
			dataAsOf={(data as any).meta?.dataAsOf}
			compareDisabled={true}
			onClose={() => {}}
		/>
	{:else}
		<div class="miss">
			<p>종목을 찾을 수 없습니다: <code>{(data as any).code}</code></p>
			<a href="{base}/map" target="_top">산업지도로 →</a>
		</div>
	{/if}

	{#if showBrand}
		<a class="brand-footer" href="{base}/map?focus={(data as any).code}" target="_top">
			<picture>
				<source srcset="{base}/avatar.webp" type="image/webp" />
				<img src="{base}/avatar.png" alt="dartlab" width="14" height="14" />
			</picture>
			<span>dartlab 산업지도에서 보기 →</span>
		</a>
	{/if}
</div>

<style>
	:global(html),
	:global(body) {
		margin: 0;
		padding: 0;
		background: transparent;
	}
	.embed-root {
		background: #050811;
		color: #f1f5f9;
		padding: 0;
		min-height: 100vh;
		font-family: 'Pretendard Variable', sans-serif;
	}
	.embed-root.light {
		background: #ffffff;
		color: #0f172a;
	}
	.miss {
		padding: 40px 24px;
		text-align: center;
		color: #94a3b8;
	}
	.miss code {
		background: #1e2433;
		padding: 2px 6px;
		border-radius: 4px;
	}
	.miss a {
		color: #60a5fa;
	}
	.brand-footer {
		display: flex;
		align-items: center;
		gap: 6px;
		justify-content: center;
		padding: 10px 12px;
		background: rgba(15, 18, 25, 0.6);
		border-top: 1px solid #1e2433;
		color: #94a3b8;
		text-decoration: none;
		font-size: 11px;
	}
	.brand-footer:hover {
		color: #60a5fa;
	}
	.brand-footer img {
		border-radius: 50%;
	}
	.embed-root.light .brand-footer {
		background: #f8fafc;
		border-top-color: #e2e8f0;
		color: #64748b;
	}
</style>
