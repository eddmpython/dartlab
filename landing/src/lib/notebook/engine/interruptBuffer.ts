/**
 * COOP/COEP가 없는 일반 페이지에는 SharedArrayBuffer 전역 자체가 없다.
 * 기본 Python 머신은 그 환경에서도 떠야 하므로 인터럽트 능력만 안전하게 내린다.
 */
export function isSharedInterruptBuffer(
	buffer: Uint8Array | null | undefined
): buffer is Uint8Array<SharedArrayBuffer> {
	return (
		typeof globalThis.SharedArrayBuffer === 'function' &&
		buffer?.buffer instanceof globalThis.SharedArrayBuffer
	);
}
