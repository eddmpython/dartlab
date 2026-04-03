/**
 * Playwright 스크린샷 — UI 변경 전/후 시각 비교용
 * Usage: node tests/e2e/screenshot.mjs [label]
 * Example: node tests/e2e/screenshot.mjs before-timeline
 */
import { chromium } from "playwright";
import { mkdirSync } from "fs";

const label = process.argv[2] || "snap";
mkdirSync("screenshots", { recursive: true });

// 더미 대화 데이터 — 타임라인/메시지 렌더링 확인용
const MOCK_CONVERSATION = {
	conversations: [{
		id: "test1",
		title: "삼성전자 분석",
		createdAt: Date.now(),
		updatedAt: Date.now(),
		messages: [
			{ role: "user", text: "삼성전자 재무 건전성을 분석해줘" },
			{
				role: "assistant",
				text: "## 삼성전자 재무 건전성 분석\n\n삼성전자의 최근 재무 데이터를 기반으로 분석했습니다.\n\n### 핵심 지표\n\n| 지표 | 2023 | 2024 | 변화 |\n|------|------|------|------|\n| 부채비율 | 32.1% | 29.8% | ▼ |\n| 유동비율 | 258% | 271% | ▲ |\n| 이자보상배율 | 12.3x | 15.1x | ▲ |\n| 순현금 | 89.2조 | 102.3조 | ▲ |\n\n**결론**: 삼성전자는 순현금 보유 기업으로 재무 안정성이 매우 높습니다. 부채비율이 지속 하락하고 유동비율이 개선되고 있어 단기 유동성 위험도 낮습니다.",
				meta: { company: "삼성전자", stockCode: "005930", includedModules: ["재무제표", "비율분석", "안정성"] },
				snapshot: {
					items: [
						{ label: "수익성", value: "B+", status: "good" },
						{ label: "안정성", value: "A", status: "good" },
						{ label: "성장성", value: "C+", status: "caution" },
						{ label: "현금흐름", value: "A-", status: "good" },
					],
				},
				toolEvents: [
					{ type: "call", name: "companyFinancials", arguments: { stockCode: "005930", years: "2021-2024" } },
					{ type: "result", name: "companyFinancials", result: "| 항목 | 2022 | 2023 | 2024 |\n|------|------|------|------|\n| 매출액 | 302조 | 259조 | 301조 |\n| 영업이익 | 43.4조 | 6.6조 | 32.7조 |" },
					{ type: "call", name: "companyRatios", arguments: { stockCode: "005930" } },
					{ type: "result", name: "companyRatios", result: "비율 분석 완료: ROE 8.2%, PER 12.4x, PBR 1.1x" },
				],
				codeRounds: [
					{ round: 1, maxRounds: 3, status: "done", code: "c = dartlab.Company('005930')\nr = c.analysis('financial', '안정성')\nprint(r)", result: "| 지표 | 2022 | 2023 | 2024 |\n|------|------|------|------|\n| 부채비율 | 35.2% | 32.1% | 29.8% |\n| 유동비율 | 245% | 258% | 271% |\n| 이자보상배율 | 8.5x | 12.3x | 15.1x |" },
				],
			},
			{ role: "user", text: "현금흐름도 같이 점검해줘" },
			{
				role: "assistant",
				text: "### 현금흐름 분석\n\n영업활동 현금흐름이 순이익을 초과하여 이익의 질이 높습니다.\n\n- **영업CF**: 48.2조 (순이익 대비 146%)\n- **FCF**: 21.3조\n- **CCC**: 42일 (전년 대비 3일 개선)\n\n현금 전환 효율이 우수하며, 반도체 사이클 회복에 따라 향후 더 개선될 여지가 있습니다.",
				meta: { company: "삼성전자", stockCode: "005930" },
			},
		],
	}],
	activeId: "test1",
};

const browser = await chromium.launch();

async function takeScreenshot(viewport, suffix) {
	const page = await browser.newPage({ viewport });
	// localStorage에 대화 데이터 주입
	await page.goto("http://localhost:5400", { waitUntil: "domcontentloaded", timeout: 20000 });
	await page.evaluate((data) => {
		localStorage.setItem("dartlab-conversations", JSON.stringify(data));
	}, MOCK_CONVERSATION);
	await page.reload({ waitUntil: "domcontentloaded", timeout: 20000 });
	await page.waitForTimeout(800);
	const path = `screenshots/${label}_${suffix}.png`;
	await page.screenshot({ path, fullPage: false });
	console.log(`✓ ${path}`);

	// EmptyState도 찍기 (대화 없는 상태)
	await page.evaluate(() => localStorage.removeItem("dartlab-conversations"));
	await page.reload({ waitUntil: "domcontentloaded", timeout: 20000 });
	await page.waitForTimeout(500);
	const emptyPath = `screenshots/${label}_${suffix}_empty.png`;
	await page.screenshot({ path: emptyPath, fullPage: false });
	console.log(`✓ ${emptyPath}`);

	await page.close();
}

await takeScreenshot({ width: 1280, height: 900 }, "desktop");
await takeScreenshot({ width: 375, height: 812 }, "mobile");

await browser.close();
console.log("Done.");
