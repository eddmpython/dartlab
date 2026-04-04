/**
 * Browser E2E test -- webview를 브라우저에서 직접 열고 동작 확인.
 * Vite dev server가 떠있어야 한다 (port 5199).
 * `cd ui/vscode/webview && npx vite --port 5199 &` 후 실행.
 */
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { chromium, Browser, Page } from "playwright";

const URL = "http://localhost:5199/";

describe("DartLab webview in browser", () => {
  let browser: Browser;
  let page: Page;

  beforeAll(async () => {
    browser = await chromium.launch({ headless: true });
    page = await browser.newPage();
    await page.goto(URL);
    // Wait for Svelte to mount
    await page.waitForSelector("#app", { timeout: 10000 });
    // Wait for mock bridge to send serverState=ready
    await page.waitForTimeout(500);
  }, 30000);

  afterAll(async () => {
    await browser?.close();
  });

  it("renders the app container", async () => {
    const app = await page.$("#app");
    expect(app).not.toBeNull();
  });

  it("shows welcome text or chat header", async () => {
    // Either welcome text or header with "Ready" should be visible
    const text = await page.textContent("body");
    expect(text).toBeTruthy();
    console.log("[browser] body text:", text?.slice(0, 200));
  });

  it("has input area", async () => {
    const textarea = await page.$("textarea");
    expect(textarea).not.toBeNull();
  });

  it("input is NOT disabled (serverState=ready from mock)", async () => {
    const textarea = await page.$("textarea");
    const disabled = await textarea?.getAttribute("disabled");
    expect(disabled).toBeNull(); // not disabled
  });

  it("submit text and get mock response", async () => {
    const textarea = await page.$("textarea");
    expect(textarea).not.toBeNull();

    // Type text (basic question, not "분석" or "에러" to get standard mock response)
    await textarea!.fill("안녕하세요");
    await page.keyboard.press("Enter");
    await page.waitForTimeout(1000);

    const body = await page.textContent("body");
    console.log("[browser] after submit:", body?.slice(0, 500));
    expect(body).toContain("mock 응답");
  });

  it("no console errors", async () => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });

    // Navigate again to catch fresh errors
    await page.reload();
    await page.waitForTimeout(1000);

    // Filter out known benign errors
    const real = errors.filter((e) => !e.includes("[vite]") && !e.includes("favicon"));
    expect(real).toEqual([]);
  });

  it("code_round scenario shows execution indicator", async () => {
    await page.reload();
    await page.waitForTimeout(500);
    const textarea = await page.$("textarea");
    await textarea!.fill("삼성전자 분석해줘");
    await page.keyboard.press("Enter");
    await page.waitForTimeout(1500);

    const body = await page.textContent("body");
    console.log("[browser] code_round:", body?.slice(0, 500));
    // Should contain code round indicator text
    expect(body).toContain("Python 실행");
  });

  it("error scenario shows provider switch buttons", async () => {
    await page.reload();
    await page.waitForTimeout(500);
    const textarea = await page.$("textarea");
    await textarea!.fill("에러 테스트");
    await page.keyboard.press("Enter");
    await page.waitForTimeout(1000);

    const body = await page.textContent("body");
    console.log("[browser] error:", body?.slice(0, 500));
    // Should show provider switch buttons
    expect(body).toContain("Gemini");
  });
});
