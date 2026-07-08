// 개별 노트북 에디터 = 브라우저 전용(pyodide 워커 + CodeMirror + IndexedDB).
// 사용자 노트북 id 는 런타임 uuid 라 prerender 불가 → SPA 셸(fallback)이 클라에서 id 로 로드.
export const ssr = false;
export const prerender = false;
