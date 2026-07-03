<script lang="ts">
	// 인스타식 포스트 다이얼로그 · 좌 캐러셀(Deck, 스와이프) + 우 캡션(계약 title/caption/pinned). 배경/✕/Esc 닫기.
	// /cards 피드와 /terminal 회사 네비「카드뉴스」가 공유(단일 SSOT). 계약은 code 로 직접 로드(레이스 가드).
	import type { DartLabRuntime } from '@dartlab/ui-contracts';
	import Deck from './Deck.svelte';
	import { loadContract, contractToCards } from './contract';
	import { loadCompanyBadges, type CompanyBadges } from './meta';
	import { cardShareUrl } from './share';
	import { heroUrls } from './media';
	import type { MediaIndex, CarouselContract } from './model';
	// 관련 팟캐스트 조인 · 블로그 주제허브와 같은 로더(팟캐스트 R2 index.json) 재사용. code 로 회사 에피소드 매칭.
	import { loadPodcastEpisodes, podcastFor } from '$lib/subjects/subjects';
	import type { PodcastEpisode } from '$lib/subjects/model';
	import YouTube from '$lib/components/YouTube.svelte';

	let {
		rt,
		code,
		slug,
		corpName,
		media = null,
		base = '',
		onClose
	}: {
		rt: DartLabRuntime;
		code: string;
		slug: string;
		corpName: string;
		media?: MediaIndex | null;
		base?: string;
		onClose: () => void;
	} = $props();

	let contract = $state<CarouselContract | null>(null);
	// slug 가 바뀌면(다이얼로그 재사용) 재로딩 · 레이스 가드로 늦게 온 응답 무시.
	$effect(() => {
		const s = slug;
		contract = null;
		loadContract(s).then((r) => {
			if (s === slug) contract = r;
		});
	});

	// 섹션 점프 네비 · Deck 이 빌드 후 챕터 앵커를 onSections 로 넘긴다. jumpTo 는 bind:this 로 호출.
	let deckRef = $state<{ jumpTo: (i: number) => void } | null>(null);
	let anchors = $state<{ label: string; index: number }[]>([]);

	// 캡션 배지 · 제품·지주(rt.company.products 직독 + 회사명 휴리스틱). code 바뀌면 재로딩(레이스 가드).
	let badges = $state<CompanyBadges | null>(null);
	$effect(() => {
		const c = code;
		badges = null;
		anchors = []; // 새 회사 = 새 덱 → 옛 앵커 비움(다이얼로그 재사용 시 stale 방지)
		loadCompanyBadges(rt, c, corpName).then((b) => {
			if (c === code) badges = b;
		});
	});

	// 관련 팟캐스트 · code(회사) 로 팟캐스트 index.json 조인. 매칭 에피소드 있으면 '듣기' CTA 표시(없으면 미표시).
	let podcast = $state<PodcastEpisode | null>(null);
	$effect(() => {
		const c = code;
		podcast = null;
		if (!c) return; // 이슈(standalone)는 code 가 비어 조인 대상 아님
		loadPodcastEpisodes().then((all) => {
			if (c !== code) return;
			podcast = podcastFor(all, c, '')[0] ?? null;
		});
	});
	function fmtDur(sec: number): string {
		const m = Math.floor((sec || 0) / 60);
		const s = (sec || 0) % 60;
		return `${m}:${String(s).padStart(2, '0')}`;
	}

	// 캡션 산문 → 문단 배열(빈 줄 구분). 문단 내부 \n 은 pre-line 으로 보존.
	function captionParas(caption?: string): string[] {
		return String(caption ?? '')
			.split(/\n\s*\n/)
			.map((p) => p.trim())
			.filter(Boolean);
	}
	function newsMeta(news: NonNullable<CarouselContract['relatedNews']>[number]): string {
		return [news.source, news.date, news.track === 'naver' ? '네이버 보관' : ''].filter(Boolean).join(' · ');
	}
	function onKey(e: KeyboardEvent) {
		if (e.key === 'Escape') onClose();
	}

	// 공유 · cardShare 워커 링크(첫 슬라이드 OG 미리보기 + 이 캐러셀로 딥링크) 복사. 워커 미설정 시 /cards?post= 폴백.
	let copied = $state(false);
	async function share() {
		try {
			await navigator.clipboard.writeText(cardShareUrl(slug, base));
			copied = true;
			setTimeout(() => (copied = false), 1600);
		} catch {
			/* clipboard 차단 환경 무시 */
		}
	}
</script>

<svelte:window onkeydown={onKey} />

<!-- 좌 캐러셀(스와이프) + 우 캡션. 배경 클릭/Esc 닫기. -->
<div class="post" role="dialog" aria-modal="true" aria-label="{corpName} 포스트" onclick={onClose}>
	<div class="postInner" role="document" onclick={(e) => e.stopPropagation()}>
		<div class="postLeft">
			<Deck bind:this={deckRef} {rt} sym={code} {slug} {corpName} heroUrls={heroUrls(media, code)} leadCards={contract ? contractToCards(contract, media) : []} onSections={(a) => (anchors = a)} />
		</div>
		<aside class="postRight">
			<header class="prHead">
				<picture>
					<source srcset="{base}/avatar.webp" type="image/webp" />
					<img src="{base}/avatar.png" alt="DartLab" width="34" height="34" />
				</picture>
				<div class="prWho"><b>dartlab</b><small>{contract?.standalone ? 'DARTLAB · 이슈' : 'COMPANY STORY BY TICKER'}</small></div>
				<button class="prShare" onclick={share} title="공유 링크 복사" aria-label="공유 링크 복사">
					{#if copied}복사됨 ✓{:else}<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.6" y1="13.5" x2="15.4" y2="17.5"/><line x1="15.4" y1="6.5" x2="8.6" y2="10.5"/></svg>공유{/if}
				</button>
			</header>
			<!-- 섹션 점프 프리셋 · 캡션 헤더 바로 아래(사진 밖 웹 리더 크롬). 20장+ 익명 닷 보완. -->
			{#if anchors.length > 1}
				<nav class="prNav" aria-label="섹션 바로가기">
					{#each anchors as a (a.index)}<button onclick={() => deckRef?.jumpTo(a.index)}>{a.label}</button>{/each}
				</nav>
			{/if}
			<div class="prScroll">
				<p class="prMeta">{contract?.name ?? corpName}{code ? ` · ${code}` : ''}</p>
				{#if badges && (badges.product || badges.isHolding)}
					<div class="prBadges">
						{#if badges.isHolding}<span class="prTag prTagHold">지주회사</span>{/if}
						{#if badges.product}<span class="prTag">{badges.product}</span>{/if}
					</div>
				{/if}
				{#if contract?.title}<h2 class="prTitle">{contract.title}</h2>{/if}
				{#if contract}
					{#each captionParas(contract.caption) as para (para)}<p class="prPara">{para}</p>{/each}
					{#if !contract.caption}<p class="prPara prMuted">캡션이 아직 준비되지 않았습니다.</p>{/if}
					{#if contract.explainers?.length}
						<section class="prInfoBlock" aria-label="짧은 설명">
							<h3>짧은 설명</h3>
							<div class="prExplainers">
								{#each contract.explainers as item (item.term)}
									<p class="prExplainer"><b>{item.term}</b><span>{item.body}</span></p>
								{/each}
							</div>
						</section>
					{/if}
					{#if contract.relatedNews?.length}
						<section class="prInfoBlock" aria-label="관련 뉴스">
							<h3>관련 뉴스</h3>
							<div class="prNewsList">
								{#each contract.relatedNews as news (news.url)}
									<a class="prNews" href={news.url} target="_blank" rel="noopener">
										<span class="prNewsTitle">{news.title}</span>
										{#if newsMeta(news)}<small>{newsMeta(news)}</small>{/if}
										{#if news.description}<span class="prNewsDesc">{news.description}</span>{/if}
									</a>
								{/each}
							</div>
						</section>
					{/if}
					<!-- 블로그 이어 읽기 · 회사 캐러셀만(같은 slug=blog [slug]). 이슈(standalone)는 원문 글이 없어 숨김. -->
					{#if !contract.standalone}
						<a class="prBlog" href="{base}/blog/{slug}" target="_blank" rel="noopener">
							<span class="prBlogIco" aria-hidden="true"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" /></svg></span>
							<span class="prBlogTxt"><small>블로그에서 이어 읽기</small><b>{contract.title ?? contract.name}</b></span>
							<span class="prBlogArr" aria-hidden="true">↗</span>
						</a>
					{/if}
					<!-- 관련 팟캐스트 · youtubeId 있으면 유튜브 플레이어 임베드, 없으면 R2 오디오 CTA. 매칭 없으면 미표시. -->
					{#if podcast?.youtubeId}
						<div class="prPodYt">
							<span class="prPodYtLbl">관련 팟캐스트 · EP.{String(podcast.episodeNo).padStart(2, '0')}{podcast.durationSec ? ` · ${fmtDur(podcast.durationSec)}` : ''}</span>
							<YouTube id={podcast.youtubeId} title={podcast.title} facade />
						</div>
					{:else if podcast}
						<a class="prPod" href={podcast.audioUrl} target="_blank" rel="noopener">
							<span class="prPodIco" aria-hidden="true"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 14v-3a9 9 0 0 1 18 0v3" /><path d="M21 16.5A2.5 2.5 0 0 1 18.5 19H18a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1h3z" /><path d="M3 16.5A2.5 2.5 0 0 0 5.5 19H6a1 1 0 0 0 1-1v-4a1 1 0 0 0-1-1H3z" /></svg></span>
							<span class="prPodTxt"><small>팟캐스트로 듣기 · EP.{String(podcast.episodeNo).padStart(2, '0')}{podcast.durationSec ? ` · ${fmtDur(podcast.durationSec)}` : ''}</small><b>{podcast.title}</b></span>
							<span class="prPodArr" aria-hidden="true">▶</span>
						</a>
					{/if}
					{#if contract.pinnedComment}<p class="prPinned">{contract.pinnedComment}</p>{/if}
				{:else}
					<p class="prPara prMuted">불러오는 중…</p>
				{/if}
			</div>
		</aside>
		<button class="postClose" onclick={onClose} aria-label="닫기">✕</button>
	</div>
</div>

<style>
	/* 인스타 포스트 모달 · 좌 캐러셀(4:5) + 우 캡션 패널. z-index 는 터미널 오버레이(scrimWrap 10050)
	   위로 떠야 하므로 높게(10060). /cards 에선 경쟁 오버레이가 없어 무해. */
	.post {
		position: fixed;
		inset: 0;
		z-index: 10060;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 3vh 3vw;
		background: rgba(2, 4, 8, 0.92);
		backdrop-filter: blur(6px);
	}
	.postInner {
		display: flex;
		height: min(90vh, 880px);
		max-width: 96vw;
		background: #0b0e14;
		border: 1px solid #1e2433;
		border-radius: 14px;
		overflow: hidden;
	}
	.postLeft {
		height: 100%;
		aspect-ratio: 1080 / 1350;
		flex: 0 0 auto;
		background: #050811;
	}
	.postRight {
		width: 360px;
		max-width: 42vw;
		height: 100%;
		display: flex;
		flex-direction: column;
		border-left: 1px solid #1e2433;
	}
	.prHead {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 16px 18px;
		border-bottom: 1px solid #161b26;
		flex: 0 0 auto;
	}
	.prHead img {
		border-radius: 50%;
	}
	.prWho {
		display: flex;
		flex-direction: column;
		line-height: 1.2;
	}
	.prWho b {
		font-size: 14px;
		font-weight: 800;
		color: #f6f8fb;
	}
	.prWho small {
		font-size: 8px;
		letter-spacing: 0.14em;
		color: #94a3b8;
		text-transform: uppercase;
	}
	/* 공유 버튼 · 헤더 우측. 링크 복사 시 '복사됨 ✓'. 테마색 보더. */
	.prShare {
		margin-left: auto;
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 6px 11px;
		border-radius: 999px;
		border: 1px solid rgba(var(--dl-accent-rgb), 0.4);
		background: rgba(var(--dl-accent-rgb), 0.1);
		color: var(--dl-accent);
		font-size: 12px;
		font-weight: 700;
		cursor: pointer;
		white-space: nowrap;
		transition:
			background 0.15s,
			border-color 0.15s;
	}
	.prShare:hover {
		background: rgba(var(--dl-accent-rgb), 0.18);
		border-color: rgba(var(--dl-accent-rgb), 0.7);
	}
	.prScroll {
		flex: 1;
		overflow-y: auto;
		padding: 18px;
	}
	.prMeta {
		margin: 0 0 6px;
		font-family: Menlo, Consolas, monospace;
		font-size: 12px;
		letter-spacing: 0.08em;
		color: var(--dl-accent);
		font-weight: 700;
	}
	/* 섹션 점프 프리셋 · 캡션 헤더 아래 가로 칩 행(넘치면 가로 스크롤, 줄바꿈 금지). */
	.prNav {
		display: flex;
		gap: 6px;
		padding: 9px 18px;
		border-bottom: 1px solid #161b26;
		overflow-x: auto;
		scrollbar-width: none;
		flex: 0 0 auto;
	}
	.prNav::-webkit-scrollbar {
		display: none;
	}
	.prNav button {
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
		transition:
			border-color 0.15s,
			color 0.15s;
	}
	.prNav button:hover {
		border-color: rgba(var(--dl-accent-rgb), 0.6);
		color: var(--dl-accent);
	}
	/* 회사 배지 · 제품·지주(캡션 메타 아래). 작은 칩. */
	.prBadges {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin: 0 0 12px;
	}
	.prTag {
		font-size: 11px;
		font-weight: 700;
		padding: 3px 9px;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.05);
		color: #aab8c8;
		border: 1px solid #1e2433;
		word-break: keep-all;
	}
	.prTagHold {
		color: var(--dl-accent);
		border-color: rgba(var(--dl-accent-rgb), 0.4);
		background: rgba(var(--dl-accent-rgb), 0.08);
	}
	.prTitle {
		margin: 0 0 14px;
		font-size: 19px;
		font-weight: 800;
		line-height: 1.3;
		color: #f6f8fb;
		word-break: keep-all;
	}
	.prPara {
		margin: 0 0 13px;
		font-size: 14.5px;
		line-height: 1.62;
		color: #d8e2f0;
		white-space: pre-line;
		word-break: keep-all;
	}
	.prPinned {
		margin: 16px 0 0;
		padding-top: 14px;
		border-top: 1px solid #1e2433;
		font-size: 12.5px;
		line-height: 1.55;
		color: #94a3b8;
		white-space: pre-line;
		word-break: keep-all;
	}
	.prMuted {
		color: #64748b;
	}
	.prInfoBlock {
		margin: 18px 0 0;
		padding-top: 15px;
		border-top: 1px solid #1e2433;
	}
	.prInfoBlock h3 {
		margin: 0 0 9px;
		font-size: 11px;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: #94a3b8;
		font-weight: 800;
	}
	.prExplainers,
	.prNewsList {
		display: flex;
		flex-direction: column;
		gap: 9px;
	}
	.prExplainer {
		margin: 0;
		display: grid;
		grid-template-columns: minmax(54px, 0.34fr) minmax(0, 1fr);
		gap: 10px;
		font-size: 13px;
		line-height: 1.55;
		color: #cbd5e1;
		word-break: keep-all;
	}
	.prExplainer b {
		color: #f6f8fb;
		font-weight: 800;
	}
	.prExplainer span {
		min-width: 0;
	}
	.prNews {
		display: flex;
		flex-direction: column;
		gap: 3px;
		padding: 9px 0 10px;
		border-bottom: 1px solid #161b26;
		color: inherit;
		text-decoration: none;
	}
	.prNews:hover .prNewsTitle {
		color: var(--dl-accent);
	}
	.prNewsTitle {
		font-size: 13.5px;
		line-height: 1.42;
		font-weight: 800;
		color: #e8f0fb;
		word-break: keep-all;
	}
	.prNews small {
		font-size: 10.5px;
		line-height: 1.35;
		color: #94a3b8;
	}
	.prNewsDesc {
		font-size: 12px;
		line-height: 1.45;
		color: #9fb0c4;
		word-break: keep-all;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	/* 블로그 이어 읽기 CTA · 캡션 아래, 면책 위. 테마색(--dl-accent) 배선(캐러셀 점·재생버튼과 동색). */
	.prBlog {
		display: flex;
		align-items: center;
		gap: 11px;
		margin: 18px 0 2px;
		padding: 11px 13px;
		border: 1px solid rgba(var(--dl-accent-rgb), 0.34);
		border-radius: 11px;
		background: rgba(var(--dl-accent-rgb), 0.08);
		text-decoration: none;
		transition:
			border-color 0.15s,
			background 0.15s,
			transform 0.12s;
	}
	.prBlog:hover {
		border-color: rgba(var(--dl-accent-rgb), 0.7);
		background: rgba(var(--dl-accent-rgb), 0.14);
		transform: translateY(-1px);
	}
	.prBlogIco {
		flex: 0 0 auto;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		background: rgba(var(--dl-accent-rgb), 0.16);
		color: var(--dl-accent);
	}
	.prBlogTxt {
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}
	.prBlogTxt small {
		font-size: 9.5px;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		font-weight: 700;
		color: var(--dl-accent);
	}
	.prBlogTxt b {
		font-size: 13px;
		font-weight: 700;
		line-height: 1.35;
		color: #e8f0fb;
		word-break: keep-all;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.prBlogArr {
		flex: 0 0 auto;
		margin-left: auto;
		font-size: 15px;
		color: var(--dl-accent);
		opacity: 0.85;
	}
	/* 관련 팟캐스트 듣기 CTA · 블로그 CTA 바로 아래. 로즈 강조는 유지하되 채움(accent fill)으로 '듣기'를 구분. */
	.prPod {
		display: flex;
		align-items: center;
		gap: 11px;
		margin: 9px 0 2px;
		padding: 11px 13px;
		border: 1px solid rgba(var(--dl-accent-rgb), 0.34);
		border-radius: 11px;
		background: rgba(var(--dl-accent-rgb), 0.13);
		text-decoration: none;
		transition:
			border-color 0.15s,
			background 0.15s,
			transform 0.12s;
	}
	.prPod:hover {
		border-color: rgba(var(--dl-accent-rgb), 0.7);
		background: rgba(var(--dl-accent-rgb), 0.2);
		transform: translateY(-1px);
	}
	.prPodIco {
		flex: 0 0 auto;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		background: var(--dl-accent);
		color: #0b0e14;
	}
	.prPodTxt {
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}
	.prPodTxt small {
		font-size: 9.5px;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		font-weight: 700;
		color: var(--dl-accent);
	}
	.prPodTxt b {
		font-size: 13px;
		font-weight: 700;
		line-height: 1.35;
		color: #e8f0fb;
		word-break: keep-all;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.prPodArr {
		flex: 0 0 auto;
		margin-left: auto;
		font-size: 12px;
		color: var(--dl-accent);
		opacity: 0.9;
	}
	/* 관련 팟캐스트 유튜브 임베드 · 좁은 캡션 패널에 맞게 컴포넌트 기본 여백/폭 override(16:9 그대로). */
	.prPodYt {
		margin: 12px 0 2px;
	}
	.prPodYtLbl {
		display: block;
		margin-bottom: 7px;
		font-size: 9.5px;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		font-weight: 700;
		color: var(--dl-accent);
	}
	.prPodYt :global(.yt-wrap) {
		margin: 0;
		max-width: 100%;
	}
	.postClose {
		position: absolute;
		top: 18px;
		right: 22px;
		width: 40px;
		height: 40px;
		border-radius: 50%;
		border: 1px solid #243244;
		background: rgba(8, 12, 18, 0.8);
		color: #cbd5e1;
		font-size: 18px;
		cursor: pointer;
		z-index: 2;
	}
	/* 좁은 화면 · 세로 스택(캐러셀 위, 캡션 아래) */
	@media (max-width: 820px) {
		.postInner {
			flex-direction: column;
			height: auto;
			max-height: 92vh;
			overflow-y: auto;
		}
		.postLeft {
			height: auto;
			width: 100%;
			aspect-ratio: 1080 / 1350;
		}
		.postRight {
			width: 100%;
			max-width: none;
			border-left: none;
			border-top: 1px solid #1e2433;
		}
		/* 모바일: 캡션 내부 스크롤 제거. postInner 하나만 스크롤해 이중 스크롤(카드+캡션 한 흐름)을 막는다. */
		.prScroll {
			flex: 0 0 auto;
			overflow-y: visible;
		}
	}
	/* 폰(≤640) · 모달을 화면 꽉 채움(거터 0). 카드 위 / 캡션 아래 한 흐름으로 스크롤.
	   100dvh = iOS Safari 주소창 가변 높이 잘림 방지(미지원 시 위 820 블록 max-height:92vh 폴백). */
	@media (max-width: 640px) {
		.post {
			padding: 0;
			background: #050811;
			backdrop-filter: none;
		}
		.postInner {
			width: 100vw;
			max-width: 100vw;
			height: 100dvh;
			max-height: 100dvh;
			border: 0;
			border-radius: 0;
		}
		.postLeft {
			aspect-ratio: 1080 / 1350;
		}
		.prScroll {
			padding: 16px 14px 28px;
		}
		.prHead {
			padding: 12px 14px;
		}
		/* 닫기 = 폰 풀스크린에선 좌상단(우상단 회사 badge·우하단 page badge 와 충돌 회피, 좌상단은 enlarge 미사용으로 빔).
		   터치 38px, z5 로 캐러셀 크롬 위. */
		.postClose {
			top: calc(8px + env(safe-area-inset-top, 0px));
			left: 12px;
			right: auto;
			width: 38px;
			height: 38px;
			z-index: 5;
		}
	}
</style>
