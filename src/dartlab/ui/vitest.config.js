import { defineConfig } from "vitest/config";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
	plugins: [svelte()],
	test: {
		environment: "node",
		globals: true,
		include: ["src/**/*.test.{js,ts}"],
		pool: "forks",
		fileParallelism: false,
		maxWorkers: 1,
		minWorkers: 1,
	},
});
