<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { Search, FileText, BookOpen, ArrowRight } from 'lucide-svelte';
	import { navigation, flattenNav } from '$lib/docs/navigation';
	import { posts } from '$lib/blog/posts';

	let open = $state(false);
	let query = $state('');
	let selectedIndex = $state(0);
	let inputEl = $state<HTMLInputElement | null>(null);

	interface SearchItem {
		title: string;
		href: string;
		category: 'Docs' | 'Blog' | 'Quick Links';
	}

	const docsItems: SearchItem[] = flattenNav(navigation).map((item) => ({
		title: item.title,
		href: `${base}${item.href}`,
		category: 'Docs'
	}));

	const blogItems: SearchItem[] = posts.map((post) => ({
		title: post.title,
		href: `${base}/blog/${post.slug}`,
		category: 'Blog'
	}));

	const quickLinks: SearchItem[] = [
		{ title: 'Installation', href: `${base}/docs/getting-started/installation`, category: 'Quick Links' },
		{ title: 'Quickstart', href: `${base}/docs/getting-started/quickstart`, category: 'Quick Links' },
		{ title: 'API Overview', href: `${base}/docs/api/overview`, category: 'Quick Links' },
		{ title: 'Changelog', href: `${base}/docs/changelog`, category: 'Quick Links' }
	];

	const allItems = [...quickLinks, ...docsItems, ...blogItems];

	let filtered = $derived.by(() => {
		if (!query.trim()) return allItems.slice(0, 8);
		const q = query.toLowerCase();
		return allItems
			.filter((item) => item.title.toLowerCase().includes(q))
			.slice(0, 12);
	});

	$effect(() => {
		if (filtered.length > 0 && selectedIndex >= filtered.length) {
			selectedIndex = 0;
		}
	});

	function handleOpen() {
		open = true;
		query = '';
		selectedIndex = 0;
		requestAnimationFrame(() => inputEl?.focus());
	}

	function handleClose() {
		open = false;
	}

	function navigate(href: string) {
		handleClose();
		goto(href);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			selectedIndex = (selectedIndex + 1) % filtered.length;
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			selectedIndex = (selectedIndex - 1 + filtered.length) % filtered.length;
		} else if (e.key === 'Enter') {
			e.preventDefault();
			if (filtered[selectedIndex]) {
				navigate(filtered[selectedIndex].href);
			}
		} else if (e.key === 'Escape') {
			handleClose();
		}
	}

	function handleGlobalKeydown(e: KeyboardEvent) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
			e.preventDefault();
			if (open) handleClose();
			else handleOpen();
		}
	}

	$effect(() => {
		const handler = () => handleOpen();
		window.addEventListener('open-command-palette', handler);
		return () => window.removeEventListener('open-command-palette', handler);
	});

	function getCategoryIcon(category: string) {
		if (category === 'Docs') return BookOpen;
		if (category === 'Blog') return FileText;
		return ArrowRight;
	}
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

{#if open}
	<div class="fixed inset-0 z-[100] flex items-start justify-center pt-[20vh]">
		<div class="fixed inset-0 bg-black/60 backdrop-blur-sm" onclick={handleClose} role="presentation"></div>
		<div
			class="relative w-full max-w-lg mx-4 rounded-lg border border-dl-border bg-dl-bg-darker shadow-2xl shadow-black/50 overflow-hidden"
			onkeydown={handleKeydown}
			role="dialog"
			aria-label="Search"
		>
			<div class="flex items-center gap-3 px-4 py-3 border-b border-dl-border">
				<Search class="w-4 h-4 text-dl-text-dim shrink-0" />
				<input
					bind:this={inputEl}
					bind:value={query}
					type="text"
					placeholder="Search docs, blog..."
					class="flex-1 bg-transparent text-sm text-dl-text placeholder:text-dl-text-dim outline-none"
				/>
				<kbd class="px-1.5 py-0.5 rounded bg-dl-bg-card border border-dl-border text-[10px] font-mono text-dl-text-dim leading-none">ESC</kbd>
			</div>

			<div class="max-h-[320px] overflow-y-auto py-2">
				{#if filtered.length === 0}
					<div class="px-4 py-6 text-center text-sm text-dl-text-dim">No results found.</div>
				{:else}
					{#each filtered as item, i}
						{@const Icon = getCategoryIcon(item.category)}
						<button
							class="w-full flex items-center gap-3 px-4 py-2 text-left text-sm cursor-pointer transition-colors {i === selectedIndex ? 'bg-dl-bg-card text-dl-text' : 'text-dl-text-muted hover:bg-dl-bg-card/50'}"
							onclick={() => navigate(item.href)}
							onmouseenter={() => selectedIndex = i}
						>
							<Icon class="w-3.5 h-3.5 shrink-0 text-dl-text-dim" />
							<span class="flex-1 truncate">{item.title}</span>
							<span class="text-[10px] text-dl-text-dim font-mono">{item.category}</span>
						</button>
					{/each}
				{/if}
			</div>
		</div>
	</div>
{/if}
