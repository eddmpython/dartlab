// 캐러셀 공유 링크 · cardShare 워커(/c/<slug>)가 동적 OG(첫 슬라이드 미리보기) + 딥링크를 제공한다.
// 워커 base(VITE_DARTLAB_CARD_SHARE_BASE)가 설정돼 있으면 그 워커 URL(스레드·인스타 등에서 리치 미리보기),
// 미설정이면 같은 사이트 딥링크(/cards?post=)로 graceful · 사람은 카드가 열리되 OG 미리보기는 일반.
// 기본값 = 배포된 cardShare 워커(동적 OG). 빌드 env VITE_DARTLAB_CARD_SHARE_BASE 로 override(미러/도메인 교체).
// hf.ts 의 DEFAULT_HF_MEDIA_RESOLVE 와 동일 패턴(하드코딩 기본 + env 가역).
const DEFAULT_SHARE_BASE = 'https://dartlab-card-share.eddmpython.workers.dev';
const SHARE_BASE = String(
	(import.meta.env as Record<string, string | undefined>).VITE_DARTLAB_CARD_SHARE_BASE ?? DEFAULT_SHARE_BASE
).replace(/\/+$/, '');

/** 슬러그 → 공유 URL. 워커 설정 시 `<worker>/c/<slug>`(리치 OG), 아니면 `<origin><base>/cards?post=<slug>`. */
export function cardShareUrl(slug: string, base = ''): string {
	if (SHARE_BASE) return `${SHARE_BASE}/c/${encodeURIComponent(slug)}`;
	const origin = typeof location !== 'undefined' ? location.origin : '';
	return `${origin}${base}/cards?post=${encodeURIComponent(slug)}`;
}
