<script lang="ts">
	// 첫 화면의 소개는 이 한 섹션뿐이다. 라이브러리 설명(엔진, 데모, 설치 안내)은 /developers 에 있다.
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { Check, Copy, ArrowRight } from 'lucide-svelte';
	import CompanySearch from './CompanySearch.svelte';

	let { storyIndex = {} }: { storyIndex?: Record<string, string> } = $props();

	const installCommand = 'pip install dartlab';
	let copied = $state(false);

	async function copyInstall() {
		try {
			await navigator.clipboard.writeText(installCommand);
			copied = true;
			setTimeout(() => (copied = false), 1600);
		} catch {
			copied = false;
		}
	}
</script>

<section class="home-intro">
	<div class="intro-glow"></div>
	<div class="intro-inner">
		<div class="intro-head">
			<picture>
				<source srcset="{base}/avatar.webp" type="image/webp" />
				<img src="{base}/avatar.png" alt="DartLab" width="72" height="72" fetchpriority="high" class="intro-avatar" />
			</picture>
			<h1 class="intro-title">
				<span>종목코드 하나 →</span>
				<span class="intro-accent">기업의 전체 이야기</span>
			</h1>
		</div>
		<p class="intro-desc">
			한국 DART와 미국 SEC EDGAR 공시로 회사마다 재무, 사업보고서, 공시를 한곳에 모아 읽습니다.
		</p>

		<CompanySearch {storyIndex} />

		<div class="intro-actions">
			<button type="button" class="install-chip" onclick={copyInstall} aria-label="설치 명령 복사">
				<span class="install-prompt">$</span>
				<code>{installCommand}</code>
				{#if copied}<Check size={14} />{:else}<Copy size={14} />{/if}
			</button>
			<a class="intro-link" href="{base}/developers">라이브러리 소개 <ArrowRight size={14} /></a>
			<a class="intro-link" href={brand.colab} target="_blank" rel="noopener">Colab 열기 <ArrowRight size={14} /></a>
		</div>
	</div>
</section>

<style>
	/* 안쪽 여백을 아래 기업이야기·최신 글 머리(72rem 안 1.5rem)와 같게 두어 왼쪽 끝을 맞춘다. */
	.home-intro {
		position: relative;
		padding: 6.5rem 0 2.25rem;
		overflow: hidden;
	}
	.intro-glow {
		position: absolute;
		inset: 0;
		background: radial-gradient(ellipse at top, rgba(234, 70, 71, 0.07) 0%, transparent 60%);
		pointer-events: none;
	}
	.intro-inner {
		position: relative;
		max-width: 72rem;
		margin: 0 auto;
		padding: 0 1.5rem;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 1.1rem;
	}
	.intro-head {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	.intro-avatar {
		width: 72px;
		height: 72px;
		filter: drop-shadow(0 0 22px rgba(234, 70, 71, 0.3));
	}
	.intro-title {
		margin: 0;
		display: flex;
		flex-wrap: wrap;
		column-gap: 0.5em;
		font-size: clamp(1.9rem, 4.2vw, 3.1rem);
		font-weight: 800;
		letter-spacing: -0.02em;
		line-height: 1.15;
		color: var(--dl-ink);
	}
	.intro-accent {
		background: linear-gradient(90deg, var(--dl-red), var(--p-red-400, #f87171));
		-webkit-background-clip: text;
		background-clip: text;
		color: transparent;
	}
	.intro-desc {
		margin: 0;
		max-width: 44rem;
		font-size: 1.05rem;
		line-height: 1.6;
		color: var(--dl-ink-mute);
	}
	.intro-actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.6rem 1.1rem;
	}
	.install-chip {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.45rem 0.8rem;
		border-radius: 8px;
		border: 1px solid var(--dl-mkt-border);
		background: var(--dl-mkt-card);
		color: var(--dl-ink);
		font-size: 0.85rem;
		cursor: pointer;
	}
	.install-chip code {
		font-family: var(--font-mono, monospace);
	}
	.install-prompt {
		font-family: var(--font-mono, monospace);
		color: var(--dl-ink-dim);
	}
	.intro-link {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--dl-ink-mute);
		text-decoration: none;
	}
	.intro-link:hover {
		color: var(--dl-red);
	}
	@media (max-width: 640px) {
		.home-intro {
			padding: 5.5rem 0 1.5rem;
		}
		.intro-inner {
			padding: 0 1rem;
		}
		.intro-avatar {
			width: 52px;
			height: 52px;
		}
	}
</style>
