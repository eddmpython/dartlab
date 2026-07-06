<script lang="ts">
	import { base } from '$app/paths';
	import { Search, Menu, X, Construction, Heart, Sun, Moon } from 'lucide-svelte';
	import { themePref, toggleTheme, isContentPath } from '$lib/theme';
	import GithubIcon from '$lib/components/GithubIcon.svelte';
	// SNS·후원·브랜드테마 = dartlab 공통 SSOT(surfaces). BrandSwitch 는 터미널·카드·Header 가 동일 컨트롤 공유.
	import { SupportDialog, DARTLAB_BRAND_LINKS, BrandSwitch } from '@dartlab/ui-surfaces/terminal';
	import { page } from '$app/state';

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
		{ label: 'Cards', href: `${base}/cards` },
		{ label: 'Scan', href: `${base}/scan` },
		{ label: 'Viewer', href: `${base}/viewer` },
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
			<BrandSwitch />
			<a href={DARTLAB_BRAND_LINKS.repo} target="_blank" rel="noopener"
				class="w-7 h-7 rounded-md flex items-center justify-center text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors no-underline"
				title="GitHub">
				<GithubIcon class="w-[15px] h-[15px]" />
			</a>
			<button onclick={() => (supportOpen = true)}
				class="w-7 h-7 rounded-md flex items-center justify-center text-[#fb7185] hover:text-[#fda4c0] hover:bg-white/5 transition-colors cursor-pointer"
				title="후원·기여" aria-label="후원·기여">
				<Heart class="w-[15px] h-[15px]" fill="rgba(251, 113, 133, 0.32)" />
			</button>
			<a href={DARTLAB_BRAND_LINKS.youtube} target="_blank" rel="noopener"
				class="w-7 h-7 rounded-md hidden sm:flex items-center justify-center text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors no-underline"
				title="YouTube · @eddmpython">
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="w-[15px] h-[15px]" fill="currentColor" aria-hidden="true">
					<path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
				</svg>
			</a>
			<a href={DARTLAB_BRAND_LINKS.threads} target="_blank" rel="noopener"
				class="w-7 h-7 rounded-md hidden sm:flex items-center justify-center text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors no-underline"
				title="Threads · @dartlab.ai">
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="w-[15px] h-[15px]" fill="currentColor" aria-hidden="true">
					<path d="M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.472 12.01v-.017c.03-3.579.879-6.43 2.525-8.482C5.845 1.205 8.6.024 12.18 0h.014c2.746.02 5.043.725 6.826 2.098 1.677 1.29 2.858 3.13 3.509 5.467l-2.04.569c-1.104-3.96-3.898-5.984-8.304-6.015-2.91.022-5.11.936-6.54 2.717C4.307 6.504 3.616 8.914 3.589 12c.027 3.086.718 5.496 2.057 7.164 1.43 1.783 3.631 2.698 6.54 2.717 2.623-.02 4.358-.631 5.8-2.045 1.647-1.613 1.618-3.593 1.09-4.798-.31-.71-.873-1.3-1.634-1.75-.192 1.352-.622 2.446-1.284 3.272-.886 1.102-2.14 1.704-3.73 1.79-1.202.065-2.361-.218-3.259-.801-1.063-.689-1.685-1.74-1.752-2.964-.065-1.19.408-2.285 1.33-3.082.88-.76 2.119-1.207 3.583-1.291a13.853 13.853 0 0 1 3.02.142c-.126-.742-.375-1.332-.75-1.757-.513-.586-1.308-.883-2.359-.89h-.029c-.844 0-1.992.232-2.721 1.32L7.734 7.847c.98-1.454 2.568-2.256 4.478-2.256h.044c3.194.02 5.097 1.975 5.287 5.388.108.046.216.094.321.142 1.49.7 2.58 1.761 3.154 3.07.797 1.82.871 4.79-1.548 7.158-1.85 1.81-4.094 2.628-7.277 2.65Zm1.003-11.69c-.242 0-.487.007-.739.021-1.836.103-2.98.946-2.916 2.143.067 1.256 1.452 1.839 2.784 1.767 1.224-.065 2.818-.543 3.086-3.71a10.5 10.5 0 0 0-2.215-.221z"/>
				</svg>
			</a>
			<a href={DARTLAB_BRAND_LINKS.instagram} target="_blank" rel="noopener"
				class="w-7 h-7 rounded-md hidden sm:flex items-center justify-center text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors no-underline"
				title="Instagram · @dartlab.ai">
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="w-[15px] h-[15px]" fill="currentColor" aria-hidden="true">
					<path d="M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 1.381.164.422.36 1.057.413 2.227.057 1.266.07 1.646.07 4.85s-.015 3.585-.074 4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.413-1.274.057-1.649.07-4.859.07-3.211 0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.165-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 0-3.196.016-3.586.061-4.861.061-1.17.255-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06l.045.03zm0 3.678c-3.405 0-6.162 2.76-6.162 6.162 0 3.405 2.76 6.162 6.162 6.162 3.405 0 6.162-2.76 6.162-6.162 0-3.405-2.76-6.162-6.162-6.162zM12 16c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm7.846-10.405c0 .795-.646 1.44-1.44 1.44-.795 0-1.44-.646-1.44-1.44 0-.794.646-1.439 1.44-1.439.793-.001 1.44.645 1.44 1.439z"/>
				</svg>
			</a>
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
