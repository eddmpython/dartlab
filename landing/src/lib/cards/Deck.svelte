<script lang="ts">
	// 인스타식 4:5 카드 캐러셀(인라인) · 첫 슬라이드(표지)는 hfMedia 만으로 즉시, 뷰포트에 들어오면
	// buildDeck(라이브)로 전체 슬라이드 업그레이드(피드 가벼움). 코너 크롬 = 회사뱃지·dartlab 아바타·페이지뱃지.
	// 색감·규격은 기존 SNS 캐러셀(colors.ts·1080×1350) 재현. 키보드 ←→ 는 포커스된 덱에만.
	import type { DartLabRuntime } from '@dartlab/ui-contracts';
	import { buildDeck, DECK_PERSPECTIVES } from './build';
	import { chapterAnchors } from './project';
	import type { CarouselDeck, CarouselCard } from './model';
	import CardSlide from './CardSlide.svelte';

	let {
		rt,
		sym,
		slug,
		corpName,
		heroUrls = [],
		leadCards = [],
		perspectiveKey = 'earningsPower',
		onEnlarge,
		onSections
	}: {
		rt: DartLabRuntime;
		sym: string;
		slug: string;
		corpName: string;
		heroUrls?: string[];
		/** 편집 계약 lead 슬라이드(부모가 contract 로 미리 투영) · 미리보기를 빌드 후 첫 슬라이드와 동일하게. */
		leadCards?: CarouselCard[];
		perspectiveKey?: string;
		onEnlarge?: () => void;
		/** 빌드 완료 후 챕터 점프 앵커 콜백 · 캡션 패널 섹션 네비(사진 밖 크롬)가 받아 렌더. */
		onSections?: (anchors: { label: string; index: number }[]) => void;
	} = $props();

	// 외부(캡션 네비)에서 호출하는 점프 · 기존 검증된 go()(scrollIntoView+idx) 재사용. bind:this 로 노출.
	export function jumpTo(i: number) {
		go(i);
	}

	// 표지 미리보기 · buildReport 없이 즉시 첫장 노출(피드 가벼움).
	function previewDeck(): CarouselDeck {
		const base = {
			stockCode: sym,
			corpName,
			perspectiveKey,
			perspectiveLabel: DECK_PERSPECTIVES.find((p) => p.key === perspectiveKey)?.label ?? '',
			asOf: '',
			heroUrls
		};
		// 편집 계약의 실제 lead 슬라이드가 주어지면 그대로 미리보기로 · 빌드 후 첫 슬라이드(들)와 동일해
		// 표지가 '엉뚱한 사진 → 다른 사진'으로 깜빡이며 바뀌는 현상 제거(빌드는 뒤에 차트만 덧붙인다).
		if (leadCards.length) return { ...base, cards: leadCards };
		// 계약 없는 자동 덱만 합성 표지(heroUrls[0]) · 이 경우 빌드 표지도 heroUrls[0] 라 깜빡임 없음.
		return {
			...base,
			cards: [
				{
					kind: 'cover',
					corpName,
					stockCode: sym,
					perspectiveLabel: DECK_PERSPECTIVES.find((p) => p.key === perspectiveKey)?.label ?? '',
					conclusion: '',
					dataBasis: '',
					bg: heroUrls[0]
				}
			]
		};
	}

	let deck = $state<CarouselDeck>(previewDeck());
	let built = $state(false);
	let idx = $state(0);
	let track = $state<HTMLDivElement | null>(null);
	let root = $state<HTMLElement | null>(null);
	let tok = 0;

	// 빌드 전에는 미디어(회사명·사진) 비동기 로드에 맞춰 표지 미리보기를 갱신 · 코드("000270")만 뜨고
	// 사진이 빈 첫 페인트 방지. previewDeck() 이 corpName/heroUrls prop 을 읽으므로 그 갱신을 추종한다.
	$effect(() => {
		if (!built) deck = previewDeck();
	});

	// 관점이 바뀌면(사용자 조작) 재빌드. 첫 진입은 IntersectionObserver 가 트리거.
	function load() {
		const t = ++tok;
		buildDeck(rt, { code: sym, slug }, perspectiveKey)
			.then((d) => {
				if (t === tok) {
					deck = d;
					built = true;
					idx = 0;
					onSections?.(chapterAnchors(d.cards));
				}
			})
			.catch(() => {});
	}

	// 뷰포트 진입 시 1회 빌드.
	$effect(() => {
		if (!root) return;
		const io = new IntersectionObserver(
			(e) => {
				if (e[0]?.isIntersecting && !built) load();
			},
			{ rootMargin: '300px' }
		);
		io.observe(root);
		return () => io.disconnect();
	});

	const total = $derived(deck.cards.length);
	const badgeName = $derived.by(() => {
		const code = (sym ?? '').trim().toUpperCase();
		const propName = (corpName ?? '').trim();
		const builtName = (deck.corpName ?? '').trim();
		if (propName && propName.toUpperCase() !== code) return propName;
		if (builtName && builtName.toUpperCase() !== code) return builtName;
		return propName || builtName || sym;
	});

	// 닷 = 인스타식 슬라이딩 윈도우(절대 줄바꿈 X). 회사 덱은 20장+이라 모든 점을 한 줄에 못 넣는다 →
	// 한 번에 고정 개수(DOT_WINDOW)만 보이고, 활성점을 가운데 두며 윈도우를 슬라이드. 양 끝점은 축소해
	// "더 있음"을 표시(IG 페이지네이션). step = 점(6px) + 간격(5px) = 11px.
	const DOT_WINDOW = 7;
	const DOT_STEP = 11;
	const winCount = $derived(Math.min(total, DOT_WINDOW));
	const winStart = $derived(
		Math.min(Math.max(idx - Math.floor(winCount / 2), 0), Math.max(0, total - winCount))
	);
	function dotScale(i: number): number {
		const pos = i - winStart;
		if (pos < 0 || pos >= winCount) return 0; // 창 밖 · 뷰포트가 클립
		const moreL = winStart > 0;
		const moreR = winStart + winCount < total;
		if (moreL && pos === 0) return 0.45;
		if (moreL && pos === 1) return 0.72;
		if (moreR && pos === winCount - 1) return 0.45;
		if (moreR && pos === winCount - 2) return 0.72;
		return 1;
	}

	function go(to: number) {
		if (!track) return;
		const n = Math.max(0, Math.min(total - 1, to));
		idx = n;
		(track.children[n] as HTMLElement | undefined)?.scrollIntoView({ behavior: 'smooth', inline: 'start', block: 'nearest' });
	}
	function onScroll() {
		if (!track) return;
		idx = Math.round(track.scrollLeft / (track.clientWidth || 1));
	}
	function onKey(e: KeyboardEvent) {
		if (e.key === 'ArrowRight') {
			e.preventDefault();
			go(idx + 1);
		} else if (e.key === 'ArrowLeft') {
			e.preventDefault();
			go(idx - 1);
		}
	}

	// 자동재생 · 점 좌측 재생버튼 토글. 3초마다 다음 슬라이드(끝이면 처음으로 순환). 다시 누르면 정지.
	let playing = $state(false);
	let timer: ReturnType<typeof setInterval> | null = null;
	function togglePlay() {
		playing = !playing;
		if (timer) {
			clearInterval(timer);
			timer = null;
		}
		if (playing) timer = setInterval(() => go(idx >= total - 1 ? 0 : idx + 1), 3000);
	}
	$effect(() => () => {
		if (timer) clearInterval(timer);
	});
</script>

<section
	class="deck"
	bind:this={root}
	tabindex="0"
	role="group"
	aria-roledescription="carousel"
	aria-label="{corpName} 카드 캐러셀"
	onkeydown={onKey}
>
	<div class="frame">
		<div class="track" bind:this={track} onscroll={onScroll}>
			{#each deck.cards as card, i (i)}
				<div class="slot" aria-hidden={i !== idx}><CardSlide {card} {rt} /></div>
			{/each}
		</div>

		<!-- 코너 크롬(전 슬라이드 고정) · 회사명·코드 + 페이지 + 확대. dartlab 서명은 우측 캡션 패널에 있어
		     캐러셀 이미지엔 안 얹는다(중복 + 슬라이드 본문과 겹침 방지). -->
		<div class="badge">{badgeName}{sym ? ` · ${sym}` : ''}</div>
		{#if total > 1}<div class="pageBadge">{idx + 1} / {total}</div>{/if}
		{#if onEnlarge}<button class="enlarge" onclick={onEnlarge} title="확대" aria-label="확대">⤢</button>{/if}

		<!-- 좌우 네비 -->
		{#if total > 1}
			<button class="nav left" onclick={() => go(idx - 1)} disabled={idx === 0} aria-label="이전">‹</button>
			<button class="nav right" onclick={() => go(idx + 1)} disabled={idx >= total - 1} aria-label="다음">›</button>
			<div class="dots">
				<button class="playBtn" class:on={playing} onclick={togglePlay} aria-label={playing ? '자동재생 정지' : '자동재생'} title={playing ? '정지' : '자동재생 (3초)'}>
					{#if playing}
						<svg viewBox="0 0 10 10" width="8" height="8" aria-hidden="true"><rect x="1.5" y="1" width="2.5" height="8" /><rect x="6" y="1" width="2.5" height="8" /></svg>
					{:else}
						<svg viewBox="0 0 10 10" width="8" height="8" aria-hidden="true"><path d="M2 1 L9 5 L2 9 Z" /></svg>
					{/if}
				</button>
				<div class="dotWin" style="width:{winCount * DOT_STEP - 5}px">
						<div class="dotStrip" style="transform: translateX({-winStart * DOT_STEP}px)">
							{#each deck.cards as _, i (i)}
								<button class="dot" class:on={i === idx} style="transform: scale({dotScale(i)})" onclick={() => go(i)} aria-label="{i + 1}번" aria-current={i === idx}></button>
							{/each}
						</div>
					</div>
			</div>
		{/if}
		<p class="live" aria-live="polite">{idx + 1} / {total}</p>
	</div>
</section>

<style>
	.deck {
		outline: none;
	}
	.deck:focus-visible .frame {
		box-shadow: 0 0 0 2px var(--dl-accent);
	}
	.frame {
		position: relative;
		aspect-ratio: 1080 / 1350;
		width: 100%;
		border-radius: 16px;
		overflow: hidden;
		background: #050811;
		border: 1px solid #1e2433;
	}
	.track {
		display: flex;
		height: 100%;
		overflow-x: auto;
		scroll-snap-type: x mandatory;
		scrollbar-width: none;
	}
	.track::-webkit-scrollbar {
		display: none;
	}
	.slot {
		flex: 0 0 100%;
		width: 100%;
		height: 100%;
		scroll-snap-align: start;
		/* 빠른 스와이프가 여러 스냅을 건너뛰어 두세 장이 한 번에 넘어가는 것 방지 · 한 번에 한 장만. */
		scroll-snap-stop: always;
	}
	/* chrome */
	.badge {
		position: absolute;
		top: 14px;
		right: 16px;
		font-size: 13px;
		font-weight: 700;
		color: #f1f5f9;
		padding: 6px 13px;
		background: rgba(5, 8, 17, 0.78);
		border: 1px solid rgba(232, 234, 237, 0.12);
		border-radius: 999px;
		z-index: 3;
	}
	.pageBadge {
		position: absolute;
		right: 16px;
		bottom: 14px;
		font-size: 12px;
		font-weight: 700;
		color: #f1f5f9;
		padding: 5px 11px;
		background: rgba(5, 8, 17, 0.78);
		border: 1px solid rgba(232, 234, 237, 0.12);
		border-radius: 999px;
		z-index: 3;
	}
	.enlarge {
		position: absolute;
		top: 12px;
		left: 12px;
		width: 30px;
		height: 30px;
		border-radius: 8px;
		border: 1px solid rgba(232, 234, 237, 0.14);
		background: rgba(5, 8, 17, 0.6);
		color: #e7ecf3;
		font-size: 15px;
		cursor: pointer;
		z-index: 3;
		opacity: 0;
		transition: opacity 0.15s;
	}
	.frame:hover .enlarge {
		opacity: 1;
	}
	.nav {
		position: absolute;
		top: 50%;
		transform: translateY(-50%);
		width: 34px;
		height: 34px;
		border-radius: 50%;
		border: none;
		background: rgba(5, 8, 17, 0.5);
		color: #f1f5f9;
		font-size: 18px;
		cursor: pointer;
		z-index: 3;
		opacity: 0;
		transition: opacity 0.15s;
	}
	.frame:hover .nav {
		opacity: 1;
	}
	.nav:disabled {
		opacity: 0 !important;
	}
	.nav.left {
		left: 8px;
	}
	.nav.right {
		right: 8px;
	}
	.dots {
		position: absolute;
		bottom: 16px;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		align-items: center;
		gap: 3px;
		z-index: 3;
	}
	/* 닷 뷰포트 · 고정 폭(winCount*step) 클립. 창 밖 점은 잘려 절대 줄바꿈 안 됨(IG 페이지네이션). */
	.dotWin {
		overflow: hidden;
		display: flex;
	}
	.dotStrip {
		display: flex;
		align-items: center;
		gap: 5px;
		transition: transform 0.25s ease;
	}
	/* 재생/정지 · 점 행 맨 좌측 작은 토글. 켜지면 테마색. */
	.playBtn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 14px;
		height: 14px;
		margin-right: 3px;
		border-radius: 50%;
		border: none;
		padding: 0;
		cursor: pointer;
		background: rgba(255, 255, 255, 0.4);
		color: #050811;
	}
	.playBtn svg {
		fill: currentColor;
	}
	.playBtn.on,
	.playBtn:hover {
		background: var(--dl-accent);
	}
	.dot {
		flex: 0 0 6px;
		width: 6px;
		height: 6px;
		border-radius: 50%;
		border: none;
		background: rgba(255, 255, 255, 0.45);
		cursor: pointer;
		padding: 0;
		transition:
			transform 0.2s ease,
			background 0.2s ease;
	}
	.dot.on {
		background: var(--dl-accent);
	}
	.live {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0 0 0 0);
	}
</style>
