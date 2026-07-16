import { Link } from "react-router-dom";
import type { RecentTerritory } from "../types";

export function TerritoireCard(props: RecentTerritory) {
  return (
    <div className="card">
      <h4>
        {props.nomDept} <span className="muted">({props.codeDept})</span>
      </h4>
      <p className="muted">{props.nbEtablissements} établissements industriels</p>
      <Link to={`/territoire/${props.codeDept}`} className="card-link">
        Voir fiche →
      </Link>
    </div>
  );
}
