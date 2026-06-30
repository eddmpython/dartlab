<script lang="ts">
	// 종목 토론 드로어 · giscus(GitHub Discussions 임베드) 직결.
	// mapping=specific + term=`terminal:{code}` + strict=1: 종목당 스레드 1개, Discussion 은
	// 첫 댓글 시에만 giscus 봇이 lazy 생성하므로 전종목 폭증 없음. strict(SHA-1 정확 일치)는
	// 'terminal:005930' vs 'terminal:005935' 류 유사 term 의 fuzzy 매칭 오염 차단.
	// 드로어는 mount 유지 + 표시 토글 · iframe 을 회사 전환·재오픈에도 보존(재주입 0),
	// 전환은 postMessage setConfig 만 보낸다 (giscus ADVANCED-USAGE 공식 API).
	import type { Lang } from '../lib/types';

	interface Props {
		code: string;
		name: string;
		lang: Lang;
		open: boolean;
		onClose: () => void;
	}
	let { code, name, lang, open, onClose }: Props = $props();

	const GISCUS_ORIGIN = 'https://giscus.app';
	// giscus 식별자 · GitHub GraphQL 실측 (public repo 메타, 비밀 아님).
	// Terminal 카테고리 = Announcement 포맷: giscus 봇·메인테이너만 스레드 생성, 댓글은 누구나
	// · 일반 사용자가 종목 스레드 사이에 잡담 Discussion 을 직접 만드는 오염을 구조 차단.
	const REPO = 'eddmpython/dartlab';
	const REPO_ID = 'R_kgDORgID2A';
	const CATEGORY = 'Terminal';
	const CATEGORY_ID = 'DIC_kwDORgID2M4C_Bt_';

	let host = $state<HTMLDivElement | null>(null);
	let injected = false; // 최초 오픈 1회만 script 주입 · 미사용 사용자 iframe 비용 0

	const term = $derived(`terminal:${code}`);
	const desc = $derived(`${name}(${code}) 종목 토론 · dartlab /terminal`);

	function postConfig(t: string, d: string) {
		const iframe = host?.querySelector<HTMLIFrameElement>('iframe.giscus-frame');
		iframe?.contentWindow?.postMessage({ giscus: { setConfig: { term: t, description: d } } }, GISCUS_ORIGIN);
	}

	$effect(() => {
		if (!open || !host || injected) return;
		injected = true;
		const s = document.createElement('script');
		s.src = `${GISCUS_ORIGIN}/client.js`;
		s.async = true;
		s.crossOrigin = 'anonymous';
		const attrs: Record<string, string> = {
			'data-repo': REPO,
			'data-repo-id': REPO_ID,
			'data-category': CATEGORY,
			'data-category-id': CATEGORY_ID,
			'data-mapping': 'specific',
			'data-term': term,
			'data-strict': '1',
			'data-reactions-enabled': '1',
			'data-emit-metadata': '0',
			'data-input-position': 'top',
			'data-theme': 'noborder_dark',
			'data-lang': 'ko',
			'data-loading': 'lazy'
		};
		for (const [k, v] of Object.entries(attrs)) s.setAttribute(k, v);
		host.appendChild(s);
		// 주입 직후 회사가 바뀐 채 iframe 이 늦게 뜨는 경합 · iframe 생성을 관찰해 load 시점에
		// 현재 term 재적용 (setConfig 는 idempotent 라 동일 term 재전송 무해).
		const mo = new MutationObserver(() => {
			const iframe = host?.querySelector<HTMLIFrameElement>('iframe.giscus-frame');
			if (!iframe) return;
			mo.disconnect();
			iframe.addEventListener('load', () => postConfig(term, desc), { once: true });
		});
		mo.observe(host, { childList: true, subtree: true });
	});

	// 회사 전환 · iframe 재주입 없이 setConfig (스레드 즉시 교체)
	$effect(() => {
		postConfig(term, desc);
	});

	// ESC 닫기 · 열려 있을 때만 (FinFullscreen 패턴)
	$effect(() => {
		if (!open) return;
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') {
				e.stopPropagation();
				onClose();
			}
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

<aside class={'dscDrawer' + (open ? ' on' : '')} aria-label={lang === 'en' ? 'stock discussion' : '종목 토론'} aria-hidden={!open}>
	<header class="dscHead">
		<span class="dscTitle">{lang === 'en' ? 'DISCUSS' : '종목 토론'} · <b>{name}</b> <span class="dscCode mono">{code}</span></span>
		<span class="dscActs">
			<a class="lensScan" href="https://github.com/{REPO}/discussions" target="_blank" rel="noopener" title="GitHub Discussions">GitHub ↗</a>
			<button class="finFullBtn" onclick={onClose} title={lang === 'en' ? 'close (Esc)' : '닫기 (Esc)'}>✕</button>
		</span>
	</header>
	<div class="dscBody" bind:this={host}></div>
	<div class="dscNote">giscus · GitHub Discussions · {lang === 'en' ? 'sign in with GitHub to comment' : '댓글 작성에는 GitHub 로그인 필요'}</div>
</aside>
