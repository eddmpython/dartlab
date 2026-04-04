const path = require("path");

exports.config = {
  runner: "local",
  specs: ["./test/e2e/**/*.test.js"],
  capabilities: [
    {
      browserName: "vscode",
      browserVersion: "1.96.0",
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
