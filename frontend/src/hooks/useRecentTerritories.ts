import { useEffect, useState } from "react";
import type { RecentTerritory } from "../types";

const STORAGE_KEY = "recent_territories";
const MAX_TERRITORIES = 5;

export function useRecentTerritories() {
  const [territories, setTerritories] = useState<RecentTerritory[]>([]);

  // Charger depuis localStorage au montage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setTerritories(JSON.parse(stored));
      } catch {
        // localStorage corrompu, ignorer
        setTerritories([]);
      }
    }
  }, []);

  const addTerritory = (codeDept: string, nomDept: string, nbEtablissements: number) => {
    setTerritories((prev) => {
      // Créer le nouvel élément
      const newTerritory: RecentTerritory = {
        codeDept,
        nomDept,
        nbEtablissements,
        dateVisite: new Date().toISOString(),
      };

      // Éliminer les doublons et ajouter le nouveau au début
      const filtered = prev.filter((t) => t.codeDept !== codeDept);
      const updated = [newTerritory, ...filtered].slice(0, MAX_TERRITORIES);

      // Sauvegarder dans localStorage
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

      return updated;
    });
  };

  return { territories, addTerritory };
}
