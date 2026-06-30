import type { EntryGenerator } from './$types';
import type { CompanyAnnualFinance } from '@dartlab/ui-runtime/data/finance/annual';

const modules = import.meta.glob('@blog/**/index.md', { eager: true }) as Record<
	string,
	{ default: ConstructorOfATypedSvelteComponent; metadata?: Record<string, string> }
>;
const rawModules = import.meta.glob('@blog/**/index.md', { eager: true, query: '?raw', import: 'default' }) as Record<string, string>;

function normalizePath(rawPath: string): string {
	const match = rawPath.match(/\/blog\/[^/]+\/\d+-([^/]+)\/index\.md$/);
	return match?.[1] ?? '';
}

const slugMap = new Map<
	string,
	{ component: ConstructorOfATypedSvelteComponent; metadata?: Record<string, string>; rawMarkdown: string }
>();

for (const [path, mod] of Object.entries(modules)) {
	const slug = normalizePath(path);
	if (!slug) continue;
	slugMap.set(slug, { component: mod.default, metadata: mod.metadata, rawMarkdown: rawModules[path] ?? '' });
}

export const entries: EntryGenerator = () => {
	return [...slugMap.keys()].map((slug) => ({ slug }));
};

export const prerender = true;

// server load(+page.server.ts)의 companyFinance 를 universal 반환에 forward · 둘 다 있을 때 page `data` 는
// universal 반환이 권위라 명시 병합 필요(블로그 회사글 재무 = 빌드타임 SSOT 직독, +page.server.ts 참조).
export function load({ params, data }: { params: { slug: string }; data: { companyFinance?: CompanyAnnualFinance | null } }) {
	const entry = slugMap.get(params.slug);
	const companyFinance = data?.companyFinance ?? null;

	if (!entry) {
		return { status: 404, companyFinance };
	}

	return {
		component: entry.component,
		metadata: entry.metadata ?? {},
		rawMarkdown: entry.rawMarkdown,
		slug: params.slug,
		currentCategory: entry.metadata?.category ?? null,
		companyFinance
	};
}
