/** VSCode webview screenshot — mock bridge dev mode */
import { chromium } from "playwright";
import { fileURLToPath } from "url";
import path from "path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SCREENSHOTS = path.resolve(__dirname, "../../../../screenshots");
const label = process.argv[2] || "vscode";
const PORT = 5404;

async function run() {
  const browser = await chromium.launch();

  // Desktop (VSCode panel width ~400px)
  const desktop = await browser.newPage({ viewport: { width: 420, height: 800 } });
  await desktop.goto(`http://localhost:${PORT}`, { waitUntil: "networkidle" });
  // Wait for mock bridge to init
  await desktop.waitForTimeout(600);
  await desktop.screenshot({ path: path.join(SCREENSHOTS, `${label}_empty.png`) });

  // Type a question to trigger mock response
  const textarea = desktop.locator("textarea");
  if (await textarea.count()) {
    await textarea.click();
    await desktop.keyboard.type("SK하이닉스 분석", { delay: 30 });
    await desktop.waitForTimeout(200);
    // Debug: check textarea value before submit
    const val = await textarea.inputValue();
    console.log("[debug] textarea value before Enter:", JSON.stringify(val));
    await desktop.keyboard.press("Enter");
    // Wait for mock SSE to complete (mock takes ~1.4s)
    await desktop.waitForTimeout(3500);
    // Debug: check DOM state
    const msgCount = await desktop.evaluate(() => document.querySelectorAll(".msg").length);
    const welcomeVisible = await desktop.evaluate(() => !!document.querySelector(".welcome"));
    console.log("[debug] messages:", msgCount, "welcome visible:", welcomeVisible);
    await desktop.screenshot({ path: path.join(SCREENSHOTS, `${label}_chat.png`), fullPage: false });
  }

  // Wide mode (editor tab width ~800px)
  const wide = await browser.newPage({ viewport: { width: 800, height: 900 } });
  await wide.goto(`http://localhost:${PORT}`, { waitUntil: "networkidle" });
  await wide.waitForTimeout(800);
  // Trigger a chat
  const wideTA = wide.locator("textarea");
  if (await wideTA.count()) {
    await wideTA.click();
    await wide.keyboard.type("SK하이닉스 분석", { delay: 30 });
    await wide.waitForTimeout(200);
    await wide.keyboard.press("Enter");
    await wide.waitForTimeout(3500);
    await wide.screenshot({ path: path.join(SCREENSHOTS, `${label}_wide.png`), fullPage: false });
  }

  await browser.close();
  console.log(`Screenshots saved to ${SCREENSHOTS}/${label}_*.png`);
}

run().catch((e) => { console.error(e); process.exit(1); });
