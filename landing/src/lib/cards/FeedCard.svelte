<script lang="ts">
	// 피드 카드 · 인스타식 반응형. 모바일(≤640px): 풀폭 카드가 그 자리에서 좌우 스와이프되는 *인라인 캐러셀*
	// (Deck 재사용 · 점 인디케이터·스냅·페이지카운터, 화살표는 hover 없으니 자동 숨김=스와이프만). 캡션은
	// 이미지 아래(이름·공유·제목 더보기→모달). 데스크톱(>640px): 기존 그리드 커버 썸네일(CoverThumb) 탭→모달.
	// 둘 다 가벼움 · Deck/CoverThumb 가 뷰포트 진입 시에만 라이브 빌드(지연).
	import type { DartLabRuntime } from '@dartlab/ui-contracts';
	import Deck from './Deck.svelte';
	import CoverThumb from './CoverThumb.svelte';
	import { loadCompanyBadges, type CompanyBadges } from './meta';
	import { cardShareUrl } from './share';
	import { heroUrls } from './media';
	import type { MediaIndex, CarouselCard } from './model';

	let {
		rt,
		code,
		slug,
		corpName,
		title = '',
		caption = '',
		pinnedComment = '',
		standalone = false,
		leadCards = [],
		base = '',
		media,
		onOpen
	}: {
		rt: DartLabRuntime;
		code: string;
		slug: string;
		corpName: string;
		title?: string;
		caption?: string;
		pinnedComment?: string;
		standalone?: boolean;
		leadCards?: CarouselCard[];
		base?: string;
		media: MediaIndex | null;
		onOpen: () => void;
	} = $props();

	// 섹션 점프 네비 + 캡션 배지(제품·지주) · PostModal 과 동형. Deck 이 onSections 로 앵커를 넘기고
	// jumpTo 는 bind:this 로 호출. 배지는 rt.company.products 직독(공유 이미지 무변경, 캡션 크롬만).
	let deckRef = $state<{ jumpTo: (i: number) => void } | null>(null);
	let anchors = $state<{ label: string; index: number }[]>([]);
	let badges = $state<CompanyBadges | null>(null);
	$effect(() => {
		const c = code;
		badges = null;
		anchors = [];
		loadCompanyBadges(rt, c, corpName).then((b) => {
			if (c === code) badges = b;
		});
	});

	// 캡션 인라인 펼침(인스타 피드식) · 클릭 시 모달이 아니라 그 자리(같은 페이지) 이미지 아래에서 펼침/접힘.
	let expanded = $state(false);
	function captionParas(c: string): string[] {
		return String(c ?? '')
			.split(/\n\s*\n/)
			.map((p) => p.trim())
			.filter(Boolean);
	}
	const hasCaption = $derived(!!caption.trim());

	// 뷰포트 분기 · matchMedia(반응형). 모바일=인라인 스와이프, 데스크톱=그리드 썸네일.
	let mobile = $state(false);
	$effect(() => {
		const mq = window.matchMedia('(max-width: 640px)');
		const apply = () => (mobile = mq.matches);
		apply();
		mq.addEventListener('change', apply);
		return () => mq.removeEventListener('change', apply);
	});

	// 공유 · cardShare 워커 링크(첫 슬라이드 OG + 딥링크) 복사.
	let copied = $state(false);
	async function share() {
		try {
			await navigator.clipboard.writeText(cardShareUrl(slug, base));
			copied = true;
			setTimeout(() => (copied = false), 1500);
		} catch {
			/* clipboard 차단 환경 무시 */
		}
	}
</script>

{#if mobile}
	<!-- 인스타 피드식 · 풀폭 인라인 스와이프 캐러셀 + 아래 캡션 바. -->
	<article class="fc">
		<div class="fcDeck">
			<Deck bind:this={deckRef} {rt} sym={code} {slug} {corpName} heroUrls={heroUrls(media, code)} {leadCards} onSections={(a) => (anchors = a)} />
		</div>
		<div class="fcBar">
			<picture>
				<source srcset="{base}/avatar.webp" type="image/webp" />
				<img class="fcAva" src="{base}/avatar.png" alt="" width="26" height="26" />
			</picture>
			<b class="fcName">{corpName}{code ? ` · ${code}` : ''}</b>
			<button class="fcShare" onclick={share} aria-label="공유 링크 복사" title="공유">
				{#if copied}
					복사됨 ✓
				{:else}
					<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><line x1="8.6" y1="13.5" x2="15.4" y2="17.5" /><line x1="15.4" y1="6.5" x2="8.6" y2="10.5" /></svg>
					공유
				{/if}
			</button>
		</div>
		{#if anchors.length > 1}
			<nav class="fcNav" aria-label="섹션 바로가기">
				{#each anchors as a (a.index)}<button onclick={() => deckRef?.jumpTo(a.index)}>{a.label}</button>{/each}
			</nav>
		{/if}
		{#if badges && (badges.product || badges.isHolding)}
			<div class="fcBadges">
				{#if badges.isHolding}<span class="fcTag fcTagHold">지주회사</span>{/if}
				{#if badges.product}<span class="fcTag">{badges.product}</span>{/if}
			</div>
		{/if}
		{#if title || hasCaption}
			<div class="fcCap">
				{#if title}<p class="fcCapTitle" class:clamp={!expanded}>{title}</p>{/if}
				{#if expanded}
					{#each captionParas(caption) as para (para)}<p class="fcCapPara">{para}</p>{/each}
					{#if !standalone}
						<a class="fcCapBlog" href="{base}/blog/{slug}" target="_blank" rel="noopener">블로그에서 이어 읽기 ↗</a>
					{/if}
					{#if pinnedComment}<p class="fcCapPinned">{pinnedComment}</p>{/if}
				{/if}
				{#if hasCaption}
					<button class="fcMore" onclick={() => (expanded = !expanded)}>{expanded ? '접기' : '… 더 보기'}</button>
				{/if}
			</div>
		{/if}
	</article>
{:else}
	<CoverThumb {rt} {code} {slug} {corpName} {base} {media} {onOpen} />
{/if}

<style>
	/* 모바일 인라인 피드 카드 · 풀폭, 캐러셀 + 캡션 바. */
	.fc {
		display: flex;
		flex-direction: column;
		padding-bottom: 20px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.07); /* 다음 카드뉴스와의 명확한 구분선(모바일 피드) */
	}
	.fcDeck {
		width: 100%;
	}
	/* 캡션 바 · 아바타 · 이름 · 공유(우측). 인스타 포스트 헤더/액션 줄 역할. */
	.fcBar {
		display: flex;
		align-items: center;
		gap: 9px;
		padding: 11px 4px 6px;
	}
	.fcAva {
		border-radius: 50%;
		flex: 0 0 auto;
	}
	.fcName {
		font-size: 14px;
		font-weight: 800;
		color: #f1f5f9;
		letter-spacing: -0.01em;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.fcShare {
		margin-left: auto;
		flex: 0 0 auto;
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 6px 12px;
		border-radius: 999px;
		border: 1px solid rgba(var(--dl-accent-rgb), 0.4);
		background: rgba(var(--dl-accent-rgb), 0.1);
		color: var(--dl-accent);
		font-size: 12.5px;
		font-weight: 700;
		cursor: pointer;
		white-space: nowrap;
	}
	.fcShare:active {
		background: rgba(var(--dl-accent-rgb), 0.2);
	}
	/* 섹션 점프 프리셋(모바일) · 캡션 바 아래 가로 칩 행(넘치면 가로 스크롤). */
	.fcNav {
		display: flex;
		gap: 6px;
		padding: 2px 4px 8px;
		overflow-x: auto;
		scrollbar-width: none;
	}
	.fcNav::-webkit-scrollbar {
		display: none;
	}
	.fcNav button {
		flex: 0 0 auto;
		padding: 5px 11px;
		border-radius: 999px;
		border: 1px solid #243244;
		background: rgba(255, 255, 255, 0.03);
		color: #cbd5e1;
		font-size: 12px;
		font-weight: 700;
		cursor: pointer;
		white-space: nowrap;
	}
	.fcNav button:active {
		border-color: rgba(var(--dl-accent-rgb), 0.6);
		color: var(--dl-accent);
	}
	/* 회사 배지(모바일) · 제품·지주. */
	.fcBadges {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		padding: 0 4px 8px;
	}
	.fcTag {
		font-size: 11px;
		font-weight: 700;
		padding: 3px 9px;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.05);
		color: #aab8c8;
		border: 1px solid #1e2433;
		word-break: keep-all;
	}
	.fcTagHold {
		color: var(--dl-accent);
		border-color: rgba(var(--dl-accent-rgb), 0.4);
		background: rgba(var(--dl-accent-rgb), 0.08);
	}
	/* 인스타 피드 캡션 · 이미지 아래 같은 페이지. 접힘=제목 2줄, '더 보기'로 캡션 본문 인라인 펼침(모달 아님). */
	.fcCap {
		padding: 0 4px 2px;
	}
	.fcCapTitle {
		margin: 0;
		font-size: 14.5px;
		font-weight: 700;
		line-height: 1.45;
		color: #e8eef6;
		word-break: keep-all;
	}
	.fcCapTitle.clamp {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.fcCapPara {
		margin: 9px 0 0;
		font-size: 14px;
		line-height: 1.62;
		color: #cdd9e6;
		white-space: pre-line;
		word-break: keep-all;
	}
	.fcCapBlog {
		display: inline-block;
		margin: 12px 0 2px;
		font-size: 13px;
		font-weight: 700;
		color: var(--dl-accent);
		text-decoration: none;
	}
	.fcCapPinned {
		margin: 12px 0 0;
		font-size: 12px;
		line-height: 1.5;
		color: #7c8aa0;
		white-space: pre-line;
		word-break: keep-all;
	}
	.fcMore {
		display: inline-block;
		margin-top: 4px;
		padding: 2px 0;
		border: none;
		background: none;
		color: #64748b;
		font-weight: 700;
		font-size: 13.5px;
		cursor: pointer;
	}
</style>
