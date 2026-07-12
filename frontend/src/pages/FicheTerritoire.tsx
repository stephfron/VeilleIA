import { useEffect, useRef, useState } from "react";
import { fetchParlementaires } from "../api";
import ActiviteLegislative from "../components/ActiviteLegislative";
import TopEmployeurs from "../components/TopEmployeurs";
import { TopNafChart } from "../components/charts";
import { Alert, Eyebrow, FicheHeader, Loading, ResultCount, StatCard } from "../components/ui";
import type { Fiche } from "../types";

const CHAMBRES = ["Les deux", "Sénat", "Assemblée nationale"] as const;

const fmtEffectifs = (n: number) => n.toLocaleString("fr-FR");

export default function FicheTerritoire() {
  const [query, setQuery] = useState("");
  const [chambre, setChambre] = useState<(typeof CHAMBRES)[number]>("Les deux");
  const [fiches, setFiches] = useState<Fiche[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounce = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    clearTimeout(debounce.current);
    const q = query.trim();
    if (!q) {
      setFiches(null);
      setError(null);
      setLoading(false);
      return;
    }
    debounce.current = setTimeout(() => {
      setLoading(true);
      setError(null);
      fetchParlementaires(q, chambre === "Les deux" ? undefined : chambre)
        .then((r) => setFiches(r.results))
        .catch((e: Error) => {
          setFiches(null);
          setError(e.message);
        })
        .finally(() => setLoading(false));
    }, 400);
    return () => clearTimeout(debounce.current);
  }, [query, chambre]);

  const reset = () => {
    setQuery("");
    setChambre("Les deux");
  };

  return (
    <>
      <Eyebrow>Recherche</Eyebrow>
      <div className="filters">
        <label className="field field--grow">
          Nom, département ou code département
          <input
            className="input"
            type="search"
            placeholder="ex : Dupont, 69, Rhône"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <label className="field">
          Chambre
          <select
            className="select"
            value={chambre}
            onChange={(e) => setChambre(e.target.value as (typeof CHAMBRES)[number])}
          >
            {CHAMBRES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <button type="button" className="btn btn--secondary" onClick={reset}>
          Réinitialiser
        </button>
      </div>

      {loading && <Loading label="Recherche en cours…" />}
      {error && <Alert kind="error">{error}</Alert>}
      {fiches !== null && !loading && !error && fiches.length === 0 && (
        <Alert kind="warning">Aucun résultat pour cette recherche.</Alert>
      )}

      {fiches !== null && fiches.length > 0 && !loading && (
        <>
          <ResultCount n={fiches.length} singulier="résultat" />
          {fiches.map((fiche, i) => {
            const { parlementaire: parl, territoire: terr } = fiche;
            return (
              <article key={`${parl.nom}-${parl.prenom}-${parl.code_dept}-${i}`}>
                <FicheHeader parlementaire={parl} />
                <div className="grid-2">
                  <StatCard value={terr.nb_etablissements_industriels} label="Établissements industriels" />
                  <StatCard value={fmtEffectifs(terr.effectifs_estimes)} label="Effectifs estimés" />
                </div>
                {terr.top_naf.length > 0 && <TopNafChart data={terr.top_naf} />}
                <TopEmployeurs employeurs={terr.top_employeurs ?? []} />
                <ActiviteLegislative parlementaire={parl} />
                <hr className="divider" />
              </article>
            );
          })}
        </>
      )}
    </>
  );
}
