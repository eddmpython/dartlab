function normalizeMissing(missing) {
	if (!Array.isArray(missing)) return [];
	return missing.filter(Boolean).map(String);
}

export function summarizeDataReady(dataReady) {
	if (!dataReady) return null;

	if (typeof dataReady === "string") {
		const summary = dataReady.replace(/^- 데이터 상태:\s*/, "").trim();
		const missingMatch = summary.match(/누락=([^.;]+)/);
		const missing = missingMatch
			? missingMatch[1]
				.split(",")
				.map((item) => item.trim())
				.filter((item) => item && item !== "없음")
			: [];
		return {
			label: summary.includes("모두 준비") ? "데이터 준비 완료" : "일부 데이터 누락",
			summary,
			missing,
			allReady: missing.length === 0,
		};
	}

	const missing = normalizeMissing(dataReady.missing);
	const available = normalizeMissing(dataReady.available);
	const allReady = Boolean(dataReady.allReady);
	const summary = allReady
		? "docs, finance, report가 모두 준비되어 있습니다."
		: `준비됨: ${available.join(", ") || "없음"} / 누락: ${missing.join(", ") || "없음"}`;

	return {
		label: allReady ? "데이터 준비 완료" : "일부 데이터 누락",
		summary,
		missing,
		allReady,
	};
}
