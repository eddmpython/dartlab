<script lang="ts">
	// 공시 토론 · 회사별 GitHub Discussions 댓글(giscus) 우측 슬라이드오버.
	// blog/[slug] 의 giscus 설정과 동일(repo/category/lang) · mapping=pathname 이라 회사 URL(/viewer/company/{code})
	// 당 독립 토론 스레드. theme=transparent_dark 로 드로어 배경(#050811)에 블렌드.
	// 드로어는 항상 마운트(CSS transform 토글 + inert) · 닫아도 giscus 가 DOM 에 유지돼 재오픈 즉시(깜빡임 0).
	// 주입은 처음 열 때 1회, 종목 전환 시에만 재주입(loadedKey).
	import { X } from 'lucide-svelte';
	import { fade } from 'svelte/transition';

	let { code, corpName, open, onclose }: { code: string; corpName: string; open: boolean; onclose: () => void } = $props();

	let giscusEl = $state<HTMLElement>();
	let loadedKey = $state<string | null>(null);

	$effect(() => {
		if (!open || !giscusEl) return;
		if (loadedKey === code) return; // 같은 종목 = 유지된 giscus 재사용(재주입 안 함)
		loadedKey = code;
		giscusEl.innerHTML = '';
		const s = document.createElement('script');
		s.src = 'https://giscus.app/client.js';
		s.setAttribute('data-repo', 'eddmpython/dartlab');
		s.setAttribute('data-repo-id', 'R_kgDORgID2A');
		s.setAttribute('data-category', 'General');
		s.setAttribute('data-category-id', 'DIC_kwDORgID2M4C38mI');
		s.setAttribute('data-mapping', 'pathname');
		s.setAttribute('data-strict', '0');
		s.setAttribute('data-reactions-enabled', '1');
		s.setAttribute('data-emit-metadata', '0');
		s.setAttribute('data-input-position', 'top');
		s.setAttribute('data-theme', 'transparent_dark');
		s.setAttribute('data-lang', 'ko');
		s.setAttribute('crossorigin', 'anonymous');
		s.async = true;
		giscusEl.appendChild(s);
	});

	// Esc 닫기 (열렸을 때만).
	$effect(() => {
		if (!open) return;
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') onclose();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

{#if open}
	<button type="button" class="overlay" aria-label="토론 닫기" onclick={onclose} transition:fade={{ duration: 150 }}></button>
{/if}

<aside class="drawer" class:open aria-label="공시 토론" inert={!open}>
	<header class="dh">
		<div class="dh-title">
			<span class="dh-corp">{corpName || code}</span>
			<span class="dh-sub">공시 토론</span>
		</div>
		<button type="button" class="dh-close" onclick={onclose} title="닫기 (Esc)"><X size={16} /></button>
	</header>
	<div class="dbody">
		<div bind:this={giscusEl}></div>
		<p class="dhint">
			GitHub 로그인으로 이 회사 공시를 토론하세요 · 회사별로 스레드가 분리됩니다.<br />
			뷰어 개선·새 기능 건의는
			<a href="https://github.com/eddmpython/dartlab/discussions/new?category=ideas" target="_blank" rel="noopener noreferrer">아이디어 남기기 →</a>
		</p>
	</div>
</aside>

<style>
	.overlay {
		position: fixed;
		inset: 0;
		z-index: 300;
		border: 0;
		padding: 0;
		background: rgba(2, 4, 9, 0.62);
		cursor: default;
	}
	.drawer {
		position: fixed;
		top: 0;
		right: 0;
		bottom: 0;
		z-index: 301;
		width: min(460px, 94vw);
		display: flex;
		flex-direction: column;
		background: #050811;
		border-left: 1px solid #1e2433;
		transform: translateX(100%);
		transition: transform 0.22s ease;
	}
	.drawer.open {
		transform: translateX(0);
		box-shadow: -16px 0 48px rgba(0, 0, 0, 0.5); /* 열렸을 때만 · 닫힘 시 우측 가장자리 그림자 누출 차단 */
	}
	.dh {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 12px 14px;
		border-bottom: 1px solid #1e2433;
	}
	.dh-title {
		display: flex;
		align-items: baseline;
		gap: 8px;
		min-width: 0;
	}
	.dh-corp {
		font-size: 15px;
		font-weight: 700;
		color: #f1f5f9;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.dh-sub {
		flex-shrink: 0;
		font-size: 11px;
		color: #cbd5e1;
	}
	.dh-sub::before {
		content: '·';
		margin-right: 6px;
		color: #64748b;
	}
	.dh-close {
		flex-shrink: 0;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		border: 1px solid #1e2433;
		border-radius: 6px;
		background: transparent;
		color: #cbd5e1;
		cursor: pointer;
	}
	.dh-close:hover {
		border-color: var(--amber);
		color: var(--amber);
	}
	.dbody {
		flex: 1 1 auto;
		min-height: 0;
		overflow-y: auto;
		padding: 12px 14px;
	}
	.dhint {
		margin: 14px 2px 0;
		font-size: 11px;
		line-height: 1.7;
		color: #94a3b8;
	}
	.dhint a {
		color: var(--amber);
		text-decoration: none;
		white-space: nowrap;
	}
	.dhint a:hover {
		text-decoration: underline;
	}
</style>
