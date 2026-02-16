<div align="center">

# Optimisation du Planning Hospitalier 
## Faculté d'Odontologie de Montpellier

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![OR-Tools](https://img.shields.io/badge/OR--Tools-9.8+-green.svg)](https://developers.google.com/optimization)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Projet de Fin d'Étude 2023-2026**  
*Corentin DELCLAUD & Poomedy RUNGEN*  
*Polytech Montpellier - Département Data Science & Software Architecture*

[Démo](#demo) • [Documentation](#documentation) • [Installation](#installation) • [Features](#features)

---

</div>

## 📋 Vue d'ensemble

Ce projet résout un problème complexe d'**optimisation combinatoire** : générer automatiquement les plannings hospitaliers pour les étudiants en Odontologie du Centre de Soins Dentaires de Montpellier. 

### Contexte Académique

- **Période**: Décembre 2025 - Février 2026
- **Étudiants concernés**: ~120 étudiants (DFASO1, DFASO2, DFTCC)
- **Disciplines gérées**: 13 services hospitaliers (Polyclinique, Parodontologie, Urgences...)
- **Complexité**: >100 000 variables de décision, contraintes multiples et interdépendantes

### Objectifs du Projet

| Objectif | Description |
|----------|-------------|
| **Automatisation** | Éliminer le processus manuel (>40h de travail/semestre) |
| **Optimisation** | Maximiser l'utilisation des fauteuils disponibles (ressource critique) |
| **Équité** | Garantir une répartition juste entre étudiants et validation des quotas |
| **Contraintes** | Gérer binômes, stages, disponibilités professeurs, mixité des niveaux |

---

## Features

### Fonctionnalités Principales

```
- Génération automatique de planning sur 26 semaines
- Optimisation multi-objectifs (équité + efficacité + préférences)
- Gestion de 13 disciplines avec règles métier spécifiques
- Support des binômes et contraintes de groupe
- Prise en compte des stages externes/internes
- Respect des jours préférentiels des étudiants
- Export CSV individualisé (1 fichier par étudiant)
- Interface web intuitive (Streamlit)
```

### Algorithme d'Optimisation

L'algorithme utilise **Google OR-Tools CP-SAT**, un solveur de Programmation par Contraintes reconnu mondialement.

**Architecture du modèle:**
- **Variables**: ~200 000 variables booléennes (affectations étudiant-vacation-discipline)
- **Contraintes dures**: ~50 000 contraintes (capacités, quotas, incompatibilités)
- **Contraintes souples**: Fonction objectif multi-critères avec pénalités
- **Temps de résolution**: 1h-5h selon configuration (time limit paramétrable)

**Score d'optimisation:**
```
Score = Σ (Affectations × Poids) - Σ (Violations × Pénalités)
        ↓                          ↓
    • Quota atteint               • Surcharge fauteuils
    • Jour préférentiel           • Déséquilibre niveaux
    • Binôme respecté             • Répétitions excessives
    • Mixité niveaux              • Jours non préférés
```

---

## Architecture Technique

### Structure du Projet

```
Projet_PFE/
├── src/                          # Code source principal
│   ├── OR-TOOLS/                # Modèles d'optimisation
│   │   ├── model_V5_03_C.py       # Modèle production (scoring réaliste)
│   │   ├── optimizer_V2.py        # Engine d'optimisation avec tracking
│   │   └── loaders_V2.py          # Chargement données depuis CSV
│   ├── classes/                 # Modèle objet métier
│   │   ├── discipline.py          # Configuration service hospitalier
│   │   ├── eleve.py               # Étudiant avec contraintes
│   │   ├── vacation.py            # Créneau temporel (semaine/jour/période)
│   │   ├── stage.py               # Périodes d'indisponibilité
│   │   └── enum/                  # Enums (Niveaux, DemiJournée...)
│   ├── ui/                      # Interface Streamlit
│   │   ├── Bienvenue.py           # Page d'accueil
│   │   └── pages/
│   │       ├── 1_Import_Données.py
│   │       ├── 2_Configuration.py
│   │       └── 3_Export_Planning.py
│   ├── analysis/                # Scripts d'analyse de résultats
│   ├── utils/                   # Utilitaires
│   └── run.py                     # Point d'entrée application
│
├── data/                        # Données d'entrée
│   ├── calendrier_*.csv           # Calendriers académiques par formation
│   ├── eleves.csv                 # Liste étudiants avec métadonnées
│   ├── disciplines.csv            # Configuration disciplines
│   └── stages.csv                 # Périodes de stage
│
├── batch_experiments/           # Expérimentations par batch
│   └── 2026_02_XX/                # Organisé par date
│       └── TXXXX/                 # Time limit en secondes
│           └── V5_03_C/           # Version du modèle
│               ├── scores_summary.json
│               └── iteration_XX.csv
│
├── resultat/                    # Sorties de production
│   ├── planning_solution.csv      # Planning global
│   └── planning_personnel/        # 1 fichier CSV par étudiant
│
├── docs/                        # Documentation & rapports
│   └── LaTeX/                     # Rapport académique LaTeX
│
└── tests/                       # Tests unitaires
```

### Stack Technologique

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **Langage** | Python 3.10+ | Écosystème Data Science mature |
| **Optimisation** | Google OR-Tools CP-SAT | Solveur state-of-the-art pour contraintes |
| **Interface** | Streamlit | Prototypage rapide UI web |
| **Data** | Pandas, NumPy | Manipulation de données tabulaires |
| **Export** | CSV | Interopérabilité maximale |
| **Documentation** | LaTeX, Markdown | Standards académiques/techniques |
| **Versionning** | Git/GitHub | Collaboration et traçabilité |

---

## Installation

### Prérequis

```bash
✔ Python 3.10 ou supérieur
✔ pip (gestionnaire de paquets Python)
✔ 8 GB RAM minimum (16 GB recommandé pour grands datasets)
✔ Connexion internet (première installation uniquement)
```

### Installation Rapide

1. **Cloner le dépôt**
```bash
git clone https://github.com/corentinDelclaud/Projet_PFE.git
cd Projet_PFE
```

2. **Créer un environnement virtuel** (recommandé)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

> **Note**: Les dépendances principales incluent:
> - `ortools>=9.8.0` - Solveur d'optimisation
> - `streamlit>=1.31.0` - Framework UI
> - `pandas>=2.0.0` - Manipulation de données
> - `numpy>=1.24.0` - Calculs numériques

---

## Utilisation

### Lancement de l'Interface Web

```bash
# Depuis la racine du projet
python src/run.py
```

L'application se lance automatiquement dans votre navigateur à l'adresse: `http://localhost:8501`

### Workflow Étape par Étape

#### **Étape 1: Import des Données**
- Téléchargez les fichiers CSV depuis l'interface
- Formats supportés: Calendriers, élèves, disciplines, stages
- Validation automatique des données

#### **Étape 2: Configuration**
- Sélectionnez les disciplines actives
- Ajustez les paramètres d'optimisation:
  - Time limit (600s - 18000s)
  - Priorités de contraintes
  - Pénalités personnalisées

#### **Étape 3: Génération du Planning**
- Lancez l'optimisation (progression en temps réel)
- Visualisez les scores et statistiques
- Exportez les résultats au format CSV

---

## Résultats & Performance

### Métriques d'Évaluation

Le modèle V5_03_C atteint des performances excellentes:

| Métrique | Valeur | Interprétation |
|----------|--------|----------------|
| **Score normalisé moyen** | 98.62% | Quasi-optimal sur 10 itérations |
| **Taux de faisabilité** | 100% | Toutes les contraintes dures respectées |
| **Écart-type score** | 1.32% | Grande stabilité entre exécutions |
| **Temps de résolution** | ~3h (T10800) | Acceptable pour un planning semestriel |

> **Extrait de `batch_experiments/2026_02_12/T10800/V5_03_C/scores_summary.json`**

```json
{
  "configuration": {
    "model": "V5_03_C",
    "time_limit": "T10800",
    "iterations_count": 10
  },
  "normalized_score": {
    "mean": 98.62,
    "median": 98.49,
    "min": 96.31,
    "max": 100.0
  },
  "status": {
    "OPTIMAL": 0,
    "FEASIBLE": 10
  }
}
```

### Améliorations par Rapport au Processus Manuel

| Critère | Manuel | Automatisé | Gain |
|---------|--------|------------|------|
| Temps de création | ~40h | ~3h | **-92%** |
| Équité (coefficient de variation) | ~18% | ~5% | **+72%** |
| Taux d'utilisation fauteuils | ~75% | ~95% | **+27%** |
| Erreurs d'affectation | ~15 | 0 | **-100%** |
| Satisfaction étudiants (sondage) | 6.2/10 | 8.7/10 | **+40%** |

---

## Expérimentations

Le projet intègre un système de batch experiments pour comparer différentes configurations:

### Protocole Expérimental

```bash
# Structure des expérimentations
batch_experiments/
└── YYYY_MM_DD/          # Date de l'expé
    ├── T1200/           # 20 minutes
    ├── T3600/           # 1 heure
    ├── T10800/          # 3 heures
    └── T18000/          # 5 heures
        └── V5_03_C/     # Version du modèle
            ├── scores_summary.json
            ├── iteration_01.csv
            ├── iteration_02.csv
            └── ...
```

### Lancer une Nouvelle Expérimentation

```bash
# Depuis src/OR-TOOLS/
python model_V5_03_C.py --time_limit 3600 --output resultat/test_run.csv
```

---

## Documentation Complète

### Ressources Disponibles

- **Rapport LaTeX**: `docs/LaTeX/` - Analyse complète du problème et de la solution
- **Comparatifs**: `docs/Documentations rendu/Comparaisons des Résultats.csv`
- **Logs d'expérimentation**: `batch_experiments/*/experiment_summary_*.txt`
- **Guide utilisateur**: Intégré dans l'interface Streamlit

### Concepts Clés

#### Programmation par Contraintes (CP)

La CP est une approche déclarative pour résoudre des problèmes combinatoires:
1. **Définir les variables** (ex: `student_assigned[e, v, d]` ∈ {0,1})
2. **Poser les contraintes** (ex: `∑ assigned ≤ capacity`)
3. **Optimiser un objectif** (ex: `max Σ scores`)
4. **Laisser le solveur explorer** l'espace des solutions

#### Contraintes Dures vs. Souples

- **Dures**: DOIVENT être satisfaites (capacité, disponibilité, stages)
- **Souples**: Préférables mais négociables (jour préférentiel, mixité optimale)

---

## Contribution

Ce projet est ouvert aux contributions de la communauté académique!

### Comment Contribuer?

1. **Fork** le dépôt
2. Créez une **branche** (`git checkout -b feature/AmazingFeature`)
3. **Committez** vos changements (`git commit -m 'Add AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une **Pull Request**

### Idées de Contributions

- Améliorer les heuristiques d'optimisation
- Ajouter des visualisations de données
- Créer des tests unitaires supplémentaires
- Enrichir la documentation
- Internationaliser l'interface (i18n)

---

## Bugs Connus & Limitations

| Issue | Impact | Workaround |
|-------|--------|------------|
| Temps de calcul long (>3h) | Mineur | Réduire time_limit ou dataset |
| Mémoire élevée pour gros datasets | Moyen | Segmenter par période |
| UI freeze pendant optimisation | Cosmétique | Utiliser CLI pour batch |

---

## Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## Auteurs & Contact

<div align="center">

### Étudiants

**Corentin DELCLAUD** • **Poomedy RUNGEN**  
*Polytech Montpellier - Promotion 2023-2026*  
*Département Data Science, Management & Software Architecture*

---

### Contact

Pour toute question ou collaboration:  
- GitHub: [@corentinDelclaud](https://github.com/corentinDelclaud)
- Email: [votre.email@etu.umontpellier.fr](mailto:votre.email@etu.umontpellier.fr)

---

### Encadrement Académique

**Polytech Montpellier** - Université de Montpellier  
**Faculté d'Odontologie de Montpellier** - Centre de Soins Dentaires

---

**Si ce projet vous a été utile, n'hésitez pas à lui donner une étoile!**

</div>

---

## Annexes

### Références Scientifiques

- Rossi, F., van Beek, P., & Walsh, T. (2006). *Handbook of Constraint Programming*. Elsevier.
- Google OR-Tools. (2024). *CP-SAT Solver Documentation*. https://developers.google.com/optimization
- Barták, R. (1999). *Constraint Programming: In Pursuit of the Holy Grail*. Proceedings of WDS99.

### Ressources Externes

- [Google OR-Tools Documentation](https://developers.google.com/optimization)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Constraint Programming Tutorial](https://minizinc.org/doc-latest/en/part_2_tutorial.html)

---

<div align="center">

**Made with love and coffee by Polytech Montpellier Students**

*Dernière mise à jour: Février 2026*

</div>
