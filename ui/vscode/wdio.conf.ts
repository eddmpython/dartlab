import path from "path";

export const config = {
  runner: "local",
  specs: ["./dist/test/e2e/**/*.js"],
  capabilities: [
    {
      browserName: "vscode",
      browserVersion: "stable",
      "wdio:vscodeOptions": {
        extensionPath: path.resolve(__dirname),
        userSettings: {},
      },
    },
  ],
  services: ["vscode"],
  framework: "mocha",
  mochaOpts: {
    ui: "bdd",
    timeout: 60000,
  },
  logLevel: "info",
};
