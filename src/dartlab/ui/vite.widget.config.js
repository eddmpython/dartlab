import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import path from "path";

export default defineConfig({
	plugins: [svelte()],
	build: {
		lib: {
			entry: path.resolve("./widget/embed.js"),
			formats: ["iife"],
			name: "DartLabEmbed",
			fileName: () => "embed.js",
		},
		outDir: "build",
		emptyOutDir: false,
		rollupOptions: {
			output: {
				inlineDynamicImports: true,
			},
		},
	},
});
