const BASE_URL = "http://4.187.167.49:8000";

async function request(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export function fetchProducts() {
  return request("/products");
}

export function fetchExplanation(productId, branch) {
  return request(`/explain/${encodeURIComponent(productId)}/${encodeURIComponent(branch)}`);
}
