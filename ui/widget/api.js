/**
 * DartLab Embed — 경량 fetch 클라이언트.
 * 외부 의존성 없음. fetch + JSON only.
 */

async function _get(url, token) {
  const headers = { Accept: "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(url, {
    headers,
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchCompany(baseUrl, code, token) {
  return _get(`${baseUrl}/api/company/${code}`, token);
}

export async function fetchInsights(baseUrl, code, token) {
  return _get(`${baseUrl}/api/company/${code}/insights`, token);
}
