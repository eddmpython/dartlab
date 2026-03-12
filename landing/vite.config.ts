import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import path from 'path';
import fs from 'fs';

const docsDir = path.resolve(__dirname, '..', 'docs');
const blogDir = path.resolve(__dirname, '..', 'blog');
const blogAssetsDir = path.resolve(blogDir, 'assets');

function contentType(filePath: string): string {
	const ext = path.extname(filePath).toLowerCase();
	if (ext === '.svg') return 'image/svg+xml';
	if (ext === '.png') return 'image/png';
	if (ext === '.jpg' || ext === '.jpeg') return 'image/jpeg';
	if (ext === '.webp') return 'image/webp';
	return 'application/octet-stream';
}

function blogAssetsPlugin() {
	return {
		name: 'blog-assets-plugin',
		configureServer(server) {
			server.middlewares.use('/blog/assets', (req, res, next) => {
				const rawPath = req.url?.split('?')[0] ?? '/';
				const relativePath = rawPath.replace(/^\/+/, '');
				const filePath = path.resolve(blogAssetsDir, relativePath);
				if (!filePath.startsWith(blogAssetsDir + path.sep) || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
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
