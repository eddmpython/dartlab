import { writeFileSync, readFileSync, mkdirSync, existsSync, copyFileSync, readdirSync } from 'fs';
import { resolve, dirname, relative } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const buildDir = resolve(__dirname, '..', 'build');
const projectRoot = resolve(__dirname, '..', '..');
const basePath = process.env.BASE_PATH || '';
const siteUrl = 'https://eddmpython.github.io/dartlab';
const target = `${basePath}/docs/getting-started/installation`;
const extraPages = [];

const docsDir = resolve(buildDir, 'docs');

// docs/index.html — redirect to quickstart
const docsIndex = resolve(docsDir, 'index.html');
if (!existsSync(docsIndex)) {
	mkdirSync(docsDir, { recursive: true });
	writeFileSync(docsIndex, `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0;url=${target}">
<link rel="canonical" href="${target}">
<title>Redirecting...</title>
</head>
<body>
<script>window.location.replace("${target}")</script>
</body>
</html>
`);
	console.log(`  -> docs/index.html redirect to ${target}`);
}

// blog/index.html — copy from blog.html if SvelteKit generated it as blog.html
const blogHtml = resolve(buildDir, 'blog.html');
const blogDir = resolve(buildDir, 'blog');
const blogIndex = resolve(blogDir, 'index.html');

if (existsSync(blogHtml) && !existsSync(blogIndex)) {
	mkdirSync(blogDir, { recursive: true });
	copyFileSync(blogHtml, blogIndex);
	console.log('  -> blog/index.html copied from blog.html');
}

// llms.txt + llms-full.txt — auto-generate from docs/ and blog/ markdown
function collectMdFiles(dir, prefix = '', options = {}) {
	const results = [];
	if (!existsSync(dir)) return results;
	const { includeIndex = false } = options;
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		if (entry.name === 'STATUS.md') continue;
		if (entry.name === 'index.md' && !includeIndex) continue;
		if (entry.name === '_deprecated' || entry.name === '_backup' || entry.name === '_reference') continue;
		const full = resolve(dir, entry.name);
		if (entry.isDirectory()) {
			results.push(...collectMdFiles(full, `${prefix}${entry.name}/`, options));
		} else if (entry.name.endsWith('.md')) {
			results.push({ path: full, rel: `${prefix}${entry.name}` });
		}
	}
	return results;
}

function extractTitle(content) {
	const fm = content.match(/^---\s*\n([\s\S]*?)\n---/);
	if (fm) {
		const titleMatch = fm[1].match(/title:\s*(.+)/);
		if (titleMatch) return titleMatch[1].trim().replace(/^['"]|['"]$/g, '');
	}
	const h1 = content.match(/^#\s+(.+)/m);
	if (h1) return h1[1].trim();
	return null;
}

function stripFrontmatter(content) {
	return content.replace(/^---\s*\n[\s\S]*?\n---\s*\n/, '').trim();
}

function writeMarkdownMirror(relPath, title, url, description, content) {
	const outPath = resolve(buildDir, 'markdown', relPath);
	const body = stripFrontmatter(content);
	const parts = [`# ${title}`, `Source: ${url}`];
	if (description) parts.push(`Summary: ${description}`);
	parts.push(body);
	mkdirSync(dirname(outPath), { recursive: true });
	writeFileSync(outPath, parts.join('\n\n').trim() + '\n', 'utf-8');
	return `${siteUrl}/markdown/${relPath.replace(/\\/g, '/')}`;
}

const docsRoot = resolve(projectRoot, 'docs');
const blogRoot = resolve(projectRoot, 'blog');

const docFiles = collectMdFiles(docsRoot);
const blogFiles = collectMdFiles(blogRoot, '', { includeIndex: true }).filter((file) =>
	/^[^/]+\/\d+-[^/]+\/index\.md$/.test(file.rel)
);

const sections = [
	{
		heading: 'Docs',
		description: '설치, quickstart, API reference, 튜토리얼. DartLab을 실제 코드와 데이터 흐름으로 사용하는 문서.',
		files: docFiles,
		urlPrefix: `${siteUrl}/docs/`,
		pathToUrl: (rel) => {
			return rel
				.replace(/\.md$/, '')
				.replace(/^\d+_/, '')
				.replace(/\/\d+_/g, '/');
		}
	},
	{
		heading: 'Blog',
		description: 'DART, EDGAR, 사업보고서 읽기, 재무 해석, 데이터 자동화에 관한 장문 가이드.',
		files: blogFiles,
		urlPrefix: `${siteUrl}/blog/`,
		pathToUrl: (rel) => {
			const match = rel.match(/^[^/]+\/\d+-([^/]+)\/index\.md$/);
			return match?.[1] ?? rel.replace(/\.md$/, '');
		}
	}
];

let llmsTxt = `# DartLab

> A Python library for comprehensive DART disclosure analysis. Read Beyond the Numbers.

DartLab은 한국 금융감독원 DART 전자공시 데이터를 수집·분석하는 Python 라이브러리다.
정량 데이터(재무제표, 밸류에이션)와 정성 데이터(감사의견, 지배구조), 공시 문서 텍스트를 모두 다룬다.
AI 크롤러와 답변 엔진을 위해 각 페이지의 markdown mirror도 함께 제공한다.

`;

let fullParts = [];

for (const section of sections) {
	if (section.files.length === 0) continue;
	llmsTxt += `## ${section.heading}\n`;
	llmsTxt += `${section.description}\n\n`;
	for (const file of section.files) {
		const content = readFileSync(file.path, 'utf-8');
		const fm = extractFrontmatter(content);
		const title = extractTitle(content) || file.rel;
		const url = section.urlPrefix + section.pathToUrl(file.rel);
		const description = fm.description || '';
		const mirrorRelPath =
			section.heading === 'Docs'
				? `docs/${section.pathToUrl(file.rel)}.md`
				: `blog/${section.pathToUrl(file.rel)}.md`;
		const mirrorUrl = writeMarkdownMirror(mirrorRelPath, title, url, description, content);
		const detail = description ? ` — ${description}` : '';
		llmsTxt += `- [${title}](${url})${detail} | Markdown: ${mirrorUrl}\n`;
		fullParts.push(`# ${title}\n\nSource: ${url}\n\n${stripFrontmatter(content)}`);
	}
	llmsTxt += '\n';
}

writeFileSync(resolve(buildDir, 'llms.txt'), llmsTxt.trim() + '\n', 'utf-8');
console.log(`  -> llms.txt generated (${sections.reduce((n, s) => n + s.files.length, 0)} files)`);

writeFileSync(resolve(buildDir, 'llms-full.txt'), fullParts.join('\n\n---\n\n') + '\n', 'utf-8');
console.log(`  -> llms-full.txt generated (${Math.round(fullParts.join('').length / 1024)}KB)`);

// sitemap.xml — auto-generate with docs + blog
function extractFrontmatter(content) {
	const fm = content.match(/^---\s*\n([\s\S]*?)\n---/);
	if (!fm) return {};
	const result = {};
	for (const line of fm[1].split('\n')) {
		const m = line.match(/^(\w+):\s*(.+)/);
		if (m) result[m[1]] = m[2].trim().replace(/^['"]|['"]$/g, '');
	}
	return result;
}

const docUrls = docFiles.map(f => {
	const url = `${siteUrl}/docs/` + f.rel.replace(/\.md$/, '').replace(/^\d+_/, '').replace(/\/\d+_/g, '/');
	return { loc: url, priority: '0.7', changefreq: 'monthly' };
});

const blogPosts = blogFiles.map(f => {
	const content = readFileSync(f.path, 'utf-8');
	const fm = extractFrontmatter(content);
	const slugMatch = f.rel.match(/^[^/]+\/\d+-([^/]+)\/index\.md$/);
	const slug = slugMatch?.[1] ?? f.rel.replace(/\.md$/, '');
	return {
		loc: `${siteUrl}/blog/${slug}`,
		priority: '0.8',
		changefreq: 'monthly',
		lastmod: fm.date || null,
		title: fm.title || slug,
		description: fm.description || '',
		date: fm.date || null
	};
});

const blogCategories = [...new Set(blogFiles
	.map(f => {
		const content = readFileSync(f.path, 'utf-8');
		const fm = extractFrontmatter(content);
		return fm.category || null;
	})
	.filter(Boolean))];

const blogSeries = [...new Set(blogFiles
	.map(f => {
		const content = readFileSync(f.path, 'utf-8');
		const fm = extractFrontmatter(content);
		return fm.series || null;
	})
	.filter(Boolean))];

let sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n`;
sitemap += `  <url>\n    <loc>${siteUrl}/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n`;
sitemap += `  <url>\n    <loc>${siteUrl}/docs/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.9</priority>\n  </url>\n`;
sitemap += `  <url>\n    <loc>${siteUrl}/blog/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.9</priority>\n  </url>\n`;
for (const extraPage of extraPages) {
	sitemap += `  <url>\n    <loc>${extraPage.loc}</loc>\n    <changefreq>${extraPage.changefreq}</changefreq>\n    <priority>${extraPage.priority}</priority>\n  </url>\n`;
}
for (const category of blogCategories) {
	sitemap += `  <url>\n    <loc>${siteUrl}/blog/category/${category}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.75</priority>\n  </url>\n`;
}
for (const series of blogSeries) {
	sitemap += `  <url>\n    <loc>${siteUrl}/blog/series/${series}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.72</priority>\n  </url>\n`;
}
for (const u of docUrls) {
	sitemap += `  <url>\n    <loc>${u.loc}</loc>\n    <changefreq>${u.changefreq}</changefreq>\n    <priority>${u.priority}</priority>\n  </url>\n`;
}
for (const p of blogPosts) {
	sitemap += `  <url>\n    <loc>${p.loc}</loc>\n    <changefreq>${p.changefreq}</changefreq>\n    <priority>${p.priority}</priority>\n`;
	if (p.lastmod) sitemap += `    <lastmod>${p.lastmod}</lastmod>\n`;
	sitemap += `  </url>\n`;
}
sitemap += `</urlset>\n`;

writeFileSync(resolve(buildDir, 'sitemap.xml'), sitemap, 'utf-8');
console.log(`  -> sitemap.xml generated (${docUrls.length} docs + ${blogPosts.length} blog posts)`);

// RSS feed (Atom)
const feedUpdated = blogPosts.length > 0 ? blogPosts[0].date || new Date().toISOString().slice(0, 10) : new Date().toISOString().slice(0, 10);

let atom = `<?xml version="1.0" encoding="UTF-8"?>\n`;
atom += `<feed xmlns="http://www.w3.org/2005/Atom">\n`;
atom += `  <title>DartLab Blog</title>\n`;
atom += `  <subtitle>DART 전자공시 데이터 분석 — Read Beyond the Numbers</subtitle>\n`;
atom += `  <link href="${siteUrl}/feed.xml" rel="self" type="application/atom+xml"/>\n`;
atom += `  <link href="${siteUrl}/blog/" rel="alternate" type="text/html"/>\n`;
atom += `  <id>${siteUrl}/blog/</id>\n`;
atom += `  <updated>${feedUpdated}T00:00:00Z</updated>\n`;
atom += `  <author>\n    <name>eddmpython</name>\n    <uri>https://github.com/eddmpython</uri>\n  </author>\n`;

for (const p of blogPosts) {
	atom += `  <entry>\n`;
	atom += `    <title>${p.title.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</title>\n`;
	atom += `    <link href="${p.loc}" rel="alternate" type="text/html"/>\n`;
	atom += `    <id>${p.loc}</id>\n`;
	if (p.date) atom += `    <published>${p.date}T00:00:00Z</published>\n`;
	if (p.date) atom += `    <updated>${p.date}T00:00:00Z</updated>\n`;
	if (p.description) atom += `    <summary>${p.description.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</summary>\n`;
	atom += `  </entry>\n`;
}

atom += `</feed>\n`;

writeFileSync(resolve(buildDir, 'feed.xml'), atom, 'utf-8');
console.log(`  -> feed.xml generated (${blogPosts.length} entries)`);
