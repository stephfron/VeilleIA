/**
 * Graphiques Recharts — mono-série (magnitude), teinte de marque unique
 * validée (#C6303A, contraste >= 3:1 sur blanc), pas de légende (le titre
 * nomme la série), grille discrète, tooltip au survol, extrémités arrondies.
 */
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TopNaf } from "../types";

const BAR = "#c6303a";
const GRID = "#e2e8f0";
const INK_MUTED = "#565f6e";

const tooltipStyle = {
  borderRadius: 8,
  border: `1px solid ${GRID}`,
  fontSize: "0.85rem",
  fontFamily: "Inter, sans-serif",
};

export function TopNafChart({ data }: { data: TopNaf[] }) {
  return (
    <figure className="chart-card" aria-label="Top codes NAF par nombre d'établissements">
      <h5>Top codes NAF (nb établissements)</h5>
      <ResponsiveContainer width="100%" height={data.length * 44 + 30}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 24, bottom: 0, left: 8 }}>
          <CartesianGrid horizontal={false} stroke={GRID} />
          <XAxis type="number" tick={{ fontSize: 12, fill: INK_MUTED }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="naf"
            width={70}
            tick={{ fontSize: 12, fill: INK_MUTED }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: "rgba(23,26,31,0.05)" }}
            contentStyle={tooltipStyle}
            formatter={(value: number) => [`${value} établissements`, ""]}
            separator=""
          />
          <Bar dataKey="nb" name="Établissements" fill={BAR} barSize={14} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </figure>
  );
}

export function TextesParAnneeChart({ parAnnee }: { parAnnee: Record<string, number> }) {
  const data = Object.entries(parAnnee)
    .map(([annee, nb]) => ({ annee, nb }))
    .sort((a, b) => a.annee.localeCompare(b.annee));

  if (data.length <= 1) return null;

  return (
    <figure className="chart-card" aria-label="Évolution du nombre de textes par année">
      <h5>Évolution du nombre de textes par année</h5>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke={GRID} />
          <XAxis dataKey="annee" tick={{ fontSize: 12, fill: INK_MUTED }} axisLine={false} tickLine={false} />
          <YAxis allowDecimals={false} width={32} tick={{ fontSize: 12, fill: INK_MUTED }} axisLine={false} tickLine={false} />
          <Tooltip
            cursor={{ fill: "rgba(23,26,31,0.05)" }}
            contentStyle={tooltipStyle}
            formatter={(value: number) => [`${value} texte${value > 1 ? "s" : ""}`, ""]}
            separator=""
          />
          <Bar dataKey="nb" name="Textes" fill={BAR} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </figure>
  );
}
