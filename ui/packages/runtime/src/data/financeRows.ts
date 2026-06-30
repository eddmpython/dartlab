// 정량재무제표 표용 raw 행 · SSR 안전 subpath (`@dartlab/ui-runtime/data/financeRows`). landing +layout 가
// 메인 index 를 SSR 로 끌어오면(extensionless contracts re-export) Node ESM 해석 실패라, dartlabData 와
// 동일하게 좁은 subpath 로 노출한다. 차트 bundle 과 같은 rowsCache 공유(회사당 1회 다운로드).
export { loadFinanceRows, loadFinanceBundle } from '../adapters/public/sources/financeSource';
