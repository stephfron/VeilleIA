import { useState } from "react";
import { fetchActivite } from "../api";
import type { Activite, Parlementaire } from "../types";
import { Alert, Badge, Loading } from "./ui";

const STATS: Array<[keyof Activite, string]> = [
  ["amendements_proposes", "Amendements proposés"],
  ["amendements_adoptes", "Amendements adoptés"],
  ["questions_ecrites", "Questions écrites"],
  ["questions_orales", "Questions orales"],
  ["rapports", "Rapports"],
  ["interventions", "Interventions"],
];

/**
 * Activité législative chargée à la demande (bouton) pour ne pas ralentir
 * la recherche — source Regards Citoyens, best-effort.
 */
export default function ActiviteLegislative({ parlementaire }: { parlementaire: Parlementaire }) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [activite, setActivite] = useState<Activite | null>(null);

  const charger = () => {
    setState("loading");
    fetchActivite(parlementaire.nom, parlementaire.prenom, parlementaire.chambre)
      .then((a) => {
        setActivite(a);
        setState("done");
      })
      .catch(() => setState("error"));
  };

  if (state === "idle") {
    return (
      <button type="button" className="btn btn--secondary" onClick={charger}>
        Voir l'activité législative
      </button>
    );
  }
  if (state === "loading") return <Loading label="Chargement de l'activité…" />;
  if (state === "error" || !activite?.disponible) {
    return (
      <Alert kind="warning">
        Activité législative indisponible pour cet élu (source citoyenne hors ligne ou élu non référencé).{" "}
        <button type="button" className="btn btn--secondary" style={{ padding: "0.2rem 0.8rem", fontSize: "0.8rem" }} onClick={charger}>
          Réessayer
        </button>
      </Alert>
    );
  }

  return (
    <div className="chart-card">
      <h5>
        Activité législative{" "}
        {activite.groupe_sigle && <Badge>{activite.groupe_sigle}</Badge>}
      </h5>
      <div className="activite-grid">
        {STATS.map(([key, label]) => {
          const value = activite[key];
          if (value === null || value === undefined) return null;
          return (
            <div className="stat" key={key}>
              <div className="stat__value">{Number(value).toLocaleString("fr-FR")}</div>
              <div className="stat__label">{label}</div>
            </div>
          );
        })}
      </div>
      {activite.source_url && (
        <p className="muted" style={{ marginBottom: 0 }}>
          Source :{" "}
          <a href={activite.source_url} target="_blank" rel="noreferrer">
            {activite.source_url.replace("https://www.", "")}
          </a>
        </p>
      )}
    </div>
  );
}
