// 테마(다크/라이트) SSOT · 색은 tokens.css(--dl-*) 가 제어하고, 여기선 *어느 표면에 라이트를 켤지*만 관리.
// 라이트는 비용 낮은 콘텐츠 표면(랜딩 마케팅·about·skills)만. 도구 표면(터미널·scan·map·viewer·블로그 등)은
// 항상 다크(정체성 + 미토큰화 회귀 방지) · 콘텐츠 표면이 늘면 CONTENT_RE 에 추가해 점진 확장한다.
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type ThemePref = 'dark' | 'light';
const KEY = 'dl-theme';

function initialPref(): ThemePref {
	if (!browser) return 'dark';
	try {
		return localStorage.getItem(KEY) === 'light' ? 'light' : 'dark';
	} catch {
		return 'dark';
	}
}

// 사용자 선호(헤더 토글) · 다크 기본. 도구 표면에서도 선호는 보존되지만 적용은 콘텐츠 표면에서만.
export const themePref = writable<ThemePref>(initialPref());

if (browser) {
	themePref.subscribe((v) => {
		try {
			localStorage.setItem(KEY, v);
		} catch {
			/* private mode 등 · 무시 */
		}
	});
}

export function toggleTheme(): void {
	themePref.update((v) => (v === 'light' ? 'dark' : 'light'));
}

// 라이트 적용 콘텐츠 표면 · 루트(/)·about·skills·blog(전 트리: index·article·category·series).
// base(GH Pages /dartlab) 접두 제거 후 판정. 도구 표면(터미널·scan·map·viewer 등)은 항상 다크.
const CONTENT_RE = /(^\/?$)|(\/(about|skills|blog)(\/|$))/;

export function isContentPath(pathname: string, base = ''): boolean {
	let p = pathname;
	if (base && p.startsWith(base)) p = p.slice(base.length);
	if (p === '') p = '/';
	return CONTENT_RE.test(p);
}

// <html data-theme> + color-scheme 적용. 콘텐츠 표면이면 선호, 아니면 강제 다크.
export function applyTheme(pref: ThemePref, pathname: string, base = ''): void {
	if (!browser) return;
	const eff: ThemePref = isContentPath(pathname, base) ? pref : 'dark';
	document.documentElement.dataset.theme = eff;
	document.documentElement.style.colorScheme = eff;
}
