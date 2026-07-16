import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCibles, fetchRappels } from "../api";
import { Eyebrow, Loading, Badge } from "../components/ui";
import type { Cible, Rappel } from "../types";

const fmtDate = (iso: string) => {
  const [a, m, j] = iso.split("-");
  return a && m && j ? `${j}/${m}/${a}` : iso;
};

interface KPI {
  label: string;
  value: string | number;
  variation?: string;
}

function MetricCard({ label, value, variation }: KPI) {
  return (
    <div className="metric-card">
      <div className="metric-card__value">{value}</div>
      <div className="metric-card__label">{label}</div>
      {variation && <div className="metric-card__variation">{variation}</div>}
    </div>
  );
}

interface BarChartProps {
  title: string;
  data: Array<{ label: string; count: number }>;
}

function BarChart({ title, data }: BarChartProps) {
  const maxCount = Math.max(...data.map((d) => d.count), 1);
  return (
    <div className="bar-chart">
      <h4 className="bar-chart__title">{title}</h4>
      {data.map((item) => (
        <div key={item.label} className="bar-chart__row">
          <div className="bar-chart__label">{item.label}</div>
          <div className="bar-chart__bar-container">
            <div
              className="bar-chart__bar"
              style={{ width: `${(item.count / maxCount) * 100}%` }}
            />
            <div className="bar-chart__value">{item.count}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function TableauDeBord() {
  const [cibles, setCibles] = useState<Cible[] | null>(null);
  const [rappels, setRappels] = useState<Rappel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        let ciblesData: Cible[] = [];
        let rappelsData: Rappel[] = [];

        // Charge toutes les cibles pour les statistiques (requête générique)
        try {
          const ciblesResp = await fetchCibles("*");
          ciblesData = ciblesResp.results;
        } catch {
          // Cibles indisponibles, continue avec données vides
          ciblesData = [];
        }

        // Charge les rappels
        try {
          const rappelsResp = await fetchRappels();
          rappelsData = rappelsResp.results;
        } catch {
          // Rappels indisponibles, continue avec données vides
          rappelsData = [];
        }

        setCibles(ciblesData);
        setRappels(rappelsData);

        // N'affiche l'erreur que s'il n'y a vraiment aucune donnée
        if (ciblesData.length === 0 && rappelsData.length === 0) {
          setError("Pas de données disponibles");
        }
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) return <Loading label="Chargement du tableau de bord…" />;

  const nbCibles = cibles?.length ?? 0;
  const nbAlliees = cibles?.filter((c) => c.statut === "allie").length ?? 0;
  const tauxContact =
    nbCibles > 0
      ? Math.round((cibles!.filter((c) => c.nb_interactions > 0).length / nbCibles) * 100)
      : 0;

  // Grouper les rappels par canal
  const rapelsParCanal = rappels.reduce(
    (acc, r) => {
      acc[r.canal] = (acc[r.canal] ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  const canalLabels: Record<string, string> = {
    rendez_vous: "Meetings",
    mail: "Emails",
    appel: "Appels",
    courrier: "Courriers",
    evenement: "Événements",
    autre: "Autres",
  };

  const activiteData = Object.entries(rapelsParCanal).map(([canal, count]) => ({
    label: canalLabels[canal] || canal,
    count,
  }));

  // Grouper les cibles par territoire (code_dept)
  const ciblesParTerritoire = cibles?.reduce(
    (acc, c) => {
      const dept = c.parlementaire.code_dept || "Inconnu";
      acc[dept] = ((acc[dept] as number) ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  const territoiresData = Object.entries(ciblesParTerritoire || {})
    .map(([dept, count]) => {
      const deptInfo = cibles?.find((c) => c.parlementaire.code_dept === dept);
      const label = `${dept} (${deptInfo?.parlementaire.libelle_dept || dept})`;
      return { label, count: count as number };
    })
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  return (
    <>
      <Eyebrow>Tableau de Bord</Eyebrow>

      {error && (
        <div className="alert alert--error">
          <strong>Erreur</strong> : {error}
        </div>
      )}

      <div className="kpi-grid">
        <MetricCard label="Cibles" value={nbCibles} />
        <MetricCard label="Taux contact" value={`${tauxContact}%`} />
        <MetricCard label="Alliées" value={nbAlliees} />
        <MetricCard label="Relances dues" value={rappels.length} />
      </div>

      {activiteData.length > 0 && (
        <div className="dashboard-section">
          <BarChart title="📈 Activité Interactions (dernier mois)" data={activiteData} />
        </div>
      )}

      {territoiresData.length > 0 && (
        <div className="dashboard-section">
          <div className="territories-list">
            <h3>🗺️ Territoires Actifs</h3>
            {territoiresData.map((t) => (
              <div key={t.label} className="territory-item">
                <span className="territory-item__name">{t.label}</span>
                <span className="territory-item__count">{t.count} cibles</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {rappels.length > 0 && (
        <div className="dashboard-section">
          <h3>📅 Prochaines Actions (Relances)</h3>
          <div className="timeline">
            {rappels.slice(0, 5).map((r) => (
              <div key={r.id} className="timeline-item">
                <div className="timeline-item__date">[{fmtDate(r.rappel)}]</div>
                <div className="timeline-item__content">
                  <Link
                    to={`/dossier/${encodeURIComponent(r.prenom)}/${encodeURIComponent(r.nom)}`}
                    className="timeline-item__link"
                  >
                    {r.prenom} {r.nom}
                  </Link>
                  <div className="timeline-item__subject">{r.objet}</div>
                </div>
                <Badge>{r.canal}</Badge>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
