import { decode as decodeMsgpack } from "@msgpack/msgpack";

export const BASE = "";

export async function fetchPack(url) {
	const res = await fetch(url, {
		headers: { "Accept": "application/msgpack" },
	});
	if (!res.ok) throw new Error(`요청 실패: ${res.status}`);
	const ct = res.headers.get("content-type") || "";
	if (ct.includes("msgpack")) {
		const buf = await res.arrayBuffer();
		return decodeMsgpack(buf);
	}
	return res.json();
}
