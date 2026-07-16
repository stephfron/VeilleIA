# VeilleIA Design System
## UX/UI Redesign for UIMM Lobbyist Workflow

---

## 1. Brand Identity

### Color Palette
```
Primary Blue:    #1a5f8f  (Professional, industrial)
Secondary:       #e8931a  (Metalworking/industrial accent)
Success:         #27ae60  (For positive metrics)
Warning:         #f39c12  (For attention needed)
Error:           #e74c3c  (For critical alerts)
Neutral:         #ecf0f1 - #2c3e50 (Backgrounds to text)
```

### Typography
- **Headlines (H1-H2)**: Inter Bold, 32px/28px
- **Subheads (H3-H4)**: Inter SemiBold, 20px/16px
- **Body**: Inter Regular, 16px / 14px
- **Small**: Inter Regular, 12px

### Spacing Grid
8px base unit: 8, 16, 24, 32, 48, 64px

---

## 2. Navigation Architecture

### Main Navigation (Sidebar + Top Bar)
```
🏭 VeilleIA
├─ 🏠 Accueil
├─ 🗺️ Territoires (NEW - dropdown)
│  └─ Sélectionner département
├─ 🎯 Cibles (Prioritisation)
├─ 📊 Tableau de bord (NEW)
├─ 📜 Textes (Legislation)
└─ ⚙️ Paramètres
```

---

## 3. Screen Designs

### A. ACCUEIL (Home Screen)

**Layout**: Hero + Quick Access

```
┌─────────────────────────────────────┐
│ 🏭 VeilleIA                    ⚙️ 👤│
├─────────────────────────────────────┤
│                                     │
│  Veille Territoriale & Industrielle │
│  pour les Lobbystes UIMM            │
│                                     │
│  [ Sélectionner un Département ▼ ]  │
│                                     │
├─────────────────────────────────────┤
│                                     │
│ 📍 Territoires Récents              │
│ ┌───────────────────────────────┐   │
│ │ Rhône (69)        → Voir fiche│   │
│ │ 150 établissements            │   │
│ └───────────────────────────────┘   │
│                                     │
│ 🎯 Tâches en Attente                │
│ ┌───────────────────────────────┐   │
│ │ 3 relances dues               │   │
│ │ Anne Grand - Rappel: 15 mai   │   │
│ └───────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

---

### B. TERRITOIRE - Fiche d'Identité (Territory Profile)

**Full-screen information dashboard**

```
┌────────────────────────────────────────────────┐
│ 🏭 VeilleIA              [← Retour] [Imprimer] │
├────────────────────────────────────────────────┤
│                                                │
│  ▰▰▰ RHÔNE (69)                                │
│  🗺️  Région Auvergne-Rhône-Alpes               │
│                                                │
├────────────────────────────────────────────────┤
│ 📊 PORTRAIT INDUSTRIEL                         │
│                                                │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │ 150              │  │ 50 000           │   │
│  │ Établissements   │  │ Emplois estimés  │   │
│  └──────────────────┘  └──────────────────┘   │
│                                                │
│  📈 Distribution par Secteur (NAF)             │
│  ┌────────────────────────────────────────┐   │
│  │ Métallurgie              ███████ 45%  │   │
│  │ Chimie                   ████   28%   │   │
│  │ Agroalimentaire          ███    18%   │   │
│  │ Textiles                 ██     9%    │   │
│  └────────────────────────────────────────┘   │
│                                                │
│  🏢 Top 10 Employeurs                          │
│  ┌────────────────────────────────────────┐   │
│  │ 1. Boehringer Ingelheim   2 100 emp.   │   │
│  │ 2. Sanofi                 1 800 emp.   │   │
│  │ 3. Argenx                 1 200 emp.   │   │
│  │ ...                                    │   │
│  └────────────────────────────────────────┘   │
│                                                │
├────────────────────────────────────────────────┤
│ 🎓 FORMATIONS DISPONIBLES                      │
│                                                │
│  ┌────────────────────────────────────────┐   │
│  │ CAP Usinage - Lycée A, Lyon            │   │
│  │ Bac Pro Mécanique - Lycée B, Villeub.  │   │
│  │ BTS Productique - IUT, Saint-Étienne   │   │
│  └────────────────────────────────────────┘   │
│                                                │
├────────────────────────────────────────────────┤
│ 👥 ÉLUS DU DÉPARTEMENT (5)                    │
│                                                │
│  Afficher: [ Sénat ▼ ] [ Assemblée Nationale▼]│
│  Trier:    [ Par Priorité ▼ ]                 │
│                                                │
│  ┌────────────────────────────────────────┐   │
│  │ Anne Grand (Sénat) - Rhône             │   │
│  │ Score: 79/100 | Amendements: 12        │   │
│  │ [Voir Profil] [Contacter]              │   │
│  └────────────────────────────────────────┘   │
│                                                │
│  [Charger plus élus]                          │
│                                                │
├────────────────────────────────────────────────┤
│ 📎 ACTIONS                                     │
│ [Exporter Rapport] [Ajouter Note] [Partager]  │
└────────────────────────────────────────────────┘
```

---

### C. ÉLU - Fiche d'Identité (Elected Official Profile)

**Comprehensive elected official dossier**

```
┌────────────────────────────────────────────────┐
│ 🏭 VeilleIA              [← Retour] [Imprimer] │
├────────────────────────────────────────────────┤
│                                                │
│  👤 ANNE GRAND                                 │
│  Sénatrice - Rhône (69)                        │
│                                                │
│  ✓ Alliée                                      │
│  Score Priorité: 79/100                        │
│                                                │
├────────────────────────────────────────────────┤
│ 📋 IDENTITÉ                                    │
│                                                │
│  Prénom:              Anne                     │
│  Nom:                 Grand                    │
│  Chambre:             Sénat                    │
│  Circonscription:     Rhône                    │
│  Mandat depuis:       2020                     │
│  Catégorie socio-pro: Ingénieur                │
│                                                │
├────────────────────────────────────────────────┤
│ 🗺️  TERRITOIRES REPRÉSENTÉS                    │
│                                                │
│  Rhône (69)                                    │
│  • 150 établissements industriels              │
│  • 50 000 emplois estimés                      │
│  • Secteur principal: Métallurgie (45%)        │
│                                                │
├────────────────────────────────────────────────┤
│ 📈 ACTIVITÉ LÉGISLATIVE                        │
│                                                │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │ 12               │  │ 8                │   │
│  │ Amendements      │  │ Questions orales │   │
│  └──────────────────┘  └──────────────────┘   │
│                                                │
│  📊 Domaines d'intérêt:                        │
│  • Industrie (60%)                             │
│  • Emploi (25%)                                │
│  • Environnement (15%)                         │
│                                                │
├────────────────────────────────────────────────┤
│ 📄 TEXTES PERTINENTS                           │
│                                                │
│  Propositions soumises:                        │
│  • Loi sur la relocalisation industrielle      │
│  • Décret formations professionnelles          │
│  • Amendement fiscalité PME                    │
│                                                │
├────────────────────────────────────────────────┤
│ 📞 SUIVI & CRM                                 │
│                                                │
│  Dernier contact: 15 mai 2026 (Email)          │
│  Interactions: 3 (Meeting, Email, Appel)       │
│  Statut: Alliée                                │
│                                                │
│  📅 Rappel: 15 juin (suivi trimestriel)        │
│                                                │
│  [Ajouter Interaction] [Modifier Statut]       │
│  [Télécharger Dossier Complet]                 │
│                                                │
└────────────────────────────────────────────────┘
```

---

### D. CIBLES (Targeting & Prioritization)

**Scored list with filtering**

```
┌────────────────────────────────────────────────┐
│ 🏭 VeilleIA                            [⚙️ 👤]│
├────────────────────────────────────────────────┤
│ 🎯 CIBLES PRIORITAIRES                         │
│                                                │
│  Filtrer:                                      │
│  [Territoire ____________] [Sénat ▼]          │
│  [ ] Inclure activité législative (lent)       │
│  [Réinitialiser]                              │
│                                                │
├────────────────────────────────────────────────┤
│                                                │
│ 3 Relances dues:                               │
│ ⚠️  Anne Grand (Rappel: 15 mai)                │
│ ⚠️  Bob Petit (Rappel: 12 mai)                 │
│ ⚠️  Carol Medium (Rappel: 10 mai)              │
│                                                │
├────────────────────────────────────────────────┤
│                                                │
│ RÉSULTATS (14 cibles)                          │
│                                                │
│ ┌──────────────────────────────────────────┐  │
│ │ [79] Anne GRAND (Sénat) - Rhône          │  │
│ │ ✓ Alliée | 3 interactions | 15 mai       │  │
│ │ Industrie: 85 | Activité: 72 | Fraîch: 68  │  │
│ │ [Voir Profil] [Contacter]                │  │
│ └──────────────────────────────────────────┘  │
│                                                │
│ ┌──────────────────────────────────────────┐  │
│ │ [72] Bob PETIT (AN) - Loire              │  │
│ │ À contacter | 1 interaction | 3 mois     │  │
│ │ Industrie: 78 | Activité: 65 | Fraîch: 72  │  │
│ │ [Voir Profil] [Contacter]                │  │
│ └──────────────────────────────────────────┘  │
│                                                │
│ [Charger plus] [Exporter CSV]                 │
│                                                │
└────────────────────────────────────────────────┘
```

---

### E. TABLEAU DE BORD (Analytics Dashboard) - NEW

**Executive overview**

```
┌────────────────────────────────────────────────┐
│ 🏭 VeilleIA              [📅 Mois] [Année ▼]  │
├────────────────────────────────────────────────┤
│                                                │
│ 📊 KPIs LOBBYING                               │
│                                                │
│ ┌──────────────┐ ┌──────────────┐             │
│ │ 47           │ │ 23%          │             │
│ │ Cibles       │ │ Taux contact │             │
│ └──────────────┘ └──────────────┘             │
│                                                │
│ ┌──────────────┐ ┌──────────────┐             │
│ │ 15           │ │ 8            │             │
│ │ Alliées      │ │ Relances dues│             │
│ └──────────────┘ └──────────────┘             │
│                                                │
│ 📈 Activité Interactions (dernier mois)        │
│ ┌────────────────────────────────────────┐    │
│ │ Meetings      ████    12               │    │
│ │ Emails        ██████  28               │    │
│ │ Appels        ███     7                │    │
│ │ Événements    ██      3                │    │
│ └────────────────────────────────────────┘    │
│                                                │
│ 🗺️  Territoires Actifs                        │
│ ┌────────────────────────────────────────┐    │
│ │ Rhône (69)          15 cibles          │    │
│ │ Auvergne (63)       12 cibles          │    │
│ │ Loire (42)          10 cibles          │    │
│ │ ...                                    │    │
│ └────────────────────────────────────────┘    │
│                                                │
│ 📅 Timeline Prochaines Actions                 │
│ ┌────────────────────────────────────────┐    │
│ │ [15 mai] Relance Anne Grand            │    │
│ │ [18 mai] Meeting Bob Petit             │    │
│ │ [20 mai] Follow-up Carol Medium        │    │
│ └────────────────────────────────────────┘    │
│                                                │
└────────────────────────────────────────────────┘
```

---

## 4. Component Library

### Cards
```
Card Variants:
├─ TerritoryCard (territory with key stats)
├─ ElectedOfficialCard (official with score)
├─ FormationCard (training program)
├─ InteractionCard (timeline item)
└─ MetricCard (KPI display)
```

### Buttons
```
Primary:    [Voir Profil]     (Blue #1a5f8f)
Secondary:  [Ajouter Note]    (Light gray)
Accent:     [Contacter]       (Orange #e8931a)
Danger:     [Supprimer]       (Red #e74c3c)
```

### Status Badges
```
✓ Alliée         (Green #27ae60)
→ À contacter    (Blue #1a5f8f)
! Neutre         (Gray #95a5a6)
✗ Opposant       (Red #e74c3c)
```

---

## 5. UX Flows

### Flow 1: Recherche Territoire → Fiches
```
Accueil
  ↓
Sélectionner Département (Rhône)
  ↓
Fiche Territoire (Portrait complet)
  ├─ Portrait industriel
  ├─ Formations disponibles
  └─ Élus du département
       ↓
    Clic sur élu
       ↓
    Fiche Élu (Profil complet)
```

### Flow 2: Ciblage & Prioritization
```
Cibles (liste filtrée)
  ↓
Sélectionner élus par score/territoire
  ↓
Voir Profil (Fiche Élu)
  ↓
Ajouter Interaction (Email, RDV, etc)
  ↓
Modifier Statut (Alliée, Neutre, etc)
  ↓
Définir Rappel (suivi)
```

---

## 6. Responsive Design

### Breakpoints
- **Desktop**: 1440px+ (full sidebar)
- **Laptop**: 1024px+ (sidebar)
- **Tablet**: 768px (collapsed sidebar)
- **Mobile**: 375px (bottom nav)

### Mobile-First Strategy
- Bottom navigation for mobile
- Collapsible sections on tablet
- Full sidebar on desktop
- Touch-friendly (48px min target size)

---

## 7. Accessibility (WCAG AA)

- Color contrast: 4.5:1 minimum
- All interactive elements keyboard accessible
- Screen reader friendly labels
- Focus indicators visible
- Motion: reduced motion option

---

## 8. Typography Hierarchy

```
H1: 32px Bold    - Page titles
H2: 28px Bold    - Section titles
H3: 20px SemiBold - Subsections
H4: 16px SemiBold - Card titles
Body: 16px       - Main content
Small: 14px      - Secondary text
Micro: 12px      - Metadata
```

---

## Next Phase: Implementation

Screens to build in priority order:
1. ✅ TerritoireDetail (Fiche Territoire) 
2. ✅ Dossier (Fiche Élu)
3. ⭕ Tableau de Bord (Analytics)
4. ⭕ Enhanced Cibles (with status badges)
5. ⭕ Accueil Redesigned (hero + recent)

---

**Design System Version**: 1.0
**Last Updated**: 2026-07-16
**Status**: Ready for implementation
