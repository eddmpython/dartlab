<script lang="ts">
	// 브랜드 마크 SSOT (아바타 · DartLab · / · 표면 태그). 터미널·카드·리포트·노트북 허브가 공유한다.
	//
	// 예전엔 네 표면이 같은 마크업(picture > source/img + 3 span)을 각자 복붙하고, 스타일은 terminal.css
	// `.dlTerm .brand*` 전역 규칙에 얹혀 있었다. 그래서 `.dlTerm` 래퍼를 안 두르면 모양이 깨지고,
	// 로고 크기(22 vs 24px)도 표면마다 갈렸다. 이제 컴포넌트가 마크업·치수·색을 전부 소유한다.
	//
	// 색은 tokens.css 토큰만 쓴다. 라이트 테마가 켜지는 콘텐츠 표면(노트북 허브 등)에서도 그대로 읽힌다.
	import type { Snippet } from 'svelte';

	let {
		tag,
		href,
		base = '',
		size = 22,
		title = 'DartLab',
		trailing
	}: {
		/** 브랜드 뒤에 붙는 표면 이름 (terminal · cards · report · notebook). */
		tag: string;
		href: string;
		/** 정적 자산 경로 접두 (GitHub Pages base). */
		base?: string;
		size?: number;
		title?: string;
		trailing?: Snippet;
	} = $props();
</script>

<a class="brand" {href} {title}>
	<picture>
		<source srcset="{base}/avatar.webp" type="image/webp" />
		<img class="brandLogo" src="{base}/avatar.png" alt="DartLab" width={size} height={size} style="width:{size}px;height:{size}px" />
	</picture>
	<span class="brandName">DartLab</span>
	<span class="brandSlash">/</span>
	<span class="brandTag">{tag}</span>
	{@render trailing?.()}
</a>

<style>
	.brand {
		display: flex;
		align-items: center;
		gap: 6px;
		text-decoration: none;
		flex-shrink: 0;
	}
	.brandLogo {
		border-radius: 50%;
		display: block;
	}
	.brandName {
		font-family: var(--dl-font-ui);
		font-weight: 700;
		font-size: 14px;
		letter-spacing: -0.01em;
		color: var(--dl-ink-print);
	}
	.brandSlash {
		color: var(--dl-ink-dim);
		font-weight: 300;
		font-size: 13px;
	}
	.brandTag {
		font-family: var(--dl-font-mono);
		font-weight: 600;
		font-size: 10px;
		letter-spacing: 0.16em;
		color: var(--dl-accent);
		text-transform: uppercase;
	}
</style>
