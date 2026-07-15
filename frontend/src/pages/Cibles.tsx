import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCibles, fetchRappels } from "../api";
import { STATUT_LABEL } from "../components/SuiviContact";
import { Alert, Badge, Eyebrow, Loading, ResultCount } from "../components/ui";
import type { Cible, Rappel } from "../types";

const CHAMBRES = ["Les deux", "Sénat", "Assemblée nationale"] as const;

const fmtDate = (iso: string) => {
  const [a, m, j] = iso.split("-");
  return a && m && j ? `${j}/${m}/${a}` : iso;
};

/** Nombre au format CSV français : virgule décimale (séparateur de champ ;). */
const csvNum = (n: number) => String(n).replace(/\./g, ",");

const csvCell = (v: string | number | null | undefined) => {
  const s = v === null || v === undefined ? "" : String(v);
  return /[;"\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};

function exporterCsv(cibles: Cible[]) {
  const lignes = [
    ["Nom", "Prénom", "Chambre", "Département", "Statut", "Interactions",
      "Dernier contact", "Score /100", "Industrie /100", "Activité /100",
      "Fraîcheur /100", "Motif fraîcheur"].join(";"),
    ...cibles.map((c) =>
      [
        csvCell(c.parlementaire.nom),
        csvCell(c.parlementaire.prenom),
        csvCell(c.parlementaire.chambre),
        csvCell(c.parlementaire.libelle_dept),
        csvCell(STATUT_LABEL[c.statut]),
        c.nb_interactions,
        csvCell(c.dernier_contact),
        csvNum(c.score),
        csvNum(c.detail_score.industrie),
        csvNum(c.detail_score.activite),
        csvNum(c.detail_score.fraicheur),
        csvCell(c.detail_score.motif_fraicheur),
      ].join(";"),
    ),
  ];
  // BOM UTF-8 : Excel FR ouvre le fichier avec les accents corrects
  const blob = new Blob(["﻿" + lignes.join("\r\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "cibles-veilleia.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function CibleCard({ cible }: { cible: Cible }) {
  const { parlementaire: parl, detail_score: detail } = cible;
  return (
    <div className="card card--row">
      <div className="card__score" aria-label={`Score de priorité ${cible.score} sur 100`}>
        {Math.round(cible.score)}
      </div>
      <div className="card__body">
        <Badge>{STATUT_LABEL[cible.statut]}</Badge>
        {parl.chambre && <Badge light>{parl.chambre}</Badge>}
        <h4>
          <Link to={`/dossier/${encodeURIComponent(parl.prenom)}/${encodeURIComponent(parl.nom)}`}>
            {parl.prenom} {parl.nom}
          </Link>
        </h4>
        <p className="muted">
          {parl.libelle_dept ?? "Département inconnu"}
          {cible.nb_interactions > 0
            ? ` · ${cible.nb_interactions} interaction${cible.nb_interactions > 1 ? "s" : ""}`
            : ""}
          {cible.dernier_contact ? ` · dernier contact le ${fmtDate(cible.dernier_contact)}` : ""}
        </p>
        <p className="muted">
          Industrie {detail.industrie}/100 · Activité {detail.activite}/100 · Fraîcheur{" "}
          {detail.fraicheur}/100 ({detail.motif_fraicheur})
        </p>
      </div>
    </div>
  );
}

export default function Cibles() {
  const [query, setQuery] = useState("");
  const [chambre, setChambre] = useState<(typeof CHAMBRES)[number]>("Les deux");
  const [avecActivite, setAvecActivite] = useState(false);
  const [cibles, setCibles] = useState<Cible[] | null>(null);
  const [rappels, setRappels] = useState<Rappel[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounce = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    fetchRappels()
      .then((r) => setRappels(r.results))
      .catch(() => setRappels([]));
  }, []);

  useEffect(() => {
    clearTimeout(debounce.current);
    const q = query.trim();
    if (!q) {
      setCibles(null);
      setError(null);
      setLoading(false);
      return;
    }
    debounce.current = setTimeout(() => {
      setLoading(true);
      setError(null);
      fetchCibles(q, chambre === "Les deux" ? undefined : chambre, avecActivite)
        .then((r) => setCibles(r.results))
        .catch((e: Error) => {
          setCibles(null);
          setError(e.message);
        })
        .finally(() => setLoading(false));
    }, 400);
    return () => clearTimeout(debounce.current);
  }, [query, chambre, avecActivite]);

  const reset = () => {
    setQuery("");
    setChambre("Les deux");
    setAvecActivite(false);
  };

  return (
    <>
      {rappels.length > 0 && (
        <Alert kind="warning">
          <strong>
            {rappels.length} relance{rappels.length > 1 ? "s" : ""} due{rappels.length > 1 ? "s" : ""}
          </strong>{" "}
          :{" "}
          {rappels.map((r, i) => (
            <span key={r.id}>
              {i > 0 && ", "}
              <Link to={`/dossier/${encodeURIComponent(r.prenom)}/${encodeURIComponent(r.nom)}`}>
                {r.prenom} {r.nom}
              </Link>{" "}
              ({fmtDate(r.rappel)} — {r.objet})
            </span>
          ))}
        </Alert>
      )}

      <Eyebrow>Cibles prioritaires</Eyebrow>
      <div className="filters">
        <label className="field field--grow">
          Département, code ou nom
          <input
            className="input"
            type="search"
            placeholder="ex : 69, Rhône, Dupont"
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
        <label className="field field--checkbox">
          <input
            type="checkbox"
            checked={avecActivite}
            onChange={(e) => setAvecActivite(e.target.checked)}
          />
          Activité législative (plus lent)
        </label>
        <button type="button" className="btn btn--secondary" onClick={reset}>
          Réinitialiser
        </button>
      </div>

      {loading && <Loading label="Calcul des priorités…" />}
      {error && <Alert kind="error">{error}</Alert>}
      {cibles !== null && !loading && !error && cibles.length === 0 && (
        <Alert kind="warning">Aucun parlementaire trouvé pour cette recherche.</Alert>
      )}

      {cibles !== null && cibles.length > 0 && !loading && (
        <>
          <div className="filters" style={{ justifyContent: "space-between" }}>
            <ResultCount n={cibles.length} singulier="cible (triée par priorité)" pluriel="cibles (triées par priorité)" />
            <button type="button" className="btn btn--secondary btn--small" onClick={() => exporterCsv(cibles)}>
              Exporter en CSV
            </button>
          </div>
          {cibles.map((cible, i) => (
            <CibleCard
              key={`${cible.parlementaire.nom}-${cible.parlementaire.prenom}-${i}`}
              cible={cible}
            />
          ))}
        </>
      )}
    </>
  );
}
