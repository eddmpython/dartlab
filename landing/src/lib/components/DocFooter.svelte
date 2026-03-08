<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { Github, Youtube, Mail } from 'lucide-svelte';
</script>

<footer class="doc-footer">
	<div class="doc-footer-inner">
		<div class="doc-footer-top">
			<div class="doc-footer-brand">
				<a href="{base}/" class="doc-footer-logo">
					<img src="{base}/avatar.png" alt="DartLab" width="24" height="24" />
					<span>DartLab</span>
				</a>
				<p class="doc-footer-desc">{brand.description}</p>
			</div>

			<div class="doc-footer-links">
				<div class="doc-footer-col">
					<h5>Project</h5>
					<a href="{base}/docs/">Docs</a>
					<a href="{base}/blog/">Blog</a>
					<a href={brand.repo} target="_blank" rel="noopener">GitHub</a>
					<a href={brand.pypi} target="_blank" rel="noopener">PyPI</a>
				</div>
				<div class="doc-footer-col">
					<h5>Connect</h5>
					<a href="https://www.youtube.com/@eddmpython" target="_blank" rel="noopener">YouTube</a>
					<a href="https://www.threads.net/@eddmpython" target="_blank" rel="noopener">Threads</a>
					<a href="mailto:eddmpython@gmail.com">Email</a>
				</div>
			</div>
		</div>

		<div class="doc-footer-coffee">
			<a href={brand.coffee} target="_blank" rel="noopener">
				<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="140" height="35" />
			</a>
		</div>

		<div class="doc-footer-bottom">
			<span>MIT License</span>
			<div class="doc-footer-social">
				<a href="https://github.com/eddmpython" target="_blank" rel="noopener" title="GitHub"><Github size={15} /></a>
				<a href="https://www.youtube.com/@eddmpython" target="_blank" rel="noopener" title="YouTube"><Youtube size={15} /></a>
				<a href="mailto:eddmpython@gmail.com" title="Email"><Mail size={15} /></a>
			</div>
			<span>Made by <a href="https://github.com/eddmpython" target="_blank" rel="noopener">eddmpython</a></span>
		</div>
	</div>
</footer>

<style>
	.doc-footer {
		border-top: 1px solid rgba(148, 163, 184, 0.08);
		margin-top: 4rem;
		padding: 2.5rem 1.5rem 1.5rem;
	}

	.doc-footer-inner {
		max-width: 720px;
		margin: 0 auto;
	}

	.doc-footer-top {
		display: flex;
		justify-content: space-between;
		gap: 2rem;
		margin-bottom: 1.5rem;
	}

	.doc-footer-brand {
		flex: 1;
		min-width: 0;
	}

	.doc-footer-logo {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		text-decoration: none;
		color: #e2e8f0;
		font-weight: 700;
		font-size: 0.95rem;
		margin-bottom: 0.5rem;
	}

	.doc-footer-logo img {
		border-radius: 50%;
	}

	.doc-footer-desc {
		font-size: 0.78rem;
		color: #64748b;
		line-height: 1.5;
		margin: 0;
		max-width: 280px;
	}

	.doc-footer-links {
		display: flex;
		gap: 2.5rem;
		flex-shrink: 0;
	}

	.doc-footer-col {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.doc-footer-col h5 {
		font-size: 0.68rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #64748b;
		margin: 0 0 0.25rem;
	}

	.doc-footer-col a {
		font-size: 0.8rem;
		color: #94a3b8;
		text-decoration: none;
		transition: color 0.15s;
	}

	.doc-footer-col a:hover {
		color: #ea4647;
	}

	.doc-footer-coffee {
		display: flex;
		justify-content: center;
		padding: 1rem 0 1.5rem;
	}

	.doc-footer-coffee a {
		display: inline-block;
		transition: opacity 0.15s;
	}

	.doc-footer-coffee a:hover {
		opacity: 0.85;
	}

	.doc-footer-bottom {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-top: 1rem;
		border-top: 1px solid rgba(148, 163, 184, 0.08);
		font-size: 0.72rem;
		color: #475569;
	}

	.doc-footer-bottom a {
		color: #64748b;
		text-decoration: none;
		transition: color 0.15s;
	}

	.doc-footer-bottom a:hover {
		color: #e2e8f0;
	}

	.doc-footer-social {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.doc-footer-social a {
		display: flex;
		color: #475569;
		transition: color 0.15s;
	}

	.doc-footer-social a:hover {
		color: #ea4647;
	}

	@media (max-width: 640px) {
		.doc-footer-top {
			flex-direction: column;
			gap: 1.5rem;
		}

		.doc-footer-links {
			gap: 2rem;
		}

		.doc-footer-bottom {
			flex-direction: column;
			gap: 0.5rem;
			text-align: center;
		}

		.doc-footer-social {
			order: -1;
		}
	}
</style>
