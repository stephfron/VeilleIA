import { NavLink, Route, Routes } from "react-router-dom";
import Accueil from "./pages/Accueil";
import FicheTerritoire from "./pages/FicheTerritoire";
import Textes from "./pages/Textes";

const NAV = [
  { to: "/", icon: "🏠", label: "Accueil", end: true },
  { to: "/fiche-territoire", icon: "📍", label: "Fiche territoire", end: false },
  { to: "/textes", icon: "📜", label: "Textes législatifs", end: false },
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
          <Route path="/fiche-territoire" element={<FicheTerritoire />} />
          <Route path="/textes" element={<Textes />} />
        </Routes>
      </main>
    </div>
  );
}
