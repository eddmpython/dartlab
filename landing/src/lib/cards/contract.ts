// 편집 카드 캐러셀 계약 클라이언트 — hfMedia `carousels/index.json` **한 파일**에 전 계약(슬라이드까지)이
// 배열로 담겨, 피드·상세 모두 이 1회 fetch 로 해결(별도 인덱스·카드별 round-trip 0). 슬라이드 image(semantic)는
// hfMedia 해시 파일명 URL 로 해석. 키 = 글 슬러그(회사당 N편 1:N). 굽지 않음. 미게시면 graceful(빈 배열 / null).
import { originUrl } from '@dartlab/ui-runtime/data/origins/registry';
import type { CarouselContract, ContractIndex, CarouselCard, MediaIndex } from './model';
import { mediaKey, mediaCompany } from './media';

let _all: Promise<CarouselContract[]> | null = null;

/** 전 캐러셀 계약 1회 fetch(단일 파일·프로세스 캐시). posts[] 순서 = 발간 최신순(build 가 date 내림차순). */
export function loadCarousels(): Promise<CarouselContract[]> {
	// cache:'no-cache' — index.json 은 콘텐츠해시 파일명이 아니라 in-place 갱신(republish)된다. 브라우저가 옛걸
	// 캐시하면 다이얼로그가 stale(정리된 pinnedComment 가 옛 누출본으로 보임). etag 재검증 강제로 항상 최신 보장.
	_all ??= fetch(originUrl('hfMedia', 'carousels/index.json'), { cache: 'no-cache' })
		.then((r) => (r.ok ? (r.json() as Promise<ContractIndex>) : { posts: [] }))
		.then((j) => j.posts ?? [])
		.catch(() => [] as CarouselContract[]);
	return _all;
}

/** 한 글 편집 계약(슬러그) — 캐시된 전체에서 찾기(추가 fetch 0). 없으면 null. */
export function loadContract(slug: string): Promise<CarouselContract | null> {
	return loadCarousels().then((all) => all.find((c) => c.slug === slug) ?? null);
}

/** 슬라이드 image(semantic 'cleanroom-engine') → hfMedia 해시 파일명 URL. 매니페스트에 없으면 undefined(폴백). */
export function resolveSlideImage(media: MediaIndex | null, code: string, image?: string): string | undefined {
	if (!image) return undefined;
	// 이슈 슬라이드: image 가 hfMedia 상대경로(`issues/<slug>/cover.<hash>.webp`) — 회사 매니페스트 조회 없이
	// 그대로 해석(build_carousel_contracts.py 가 콘텐츠해시 경로로 치환해 실어 보냄). 회사는 semantic 파일명.
	if (image.includes('/')) return originUrl('hfMedia', image);
	const c = mediaCompany(media, code);
	const hit = c?.assets.find((a) => a.name.startsWith(image + '.') || a.name === image);
	return hit ? originUrl('hfMedia', `companies/${mediaKey(code)}/${hit.name}`) : undefined;
}

/** 계약 → 편집 카드 슬라이드(라이브 렌더용). image 는 hfMedia URL 로 해석해 bg 에 싣는다. */
export function contractToCards(contract: CarouselContract, media: MediaIndex | null): CarouselCard[] {
	const cards: CarouselCard[] = contract.slides.map((s) => {
		const bg = resolveSlideImage(media, contract.code, s.image);
		if (s.layout === 'editorialStat') {
			return { kind: 'editorialStat', kicker: s.kicker, bigNumber: s.bigNumber ?? '', unit: s.unit, context: s.context, bg };
		}
		if (s.layout === 'editorialBeat') {
			return { kind: 'editorialBeat', kicker: s.kicker, line: s.line ?? '', sub: s.sub, bg };
		}
		return { kind: 'editorial', date: s.date, line: s.line ?? '', sub: s.sub, bg };
	});
	if (contract.keyMetrics?.length) {
		cards.push({
			kind: 'kpis',
			heading: '핵심 지표',
			chapter: '핵심지표',
			metrics: contract.keyMetrics
		});
	}
	return cards;
}
