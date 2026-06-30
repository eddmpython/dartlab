// 로컬 개발/증명 서버 — worker.js 핸들러를 node:http 위에서 그대로 구동.
// `npm run dev` → http://localhost:8787. CF/서버리스 배포 없이 `=IMPORTDATA` 가 받을 응답을
// curl 로 검증한다(같은 핸들러, 호스트만 node = 메모리 충분 → 전 카탈로그 디코드 가능).
import http from 'node:http';
import worker from './dist/worker.mjs'; // npm run dev 가 esbuild 로 financeSource(.ts) 포함 번들 생성

const port = Number(process.env.PORT) || 8787;
const env = { ...process.env }; // MAX_DECODE_BYTES 등 env 주입 가능 (미설정 시 worker 기본값)

const server = http.createServer(async (nreq, nres) => {
	try {
		const reqUrl = `http://${nreq.headers.host || `localhost:${port}`}${nreq.url}`;
		const req = new Request(reqUrl, { method: nreq.method, headers: nreq.headers });
		const ctx = { waitUntil() {} };
		const resp = await worker.fetch(req, env, ctx);
		nres.statusCode = resp.status;
		for (const [k, v] of resp.headers) nres.setHeader(k, v);
		const ab = await resp.arrayBuffer();
		nres.end(Buffer.from(ab));
	} catch (e) {
		nres.statusCode = 500;
		nres.setHeader('Content-Type', 'application/json; charset=utf-8');
		nres.end(JSON.stringify({ error: 'worker threw', detail: String((e && e.stack) || e) }));
	}
});

server.listen(port, () => console.log(`dataCsv dev API → http://localhost:${port}/v1/`));
