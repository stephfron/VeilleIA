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

export interface TopEmployeur {
  nom: string;
  commune: string | null;
  naf: string | null;
  effectifs_estimes: number;
}

export interface Territoire {
  nb_etablissements_industriels: number;
  effectifs_estimes: number;
  top_naf: TopNaf[];
  top_employeurs: TopEmployeur[];
}

export interface Activite {
  disponible: boolean;
  groupe_sigle?: string | null;
  amendements_proposes?: number | null;
  amendements_signes?: number | null;
  amendements_adoptes?: number | null;
  questions_ecrites?: number | null;
  questions_orales?: number | null;
  rapports?: number | null;
  interventions?: number | null;
  semaines_presence?: number | null;
  source_url?: string | null;
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
  score: number;
}

export interface TextesResponse {
  count: number;
  results: Texte[];
  par_annee: Record<string, number>;
}

export type Categories = Record<string, string>;

export interface Formation {
  titre: string;
  url_descriptif: string;
  etablissement: string;
  type: string;
  localite: string;
}

export interface FormationsResponse {
  count: number;
  results: Formation[];
  disponible: boolean;
}

/* ------------------------------------------------------------------ CRM */

export type Statut = "a_contacter" | "contacte" | "allie" | "neutre" | "opposant";

export type Canal = "rendez_vous" | "mail" | "courrier" | "appel" | "evenement" | "autre";

export interface Interaction {
  id: number;
  elu_key: string;
  date: string;
  canal: Canal;
  objet: string;
  notes: string | null;
  rappel: string | null;
  cree_le: string;
}

export interface InteractionsResponse {
  count: number;
  statut: Statut;
  results: Interaction[];
}

export interface InteractionInput {
  nom: string;
  prenom: string;
  canal: Canal;
  objet: string;
  date_interaction?: string;
  notes?: string;
  rappel?: string;
}

/** Relance due : interaction jointe à la relation (nom/prénom/statut). */
export interface Rappel {
  id: number;
  elu_key: string;
  date: string;
  canal: Canal;
  objet: string;
  notes: string | null;
  rappel: string;
  nom: string;
  prenom: string;
  statut: Statut;
}

export interface RappelsResponse {
  count: number;
  results: Rappel[];
}

/* -------------------------------------------------------------- ciblage */

export interface DetailScore {
  industrie: number;
  activite: number;
  fraicheur: number;
  motif_fraicheur: string;
}

export interface Cible {
  parlementaire: Parlementaire;
  territoire: Territoire;
  statut: Statut;
  nb_interactions: number;
  dernier_contact: string | null;
  score: number;
  detail_score: DetailScore;
}

export interface CiblesResponse {
  count: number;
  results: Cible[];
}

/* -------------------------------------------------------------- dossier */

export interface TexteDossier {
  title: string;
  category_label: string;
  annee: number | null;
  article_synthesis: string | null;
  score: number;
}

/** Miroir de /api/dossier — l'activité y est le record brut (sans `disponible`). */
export interface Dossier {
  parlementaire: Parlementaire;
  territoire: Territoire;
  activite_legislative: Omit<Activite, "disponible"> | null;
  textes_pertinents: TexteDossier[];
  themes: string;
  synthese: string | null;
  synthese_status: string;
}

/* --------------------------------------------------------- Territoires Récents */

export interface RecentTerritory {
  codeDept: string;
  nomDept: string;
  nbEtablissements: number;
  dateVisite?: string;
}
