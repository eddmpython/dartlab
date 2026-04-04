/** Minimal vscode module mock for vitest unit tests. */

export const window = {
  createOutputChannel: () => ({
    appendLine: () => {},
    append: () => {},
    show: () => {},
    dispose: () => {},
  }),
  showErrorMessage: () => Promise.resolve(undefined),
  showInformationMessage: () => Promise.resolve(undefined),
  createStatusBarItem: () => ({
    show: () => {},
    hide: () => {},
    dispose: () => {},
    text: "",
    tooltip: "",
    command: "",
  }),
  tabGroups: { all: [] },
};

export const workspace = {
  getConfiguration: () => ({ get: () => undefined }),
  workspaceFolders: [{ uri: { fsPath: process.cwd() } }],
  fs: {
    readFile: () => Promise.reject(new Error("mock")),
    writeFile: () => Promise.resolve(),
    createDirectory: () => Promise.resolve(),
  },
};

export const commands = {
  registerCommand: () => ({ dispose: () => {} }),
  executeCommand: () => Promise.resolve(),
  getCommands: () => Promise.resolve([]),
};

export const extensions = {
  getExtension: () => undefined,
};

export const Uri = {
  joinPath: (...args: unknown[]) => ({ fsPath: args.join("/") }),
  file: (p: string) => ({ fsPath: p }),
};

export const StatusBarAlignment = { Right: 2, Left: 1 };

export class Disposable {
  constructor(private fn?: () => void) {}
  dispose() { this.fn?.(); }
}

export class EventEmitter {
  event = () => {};
  fire = () => {};
  dispose = () => {};
}
