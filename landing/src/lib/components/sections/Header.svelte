<script lang="ts">
	import { base } from '$app/paths';
</script>

<header class="fixed top-0 left-0 right-0 z-50 border-b border-dl-border/50 backdrop-blur-xl bg-dl-bg-dark/80">
	<nav class="mx-auto max-w-6xl flex items-center justify-between px-6 h-16">
		<a href="{base}/" class="flex items-center gap-2.5">
			<div class="w-8 h-8 rounded-lg bg-gradient-to-br from-dl-primary to-dl-accent flex items-center justify-center">
				<span class="text-sm font-bold text-dl-bg-dark">D</span>
			</div>
			<span class="text-lg font-bold text-dl-text">DartLab</span>
		</a>

		<div class="hidden md:flex items-center gap-8 text-sm text-dl-text-muted">
			<a href="{base}/#features" class="hover:text-dl-text transition-colors">기능</a>
			<a href="{base}/#install" class="hover:text-dl-text transition-colors">설치</a>
			<a href="https://eddmpython.github.io/dartlab/docs/" class="hover:text-dl-text transition-colors">문서</a>
		</div>

		<div class="flex items-center gap-3">
			<a
				href="https://github.com/eddmpython/dartlab"
				target="_blank"
				rel="noopener"
				class="flex items-center gap-2 px-4 py-2 rounded-lg bg-dl-bg-card hover:bg-dl-bg-card-hover border border-dl-border text-sm text-dl-text-muted hover:text-dl-text transition-all"
			>
				<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
				GitHub
			</a>
		</div>
	</nav>
</header>
