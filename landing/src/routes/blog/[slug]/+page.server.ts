// 블로그 회사글 재무 · 데이터 SSOT(dart/finance/{code}.parquet)를 빌드타임(prerender·Node)에 직독해
// 정적 HTML 에 굽는다. 터미널과 동일한 표준화(@dartlab/ui-runtime accounts.ts SSOT) → 숫자 일치·화석화 불가.
// 옛 blog/_scripts/sync_financials.py(커밋 시점 정적 bake) 대체. KR 6자리 코드만(EDGAR=Phase 2).
//
// 서버 load 라 prerender 시 1회 산출→정적, 클라이언트 네비게이션은 baked __data.json 재사용(HF 재페치 0).
import { loadAnnualStatements, type CompanyAnnualFinance } from '@dartlab/ui-runtime/data/finance/annual';

// slug → stockCode (frontmatter). raw 글롭은 posts.ts·+page.ts 도 쓰는 동일 소스(추가 비용 0).
const raw = import.meta.glob('@blog/**/index.md', { eager: true, query: '?raw', import: 'default' }) as Record<string, string>;

function frontmatterField(md: string, key: string): string | null {
	const fm = md.match(/^---\r?\n([\s\S]*?)\r?\n---/);
	if (!fm || !fm[1]) return null;
	const line = fm[1].match(new RegExp(`^${key}:\\s*["']?([^"'\\r\\n]+)`, 'm'));
	return line && line[1] ? line[1].trim() : null;
}

const codeBySlug = new Map<string, string>();
for (const [path, md] of Object.entries(raw)) {
	const m = path.match(/\/blog\/[^/]+\/\d+-([^/]+)\/index\.md$/);
	if (!m || !m[1]) continue;
	const code = frontmatterField(md, 'stockCode');
	if (code) codeBySlug.set(m[1], code);
}

export async function load({ params }: { params: { slug: string } }): Promise<{ companyFinance: CompanyAnnualFinance | null }> {
	const code = codeBySlug.get(params.slug);
	if (!code || !/^\d{6}$/.test(code)) return { companyFinance: null };
	return { companyFinance: await loadAnnualStatements(code) };
}
