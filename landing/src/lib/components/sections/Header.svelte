<script lang="ts">
	import { base } from '$app/paths';
	import { Search, Menu, X, Construction, Sun, Moon } from 'lucide-svelte';
	import { themePref, toggleTheme, isContentPath } from '$lib/theme';
	// SNS·후원·브랜드테마 = dartlab 공통 SSOT(surfaces). BrandSwitch 는 터미널·카드·Header 가 동일 컨트롤 공유.
	import { SupportDialog, DARTLAB_BRAND_LINKS, BrandSwitch, BrandSocial, fetchGithubStars } from '@dartlab/ui-surfaces/terminal';
	import { page } from '$app/state';

	// GitHub 스타 라이브 배지 · 터미널·카드·리포트 우상단 SNS 와 동일(전 라우트 공통). null=미조회/실패(배지 숨김).
	let ghStars = $state<number | null>(null);
	fetchGithubStars(DARTLAB_BRAND_LINKS.repo).then((n) => (ghStars = n));

	interface Props {
		context?: 'landing' | 'default' | 'blog' | 'skills';
	}

	let { context = 'landing' }: Props = $props();
	let scrolled = $state(false);
	let mobileOpen = $state(false);
	let supportOpen = $state(false); // 후원·기여 센터

	function handleScroll() {
		scrolled = window.scrollY > 20;
	}

	function openSearch() {
		window.dispatchEvent(new CustomEvent('open-command-palette'));
	}

	const navLinks = [
		{ label: 'Skills', href: `${base}/skills` },
		{ label: 'Blog', href: `${base}/blog` },
		// 글에서 배우고 노트북에서 실습한다. 배우는 문 옆에 실습하는 문을 둔다.
		{ label: 'Notebooks', href: `${base}/notebooks` },
		{ label: 'Cards', href: `${base}/cards` },
		{ label: 'Scan', href: `${base}/scan` },
		{ label: 'Viewer', href: `${base}/viewer` },
		{ label: 'Universe', href: `${base}/universe` },
		{ label: 'Map', href: `${base}/map` },
		{ label: 'Terminal', href: `${base}/terminal` }
	];

	const DASHBOARD_PATHS = ['/dashboard', '/company'];

	let isDashboard = $derived.by(() => {
		const path = page.url.pathname;
		const stripped = base && path.startsWith(base) ? path.slice(base.length) : path;
		return DASHBOARD_PATHS.some((p) => stripped === p || stripped.startsWith(`${p}/`));
	});

	// 라이트 토글은 라이트가 실제 적용되는 콘텐츠 표면에서만 노출(도구 표면은 항상 다크 → inert 버튼 숨김).
	let themeAvailable = $derived(isContentPath(page.url.pathname, base));
</script>

<svelte:window onscroll={handleScroll} />

<header class="fixed top-0 left-0 right-0 z-50 transition-all duration-200 border-b {scrolled ? 'bg-dl-bg-darker/95 backdrop-blur-xl border-dl-border/60' : 'bg-transparent border-transparent'}">
	<nav class="max-w-6xl mx-auto flex items-center justify-between px-4 h-12">
		<div class="flex items-center gap-2 min-w-0">
			<a href="{base}/" class="flex shrink-0 items-center gap-1.5 no-underline group whitespace-nowrap">
				<picture>
					<source srcset="{base}/avatar.webp" type="image/webp" />
					<img src="{base}/avatar.png" alt="DartLab" width="24" height="24" class="rounded-full" />
				</picture>
				<span class="text-sm font-semibold text-dl-text tracking-tight">DartLab</span>
			</a>
			{#if context !== 'landing'}
				<span class="text-dl-border text-sm font-light shrink-0">/</span>
				<span class="text-sm text-dl-text-muted font-medium whitespace-nowrap shrink-0">{context === 'skills' ? 'Skills' : context === 'blog' ? 'Blog' : ''}</span>
			{/if}
			{#if isDashboard}
				<span
					class="hidden sm:inline-flex items-center gap-1.5 ml-2 px-3 h-6 rounded-md text-[11px] font-semibold tracking-tight whitespace-nowrap"
					style="background: rgba(var(--dl-accent-rgb), .12); color: var(--dl-accent); border: 1px solid rgba(var(--dl-accent-rgb), .4);"
					title="이 페이지는 개발 중 · 데이터·기능 검증 중, 정확성 보장 안 함"
				>
					<Construction class="w-3 h-3" />
					<span>개발중 · 데이터 검증 중, 정확성 보장 안 함</span>
				</span>
			{/if}
		</div>

		<div class="hidden md:flex items-center gap-0.5">
			{#each navLinks as link}
				<a href={link.href}
					class="px-3 py-1.5 text-[13px] text-dl-text-muted hover:text-dl-text transition-colors no-underline rounded-md hover:bg-white/5">
					{link.label}
				</a>
			{/each}
		</div>

		<div class="flex items-center gap-0.5">
			<button
				onclick={openSearch}
				class="hidden md:inline-flex items-center gap-2 px-3 py-1 mr-1 rounded-md border border-dl-border bg-dl-bg-card/50 text-dl-text-dim text-xs hover:text-dl-text-muted hover:border-dl-border transition-colors cursor-pointer h-7"
			>
				<Search class="w-3 h-3" />
				<span>검색...</span>
				<kbd class="ml-1 px-1 py-0.5 rounded bg-dl-bg-darker border border-dl-border text-[10px] font-mono leading-none">⌘K</kbd>
			</button>
			{#if themeAvailable}
				<button onclick={toggleTheme}
					class="w-7 h-7 rounded-md flex items-center justify-center text-dl-text-dim hover:text-dl-text hover:bg-dl-bg-card transition-colors cursor-pointer"
					title={$themePref === 'light' ? '다크 모드로' : '라이트 모드로'} aria-label="테마 전환">
					{#if $themePref === 'light'}<Moon class="w-[15px] h-[15px]" />{:else}<Sun class="w-[15px] h-[15px]" />{/if}
				</button>
			{/if}
			<!-- SNS 행 = 전 표면 SSOT 컴포넌트(터미널·카드·노트북·리포트와 동일 마크업·간격·별 배지).
			     색만 랜딩 테마 토큰으로 덮는다(라이트/다크). 변종 컴포넌트를 만들지 않는다. -->
			<div class="snsTheme">
				<BrandSocial links={DARTLAB_BRAND_LINKS} {ghStars} onSupport={() => (supportOpen = true)}>
					{#snippet leading()}<BrandSwitch />{/snippet}
				</BrandSocial>
			</div>
			<button
				class="md:hidden w-8 h-8 rounded-md flex items-center justify-center text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors cursor-pointer ml-1"
				onclick={() => mobileOpen = !mobileOpen}
			>
				{#if mobileOpen}<X class="w-4 h-4" />{:else}<Menu class="w-4 h-4" />{/if}
			</button>
		</div>
	</nav>

	{#if mobileOpen}
		<div class="md:hidden border-t border-dl-border bg-dl-bg-darker/95 backdrop-blur-xl">
			<div class="flex flex-col px-4 py-2">
				{#each navLinks as link}
					<a href={link.href}
						class="py-2 text-sm text-dl-text-muted hover:text-dl-text transition-colors no-underline"
						onclick={() => mobileOpen = false}>
						{link.label}
					</a>
				{/each}
				<button
					onclick={() => { mobileOpen = false; openSearch(); }}
					class="py-2 text-sm text-dl-text-muted hover:text-dl-text transition-colors text-left cursor-pointer flex items-center gap-2"
				>
					<Search class="w-3.5 h-3.5" />
					검색
				</button>
			</div>
		</div>
	{/if}

	<SupportDialog lang="kr" links={DARTLAB_BRAND_LINKS} {base} open={supportOpen} onClose={() => (supportOpen = false)} />
</header>

<style>
	/* BrandSocial 은 다크 서피스 기본색을 갖는다. 랜딩 헤더는 라이트/다크 토글이 있어 색만 토큰으로 덮는다. */
	.snsTheme {
		display: contents;
		--brandSocial-fg: var(--dl-ink-dim);
		--brandSocial-fgHover: var(--dl-ink);
		--brandSocial-count: var(--dl-ink-dim);
	}
</style>
