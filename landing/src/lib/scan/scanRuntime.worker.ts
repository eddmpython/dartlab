// scan surface 승격(단계-8 Phase2) · financeLiteRuntime 은 surface 로 이동, 본 worker 는 라우트가 생성(URL 상대경로)
// 하므로 landing 잔류. worker 번들은 svelte 컴포넌트를 파싱 못 하므로 배럴(.svelte 재export) 대신
// 순수 TS runtime sub-export(@dartlab/ui-surfaces/scan/runtime)만 import 한다(단계-8 worker 회귀 가드).
import { loadFinanceLiteRuntime } from '@dartlab/ui-surfaces/scan/runtime';
import { loadJson, setStaticBase } from '@dartlab/ui-runtime/data/dartlabData';

type BootMessage = {
	type: 'boot';
	basePath: string;
};

type FinanceMessage = {
	type: 'finance5y';
};

type WorkerMessage = BootMessage | FinanceMessage;

type RuntimeContext = {
	basePath: string;
};

type PriceSnapshotFile = {
	builtAt?: string;
	data?: Record<string, PriceSnapshotItem>;
};

type PriceSnapshotItem = {
	currentPrice?: number | null;
	marketCap?: number | null;
	return1m?: number | null;
	return3m?: number | null;
	return1y?: number | null;
	volatility1y?: number | null;
	week52High?: number | null;
	week52Low?: number | null;
	volumeAvg30d?: number | null;
	foreignPct?: number | null;
	beta?: number | null;
	priceUpdated?: string | null;
};

type NodeRow = Record<string, unknown> & {
	id: string;
	industry?: string;
	industryName?: string;
	color?: string;
};

let context: RuntimeContext | null = null;

self.onmessage = (event: MessageEvent<WorkerMessage>) => {
	const msg = event.data;
	if (msg.type === 'boot') {
		context = { basePath: msg.basePath };
		setStaticBase(msg.basePath);
		void boot(context);
		return;
	}
	if (msg.type === 'finance5y') {
		void loadFinance5y();
	}
};

async function boot(ctx: RuntimeContext) {
	try {
		setStaticBase(ctx.basePath);
		const ecosystem = await loadJson<any>('map/ecosystem.json', { fetchFn: fetch, required: true });
		const nodes = ((ecosystem?.nodes ?? []) as NodeRow[]).map(normalizeNode);
		postMessage({ type: 'ecosystem', nodes, industries: buildIndustries(nodes) });

		const [prices, meta] = await Promise.all([
			loadJson<PriceSnapshotFile>('map/prices-snapshot.json', { fetchFn: fetch }),
			loadJson<any>('map/meta.json', { fetchFn: fetch })
		]);
		const mergedNodes = mergePriceSnapshot(nodes, prices);
		postMessage({
			type: 'sidecars',
			nodes: mergedNodes,
			meta,
			industries: buildIndustries(mergedNodes)
		});
	} catch (err) {
		postMessage({ type: 'error', error: err instanceof Error ? err.message : String(err) });
	}
}

async function loadFinance5y() {
	try {
		const ctx = context;
		if (!ctx) throw new Error('scan runtime context 없음');
		const result = await loadFinanceLiteRuntime(fetch);
		postMessage({ type: 'finance5y', rows: result.rows, years: result.years });
	} catch (err) {
		postMessage({ type: 'finance5y-error', error: err instanceof Error ? err.message : String(err) });
	}
}

function normalizeNode(node: NodeRow): NodeRow {
	return node;
}

function buildIndustries(nodes: NodeRow[]) {
	const groups = new Map<string, { id: string; name: string; color: string; count: number }>();
	for (const node of nodes) {
		const id = String(node.industry || node.market || 'KRX');
		const item = groups.get(id) ?? {
			id,
			name: String(node.industryName || id),
			color: String(node.color || '#94a3b8'),
			count: 0
		};
		item.count += 1;
		groups.set(id, item);
	}
	return Array.from(groups.values());
}

function mergePriceSnapshot(nodes: NodeRow[], snapshot: PriceSnapshotFile | null): NodeRow[] {
	const prices = snapshot?.data ?? {};
	if (Object.keys(prices).length === 0) return nodes;
	return nodes.map((node) => {
		const p = prices[node.id];
		if (!p) return node;
		return {
			...node,
			currentPrice: numberOrNull(p.currentPrice),
			marketCap: numberOrNull(p.marketCap) ?? node.marketCap ?? null,
			return1m: numberOrNull(p.return1m),
			return3m: numberOrNull(p.return3m),
			return1y: numberOrNull(p.return1y),
			volatility1y: numberOrNull(p.volatility1y),
			week52High: numberOrNull(p.week52High),
			week52Low: numberOrNull(p.week52Low),
			volumeAvg30d: numberOrNull(p.volumeAvg30d),
			foreignPct: numberOrNull(p.foreignPct),
			beta: numberOrNull(p.beta)
		};
	});
}

function numberOrNull(value: unknown): number | null {
	if (typeof value === 'number') return Number.isFinite(value) ? value : null;
	if (typeof value === 'bigint') {
		const n = Number(value);
		return Number.isFinite(n) ? n : null;
	}
	if (typeof value === 'string' && value.trim()) {
		const n = Number(value.replace(/,/g, ''));
		return Number.isFinite(n) ? n : null;
	}
	return null;
}
