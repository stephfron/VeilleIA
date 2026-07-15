import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchParlementaires } from "../api";
import { Eyebrow, Loading, Alert, ResultCount, FicheHeader } from "../components/ui";
import TopEmployeurs from "../components/TopEmployeurs";
import { TopNafChart } from "../components/charts";
import ActiviteLegislative from "../components/ActiviteLegislative";
import type { Fiche } from "../types";

/**
 * Page hub territorial — point d'entrée principal pour lobbyiste UIMM.
 * Affiche industrie locale + formations + élus du département.
 */
export default function TerritoireDetail() {
  const { codeDept } = useParams<{ codeDept: string }>();
  const [fiches, setFiches] = useState<Fiche[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!codeDept) {
      setError("Code département manquant");
      return;
    }
    setLoading(true);
    setError(null);
    // Recherche sans filtre (query vide) pour le département
    fetchParlementaires(codeDept)
      .then((r) => setFiches(r.results))
      .catch((e: Error) => {
        setError(e.message);
        setFiches([]);
      })
      .finally(() => setLoading(false));
  }, [codeDept]);

  if (!codeDept) {
    return <Alert kind="error">Code département manquant.</Alert>;
  }

  return (
    <>
      <Eyebrow>Territoire</Eyebrow>
      <h2>Département {codeDept}</h2>

      {loading && <Loading label="Chargement des données…" />}
      {error && <Alert kind="error">{error}</Alert>}

      {fiches.length > 0 && (
        <>
          <h3>Situation industrielle</h3>
          {/* Afficher industrie du premier résultat (tous du même département) */}
          {fiches[0].territoire.top_naf.length > 0 && (
            <TopNafChart data={fiches[0].territoire.top_naf} />
          )}
          <TopEmployeurs employeurs={fiches[0].territoire.top_employeurs ?? []} />

          {/* TODO: Phase 2 — Formations professionnelles ici */}

          <h3>Élus du département</h3>
          <ResultCount n={fiches.length} singulier="élu" />
          {fiches.map((fiche, i) => {
            const { parlementaire: parl } = fiche;
            return (
              <article key={`${parl.nom}-${parl.prenom}-${i}`}>
                <FicheHeader parlementaire={parl} />
                <ActiviteLegislative parlementaire={parl} />
                <hr className="divider" />
              </article>
            );
          })}
        </>
      )}

      {fiches.length === 0 && !loading && !error && (
        <Alert kind="warning">Aucun élu trouvé pour ce département.</Alert>
      )}
    </>
  );
}
