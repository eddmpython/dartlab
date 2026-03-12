import { existsSync, mkdirSync, readdirSync, copyFileSync, statSync, rmSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const src = resolve(__dirname, '..', '..', 'blog', 'assets');

function syncDir(dest) {
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
		rmSync(resolve(dest, stale), { recursive: true, force: true });
	}

	return { copied, removed: existing.size, total: source.length };
}

function cleanDir(dest) {
	rmSync(dest, { recursive: true, force: true });
}

if (!existsSync(src)) {
	console.log('  -> blog/assets/ not found, skipping');
	process.exit(0);
}

const mode = process.argv[2] || 'build';

if (mode === 'prepare') {
	const staticDest = resolve(__dirname, '..', 'static', 'blog', 'assets');
	const result = syncDir(staticDest);
	console.log(`  -> blog assets prepared: ${result.copied} copied, ${result.removed} removed (${result.total} total)`);
	process.exit(0);
}

if (mode === 'finalize') {
	const buildDest = resolve(__dirname, '..', 'build', 'blog', 'assets');
	const staticDest = resolve(__dirname, '..', 'static', 'blog', 'assets');
	const result = syncDir(buildDest);
	cleanDir(staticDest);
	console.log(`  -> blog assets finalized: ${result.copied} copied, ${result.removed} removed (${result.total} total)`);
	process.exit(0);
}

console.error(`Unknown mode: ${mode}`);
process.exit(1);
