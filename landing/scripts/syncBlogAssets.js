import { basename, dirname, resolve } from 'path';
import { copyFileSync, existsSync, mkdirSync, readdirSync, rmSync, statSync } from 'fs';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const blogRoot = resolve(__dirname, '..', '..', 'blog');

function collectAssets(dir, result = []) {
	for (const entry of readdirSync(dir)) {
		const fullPath = resolve(dir, entry);
		const stat = statSync(fullPath);
		if (stat.isDirectory()) {
			if (entry === 'assets') {
				for (const asset of readdirSync(fullPath)) {
					const assetPath = resolve(fullPath, asset);
					if (!statSync(assetPath).isFile()) continue;
					if (asset.endsWith('.md')) continue;
					result.push(assetPath);
				}
				continue;
			}
			collectAssets(fullPath, result);
		}
	}
	return result;
}

function syncDir(dest) {
	mkdirSync(dest, { recursive: true });

	const existing = existsSync(dest) ? new Set(readdirSync(dest)) : new Set();
	const source = collectAssets(blogRoot);
	const seen = new Map();
	let copied = 0;

	for (const srcFile of source) {
		const file = basename(srcFile);
		const duplicate = seen.get(file);
		if (duplicate) {
			throw new Error(`Duplicate blog asset filename detected: ${file}\n- ${duplicate}\n- ${srcFile}`);
		}
		seen.set(file, srcFile);

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

if (!existsSync(blogRoot)) {
	console.log('  -> blog/ not found, skipping');
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
