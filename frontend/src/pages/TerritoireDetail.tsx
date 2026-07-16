import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchParlementaires, fetchFormations } from "../api";
import { Eyebrow, Loading, Alert, ResultCount, FicheHeader } from "../components/ui";
import TopEmployeurs from "../components/TopEmployeurs";
import { TopNafChart } from "../components/charts";
import ActiviteLegislative from "../components/ActiviteLegislative";
import FormationCard from "../components/FormationCard";
import { useRecentTerritories } from "../hooks/useRecentTerritories";
import type { Fiche, Formation } from "../types";

/**
 * Page hub territorial — point d'entrée principal pour lobbyiste UIMM.
 * Affiche industrie locale + formations + élus du département.
 */
export default function TerritoireDetail() {
  const { codeDept } = useParams<{ codeDept: string }>();
  const [fiches, setFiches] = useState<Fiche[]>([]);
  const [formations, setFormations] = useState<Formation[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingFormations, setLoadingFormations] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { addTerritory } = useRecentTerritories();

  useEffect(() => {
    if (!codeDept) {
      setError("Code département manquant");
      return;
    }
    setLoading(true);
    setError(null);
    // Recherche sans filtre (query vide) pour le département
    fetchParlementaires(codeDept)
      .then((r) => {
        setFiches(r.results);
        // Enregistrer ce territoire dans les récents
        if (r.results.length > 0) {
          const firstFiche = r.results[0];
          const nomDept = firstFiche.parlementaire.libelle_dept || codeDept;
          const nbEtablissements = firstFiche.territoire.nb_etablissements_industriels;
          addTerritory(codeDept, nomDept, nbEtablissements);
        }
      })
      .catch((e: Error) => {
        setError(e.message);
        setFiches([]);
      })
      .finally(() => setLoading(false));
  }, [codeDept]);

  useEffect(() => {
    if (!codeDept) return;
    setLoadingFormations(true);
    fetchFormations(codeDept)
      .then((r) => setFormations(r.results))
      .catch(() => setFormations([]))
      .finally(() => setLoadingFormations(false));
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

          {loadingFormations && <Loading label="Chargement des formations…" />}
          {formations.length > 0 && (
            <>
              <h3>Formations professionnelles</h3>
              <ResultCount n={formations.length} singulier="formation" />
              <div className="grid-3">
                {formations.map((f, i) => (
                  <FormationCard key={`${f.titre}-${i}`} formation={f} />
                ))}
              </div>
            </>
          )}

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
