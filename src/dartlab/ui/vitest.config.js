import { defineConfig } from "vitest/config";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import path from "path";

export default defineConfig({
	plugins: [svelte({ hot: false })],
	resolve: {
		conditions: ["browser"],
		alias: {
			$lib: path.resolve("./src/lib"),
		},
	},
	test: {
		globals: true,
		pool: "forks",
		fileParallelism: false,
		maxWorkers: 1,
		minWorkers: 1,
		projects: [
			{
				test: {
					name: "contracts",
					environment: "node",
					include: ["src/test/**/*.test.{js,ts}"],
				},
			},
			{
				extends: true,
				test: {
					name: "components",
					environment: "jsdom",
					include: ["src/**/*.component.test.{js,ts}"],
					setupFiles: ["src/test/setup-component.js"],
				},
			},
		],
	},
});
