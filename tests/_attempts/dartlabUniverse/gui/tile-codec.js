const MAGIC = [68, 85, 71, 80, 85, 49, 0, 0];

function hex(bytes) {
	return [...bytes].map((value) => value.toString(16).padStart(2, '0')).join('');
}

async function request(path, token) {
	const response = await fetch(path, {
		cache: 'no-store',
		headers: { 'X-DartLab-Universe-Token': token }
	});
	if (!response.ok) throw new Error(`runtime 요청 실패 (${response.status})`);
	return response;
}

export async function loadManifest(token) {
	const response = await request('/api/manifest', token);
	const manifest = await response.json();
	if (manifest.schemaVersion !== 'du-gpu-manifest-v1') throw new Error('지원하지 않는 manifest');
	if (manifest.transport?.persistenceMode !== 'EPHEMERAL') throw new Error('영속 tile은 허용되지 않음');
	if (manifest.meaningPreservation !== 1) throw new Error('의미 보존이 완전하지 않음');
	return manifest;
}

export async function loadTile(tileId, token, expectedProjectionDigest) {
	const response = await request(`/api/tile/${encodeURIComponent(tileId)}`, token);
	const buffer = await response.arrayBuffer();
	const bytes = new Uint8Array(buffer);
	if (bytes.length < 12 || MAGIC.some((value, index) => bytes[index] !== value)) {
		throw new Error('GPU tile magic 불일치');
	}
	const view = new DataView(buffer);
	const headerLength = view.getUint32(8, true);
	const recordOffset = 12 + headerLength;
	if (recordOffset > bytes.length) throw new Error('GPU tile header 범위 오류');
	const header = JSON.parse(new TextDecoder().decode(bytes.subarray(12, recordOffset)));
	if (header.schemaVersion !== 'du-gpu-tile-v1') throw new Error('GPU tile schema 불일치');
	if (header.projectionDigest !== expectedProjectionDigest) throw new Error('stale GPU tile 거부');
	if (header.nodeStride !== 28 || header.edgeStride !== 32) throw new Error('GPU record stride 불일치');
	if (recordOffset + header.nodeBytes + header.edgeBytes !== bytes.length) {
		throw new Error('GPU tile byte cardinality 불일치');
	}
	const digest = hex(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes.subarray(recordOffset))));
	if (digest !== header.recordDigest) throw new Error('GPU tile record digest 불일치');

	const nodes = [];
	for (let index = 0; index < header.nodeCount; index += 1) {
		const offset = recordOffset + index * header.nodeStride;
		nodes.push({
			position: [view.getFloat32(offset, true), view.getFloat32(offset + 4, true), view.getFloat32(offset + 8, true)],
			size: view.getFloat32(offset + 12, true),
			pickId: view.getUint32(offset + 16, true),
			styleIndex: view.getUint16(offset + 20, true),
			flags: view.getUint16(offset + 22, true),
			importance: view.getFloat32(offset + 24, true),
			metadata: header.nodeMetadata[index]
		});
	}

	const edges = [];
	const edgeBase = recordOffset + header.nodeBytes;
	for (let index = 0; index < header.edgeCount; index += 1) {
		const offset = edgeBase + index * header.edgeStride;
		edges.push({
			from: [view.getFloat32(offset, true), view.getFloat32(offset + 4, true), view.getFloat32(offset + 8, true)],
			to: [view.getFloat32(offset + 12, true), view.getFloat32(offset + 16, true), view.getFloat32(offset + 20, true)],
			weight: view.getFloat32(offset + 24, true),
			styleIndex: view.getUint16(offset + 28, true),
			flags: view.getUint16(offset + 30, true)
		});
	}
	return { header, nodes, edges };
}
