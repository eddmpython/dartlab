// 주제(subject) 집계 모델 · 팟캐스트 R2 index.json(dartlab-podcast/index.json) 스키마.
// publish_podcast.py build_index 산출과 1:1. 조인 키 = stockCode(회사) / topicSlug(주제).

export interface PodcastLinks {
	blogSlug: string;
	cardSlug: string;
	terminalCode: string;
}

export interface PodcastEpisode {
	slug: string;
	episodeId: string;
	episodeNo: number;
	date: string;
	title: string;
	audioUrl: string;
	durationSec: number;
	guid: string;
	stockCode: string;
	topicSlug: string;
	cardType: string;
	summary: string;
	links: PodcastLinks;
}

export interface PodcastIndex {
	version: number;
	channel: string;
	episodes: PodcastEpisode[];
}
