export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000";

export async function getOverview() {
  const r = await fetch(`${API_URL}/api/overview`, { next: { revalidate: 60 } });
  if (!r.ok) throw new Error("overview fetch failed");
  return r.json();
}
export async function getSizes() {
  const r = await fetch(`${API_URL}/api/sizes`, { next: { revalidate: 60 } });
  return r.json();
}
export async function getUmap() {
  const r = await fetch(`${API_URL}/api/umap2d`, { next: { revalidate: 60 } });
  return r.json();
}
export async function predict(formData: FormData) {
  const r = await fetch(`${API_URL}/api/predict`, { method: "POST", body: formData });
  const j = await r.json();
  if (!r.ok) throw j;
  return j;
}
