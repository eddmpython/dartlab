// 주제 집계 클라이언트 · 팟캐스트 R2 index.json 1회 fetch(프로세스 캐시) 후 stockCode/topicSlug 로 조인.
// cards/contract.ts 미러(단일 fetch·no-cache·graceful empty). 카드/블로그는 이미 각자 인덱스로 소비되고,
// 여기서는 아직 프론트가 안 읽던 팟캐스트 슬롯을 join 해 "이 주제의 팟캐스트"를 채운다(빈 슬롯 = 미표시).
import { originUrl } from '@dartlab/ui-runtime/data/origins/registry';
import type { PodcastEpisode, PodcastIndex } from './model';

let _episodes: Promise<PodcastEpisode[]> | null = null;

/** 팟캐스트 전 에피소드 1회 fetch(R2 index.json · no-cache · 프로세스 캐시). 미게시/실패 = 빈 배열. */
export function loadPodcastEpisodes(): Promise<PodcastEpisode[]> {
	_episodes ??= fetch(originUrl('podcastMedia', 'index.json'), { cache: 'no-cache' })
		.then((r) => (r.ok ? (r.json() as Promise<PodcastIndex>) : ({ episodes: [] } as unknown as PodcastIndex)))
		.then((j) => j.episodes ?? [])
		.catch(() => [] as PodcastEpisode[]);
	return _episodes;
}

/** 회사(stockCode) 또는 주제(topicSlug) 에 속한 팟캐스트 에피소드(최신순). 둘 다 없으면 빈 배열. */
export function podcastFor(episodes: PodcastEpisode[], stockCode?: string, topicSlug?: string): PodcastEpisode[] {
	const code = (stockCode ?? '').trim();
	const topic = (topicSlug ?? '').trim();
	if (!code && !topic) return [];
	return episodes
		.filter((e) => (code && e.stockCode === code) || (topic && e.topicSlug === topic))
		.sort((a, b) => b.episodeNo - a.episodeNo);
}
