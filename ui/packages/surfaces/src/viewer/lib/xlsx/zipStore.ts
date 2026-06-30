// STORE(method 0, 무압축) ZIP 작성기 · 라이브러리 0. .xlsx = ZIP 컨테이너라 이게 핵심 위험면이다.
// local file header + central directory + EOCD 바이트 레이아웃을 정확히(little-endian, CRC32, 크기 필드).
// 압축 0 이라 compressedSize == uncompressedSize, method == 0. UTF-8 파일명(general-purpose bit 11 set).
//
// 참조: PKWARE APPNOTE · Local file header(0x04034b50) / Central directory(0x02014b50) / EOCD(0x06054b50).

// ── CRC32 (IEEE 802.3, 표준 ZIP 다항식 0xEDB88320) · 256 엔트리 테이블 ──
const CRC_TABLE: Uint32Array = (() => {
	const table = new Uint32Array(256);
	for (let n = 0; n < 256; n += 1) {
		let c = n;
		for (let k = 0; k < 8; k += 1) {
			c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
		}
		table[n] = c >>> 0;
	}
	return table;
})();

/** bytes 의 CRC32 (unsigned 32-bit). */
export function crc32(bytes: Uint8Array): number {
	let crc = 0xffffffff;
	for (let i = 0; i < bytes.length; i += 1) {
		crc = CRC_TABLE[(crc ^ bytes[i]) & 0xff] ^ (crc >>> 8);
	}
	return (crc ^ 0xffffffff) >>> 0;
}

interface ZipEntry {
	nameBytes: Uint8Array;
	data: Uint8Array;
	crc: number;
	offset: number; // local header 시작 오프셋 (central directory 가 가리킴)
}

const TE = new TextEncoder();

export class ZipStore {
	private entries: ZipEntry[] = [];
	private parts: Uint8Array[] = [];
	private offset = 0;

	private push(bytes: Uint8Array): void {
		this.parts.push(bytes);
		this.offset += bytes.length;
	}

	/** 한 항목 추가 · STORE(무압축) local file header + 데이터를 즉시 쓴다. */
	addEntry(name: string, data: Uint8Array): void {
		const nameBytes = TE.encode(name);
		const crc = crc32(data);
		const localOffset = this.offset;

		const header = new Uint8Array(30 + nameBytes.length);
		const dv = new DataView(header.buffer);
		dv.setUint32(0, 0x04034b50, true); // local file header signature
		dv.setUint16(4, 20, true); // version needed to extract (2.0)
		dv.setUint16(6, 0x0800, true); // general purpose bit 11 = UTF-8 filename
		dv.setUint16(8, 0, true); // compression method = 0 (STORE)
		dv.setUint16(10, 0, true); // last mod file time
		dv.setUint16(12, 0x21, true); // last mod file date (1980-01-01)
		dv.setUint32(14, crc, true); // crc-32
		dv.setUint32(18, data.length, true); // compressed size (== uncompressed, STORE)
		dv.setUint32(22, data.length, true); // uncompressed size
		dv.setUint16(26, nameBytes.length, true); // file name length
		dv.setUint16(28, 0, true); // extra field length
		header.set(nameBytes, 30);

		this.push(header);
		this.push(data);
		this.entries.push({ nameBytes, data, crc, offset: localOffset });
	}

	/** central directory + EOCD 를 추가하고 전체 ZIP 바이트를 하나로 합쳐 반환. */
	finalize(): Uint8Array {
		const cdStart = this.offset;
		const cdParts: Uint8Array[] = [];
		let cdSize = 0;

		for (const e of this.entries) {
			const rec = new Uint8Array(46 + e.nameBytes.length);
			const dv = new DataView(rec.buffer);
			dv.setUint32(0, 0x02014b50, true); // central file header signature
			dv.setUint16(4, 20, true); // version made by
			dv.setUint16(6, 20, true); // version needed to extract
			dv.setUint16(8, 0x0800, true); // general purpose bit 11 = UTF-8
			dv.setUint16(10, 0, true); // compression method = 0 (STORE)
			dv.setUint16(12, 0, true); // last mod file time
			dv.setUint16(14, 0x21, true); // last mod file date
			dv.setUint32(16, e.crc, true); // crc-32
			dv.setUint32(20, e.data.length, true); // compressed size
			dv.setUint32(24, e.data.length, true); // uncompressed size
			dv.setUint16(28, e.nameBytes.length, true); // file name length
			dv.setUint16(30, 0, true); // extra field length
			dv.setUint16(32, 0, true); // file comment length
			dv.setUint16(34, 0, true); // disk number start
			dv.setUint16(36, 0, true); // internal file attributes
			dv.setUint32(38, 0, true); // external file attributes
			dv.setUint32(42, e.offset, true); // relative offset of local header
			rec.set(e.nameBytes, 46);
			cdParts.push(rec);
			cdSize += rec.length;
		}

		const eocd = new Uint8Array(22);
		const edv = new DataView(eocd.buffer);
		edv.setUint32(0, 0x06054b50, true); // EOCD signature
		edv.setUint16(4, 0, true); // number of this disk
		edv.setUint16(6, 0, true); // disk where central directory starts
		edv.setUint16(8, this.entries.length, true); // central dir records on this disk
		edv.setUint16(10, this.entries.length, true); // total central dir records
		edv.setUint32(12, cdSize, true); // size of central directory
		edv.setUint32(16, cdStart, true); // offset of central directory start
		edv.setUint16(20, 0, true); // comment length

		const all = [...this.parts, ...cdParts, eocd];
		let total = 0;
		for (const p of all) total += p.length;
		const out = new Uint8Array(total);
		let pos = 0;
		for (const p of all) {
			out.set(p, pos);
			pos += p.length;
		}
		return out;
	}
}
