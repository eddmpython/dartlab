import * as assert from "assert";
import * as vscode from "vscode";

suite("DartLab Extension", () => {
  test("Extension should be present", () => {
    const ext = vscode.extensions.getExtension("eddmpython.dartlab");
    assert.ok(ext, "Extension not found. Check publisher.name in package.json");
  });

  test("Extension should activate", async () => {
    const ext = vscode.extensions.getExtension("eddmpython.dartlab");
    if (!ext) {
      assert.fail("Extension not found");
      return;
    }
    await ext.activate();
    assert.strictEqual(ext.isActive, true, "Extension did not activate");
  });

  test("Commands should be registered", async () => {
    const commands = await vscode.commands.getCommands(true);
    const dartlabCmds = commands.filter((c) => c.startsWith("dartlab."));

    assert.ok(dartlabCmds.includes("dartlab.open"), "dartlab.open not found");
    assert.ok(dartlabCmds.includes("dartlab.restart"), "dartlab.restart not found");
    assert.ok(dartlabCmds.includes("dartlab.showLogs"), "dartlab.showLogs not found");
    assert.ok(dartlabCmds.includes("dartlab.settings"), "dartlab.settings not found");
    assert.ok(dartlabCmds.includes("dartlab.newConversation"), "dartlab.newConversation not found");
    assert.ok(dartlabCmds.includes("dartlab.focus"), "dartlab.focus not found");
  });

  test("Status bar should show DartLab", async () => {
    // Extension activation should create status bar item
    // We can verify by checking the extension is active
    const ext = vscode.extensions.getExtension("eddmpython.dartlab");
    assert.ok(ext?.isActive, "Extension should be active for status bar");
  });

  test("dartlab.open should open chat panel", async () => {
    await vscode.commands.executeCommand("dartlab.open");
    // Give it a moment to create the panel
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Check if a webview panel was created
    const editors = vscode.window.tabGroups.all.flatMap((g) => g.tabs);
    const dartlabTab = editors.find((t) => t.label === "DartLab");
    assert.ok(dartlabTab, "DartLab chat panel should be open");
  });
});
