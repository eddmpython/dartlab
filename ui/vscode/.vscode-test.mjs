import { defineConfig } from '@vscode/test-cli';

export default defineConfig({
  files: 'dist/test/integration/**/*.test.js',
  version: 'stable',
  mocha: {
    ui: 'tdd',
    timeout: 30000,
  },
});
