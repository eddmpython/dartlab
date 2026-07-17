// 편집 카드 캐러셀 계약 클라이언트 · hfMedia `manifests/carousels.json` 한 파일에 전 계약(슬라이드까지)이
// 배열로 담겨, 피드·상세 모두 이 1회 fetch 로 해결한다. 슬라이드 image 는 콘텐츠 주소 객체 경로다.
import { originUrl } from '@dartlab/ui-runtime/data/origins/registry';
import type { CarouselContract, ContractIndex, CarouselCard } from './model';

let _all: Promise<CarouselContract[]> | null = null;

/** 전 캐러셀 계약 1회 fetch(단일 파일·프로세스 캐시). posts[] 순서 = 발간 최신순(build 가 date 내림차순). */
export function loadCarousels(): Promise<CarouselContract[]> {
	// cache:'no-cache' · index.json 은 콘텐츠해시 파일명이 아니라 in-place 갱신(republish)된다. 브라우저가 옛걸
	// 캐시하면 다이얼로그가 stale(정리된 pinnedComment 가 옛 누출본으로 보임). etag 재검증 강제로 항상 최신 보장.
	_all ??= fetch(originUrl('hfMedia', 'manifests/carousels.json'), { cache: 'no-cache' })
		.then((r) => (r.ok ? (r.json() as Promise<ContractIndex>) : { posts: [] }))
		.then((j) => j.posts ?? [])
		.catch(() => [] as CarouselContract[]);
	return _all;
}

/** 한 글 편집 계약(슬러그) · 캐시된 전체에서 찾기(추가 fetch 0). 없으면 null. */
export function loadContract(slug: string): Promise<CarouselContract | null> {
	return loadCarousels().then((all) => all.find((c) => c.slug === slug) ?? null);
}

/** 슬라이드 객체 경로만 URL로 해석한다. 레거시 폴더나 의미 키는 폴백 처리한다. */
export function resolveSlideImage(image?: string): string | undefined {
	if (!image?.startsWith('objects/sha256/')) return undefined;
	return originUrl('hfMedia', image);
}

/** 계약 → 편집 카드 슬라이드(라이브 렌더용). image 는 hfMedia URL 로 해석해 bg 에 싣는다. */
export function contractToCards(contract: CarouselContract): CarouselCard[] {
	const cards: CarouselCard[] = contract.slides.map((s) => {
		const bg = resolveSlideImage(s.image);
		if (s.layout === 'editorialStat') {
			return { kind: 'editorialStat', kicker: s.kicker, bigNumber: s.bigNumber ?? '', unit: s.unit, context: s.context, bg };
		}
		if (s.layout === 'editorialBeat') {
			return { kind: 'editorialBeat', kicker: s.kicker, line: s.line ?? '', sub: s.sub, visual: s.visual, bg };
		}
		return { kind: 'editorial', date: s.date, line: s.line ?? '', sub: s.sub, bg };
	});
	// 핵심지표(kpis) 카드는 붙이지 않는다 · 긴 값이 4:5 카드에서 줄깨짐·넘침이라 의미 대비 비용이 크다.
	// keyMetrics 는 캡션·우측 패널 검증값으로만 쓴다(카드 슬라이드로는 렌더하지 않음).
	return cards;
}
