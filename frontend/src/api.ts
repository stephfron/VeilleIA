import type { Activite, Categories, ParlementairesResponse, TextesResponse } from "./types";

/** Client HTTP minimal — même origine (proxy Vite en dev, FastAPI statique en prod). */

async function get<T>(path: string, params: Record<string, string | string[] | undefined>): Promise<T> {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) continue;
    if (Array.isArray(value)) {
      value.forEach((v) => search.append(key, v));
    } else {
      search.set(key, value);
    }
  }
  const qs = search.toString();
  const resp = await fetch(qs ? `${path}?${qs}` : path);
  if (!resp.ok) {
    const body = await resp.json().catch(() => null);
    throw new Error(body?.detail ?? `Erreur ${resp.status}`);
  }
  return resp.json() as Promise<T>;
}

export function fetchParlementaires(q: string, chambre?: string): Promise<ParlementairesResponse> {
  return get<ParlementairesResponse>("/api/parlementaires", { q, chambre });
}

export function fetchTextes(
  q: string,
  categories: string[],
  anneeMin?: number,
): Promise<TextesResponse> {
  return get<TextesResponse>("/api/textes", {
    q,
    categories: categories.length ? categories : undefined,
    annee_min: anneeMin !== undefined && anneeMin > 1990 ? String(anneeMin) : undefined,
  });
}

export function fetchCategories(): Promise<Categories> {
  return get<Categories>("/api/categories", {});
}

export function fetchActivite(nom: string, prenom: string, chambre: string): Promise<Activite> {
  return get<Activite>("/api/activite", { nom, prenom, chambre });
}
