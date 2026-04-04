import { build } from "esbuild";

const production = process.argv.includes("--production");
const watch = process.argv.includes("--watch");

/** @type {import("esbuild").BuildOptions} */
const options = {
  entryPoints: ["src/extension.ts"],
  bundle: true,
  outfile: "dist/extension.js",
  external: ["vscode"],
  format: "cjs",
  platform: "node",
  target: "node18",
  sourcemap: !production,
  minify: production,
  logLevel: "info",
};

if (watch) {
  const ctx = await build({ ...options, plugins: [] });
  // esbuild 0.17+ watch API
  const result = await build({
    ...options,
    plugins: [
      {
        name: "watch-notify",
        setup(build) {
          build.onEnd((result) => {
            if (result.errors.length === 0) {
              console.log("[esbuild] rebuild complete");
            }
          });
        },
      },
    ],
  });
  console.log("[esbuild] watching for changes...");
} else {
  await build(options);
}
