# Projet_PFE - Optimisation du Planning Hospitalier en Odontologie

**Projet de Fin d'Étude** - Promotion 2023-2026  
**Corentin DELCLAUD & Poomedy RUNGEN**  
Département Data Science, Management & Software Architecture

---

## Contexte

Système d'optimisation de planning pour l'affectation d'étudiants en Odontologie (DFASO1, DFASO2, DFTCC) aux vacations hospitalières du Centre de Soins Dentaires de la Faculté d'Odontologie de Montpellier.

**Période** : 08 Décembre 2025 - 17 Février 2026

## Objectifs

- **Automatiser** la génération des plannings hospitaliers
- **Optimiser** l'utilisation des fauteuils disponibles
- **Garantir** l'équité entre étudiants et la validation des quotas
- **Gérer** les binômes et contraintes académiques

## Technologies

- **Approche** : Constraint Programming (Recherche Opérationnelle)
- **Langage** : Python
- **Solveur** : OR-Tools

## Installation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/username/Projet_PFE.git
   cd Projet_PFE
   ```

2. Installer les dépendances :
   ```bash

   ```

3. Configuration :
   ```bash

   ```

## Utilisation

```bash

```

## Structure du Projet

```
Projet_PFE/
├── src/          # Code source
├── data/         # Données d'entrée (calendriers, étudiants)
├── docs/         # Documentation
└── tests/        # Tests unitaires

config_manager.py - Manages and validates configuration
loaders.py - Loads data from CSV files with error handling
optimizer.py - Core optimization engine with CP-SAT
exporter.py - Exports results to various formats
app_V1.py - Main script that orchestrates everything
3_Export_du_Planning.py - Updated Streamlit UI page

```

## Contributeurs

- **Étudiants** : Corentin DELCLAUD, Poomedy RUNGEN
- **Encadrement** : 
  - Eleonora GUERRINI (Tutrice école)
  - Pr. Clara JOSEPH (Faculté d'Odontologie)
  - Dr. Bruno PICART (Faculté d'Odontologie)

## Convention Git

Utilisez les préfixes suivants pour vos commits :
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation
- `refactor`: Refactorisation
- `test`: Ajout de tests
- `perf`: Amélioration de performance
- `style`: Formatage du code
- `build`: Système de build
- `ci`: Intégration continue
- `chore`: Tâches diverses


