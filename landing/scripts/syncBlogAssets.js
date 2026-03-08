import { existsSync, mkdirSync, readdirSync, copyFileSync, statSync, rmSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const src = resolve(__dirname, '..', '..', 'blog', 'assets');
const dest = resolve(__dirname, '..', 'static', 'blog', 'assets');

if (!existsSync(src)) {
	console.log('  -> blog/assets/ not found, skipping');
	process.exit(0);
}

mkdirSync(dest, { recursive: true });

const existing = existsSync(dest) ? new Set(readdirSync(dest)) : new Set();
const source = readdirSync(src);
let copied = 0;

for (const file of source) {
	const srcFile = resolve(src, file);
	if (!statSync(srcFile).isFile()) continue;
	if (file.endsWith('.md')) continue;
	const destFile = resolve(dest, file);
	const srcMtime = statSync(srcFile).mtimeMs;
	const needsCopy = !existsSync(destFile) || statSync(destFile).mtimeMs < srcMtime;
	if (needsCopy) {
		copyFileSync(srcFile, destFile);
		copied++;
	}
	existing.delete(file);
}

for (const stale of existing) {
	rmSync(resolve(dest, stale));
}

console.log(`  -> blog assets synced: ${copied} copied, ${existing.size} removed (${source.length} total)`);
