// 드로잉 영속 · localStorage 회사별 1키. klinecharts overlay 는 points(timestamp,value) 사전 채움
// 시 생성 즉시 FINISHED 라 복원 = createOverlay 1호출. 상한 40개(초과 시 오래된 것부터 탈락).
const browser = typeof window !== 'undefined'; // $app/environment 결합 제거 (4a-3)

export interface SavedDraw {
	name: string;
	points: { timestamp?: number; value?: number }[];
	text?: string; // TEXTNOTE 전용 · extendData 문자열
}

const KEY = (code: string) => `dlTerm.draw.${code}`;
const CAP = 40;

/** 회사별 저장 드로잉 로드 · 손상·비배열은 빈 배열로 무해 처리. */
export function loadDraws(code: string): SavedDraw[] {
	if (!browser || !code) return [];
	try {
		const raw = localStorage.getItem(KEY(code));
		const arr: unknown = raw ? JSON.parse(raw) : [];
		if (!Array.isArray(arr)) return [];
		return arr.filter((d): d is SavedDraw => !!d && typeof (d as SavedDraw).name === 'string' && Array.isArray((d as SavedDraw).points));
	} catch {
		return [];
	}
}

/** 회사별 드로잉 저장 · 빈 목록은 키 제거(쓰레기 키 방지), quota 초과는 무해 무시. */
export function saveDraws(code: string, draws: SavedDraw[]): void {
	if (!browser || !code) return;
	try {
		if (!draws.length) localStorage.removeItem(KEY(code));
		else localStorage.setItem(KEY(code), JSON.stringify(draws.slice(-CAP)));
	} catch {
		/* quota · 무해 */
	}
}
