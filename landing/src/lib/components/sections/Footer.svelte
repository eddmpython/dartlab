<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { Github, Youtube, Mail } from 'lucide-svelte';

	const footerLinks = {
		'Docs': [
			{ label: 'Getting Started', href: `${base}/docs/` },
			{ label: 'API Reference', href: `${base}/docs/api/overview` }
		],
		'Project': [
			{ label: 'GitHub', href: brand.repo },
			{ label: 'PyPI', href: brand.pypi },
			{ label: 'Data', href: `${brand.repo}/releases/tag/data-v1` },
			{ label: 'Issues', href: `${brand.repo}/issues` }
		],
		'eddmpython': [
			{ label: 'GitHub Profile', href: 'https://github.com/eddmpython' },
			{ label: 'PyPI Profile', href: 'https://pypi.org/user/eddmpython/' },
			{ label: 'vectrix', href: 'https://github.com/eddmpython/vectrix' }
		],
		'Connect': [
			{ label: 'YouTube', href: 'https://www.youtube.com/@eddmpython' },
			{ label: 'Threads', href: 'https://www.threads.net/@eddmpython' },
			{ label: 'Tistory Blog', href: 'https://eddm.tistory.com' },
			{ label: 'Email', href: 'mailto:eddmpython@gmail.com' }
		]
	};

	const socialLinks = [
		{ icon: Github, href: 'https://github.com/eddmpython', label: 'GitHub' },
		{ icon: Youtube, href: 'https://www.youtube.com/@eddmpython', label: 'YouTube' },
		{ icon: Mail, href: 'mailto:eddmpython@gmail.com', label: 'Email' }
	];
</script>

<footer class="bg-dl-bg-darker border-t border-dl-border pt-14 pb-8 px-6">
	<div class="max-w-6xl mx-auto">
		<div class="grid grid-cols-1 md:grid-cols-5 gap-8 mb-10">
			<div class="md:col-span-1">
				<div class="flex items-center gap-1.5 mb-3">
					<img src="{base}/avatar.png" alt="DartLab" width="28" height="28" class="rounded-full" />
					<strong class="text-dl-text text-lg">DartLab</strong>
				</div>
				<p class="text-sm text-dl-text-dim leading-relaxed mb-4">{brand.description}</p>
				<div class="flex gap-2 mb-4">
					{#each socialLinks as link}
						<a href={link.href} target="_blank" rel="noopener" title={link.label}
							class="w-9 h-9 rounded-lg bg-dl-bg-card border border-dl-border flex items-center justify-center text-dl-text-dim hover:text-dl-primary hover:border-dl-primary transition-all no-underline">
							<link.icon class="w-4 h-4" />
						</a>
					{/each}
				</div>
				<a href={brand.coffee} target="_blank" rel="noopener">
					<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="160" height="40" class="hover:opacity-90 transition-opacity" />
				</a>
			</div>

			{#each Object.entries(footerLinks) as [title, links]}
				<div>
					<h5 class="text-xs font-semibold uppercase tracking-wider text-dl-text-muted mb-4">{title}</h5>
					<div class="flex flex-col gap-2">
						{#each links as link}
							<a href={link.href}
								target={link.href.startsWith('http') ? '_blank' : undefined}
								rel={link.href.startsWith('http') ? 'noopener' : undefined}
								class="text-sm text-dl-text-dim hover:text-dl-primary transition-colors no-underline">
								{link.label}
							</a>
						{/each}
					</div>
				</div>
			{/each}
		</div>

		<div class="flex flex-col md:flex-row justify-between items-center pt-6 border-t border-dl-border text-xs text-dl-text-dim gap-2">
			<span>MIT License</span>
			<span>Made by <a href="https://github.com/eddmpython" class="text-dl-text-muted hover:text-dl-text transition-colors no-underline">eddmpython</a></span>
		</div>
	</div>
</footer>
