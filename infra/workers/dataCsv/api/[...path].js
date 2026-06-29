// Vercel 무료(Hobby) 서버리스 함수 어댑터 — 같은 worker.js(Web fetch 핸들러)를 node (req,res) 위에 얹는다.
// CF Workers 는 128MB 라 큰 파일(fred 210MB·panel 927MB) 불가지만, Vercel Hobby 함수는 메모리 1024MB·
// maxDuration 60s(무료)라 **전 카탈로그가 $0 로 라이브**. 같은 핸들러 — 호스트만 다르다.
//
// vercel.json 이 /v1/* 를 이 함수로 rewrite(/api/v1/* 로 도착) → 원 경로 복원해 worker.fetch 에 넘긴다.
// env(MAX_DECODE_BYTES 등)는 Vercel 프로젝트 환경변수로 주입(미설정 시 worker 기본값=1GB 프로필).
import worker from '../worker.js';

export default async function handler(req, res) {
	try {
		const path = (req.url || '/').replace(/^\/api/, ''); // /api/v1/... → /v1/...
		const request = new Request(`https://${req.headers.host || 'data.local'}${path}`, {
			method: req.method,
			headers: req.headers
		});
		const resp = await worker.fetch(request, process.env, { waitUntil() {} });
		res.statusCode = resp.status;
		for (const [k, v] of resp.headers) res.setHeader(k, v);
		const ab = await resp.arrayBuffer();
		res.end(Buffer.from(ab));
	} catch (e) {
		res.statusCode = 500;
		res.setHeader('Content-Type', 'application/json; charset=utf-8');
		res.end(JSON.stringify({ error: 'function threw', detail: String((e && e.stack) || e) }));
	}
}
