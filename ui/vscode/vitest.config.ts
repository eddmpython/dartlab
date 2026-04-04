import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    include: ["src/test/*.test.ts"],
    exclude: ["src/test/suite/**"],
    testTimeout: 30_000,
  },
  resolve: {
    alias: {
      vscode: path.resolve(__dirname, "src/test/__mocks__/vscode.ts"),
    },
  },
});
