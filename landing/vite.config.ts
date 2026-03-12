import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import path from 'path';
import fs from 'fs';

const docsDir = path.resolve(__dirname, '..', 'docs');
const blogDir = path.resolve(__dirname, '..', 'blog');

function contentType(filePath: string): string {
	const ext = path.extname(filePath).toLowerCase();
	if (ext === '.svg') return 'image/svg+xml';
	if (ext === '.png') return 'image/png';
	if (ext === '.jpg' || ext === '.jpeg') return 'image/jpeg';
	if (ext === '.webp') return 'image/webp';
	return 'application/octet-stream';
}

function collectBlogAssets(dir: string, result = new Map<string, string>()) {
	for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
		const fullPath = path.resolve(dir, entry.name);
		if (entry.isDirectory()) {
			if (entry.name === 'assets') {
				for (const asset of fs.readdirSync(fullPath, { withFileTypes: true })) {
					if (!asset.isFile()) continue;
					const assetPath = path.resolve(fullPath, asset.name);
					const duplicate = result.get(asset.name);
					if (duplicate) {
						throw new Error(`Duplicate blog asset filename detected: ${asset.name}\n- ${duplicate}\n- ${assetPath}`);
					}
					result.set(asset.name, assetPath);
				}
				continue;
			}
			collectBlogAssets(fullPath, result);
		}
	}
	return result;
}

function blogAssetsPlugin() {
	return {
		name: 'blog-assets-plugin',
		configureServer(server) {
			const assetMap = collectBlogAssets(blogDir);
			server.middlewares.use('/blog/assets', (req, res, next) => {
				const rawPath = req.url?.split('?')[0] ?? '/';
				const fileName = path.basename(rawPath);
				const filePath = assetMap.get(fileName);
				if (!filePath || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
					next();
					return;
				}
				res.setHeader('Content-Type', contentType(filePath));
				fs.createReadStream(filePath).pipe(res);
			});
		}
	};
}

export default defineConfig({
	plugins: [tailwindcss(), blogAssetsPlugin(), sveltekit()],
	resolve: {
		alias: {
			'@docs': docsDir,
			'@blog': blogDir
		}
	},
	server: {
		fs: {
			allow: [
				docsDir,
				blogDir
			]
		}
	}
});
