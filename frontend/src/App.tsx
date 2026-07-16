import { NavLink, Route, Routes } from "react-router-dom";
import Accueil from "./pages/Accueil";
import TerritoireDetail from "./pages/TerritoireDetail";
import FicheTerritoire from "./pages/FicheTerritoire";
import Dossier from "./pages/Dossier";
import Cibles from "./pages/Cibles";
import TableauDeBord from "./pages/TableauDeBord";
import Textes from "./pages/Textes";

const NAV = [
  { to: "/", icon: "🏠", label: "Accueil", end: true },
  { to: "/tableau-de-bord", icon: "📊", label: "Tableau de bord", end: true },
  { to: "/cibles", icon: "🎯", label: "Cibles", end: false },
  { to: "/fiche-territoire", icon: "🔍", label: "Recherche", end: false },
  { to: "/textes", icon: "📜", label: "Textes", end: false },
];

export default function App() {
  return (
    <div className="app">
      <nav className="sidebar" aria-label="Navigation principale">
        <div className="sidebar__brand">🏭 VeilleIA</div>
        <div className="sidebar__nav">
          {NAV.map(({ to, icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              title={label}
              className={({ isActive }) =>
                `sidebar__link${isActive ? " sidebar__link--active" : ""}`
              }
            >
              <span aria-hidden="true">{icon}</span>
              <span className="label">{label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
      <main className="content">
        <Routes>
          <Route path="/" element={<Accueil />} />
          <Route path="/tableau-de-bord" element={<TableauDeBord />} />
          <Route path="/territoire/:codeDept" element={<TerritoireDetail />} />
          <Route path="/cibles" element={<Cibles />} />
          <Route path="/dossier/:prenom/:nom" element={<Dossier />} />
          <Route path="/fiche-territoire" element={<FicheTerritoire />} />
          <Route path="/textes" element={<Textes />} />
        </Routes>
      </main>
    </div>
  );
}
