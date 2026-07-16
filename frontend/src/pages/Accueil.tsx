import { Link } from "react-router-dom";
import { Eyebrow } from "../components/ui";
import { TerritoireCard } from "../components/TerritoireCard";
import { useRecentTerritories } from "../hooks/useRecentTerritories";

const SHORTCUTS = [
  {
    icon: "📍",
    titre: "Fiche territoire",
    desc: "Élus, établissements industriels et effectifs par département.",
    to: "/fiche-territoire",
  },
  {
    icon: "📜",
    titre: "Textes législatifs",
    desc: "Lois, ordonnances et propositions filtrables par mots-clés.",
    to: "/textes",
  },
  {
    icon: "📊",
    titre: "Données publiques",
    desc: "RNE, SIRENE (INSEE) et DOLE — actualisées toutes les 24 h.",
    to: null,
  },
];

export default function Accueil() {
  const { territories } = useRecentTerritories();

  return (
    <>
      <section className="section-dark">
        <Eyebrow>VeilleIA</Eyebrow>
        <h2>Veille territoriale et industrielle</h2>
        <p>
          Croisez le tissu économique local avec l'activité législative des élus — données
          publiques françaises, sans IA.
        </p>
      </section>

      <div className="grid-3">
        {SHORTCUTS.map(({ icon, titre, desc, to }) => (
          <div className="card" key={titre} style={{ display: "flex", flexDirection: "column" }}>
            <h4>
              <span aria-hidden="true">{icon}</span> {titre}
            </h4>
            <p className="muted" style={{ flex: 1 }}>
              {desc}
            </p>
            {to && (
              <Link to={to} className="btn btn--secondary" style={{ textAlign: "center", textDecoration: "none" }}>
                Ouvrir →
              </Link>
            )}
          </div>
        ))}
      </div>

      {territories.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <Eyebrow>📍 Territoires Récents</Eyebrow>
          <div className="grid-3">
            {territories.map((t) => (
              <TerritoireCard key={t.codeDept} {...t} />
            ))}
          </div>
        </div>
      )}
    </>
  );
}
