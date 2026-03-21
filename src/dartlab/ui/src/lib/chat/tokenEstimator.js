/**
 * 토큰 수 추정 + 포맷 유틸.
 * 한국어 1.5tok/char, 영문 0.29tok/char 기준 근사.
 */

export function estimateTokens(text) {
	if (!text) return 0;
	const korean = (text.match(/[\uac00-\ud7af]/g) || []).length;
	const rest = text.length - korean;
	return Math.round(korean * 1.5 + rest / 3.5);
}

export function formatTokens(n) {
	if (n >= 1000) return (n / 1000).toFixed(1) + "k";
	return String(n);
}
