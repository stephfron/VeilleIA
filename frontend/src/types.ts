/** Types miroirs des réponses de l'API FastAPI (api/main.py). */

export interface TopNaf {
  naf: string;
  nb: number;
}

export interface Parlementaire {
  nom: string;
  prenom: string;
  chambre: "Sénat" | "Assemblée nationale";
  sexe: string | null;
  code_dept: string | null;
  libelle_dept: string | null;
  date_debut_mandat: string | null;
  libelle_csp: string | null;
  circonscription?: string | null;
  code_circo?: string | null;
}

export interface Territoire {
  nb_etablissements_industriels: number;
  effectifs_estimes: number;
  top_naf: TopNaf[];
}

export interface Fiche {
  parlementaire: Parlementaire;
  territoire: Territoire;
}

export interface ParlementairesResponse {
  count: number;
  results: Fiche[];
}

export interface Texte {
  title: string;
  category_label: string;
  annee: number | null;
  article_title: string | null;
  article_synthesis: string | null;
  chunk_text: string | null;
  doc_id: string;
}

export interface TextesResponse {
  count: number;
  results: Texte[];
  par_annee: Record<string, number>;
}

export type Categories = Record<string, string>;
