import type {
  Activite,
  Categories,
  CiblesResponse,
  Dossier,
  InteractionInput,
  InteractionsResponse,
  ParlementairesResponse,
  RappelsResponse,
  Statut,
  TextesResponse,
} from "./types";

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

/** Requêtes mutantes (POST/PUT/DELETE) — corps JSON, erreurs via `detail`. */
async function send<T>(method: "POST" | "PUT" | "DELETE", path: string, body?: object): Promise<T> {
  const resp = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const data = await resp.json().catch(() => null);
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail : `Erreur ${resp.status}`);
  }
  return resp.json() as Promise<T>;
}

export function fetchCibles(
  q: string,
  chambre?: string,
  avecActivite?: boolean,
): Promise<CiblesResponse> {
  return get<CiblesResponse>("/api/cibles", {
    q,
    chambre,
    avec_activite: avecActivite ? "true" : undefined,
  });
}

export function fetchDossier(nom: string, prenom: string, themes?: string): Promise<Dossier> {
  return get<Dossier>("/api/dossier", { nom, prenom, themes: themes || undefined });
}

export function fetchInteractions(nom: string, prenom: string): Promise<InteractionsResponse> {
  return get<InteractionsResponse>("/api/interactions", { nom, prenom });
}

export function createInteraction(input: InteractionInput): Promise<{ id: number; elu_key: string }> {
  return send("POST", "/api/interactions", input);
}

export function deleteInteraction(id: number): Promise<{ deleted: boolean }> {
  return send("DELETE", `/api/interactions/${id}`);
}

export function setStatut(nom: string, prenom: string, statut: Statut): Promise<{ elu_key: string; statut: Statut }> {
  return send("PUT", "/api/statut", { nom, prenom, statut });
}

export function fetchRappels(): Promise<RappelsResponse> {
  return get<RappelsResponse>("/api/rappels", {});
}
