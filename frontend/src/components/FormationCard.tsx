import type { Formation } from "../types";

interface Props {
  formation: Formation;
}

export default function FormationCard({ formation }: Props) {
  return (
    <div className="card">
      <h4>
        {formation.url_descriptif ? (
          <a href={formation.url_descriptif} target="_blank" rel="noopener noreferrer">
            {formation.titre}
          </a>
        ) : (
          formation.titre
        )}
      </h4>
      {formation.type && <p className="muted">{formation.type}</p>}
      {formation.etablissement && <p className="muted">{formation.etablissement}</p>}
      {formation.localite && <p className="muted">{formation.localite}</p>}
    </div>
  );
}
