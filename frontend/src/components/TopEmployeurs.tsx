import type { TopEmployeur } from "../types";

const fmtEffectifs = (n: number) => n.toLocaleString("fr-FR");

/** Tableau des plus gros établissements industriels nommés du département. */
export default function TopEmployeurs({ employeurs }: { employeurs: TopEmployeur[] }) {
  if (employeurs.length === 0) return null;
  return (
    <div className="chart-card">
      <h5>Principaux employeurs industriels</h5>
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Établissement</th>
              <th>Commune</th>
              <th>NAF</th>
              <th className="num">Effectifs est.</th>
            </tr>
          </thead>
          <tbody>
            {employeurs.map((e, i) => (
              <tr key={`${e.nom}-${i}`}>
                <td className="strong">{e.nom}</td>
                <td>{e.commune ?? "—"}</td>
                <td>{e.naf ?? "—"}</td>
                <td className="num">{fmtEffectifs(e.effectifs_estimes)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
