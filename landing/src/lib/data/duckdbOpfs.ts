/**
 * OPFS (Origin Private File System) attach helper · DuckDB-WASM 1.27+.
 *
 * 첫 방문: parquet 다운 + SQL 결과를 `persisted.<table>` 로 영속화.
 * 재방문: `persisted.<table>` 즉시 SELECT → SQL 0 + parquet 다운 0.
 *
 * 미지원 브라우저 (iOS Safari 17.3↓, 일부 Firefox) 는 attach 실패 → fallback.
 *
 * Schema 버전 (`PRAGMA user_version`):
 *   - parquet 컬럼/스키마 변경 시 dartlab 측이 SCHEMA_VERSION bump.
 *   - 재방문 시 user_version 다르면 자동 DROP + rebuild.
 */

const OPFS_FILENAME = 'dartlab.duckdb';
export const OPFS_DB_ALIAS = 'persisted';
export const SCHEMA_VERSION = 1; // bump 시 모든 사용자 OPFS 자동 rebuild

/** OPFS 환경 지원 여부 (browser feature detection). */
export function isOpfsSupported(): boolean {
	if (typeof navigator === 'undefined') return false;
	if (!navigator.storage || typeof navigator.storage.getDirectory !== 'function') return false;
	if (typeof FileSystemFileHandle === 'undefined') return false;
	return true;
}

/** DuckDB instance 에 OPFS file 등록 + ATTACH AS persisted. 성공 시 true.
 *
 * @param db AsyncDuckDB instance (any 타입 · duckdb-wasm 의 export 가 dynamic)
 * @param conn AsyncDuckDBConnection
 * @param duckdbModule duckdb-wasm 모듈 (DuckDBDataProtocol enum 참조용)
 */
export async function attachOpfs(
	db: any,
	conn: any,
	duckdbModule: any
): Promise<{ ok: boolean; rebuilt: boolean; error?: string }> {
	if (!isOpfsSupported()) {
		return { ok: false, rebuilt: false, error: 'OPFS unsupported' };
	}
	try {
		const root = await navigator.storage.getDirectory();
		const fileHandle = await root.getFileHandle(OPFS_FILENAME, { create: true });

		// BROWSER_FSACCESS protocol · sync handle (worker 에서 효율적).
		const protocol =
			duckdbModule?.DuckDBDataProtocol?.BROWSER_FSACCESS ??
			(duckdbModule as any)?.DuckDBDataProtocol?.BROWSER_FSACCESS;
		if (protocol === undefined) {
			return { ok: false, rebuilt: false, error: 'DuckDBDataProtocol.BROWSER_FSACCESS not found' };
		}

		await db.registerFileHandle(OPFS_FILENAME, fileHandle, protocol, true);
		await conn.query(`ATTACH '${OPFS_FILENAME}' AS ${OPFS_DB_ALIAS} (READ_WRITE)`);

		// schema version 검사 + 자동 rebuild
		let rebuilt = false;
		try {
			const versionResult = await conn.query(`PRAGMA ${OPFS_DB_ALIAS}.user_version`);
			const rows = versionResult.toArray();
			const currentVersion = rows.length > 0 ? Number(rows[0].user_version ?? 0) : 0;
			if (currentVersion !== SCHEMA_VERSION) {
				console.info(
					`[opfs] schema version mismatch (got ${currentVersion}, expected ${SCHEMA_VERSION}) · rebuild`
				);
				await dropAllPersistedTables(conn);
				await conn.query(`PRAGMA ${OPFS_DB_ALIAS}.user_version=${SCHEMA_VERSION}`);
				rebuilt = true;
			}
		} catch (err) {
			console.warn('[opfs] user_version 검사 실패 · 안전하게 rebuild', err);
			await dropAllPersistedTables(conn);
			rebuilt = true;
		}

		console.info(`[opfs] ✅ attached (rebuilt=${rebuilt})`);
		return { ok: true, rebuilt };
	} catch (err) {
		const message = err instanceof Error ? err.message : String(err);
		console.warn('[opfs] attach 실패 · in-memory fallback', err);
		return { ok: false, rebuilt: false, error: message };
	}
}

/** persisted DB 의 모든 테이블 DROP. schema 변경 시 호출. */
async function dropAllPersistedTables(conn: any): Promise<void> {
	try {
		const result = await conn.query(`
			SELECT table_name FROM information_schema.tables
			WHERE table_schema = '${OPFS_DB_ALIAS}'
			  AND table_type = 'BASE TABLE'
		`);
		const rows = result.toArray();
		for (const r of rows) {
			const name = r.table_name;
			if (typeof name === 'string') {
				await conn.query(`DROP TABLE IF EXISTS ${OPFS_DB_ALIAS}."${name}"`);
			}
		}
	} catch (err) {
		console.warn('[opfs] DROP all 실패', err);
	}
}

/** persisted DB 에 특정 테이블이 있는지. */
export async function hasPersistedTable(conn: any, tableName: string): Promise<boolean> {
	try {
		const result = await conn.query(`
			SELECT COUNT(*) AS n FROM information_schema.tables
			WHERE table_schema = '${OPFS_DB_ALIAS}'
			  AND table_name = '${tableName}'
		`);
		const rows = result.toArray();
		const n = rows.length > 0 ? Number(rows[0].n ?? 0) : 0;
		return n > 0;
	} catch {
		return false;
	}
}

/** persisted DB 에 테이블 row count. 없으면 0. */
export async function persistedRowCount(conn: any, tableName: string): Promise<number> {
	try {
		const result = await conn.query(
			`SELECT COUNT(*) AS n FROM ${OPFS_DB_ALIAS}."${tableName}"`
		);
		const rows = result.toArray();
		return rows.length > 0 ? Number(rows[0].n ?? 0) : 0;
	} catch {
		return 0;
	}
}
