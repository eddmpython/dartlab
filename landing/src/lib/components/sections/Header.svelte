<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { Button } from '$lib/components/ui/button';
	import { Github, BookOpen, Download } from 'lucide-svelte';

	let scrolled = $state(false);

	function handleScroll() {
		scrolled = window.scrollY > 20;
	}
</script>

<svelte:window onscroll={handleScroll} />

<header class="fixed top-0 left-0 right-0 z-50 transition-all duration-300 {scrolled ? 'bg-dl-bg-darker/90 backdrop-blur-xl border-b border-dl-border/50 shadow-lg shadow-black/20' : 'bg-transparent'}">
	<nav class="max-w-6xl mx-auto flex items-center justify-between px-6 h-16">
		<a href="{base}/" class="flex items-center gap-1.5 no-underline group">
			<img src="{base}/icon-final.png" alt="DartLab" width="28" height="28" class="transition-transform group-hover:scale-110" />
			<span class="text-lg font-bold text-dl-text tracking-tight">DartLab</span>
		</a>

		<div class="hidden md:flex items-center gap-1">
			<a href="{base}/#features"
				class="px-3 py-2 text-sm text-dl-text-muted hover:text-dl-text transition-colors no-underline rounded-lg hover:bg-white/5">
				기능
			</a>
			<a href="{base}/#install"
				class="px-3 py-2 text-sm text-dl-text-muted hover:text-dl-text transition-colors no-underline rounded-lg hover:bg-white/5">
				설치
			</a>
			<a href="{base}/docs/"
				class="px-3 py-2 text-sm text-dl-text-muted hover:text-dl-text transition-colors no-underline rounded-lg hover:bg-white/5">
				문서
			</a>
		</div>

		<div class="flex items-center gap-2">
			<a href={brand.repo} target="_blank" rel="noopener"
				class="w-9 h-9 rounded-lg flex items-center justify-center text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-all no-underline"
				title="GitHub">
				<Github class="w-4.5 h-4.5" />
			</a>
			<a href="{base}/docs/"
				class="w-9 h-9 rounded-lg flex items-center justify-center text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-all no-underline"
				title="Documentation">
				<BookOpen class="w-4.5 h-4.5" />
			</a>
			<Button size="sm" href="#install">
				<Download class="w-3.5 h-3.5" />
				Install
			</Button>
		</div>
	</nav>
</header>
