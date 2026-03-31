import * as assert from "assert";
import * as vscode from "vscode";

suite("DartLab Extension", () => {
  test("extension should activate", async () => {
    const ext = vscode.extensions.getExtension("eddmpython.dartlab");
    assert.ok(ext, "Extension not found");
    if (!ext.isActive) await ext.activate();
    assert.strictEqual(ext.isActive, true, "Extension did not activate");
  });

  test("commands should be registered", async () => {
    const cmds = await vscode.commands.getCommands(true);
    const expected = ["dartlab.open", "dartlab.restart", "dartlab.showLogs", "dartlab.settings", "dartlab.newConversation", "dartlab.focus"];
    for (const cmd of expected) {
      assert.ok(cmds.includes(cmd), `Command ${cmd} not registered`);
    }
  });

  test("should open DartLab chat panel", async () => {
    await vscode.commands.executeCommand("dartlab.open");
    await new Promise((r) => setTimeout(r, 2000));
    const tabs = vscode.window.tabGroups.all.flatMap((g) => g.tabs);
    const dlTab = tabs.find((t) => t.label === "DartLab");
    assert.ok(dlTab, "DartLab tab should exist after dartlab.open");
  });
});
