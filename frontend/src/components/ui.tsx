/** Petits composants du design system — équivalents React de ui/components.py. */
import type { ReactNode } from "react";
import type { Parlementaire } from "../types";

export function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="eyebrow">/ {children} /</div>;
}

export function Badge({ children, light = false }: { children: ReactNode; light?: boolean }) {
  return <span className={`badge${light ? " badge--light" : ""}`}>{children}</span>;
}

export function ResultCount({ n, singulier, pluriel }: { n: number; singulier: string; pluriel?: string }) {
  const mot = n <= 1 ? singulier : (pluriel ?? `${singulier}s`);
  return (
    <div className="result-count" role="status">
      {n} {mot}
    </div>
  );
}

export function StatCard({ value, label }: { value: ReactNode; label: string }) {
  return (
    <div className="stat">
      <div className="stat__value">{value}</div>
      <div className="stat__label">{label}</div>
    </div>
  );
}

export function FicheHeader({ parlementaire }: { parlementaire: Parlementaire }) {
  const { prenom, nom, chambre, libelle_dept, date_debut_mandat } = parlementaire;
  const mandat = date_debut_mandat ? `Mandat depuis ${date_debut_mandat}` : "Date de mandat inconnue";
  return (
    <header className="section-dark">
      <div className="eyebrow">/ Fiche territoire /</div>
      <h2>
        {prenom} {nom}
      </h2>
      <p>
        {chambre}
        {libelle_dept ? ` — ${libelle_dept}` : ""} · {mandat}
      </p>
    </header>
  );
}

export function Loading({ label }: { label: string }) {
  return (
    <div className="loading-row" role="status">
      <span className="spinner" aria-hidden="true" />
      {label}
    </div>
  );
}

export function Alert({ kind, children }: { kind: "warning" | "error"; children: ReactNode }) {
  return (
    <div className={`alert alert--${kind}`} role="alert">
      {children}
    </div>
  );
}
