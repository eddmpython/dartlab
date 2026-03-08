import { writeFileSync, readFileSync, mkdirSync, existsSync, copyFileSync, readdirSync } from 'fs';
import { resolve, dirname, relative } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const buildDir = resolve(__dirname, '..', 'build');
const projectRoot = resolve(__dirname, '..', '..');
const basePath = process.env.BASE_PATH || '';
const siteUrl = 'https://eddmpython.github.io/dartlab';
const target = `${basePath}/docs/getting-started/quickstart`;

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
function collectMdFiles(dir, prefix = '') {
	const results = [];
	if (!existsSync(dir)) return results;
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		if (entry.name === 'STATUS.md' || entry.name === 'index.md') continue;
		const full = resolve(dir, entry.name);
		if (entry.isDirectory()) {
			results.push(...collectMdFiles(full, `${prefix}${entry.name}/`));
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

const docsRoot = resolve(projectRoot, 'docs');
const blogRoot = resolve(projectRoot, 'blog');

const docFiles = collectMdFiles(docsRoot);
const blogFiles = collectMdFiles(blogRoot);

const sections = [
	{
		heading: 'Docs',
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
		files: blogFiles,
		urlPrefix: `${siteUrl}/blog/`,
		pathToUrl: (rel) => {
			return rel
				.replace(/\.md$/, '')
				.replace(/^\d+-/, '');
		}
	}
];

let llmsTxt = `# DartLab

> A Python library for comprehensive DART disclosure analysis. Read Beyond the Numbers.

DartLab은 한국 금융감독원 DART 전자공시 데이터를 수집·분석하는 Python 라이브러리다.
정량 데이터(재무제표, 밸류에이션)와 정성 데이터(감사의견, 지배구조), 공시 문서 텍스트를 모두 다룬다.

`;

let fullParts = [];

for (const section of sections) {
	if (section.files.length === 0) continue;
	llmsTxt += `## ${section.heading}\n`;
	for (const file of section.files) {
		const content = readFileSync(file.path, 'utf-8');
		const title = extractTitle(content) || file.rel;
		const url = section.urlPrefix + section.pathToUrl(file.rel);
		llmsTxt += `- [${title}](${url})\n`;
		fullParts.push(`# ${title}\n\nSource: ${url}\n\n${stripFrontmatter(content)}`);
	}
	llmsTxt += '\n';
}

writeFileSync(resolve(buildDir, 'llms.txt'), llmsTxt.trim() + '\n', 'utf-8');
console.log(`  -> llms.txt generated (${sections.reduce((n, s) => n + s.files.length, 0)} files)`);

writeFileSync(resolve(buildDir, 'llms-full.txt'), fullParts.join('\n\n---\n\n') + '\n', 'utf-8');
console.log(`  -> llms-full.txt generated (${Math.round(fullParts.join('').length / 1024)}KB)`);
