import type { AwsUpdate, FilterParams, ListResponse } from "../types/update";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

export async function fetchUpdates(params: FilterParams): Promise<ListResponse> {
  const qs = new URLSearchParams();
  qs.set("page", String(params.page));
  qs.set("limit", String(params.limit));
  if (params.date_from) qs.set("date_from", params.date_from);
  if (params.date_to) qs.set("date_to", params.date_to);
  if (params.category) qs.set("category", params.category);
  if (params.q) qs.set("q", params.q);

  const res = await fetch(`${API_BASE}/updates?${qs.toString()}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<ListResponse>;
}

export async function fetchUpdateById(id: string): Promise<AwsUpdate> {
  const res = await fetch(`${API_BASE}/updates/${id}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<AwsUpdate>;
}

export async function fetchCategories(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/categories`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const data = await res.json() as { categories: string[] };
  return data.categories;
}
