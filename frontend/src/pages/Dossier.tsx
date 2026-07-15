import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchDossier } from "../api";
import { FicheHeader, Loading, Alert } from "../components/ui";
import ActiviteLegislative from "../components/ActiviteLegislative";
import TopEmployeurs from "../components/TopEmployeurs";
import type { Dossier as DossierType } from "../types";

/**
 * Page dossier de synthèse — profil complet d'un parlementaire.
 * Affiche : identité + territoire + activité législative + textes pertinents.
 * (CRM tracking reporté à Phase 4)
 */
export default function Dossier() {
  const { prenom, nom } = useParams<{ prenom: string; nom: string }>();
  const [dossier, setDossier] = useState<DossierType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!nom || !prenom) {
      setError("Nom ou prénom manquant");
      return;
    }
    setLoading(true);
    setError(null);
    fetchDossier(decodeURIComponent(nom), decodeURIComponent(prenom))
      .then(setDossier)
      .catch((e: Error) => {
        setError(e.message);
        setDossier(null);
      })
      .finally(() => setLoading(false));
  }, [nom, prenom]);

  if (!nom || !prenom) {
    return <Alert kind="error">Nom ou prénom manquant.</Alert>;
  }

  return (
    <>
      {loading && <Loading label="Chargement du dossier…" />}
      {error && <Alert kind="error">{error}</Alert>}

      {dossier && (
        <>
          <FicheHeader parlementaire={dossier.parlementaire} />

          <h3>Territoire</h3>
          <div className="grid-2">
            <div className="stat">
              <div className="stat__value">
                {dossier.territoire.nb_etablissements_industriels}
              </div>
              <div className="stat__label">Établissements industriels</div>
            </div>
            <div className="stat">
              <div className="stat__value">
                {dossier.territoire.effectifs_estimes?.toLocaleString("fr-FR")}
              </div>
              <div className="stat__label">Effectifs estimés</div>
            </div>
          </div>

          {dossier.territoire.top_employeurs && dossier.territoire.top_employeurs.length > 0 && (
            <TopEmployeurs employeurs={dossier.territoire.top_employeurs} />
          )}

          <h3>Activité législative</h3>
          <ActiviteLegislative parlementaire={dossier.parlementaire} />

          {dossier.textes_pertinents && dossier.textes_pertinents.length > 0 && (
            <>
              <h3>Textes pertinents ({dossier.textes_pertinents.length})</h3>
              <div className="grid-3">
                {dossier.textes_pertinents.map((t) => (
                  <div key={t.title} className="card">
                    <h4>{t.title}</h4>
                    <p className="muted">{t.category_label}</p>
                    {t.annee && <p className="muted">{t.annee}</p>}
                    {t.article_synthesis && <p>{t.article_synthesis.slice(0, 150)}…</p>}
                  </div>
                ))}
              </div>
            </>
          )}

          {/* TODO: Phase 4 — CRM tracking (SuiviContact) ici */}
        </>
      )}
    </>
  );
}
