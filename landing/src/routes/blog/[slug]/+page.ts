import type { EntryGenerator } from './$types';
import type { CompanyAnnualFinance, CompanyQuarterlyFinance } from '@dartlab/ui-runtime/data/finance/annual';

// lazy glob: 글 하나를 열 때 그 글의 컴포넌트와 원문만 받는다(예전 eager glob 은 293편 전부를 한 청크에 묶었다).
type BlogComponentModule = { default: ConstructorOfATypedSvelteComponent; metadata?: Record<string, string> };
const modules = import.meta.glob('@blog/**/index.md') as Record<string, () => Promise<BlogComponentModule>>;
const rawModules = import.meta.glob('@blog/**/index.md', { query: '?raw', import: 'default' }) as Record<string, () => Promise<string>>;

function normalizePath(rawPath: string): string {
	const match = rawPath.match(/\/blog\/[^/]+\/\d+-([^/]+)\/index\.md$/);
	return match?.[1] ?? '';
}

const pathBySlug = new Map<string, string>();
for (const path of Object.keys(modules)) {
	const slug = normalizePath(path);
	if (slug) pathBySlug.set(slug, path);
}

export const entries: EntryGenerator = () => {
	return [...pathBySlug.keys()].map((slug) => ({ slug }));
};

export const prerender = true;

// server load(+page.server.ts)의 companyFinance 를 universal 반환에 forward · 둘 다 있을 때 page `data` 는
// universal 반환이 권위라 명시 병합 필요(블로그 회사글 재무 = 빌드타임 SSOT 직독, +page.server.ts 참조).
export async function load({ params, data }: { params: { slug: string }; data: { companyFinance?: CompanyAnnualFinance | null; companyQuarter?: CompanyQuarterlyFinance | null } }) {
	const path = pathBySlug.get(params.slug);
	const companyFinance = data?.companyFinance ?? null;
	const companyQuarter = data?.companyQuarter ?? null;

	if (!path) {
		return { status: 404, companyFinance, companyQuarter };
	}

	const [mod, rawMarkdown] = await Promise.all([modules[path](), rawModules[path]()]);

	return {
		component: mod.default,
		metadata: mod.metadata ?? {},
		rawMarkdown: rawMarkdown ?? '',
		slug: params.slug,
		currentCategory: mod.metadata?.category ?? null,
		companyFinance,
		companyQuarter
	};
}
