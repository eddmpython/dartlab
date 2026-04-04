export const BASE = "";

export async function fetchPack(url) {
	const res = await fetch(url);
	if (!res.ok) throw new Error(`요청 실패: ${res.status}`);
	return res.json();
}
