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
		outDir: "build",
		emptyOutDir: true,
	},
	server: {
		proxy: {
			"/api": "http://localhost:8400",
		},
	},
});
