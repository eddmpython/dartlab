// hfMedia 회사 이미지 런타임 매니페스트 클라이언트 · manifests/companies.json 1회 로드 + 객체 URL 해석.
// 매니페스트/이미지 미게시(P0 운영자 publish 전)면 graceful null → 카드가 SVG/그라데이션 폴백(빈 화면 금지).
import { isKrStockCode, normalizeKrCode } from '@dartlab/ui-contracts';
import { originUrl } from '@dartlab/ui-runtime/data/origins/registry';
import type { MediaIndex, MediaCompany } from './model';

const MEDIA_INDEX_PATH = 'manifests/companies.json';

let _cache: Promise<MediaIndex | null> | null = null;

/** manifests/companies.json 1회 fetch(프로세스 캐시). 404/네트워크 실패 = null(폴백 신호). */
export function loadMediaIndex(): Promise<MediaIndex | null> {
	_cache ??= fetch(originUrl('hfMedia', MEDIA_INDEX_PATH))
		.then((r) => (r.ok ? (r.json() as Promise<MediaIndex>) : null))
		.catch(() => null);
	return _cache;
}

/** sym(KRX 코드 또는 티커) → canonical media key. 코드=정규화 그대로, 티커=대문자(build_index 와 동일 규칙). */
export function mediaKey(sym: string): string {
	return isKrStockCode(sym) ? normalizeKrCode(sym) : sym.toUpperCase();
}

export function mediaCompany(index: MediaIndex | null, sym: string): MediaCompany | undefined {
	return index?.companies[mediaKey(sym)];
}

/** 회사 hero 이미지 절대 URL 목록(없으면 빈 배열). 객체 경로는 콘텐츠 주소라 영구 캐시 가능. */
export function heroUrls(index: MediaIndex | null, sym: string): string[] {
	const key = mediaKey(sym);
	const c = index?.companies[key];
	return (c?.assets ?? []).map((a) => originUrl('hfMedia', a.path));
}

/** 표지용 첫 hero(없으면 undefined → 폴백). */
export function heroUrl(index: MediaIndex | null, sym: string): string | undefined {
	return heroUrls(index, sym)[0];
}
