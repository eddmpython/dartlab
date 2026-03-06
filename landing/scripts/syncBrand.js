import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const brandPath = resolve(__dirname, '..', 'src', 'lib', 'brand.ts');

const brandSrc = readFileSync(brandPath, 'utf-8');
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

const heroSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" fill="none">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="800" y2="200" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="${colors.bgDark}"/>
      <stop offset="100%" stop-color="${colors.bgCard}"/>
    </linearGradient>
    <linearGradient id="amber" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="${colors.primary}"/>
      <stop offset="100%" stop-color="${colors.primaryLight}"/>
    </linearGradient>
    <linearGradient id="blue" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="${colors.accent}"/>
      <stop offset="100%" stop-color="${colors.accentLight}"/>
    </linearGradient>
    <linearGradient id="textGrad" x1="0" y1="0" x2="400" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="${colors.primary}"/>
      <stop offset="50%" stop-color="${colors.primaryLight}"/>
      <stop offset="100%" stop-color="${colors.primary}"/>
    </linearGradient>
  </defs>

  <rect width="800" height="200" rx="16" fill="url(#bg)"/>

  <rect x="40" y="60" width="3" height="80" rx="1.5" fill="url(#amber)" opacity="0.6"/>
  <rect x="50" y="45" width="3" height="110" rx="1.5" fill="url(#amber)" opacity="0.4"/>
  <rect x="60" y="70" width="3" height="60" rx="1.5" fill="url(#blue)" opacity="0.5"/>
  <rect x="70" y="50" width="3" height="100" rx="1.5" fill="url(#amber)" opacity="0.3"/>
  <rect x="80" y="65" width="3" height="70" rx="1.5" fill="url(#blue)" opacity="0.4"/>
  <rect x="90" y="55" width="3" height="90" rx="1.5" fill="url(#amber)" opacity="0.5"/>
  <rect x="100" y="75" width="3" height="50" rx="1.5" fill="url(#blue)" opacity="0.3"/>

  <text x="140" y="105" font-family="'Inter', 'Segoe UI', system-ui, sans-serif" font-size="56" font-weight="800" fill="url(#textGrad)">DartLab</text>

  <line x1="420" y1="70" x2="420" y2="130" stroke="${colors.border}" stroke-width="1"/>

  <text x="445" y="92" font-family="'Inter', 'Segoe UI', system-ui, sans-serif" font-size="18" font-weight="500" fill="${colors.textMuted}">DART 공시 문서를 완벽하게 분석하는</text>
  <text x="445" y="120" font-family="'Inter', 'Segoe UI', system-ui, sans-serif" font-size="18" font-weight="500" fill="${colors.textMuted}">Python 라이브러리</text>

  <rect x="640" y="75" width="120" height="28" rx="14" fill="${colors.border}"/>
  <text x="700" y="94" font-family="'JetBrains Mono', 'Fira Code', monospace" font-size="13" font-weight="600" fill="${colors.primary}" text-anchor="middle">숫자 + 텍스트</text>

  <rect x="640" y="110" width="120" height="28" rx="14" fill="${colors.border}"/>
  <text x="700" y="129" font-family="'JetBrains Mono', 'Fira Code', monospace" font-size="13" font-weight="600" fill="${colors.accent}" text-anchor="middle">시계열 정렬</text>
</svg>
`;

writeFileSync(resolve(__dirname, '..', 'src', 'app.css'), appCss);
writeFileSync(resolve(__dirname, '..', '..', 'docs', 'stylesheets', 'theme.css'), mkdocsCss);
writeFileSync(resolve(__dirname, '..', '..', 'assets', 'hero.svg'), heroSvg);

console.log('Brand synced:');
console.log('  -> landing/src/app.css');
console.log('  -> docs/stylesheets/theme.css');
console.log('  -> assets/hero.svg');
