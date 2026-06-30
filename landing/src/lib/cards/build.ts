// 라이브 덱 빌더 · buildReport(라이브·무-bake) + hfMedia hero 를 합쳐 CarouselDeck 를 만든다.
// 순수 투영(projectResult)과 분리: 여기는 런타임 I/O(데이터·미디어), 투영은 fixture 테스트 가능한 순수 함수.
import type { DartLabRuntime } from '@dartlab/ui-contracts';
import { originUrl } from '@dartlab/ui-runtime/data/origins/registry';
import type { CarouselDeck, CarouselSpec, MediaIndex } from './model';
import { projectResult } from './project';
import { buildReport } from '$lib/report/build';
import { findPerspective, PERSPECTIVES } from '$lib/report/perspectives';
import { loadMediaIndex, heroUrls as allHeroUrls, mediaKey, mediaCompany } from './media';
import { loadContract, contractToCards } from './contract';

/** 회사 hero URL 전부 · spec.hero 가 있으면 그 장을 맨 앞(표지)으로. 파일명은 콘텐츠해시 stem 매칭. */
function resolveHeroes(media: MediaIndex | null, code: string, spec?: CarouselSpec): string[] {
	const all = allHeroUrls(media, code);
	if (spec?.hero) {
		const stem = spec.hero.replace(/\.[a-z]+$/i, '');
		const c = mediaCompany(media, code);
		const hit = c?.assets.find((a) => a.name.startsWith(stem + '.') || a.name === spec.hero);
		if (hit) {
			const url = originUrl('hfMedia', `companies/${mediaKey(code)}/${hit.name}`);
			return [url, ...all.filter((u) => u !== url)]; // 큐레이션 hero 를 표지로, 나머지는 뒤에
		}
	}
	return all;
}

/** 글(회사 code + 글 slug)+관점 → 라이브 슬라이드 덱. 편집 계약(carousels/{slug}.json 손글)이 있으면 그
 *  슬라이드가 서사 표지, 그 뒤에 핵심 차트(kpis·재무추이·섹션 차트·종합)를 덧붙인다. 굽지 않음.
 *  큐레이션 오버레이(spec=hero/order/notes)는 계약에 실려 와 blog 번들 비의존. skip/pending 도 정직 카드로. */
export async function buildDeck(
	rt: DartLabRuntime,
	post: { code: string; slug: string },
	perspectiveKey: string
): Promise<CarouselDeck> {
	// media·contract 먼저(둘 다 캐시된 가벼운 단일 fetch) · code 유무로 회사/이슈 경로를 가른다.
	const [media, contract] = await Promise.all([loadMediaIndex(), loadContract(post.slug)]);
	const lead = contract ? contractToCards(contract, media) : [];
	// 차트 슬라이드 배경은 **편집 계약의 큐레이션 이미지만** 순환(엉뚱한 자산[generic bg·타사 오배치] 끼우지 않게).
	const curated = [...new Set(lead.map((c) => c.bg).filter((u): u is string => !!u))];

	// 이슈(standalone·종목코드 없음) · 회사 report 조회/차트 첨부 안 하고 손글 editorial 슬라이드만 렌더.
	if (!post.code) {
		const cards = lead.length ? lead : [{ kind: 'empty' as const, reason: '카드가 아직 준비되지 않았습니다.' }];
		return {
			stockCode: '',
			corpName: contract?.name ?? '',
			perspectiveKey: '',
			perspectiveLabel: '',
			asOf: '',
			heroUrls: curated,
			cards
		};
	}

	const persp = findPerspective(perspectiveKey);
	// 주석 구성(부문별매출·비용성격별)은 수익성 덱에만 주입하므로 그 관점일 때만 fetch(나머지 4덱 낭비 0).
	// noteSeries 는 panel XBRL 태그 런타임 직독(별도 bake 0). 어댑터 throw 는 null 로 흡수(덱 무회귀).
	const wantNotes = perspectiveKey === 'earningsPower';
	const [result, noteSeries, businessTables] = await Promise.all([
		buildReport(rt, post.code, perspectiveKey),
		wantNotes ? rt.report.noteSeries(post.code).catch(() => null) : Promise.resolve(null),
		wantNotes ? rt.report.businessTables(post.code).catch(() => null) : Promise.resolve(null)
	]);
	const spec = contract?.spec;
	// 계약이 없으면(자동 덱) 회사 hero 전체로 폴백.
	const heroUrls = curated.length ? curated : resolveHeroes(media, post.code, spec);
	return projectResult(result, persp.label, { heroUrls, spec, lead, noteSeries, businessTables });
}


/** 플레이어 관점 탭 · 구현된 관점만. */
export const DECK_PERSPECTIVES = PERSPECTIVES.filter((p) => p.built).map((p) => ({ key: p.key, label: p.label }));
