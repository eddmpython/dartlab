<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { Button } from '$lib/components/ui/button';
	import { Github, Search, Menu, X } from 'lucide-svelte';

	interface Props {
		context?: 'landing' | 'docs' | 'blog';
	}

	let { context = 'landing' }: Props = $props();
	let scrolled = $state(false);
	let mobileOpen = $state(false);

	function handleScroll() {
		scrolled = window.scrollY > 20;
	}

	function openSearch() {
		window.dispatchEvent(new CustomEvent('open-command-palette'));
	}

	const navLinks = [
		{ label: 'Docs', href: `${base}/docs/` },
		{ label: 'Credit Reports', href: `${base}/blog/category/credit-reports` },
		{ label: 'Blog', href: `${base}/blog/` },
		{ label: 'Changelog', href: `${base}/docs/changelog` }
	];
</script>

<svelte:window onscroll={handleScroll} />

<header class="fixed top-0 left-0 right-0 z-50 transition-all duration-200 border-b {scrolled ? 'bg-dl-bg-darker/95 backdrop-blur-xl border-dl-border/60' : 'bg-transparent border-transparent'}">
	<nav class="max-w-6xl mx-auto flex items-center justify-between px-4 h-12">
		<div class="flex items-center gap-2">
			<a href="{base}/" class="flex items-center gap-1.5 no-underline group">
				<picture>
					<source srcset="{base}/avatar.webp" type="image/webp" />
					<img src="{base}/avatar.png" alt="DartLab" width="24" height="24" class="rounded-full" />
				</picture>
				<span class="text-sm font-semibold text-dl-text tracking-tight">DartLab</span>
			</a>
			{#if context !== 'landing'}
				<span class="text-dl-border text-sm font-light">/</span>
				<span class="text-sm text-dl-text-muted font-medium">{context === 'docs' ? 'Docs' : 'Blog'}</span>
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

		<div class="flex items-center gap-1.5">
			<button
				onclick={openSearch}
				class="hidden md:inline-flex items-center gap-2 px-3 py-1 rounded-md border border-dl-border bg-dl-bg-card/50 text-dl-text-dim text-xs hover:text-dl-text-muted hover:border-dl-border transition-colors cursor-pointer h-7"
			>
				<Search class="w-3 h-3" />
				<span>Search...</span>
				<kbd class="ml-1 px-1 py-0.5 rounded bg-dl-bg-darker border border-dl-border text-[10px] font-mono leading-none">⌘K</kbd>
			</button>
			<a href={brand.repo} target="_blank" rel="noopener"
				class="w-8 h-8 rounded-md flex items-center justify-center text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors no-underline"
				title="GitHub">
				<Github class="w-4 h-4" />
			</a>
			{#if context === 'landing'}
				<Button size="sm" href="#install" class="hidden md:inline-flex text-xs h-7">
					Install
				</Button>
			{/if}
			<button
				class="md:hidden w-8 h-8 rounded-md flex items-center justify-center text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors cursor-pointer"
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
					Search
				</button>
			</div>
		</div>
	{/if}
</header>
