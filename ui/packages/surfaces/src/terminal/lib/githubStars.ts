// GitHub 스타 수 · 헤더 SNS GitHub 버튼 옆 라이브 배지(사회적 증명, 과홍보 아님).
// 무인증 API(60/hr·IP) 를 localStorage 6h 캐시로 감싸 호출 최소화. 실패·미조회는 표시하지 않는다(정직 · 가짜 카운트 금지).

const KEY = 'dl:ghStars';
const TTL = 6 * 60 * 60 * 1000; // 6h

/** repoUrl(예: https://github.com/eddmpython/dartlab)에서 stargazers_count. 실패/파싱불가 = null(배지 숨김). */
export async function fetchGithubStars(repoUrl: string): Promise<number | null> {
	const m = repoUrl.match(/github\.com\/([^/]+)\/([^/]+?)(?:\.git)?\/?$/);
	if (!m) return null;
	const slug = `${m[1]}/${m[2]}`;
	try {
		const cached = localStorage.getItem(KEY);
		if (cached) {
			const o = JSON.parse(cached) as { slug?: string; n?: number; t?: number };
			if (o.slug === slug && typeof o.n === 'number' && typeof o.t === 'number' && Date.now() - o.t < TTL) return o.n;
		}
	} catch { /* 캐시 파싱 실패 · 무시하고 네트워크 조회 */ }
	try {
		const r = await fetch(`https://api.github.com/repos/${slug}`, { headers: { Accept: 'application/vnd.github+json' } });
		if (!r.ok) return null;
		const j = (await r.json()) as { stargazers_count?: number };
		const n = j?.stargazers_count;
		if (typeof n !== 'number') return null;
		try { localStorage.setItem(KEY, JSON.stringify({ slug, n, t: Date.now() })); } catch { /* 시크릿 모드 등 · 무시 */ }
		return n;
	} catch { return null; }
}

/** 1.2k 식 축약. */
export function fmtStars(n: number): string {
	return n >= 1000 ? (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k' : String(n);
}

export interface GhContributor { login: string; url: string; avatar: string }
const CONTRIB_KEY = 'dl:ghContrib';

/** repoUrl 의 GitHub 기여자(contributors) 자동 조회 · 봇(type!=User·[bot])·소유자 제외, 기여 많은 순 max 명.
 * GitHub 아바타(avatars.githubusercontent.com)는 임베드용으로 안정적이라 핫링크 가능(Threads 와 다름).
 * 실패/파싱불가 = [](섹션에서 자동 누락). localStorage 6h 캐시. */
export async function fetchGithubContributors(repoUrl: string, max = 12): Promise<GhContributor[]> {
	const m = repoUrl.match(/github\.com\/([^/]+)\/([^/]+?)(?:\.git)?\/?$/);
	if (!m) return [];
	const owner = m[1].toLowerCase();
	const slug = `${m[1]}/${m[2]}`;
	try {
		const cached = localStorage.getItem(CONTRIB_KEY);
		if (cached) {
			const o = JSON.parse(cached) as { slug?: string; list?: GhContributor[]; t?: number };
			if (o.slug === slug && Array.isArray(o.list) && typeof o.t === 'number' && Date.now() - o.t < TTL) return o.list;
		}
	} catch { /* 캐시 파싱 실패 · 네트워크 조회 */ }
	try {
		const r = await fetch(`https://api.github.com/repos/${slug}/contributors?per_page=100`, { headers: { Accept: 'application/vnd.github+json' } });
		if (!r.ok) return [];
		const j = (await r.json()) as Array<{ login?: string; html_url?: string; avatar_url?: string; type?: string }>;
		if (!Array.isArray(j)) return [];
		const list = j
			.filter((c) => c && c.type === 'User' && !!c.login && !c.login.includes('[bot]') && c.login.toLowerCase() !== owner) // 봇·소유자 제외
			.slice(0, max)
			.map((c) => ({ login: c.login as string, url: c.html_url as string, avatar: c.avatar_url as string }));
		try { localStorage.setItem(CONTRIB_KEY, JSON.stringify({ slug, list, t: Date.now() })); } catch { /* 시크릿 모드 등 · 무시 */ }
		return list;
	} catch { return []; }
}
