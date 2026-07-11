import { useEffect, useRef, useState } from "react";
import { fetchCategories, fetchTextes } from "../api";
import { TextesParAnneeChart } from "../components/charts";
import { Alert, Badge, Eyebrow, Loading, ResultCount } from "../components/ui";
import type { Categories, TextesResponse } from "../types";

const ANNEE_MIN_DEFAUT = 1990;

function TexteCard({ titre, categorie, annee, synthese }: {
  titre: string;
  categorie: string;
  annee: number | null;
  synthese: string | null;
}) {
  const extrait = synthese ? synthese.slice(0, 180) + (synthese.length > 180 ? "…" : "") : "";
  return (
    <div className="card">
      <Badge>{categorie}</Badge>
      {annee !== null && <Badge light>{annee}</Badge>}
      <h4>{titre}</h4>
      <p className="muted">{extrait}</p>
    </div>
  );
}

export default function Textes() {
  const [query, setQuery] = useState("");
  const [cats, setCats] = useState<string[]>([]);
  const [anneeMin, setAnneeMin] = useState(ANNEE_MIN_DEFAUT);
  const [categories, setCategories] = useState<Categories>({});
  const [data, setData] = useState<TextesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounce = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => setCategories({}));
  }, []);

  useEffect(() => {
    clearTimeout(debounce.current);
    const q = query.trim();
    if (!q) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }
    debounce.current = setTimeout(() => {
      setLoading(true);
      setError(null);
      fetchTextes(q, cats, anneeMin)
        .then(setData)
        .catch((e: Error) => {
          setData(null);
          setError(e.message);
        })
        .finally(() => setLoading(false));
    }, 400);
    return () => clearTimeout(debounce.current);
  }, [query, cats, anneeMin]);

  const toggleCat = (key: string) =>
    setCats((prev) => (prev.includes(key) ? prev.filter((c) => c !== key) : [...prev, key]));

  const reset = () => {
    setQuery("");
    setCats([]);
    setAnneeMin(ANNEE_MIN_DEFAUT);
  };

  return (
    <>
      <Eyebrow>Recherche</Eyebrow>
      <div className="filters">
        <label className="field field--grow">
          Mots-clés
          <input
            className="input"
            type="search"
            placeholder="ex : industrie automobile, décarbonation"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <label className="field">
          Année min.
          <input
            className="input"
            type="number"
            min={ANNEE_MIN_DEFAUT}
            max={2030}
            value={anneeMin}
            onChange={(e) => setAnneeMin(Number(e.target.value) || ANNEE_MIN_DEFAUT)}
          />
        </label>
        <button type="button" className="btn btn--secondary" onClick={reset}>
          Réinitialiser
        </button>
      </div>

      {Object.keys(categories).length > 0 && (
        <div style={{ marginBottom: "var(--space-lg)" }} role="group" aria-label="Filtrer par catégorie">
          {Object.entries(categories).map(([key, label]) => {
            const active = cats.includes(key);
            return (
              <button
                key={key}
                type="button"
                className={`btn ${active ? "" : "btn--secondary"}`}
                style={{ marginRight: "0.5rem", marginBottom: "0.5rem", fontSize: "0.8rem", padding: "0.35rem 0.9rem" }}
                aria-pressed={active}
                onClick={() => toggleCat(key)}
              >
                {label}
              </button>
            );
          })}
        </div>
      )}

      {loading && <Loading label="Recherche en cours…" />}
      {error && <Alert kind="error">{error}</Alert>}
      {data !== null && !loading && !error && data.count === 0 && (
        <Alert kind="warning">Aucun texte trouvé.</Alert>
      )}

      {data !== null && data.count > 0 && !loading && (
        <>
          <ResultCount n={data.count} singulier="texte trouvé" pluriel="textes trouvés" />
          <TextesParAnneeChart parAnnee={data.par_annee} />
          <div className="grid-3">
            {data.results.map((t) => (
              <TexteCard
                key={t.doc_id}
                titre={t.title}
                categorie={t.category_label}
                annee={t.annee}
                synthese={t.article_synthesis}
              />
            ))}
          </div>
        </>
      )}
    </>
  );
}
