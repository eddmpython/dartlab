import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const brandPath = resolve(__dirname, '..', 'src', 'lib', 'brand.ts');
const pyprojectPath = resolve(__dirname, '..', '..', 'pyproject.toml');

const pyproject = readFileSync(pyprojectPath, 'utf-8');
const versionMatch = pyproject.match(/^version\s*=\s*"([^"]+)"/m);
if (!versionMatch) { console.error('pyproject.toml version not found'); process.exit(1); }
const version = versionMatch[1];

let brandSrc = readFileSync(brandPath, 'utf-8');
const oldVersion = brandSrc.match(/version:\s*'([^']+)'/)?.[1];
if (oldVersion !== version) {
	brandSrc = brandSrc.replace(/version:\s*'[^']+'/, `version: '${version}'`);
	writeFileSync(brandPath, brandSrc);
	console.log(`  -> brand.ts version: ${oldVersion} -> ${version}`);
} else {
	console.log(`  -> brand.ts version: ${version} (unchanged)`);
}
const colorBlock = brandSrc.match(/color:\s*\{([^}]+)\}/s)?.[1];
if (!colorBlock) { console.error('brand.ts color block not found'); process.exit(1); }

const colors = {};
for (const m of colorBlock.matchAll(/(\w+):\s*'(#[0-9a-fA-F]+)'/g)) {
	colors[m[1]] = m[2];
}

const cssVars = Object.entries(colors).map(([k, v]) => {
	const cssKey = k.replace(/([A-Z])/g, '-$1').toLowerCase();
	return `\t--color-dl-${cssKey}: ${v};`;
}).join('\n');

const appCss = `@import "tailwindcss";

@theme {
${cssVars}

\t--font-sans: 'Pretendard Variable', 'Inter', ui-sans-serif, system-ui, sans-serif;
\t--font-mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
\t--animate-float: float 3s ease-in-out infinite;
}

@keyframes float {
\t0%, 100% { transform: translateY(0); }
\t50% { transform: translateY(-8px); }
}
`;

const mkdocsCss = `[data-md-color-scheme="slate"] {
    --md-primary-fg-color: ${colors.primary};
    --md-primary-bg-color: ${colors.bgDark};
    --md-accent-fg-color: ${colors.accent};
    --md-default-bg-color: ${colors.bgDark};
    --md-code-bg-color: ${colors.bgCard};
}

[data-md-color-scheme="default"] {
    --md-primary-fg-color: ${colors.primaryDark};
    --md-accent-fg-color: ${colors.accent};
}
`;

writeFileSync(resolve(__dirname, '..', 'src', 'app.css'), appCss);

const mkdocsDir = resolve(__dirname, '..', '..', 'docs', 'stylesheets');
mkdirSync(mkdocsDir, { recursive: true });
writeFileSync(resolve(mkdocsDir, 'theme.css'), mkdocsCss);

console.log('Brand synced:');
console.log('  -> landing/src/app.css');
console.log('  -> docs/stylesheets/theme.css');
