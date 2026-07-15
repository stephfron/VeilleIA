import { useCallback, useEffect, useState } from "react";
import { createInteraction, deleteInteraction, fetchInteractions, setStatut } from "../api";
import type { Canal, Interaction, Statut } from "../types";
import { Alert, Loading } from "./ui";

export const STATUT_LABEL: Record<Statut, string> = {
  a_contacter: "À contacter",
  contacte: "Contacté",
  allie: "Allié",
  neutre: "Neutre",
  opposant: "Opposant",
};

const CANAL_LABEL: Record<Canal, string> = {
  rendez_vous: "Rendez-vous",
  mail: "Mail",
  courrier: "Courrier",
  appel: "Appel",
  evenement: "Événement",
  autre: "Autre",
};

const fmtDate = (iso: string) => {
  const [a, m, j] = iso.split("-");
  return a && m && j ? `${j}/${m}/${a}` : iso;
};

const aujourdhui = () => new Date().toISOString().slice(0, 10);

/**
 * Suivi CRM d'un élu : statut de la relation (sauvegarde immédiate),
 * ajout d'interactions et timeline avec suppression.
 */
export default function SuiviContact({ nom, prenom }: { nom: string; prenom: string }) {
  const [statut, setStatutLocal] = useState<Statut>("a_contacter");
  const [interactions, setInteractions] = useState<Interaction[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [date, setDate] = useState(aujourdhui());
  const [canal, setCanal] = useState<Canal>("rendez_vous");
  const [objet, setObjet] = useState("");
  const [notes, setNotes] = useState("");
  const [rappel, setRappel] = useState("");
  const [saving, setSaving] = useState(false);

  const recharger = useCallback(() => {
    fetchInteractions(nom, prenom)
      .then((r) => {
        setInteractions(r.results);
        setStatutLocal(r.statut);
      })
      .catch((e: Error) => setError(e.message));
  }, [nom, prenom]);

  useEffect(() => {
    setInteractions(null);
    setError(null);
    recharger();
  }, [recharger]);

  const changerStatut = (nouveau: Statut) => {
    setStatutLocal(nouveau); // optimiste : sauvegarde immédiate
    setError(null);
    setStatut(nom, prenom, nouveau).catch((e: Error) => {
      setError(e.message);
      recharger();
    });
  };

  const ajouter = (e: React.FormEvent) => {
    e.preventDefault();
    if (!objet.trim()) return;
    setSaving(true);
    setError(null);
    createInteraction({
      nom,
      prenom,
      canal,
      objet: objet.trim(),
      date_interaction: date || undefined,
      notes: notes.trim() || undefined,
      rappel: rappel || undefined,
    })
      .then(() => {
        setObjet("");
        setNotes("");
        setRappel("");
        setDate(aujourdhui());
        recharger();
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setSaving(false));
  };

  const supprimer = (id: number) => {
    setError(null);
    deleteInteraction(id)
      .then(recharger)
      .catch((e: Error) => setError(e.message));
  };

  return (
    <div className="chart-card">
      <h5>Suivi du contact</h5>
      {error && <Alert kind="error">{error}</Alert>}

      <div className="filters" style={{ marginBottom: "var(--space-md)" }}>
        <label className="field">
          Statut de la relation
          <select
            className="select"
            value={statut}
            onChange={(e) => changerStatut(e.target.value as Statut)}
          >
            {(Object.keys(STATUT_LABEL) as Statut[]).map((s) => (
              <option key={s} value={s}>
                {STATUT_LABEL[s]}
              </option>
            ))}
          </select>
        </label>
      </div>

      <form onSubmit={ajouter}>
        <div className="filters">
          <label className="field">
            Date
            <input className="input" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </label>
          <label className="field">
            Canal
            <select className="select" value={canal} onChange={(e) => setCanal(e.target.value as Canal)}>
              {(Object.keys(CANAL_LABEL) as Canal[]).map((c) => (
                <option key={c} value={c}>
                  {CANAL_LABEL[c]}
                </option>
              ))}
            </select>
          </label>
          <label className="field field--grow">
            Objet
            <input
              className="input"
              type="text"
              required
              maxLength={300}
              placeholder="ex : présentation des enjeux de la filière"
              value={objet}
              onChange={(e) => setObjet(e.target.value)}
            />
          </label>
        </div>
        <div className="filters">
          <label className="field field--grow">
            Notes
            <input
              className="input"
              type="text"
              maxLength={2000}
              placeholder="optionnel"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </label>
          <label className="field">
            Relance le
            <input className="input" type="date" value={rappel} onChange={(e) => setRappel(e.target.value)} />
          </label>
          <button type="submit" className="btn" disabled={saving || !objet.trim()}>
            {saving ? "Enregistrement…" : "Ajouter"}
          </button>
        </div>
      </form>

      {interactions === null && !error && <Loading label="Chargement du suivi…" />}
      {interactions !== null && interactions.length === 0 && (
        <p className="muted">Aucune interaction enregistrée pour cet élu.</p>
      )}
      {interactions !== null && interactions.length > 0 && (
        <ul className="timeline">
          {interactions.map((inter) => (
            <li key={inter.id} className="timeline__item">
              <div>
                <strong>{fmtDate(inter.date)}</strong> · {CANAL_LABEL[inter.canal] ?? inter.canal} —{" "}
                {inter.objet}
                {inter.notes && <div className="muted">{inter.notes}</div>}
                {inter.rappel && <div className="muted">Relance prévue le {fmtDate(inter.rappel)}</div>}
              </div>
              <button
                type="button"
                className="btn btn--secondary btn--small"
                onClick={() => supprimer(inter.id)}
                aria-label={`Supprimer l'interaction du ${fmtDate(inter.date)}`}
              >
                Supprimer
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
