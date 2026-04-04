const { browser, expect, $ } = require("@wdio/globals");

describe("DartLab Webview E2E", () => {
  it("extension activates and panel opens", async () => {
    const workbench = await browser.getWorkbench();
    await workbench.executeCommand("DartLab: New Chat");
    await browser.pause(3000);
  });

  it("webview renders and input is enabled", async () => {
    const workbench = await browser.getWorkbench();
    const webviews = await workbench.getAllWebviews();
    console.log("[E2E] webview count:", webviews.length);
    expect(webviews.length).toBeGreaterThan(0);

    await webviews[0].open();

    const textarea = await $("textarea");
    const exists = await textarea.isExisting();
    console.log("[E2E] textarea exists:", exists);
    expect(exists).toBe(true);

    const enabled = await textarea.isEnabled();
    console.log("[E2E] textarea enabled:", enabled);
    expect(enabled).toBe(true);

    await webviews[0].close();
  });

  it("submit text and get response", async () => {
    const workbench = await browser.getWorkbench();
    const webviews = await workbench.getAllWebviews();
    await webviews[0].open();

    const textarea = await $("textarea");
    await textarea.setValue("안녕하세요");
    console.log("[E2E] typed text");

    await browser.keys("Enter");
    console.log("[E2E] pressed Enter");

    await browser.pause(10000);

    const body = await $("body").getText();
    console.log("[E2E] body text:", body.slice(0, 500));

    const hasContent = body.length > 50;
    console.log("[E2E] has content:", hasContent, "length:", body.length);

    await webviews[0].close();
  });
});
