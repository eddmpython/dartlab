<script lang="ts">
	// 주제 허브 · 이 글(회사/주제)의 관련 팟캐스트 슬롯. 카드/블로그는 각자 페이지가 이미 노출하므로,
	// 여기서는 아직 미노출이던 팟캐스트를 join 해 채운다. 에피소드 없으면 렌더 안 함(대부분 글엔 팟캐스트 없음).
	import { onMount } from 'svelte';
	import { loadPodcastEpisodes, podcastFor } from './subjects';
	import type { PodcastEpisode } from './model';
	import YouTube from '$lib/components/YouTube.svelte';

	interface Props {
		stockCode?: string;
		topicSlug?: string;
	}
	let { stockCode = '', topicSlug = '' }: Props = $props();

	let episodes = $state<PodcastEpisode[]>([]);

	onMount(async () => {
		const all = await loadPodcastEpisodes();
		episodes = podcastFor(all, stockCode, topicSlug);
	});

	function fmtDur(sec: number): string {
		const m = Math.floor((sec || 0) / 60);
		const s = (sec || 0) % 60;
		return `${m}:${String(s).padStart(2, '0')}`;
	}
</script>

{#if episodes.length}
	<section class="subject-hub" aria-label="관련 팟캐스트">
		<h2>관련 팟캐스트</h2>
		<ul>
			{#each episodes as ep (ep.guid)}
				<li class="ep">
					<div class="ep-head">
						<span class="ep-no">EP.{String(ep.episodeNo).padStart(2, '0')}</span>
						<span class="ep-title">{ep.title}</span>
						{#if ep.durationSec}<span class="ep-dur">{fmtDur(ep.durationSec)}</span>{/if}
					</div>
					{#if ep.summary}<p class="ep-sum">{ep.summary}</p>{/if}
					{#if ep.youtubeId}
						<YouTube id={ep.youtubeId} title={ep.title} facade />
					{:else}
						<audio controls preload="none" src={ep.audioUrl}></audio>
					{/if}
				</li>
			{/each}
		</ul>
	</section>
{/if}

<style>
	.subject-hub {
		margin: 2.5rem 0;
		padding-top: 1.25rem;
		border-top: 1px solid var(--border, #1e2433);
	}
	.subject-hub h2 {
		font-size: 1.05rem;
		margin: 0 0 0.9rem;
	}
	.subject-hub ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 1rem;
	}
	.ep {
		background: var(--dl-bg-card, #0f1219);
		border: 1px solid var(--border, #1e2433);
		border-radius: 10px;
		padding: 0.9rem 1rem;
	}
	.ep-head {
		display: flex;
		gap: 0.55rem;
		align-items: baseline;
		flex-wrap: wrap;
	}
	.ep-no {
		color: var(--dl-accent);
		font-weight: 700;
		font-size: 0.82rem;
		letter-spacing: 0.02em;
	}
	.ep-title {
		font-weight: 600;
	}
	.ep-dur {
		color: var(--text-muted, #9aa3ad);
		font-size: 0.8rem;
		margin-left: auto;
		font-variant-numeric: tabular-nums;
	}
	.ep-sum {
		color: var(--text-muted, #9aa3ad);
		font-size: 0.88rem;
		margin: 0.5rem 0 0.7rem;
		line-height: 1.5;
	}
	.ep audio {
		width: 100%;
		margin-top: 0.3rem;
	}
</style>
