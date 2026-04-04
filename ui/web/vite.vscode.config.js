/**
 * VSCode webview 빌드 설정.
 * 같은 Svelte 앱을 vscode/dist/webview/에 단일 번들로 출력한다.
 * Usage: npm run build:vscode
 */
import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
	plugins: [svelte(), tailwindcss()],
	resolve: {
		alias: {
			$lib: path.resolve("./src/lib"),
		},
	},
	build: {
		outDir: "../vscode/dist/webview",
		emptyOutDir: true,
		rollupOptions: {
			input: path.resolve("./src/main.js"),
			output: {
				entryFileNames: "main.js",
				chunkFileNames: "[name].js",
				assetFileNames: "[name][extname]",
			},
		},
	},
});
