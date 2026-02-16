# Guide de Documentation pour Développeurs

## Objectif

Ce document explique les standards de commentaires et de documentation utilisés dans le projet. Si vous reprenez ce code, respectez ces conventions pour maintenir la cohérence et la lisibilité.

---

## Structure de Documentation

### 1. **Docstrings de Module** (En-tête de fichier)

Chaque fichier Python commence par une docstring triple-quote décrivant:
- Le rôle du module
- Les concepts clés qu'il implémente
- L'auteur et la version (optionnel)

```python
"""
Module: nom_du_fichier.py
Description courte du rôle du module.

Description détaillée expliquant les concepts, l'architecture,
et les interactions avec d'autres modules.

Author: Votre Nom
Date: 2025-2026
Version: V5_03_C
"""
```

### 2. **Docstrings de Classe**

Format standard pour documenter une classe:

```python
class MaClasse:
    """
    Description concise en une ligne.
    
    Description détaillée expliquant le rôle de la classe,
    son utilisation, et sa place dans l'architecture.
    
    Attributes:
        attribut1 (type): Description de l'attribut
        attribut2 (type): Description de l'attribut
        
    Example:
        >>> obj = MaClasse(param=value)
        >>> obj.methode()
        
    Note:
        Informations importantes pour l'utilisation.
    """
```

### 3. **Docstrings de Méthode**

Format Google Style pour les méthodes:

```python
def ma_methode(self, param1: int, param2: str = "default") -> bool:
    """
    Description courte de ce que fait la méthode.
    
    Description détaillée si nécessaire, expliquant la logique,
    les cas particuliers, ou les effets de bord.
    
    Args:
        param1: Description du premier paramètre
        param2: Description du deuxième paramètre (optionnel)
        
    Returns:
        bool: Description de la valeur de retour
        
    Raises:
        ValueError: Quand le paramètre est invalide
        KeyError: Quand la clé n'existe pas
        
    Example:
        >>> obj.ma_methode(42, "test")
        True
        
    Note:
        Informations sur les cas limites ou optimisations.
    """
```

---

## Types de Commentaires

### Commentaires Inline (sur la ligne)

Utilisés avec parcimonie pour clarifier une ligne complexe:

```python
result = (value * coefficient) / base  # Normalisation du score [0-100]
```

### Commentaires Block (au-dessus du code)

Pour expliquer une section de code complexe:

```python
# === PHASE 1: CHARGEMENT DES DONNÉES ===
# On charge d'abord les élèves, puis leurs stages pour calculer
# les indisponibilités. L'ordre est important car les stages
# référencent les IDs des élèves.
eleves = load_students_from_csv(path)
stages = load_stages_from_csv(path, eleves)
```

### Commentaires TODO/FIXME/NOTE

Pour marquer des points d'attention:

```python
# TODO: Optimiser cette boucle (complexité O(n²) actuellement)
# FIXME: Bug quand nb_eleves = 0, ajouter validation
# NOTE: Cette fonction est thread-safe
# HACK: Workaround temporaire, à remplacer par vraie solution
```

---

## Style et Bonnes Pratiques

### Recommandations

1. **Expliquer le "Pourquoi", pas le "Quoi"**
   ```python
   # ❌ Mauvais: on incrémente i
   i += 1
   
   # ✅ Bon: on passe au prochain créneau (indices 0-9)
   creneau_index += 1
   ```

2. **Commenter les Décisions Non-Évidentes**
   ```python
   # On utilise un set plutôt qu'une liste pour éviter les doublons
   # et améliorer la performance des lookups (O(1) vs O(n))
   ids_uniques = set(eleves_ids)
   ```

3. **Documenter les Formats de Données**
   ```python
   """
   Format attendu pour le CSV eleves:
   id_eleve, id_binome, annee, ...
   4011, 401, 4, ...
   4012, 401, 4, ...
   """
   ```

4. **Expliquer les Constantes Magiques**
   ```python
   # 10 créneaux = 5 jours × 2 demi-journées (Lun-Ven, Matin+Aprem)
   NB_CRENEAUX_HEBDO = 10
   
   # Bonus de 100 points si jour préférentiel respecté
   BONUS_JOUR_PREF = 100
   ```

### À Éviter

1. **Commentaires Redondants**
   ```python
   # Ne pas faire ça
   # Initialise x à 0
   x = 0
   ```

2. **Commentaires Périmés**
   ```python
   # Le code a changé mais pas le commentaire
   # Calcule la moyenne des scores
   total = sum(scores)  # En fait on fait juste la somme!
   ```

3. **Code Commenté en Production**
   ```python
   # Si le code n'est plus utilisé, supprimez-le (Git garde l'historique)
   # result = old_calculation(x, y)
   result = new_optimized_calculation(x, y)
   ```

---

## Documentation des Modules Clés

### **classes/**
Contient les entités métier du domaine:
- `eleve.py`: Étudiant avec ses contraintes
- `discipline.py`: Service hospitalier avec ses règles
- `vacation.py`: Créneau temporel élémentaire
- `stage.py`: Période d'indisponibilité

**Commentaires requis:**
- Docstring de classe avec exemple d'utilisation
- Explication des attributs (surtout les contraintes complexes)
- Validation des paramètres dans __init__

### **OR-TOOLS/**
Moteur d'optimisation et configuration:
- `model_V5_03_C.py`: Définition du problème CP-SAT
- `optimizer_V2.py`: Orchestrateur de résolution
- `loaders_V2.py`: Chargement données CSV

**Commentaires requis:**
- Explication des contraintes CP (formules mathématiques)
- Justification des poids/pénalités
- Documentation des formats d'entrée/sortie

### **ui/**
Interface utilisateur Streamlit:
- `Bienvenue.py`: Page d'accueil
- `pages/`: Workflow en 3 étapes

**Commentaires requis:**
- Explication du flow utilisateur
- Validation des entrées
- Gestion des erreurs côté UI

---

## Exemples de Fichiers Bien Commentés

Consultez ces fichiers pour voir les standards appliqués:

1. **`src/classes/eleve.py`** - Classe simple, bien documentée
2. **`src/classes/discipline_COMMENTED.py`** - Classe complexe avec commentaires exhaustifs
3. **`src/classes/vacation.py`** - Documentation minimaliste mais efficace

---

## Outils de Documentation

### Génération de Documentation

Pour générer une documentation HTML à partir des docstrings:

```bash
# Installer pdoc
pip install pdoc3

# Générer la doc HTML
pdoc --html --output-dir docs/api src/classes src/OR-TOOLS

# Serveur local pour prévisualiser
pdoc --http localhost:8080 src/
```

### Vérification de Qualité

```bash
# Vérifier que toutes les fonctions publiques ont une docstring
pylint src/ --disable=all --enable=missing-docstring

# Vérifier la conformité PEP257 (docstring conventions)
pydocstyle src/
```

---

## Checklist pour Code Review

Avant de commit, vérifiez:

- [ ] Tous les modules ont une docstring d'en-tête
- [ ] Toutes les classes publiques ont une docstring
- [ ] Toutes les méthodes publiques ont une docstring (Args/Returns)
- [ ] Les types sont annotés (Python 3.10+ type hints)
- [ ] Les constantes magiques sont expliquées
- [ ] Les sections complexes ont des commentaires block
- [ ] Pas de code commenté inutile
- [ ] Les TODO sont datés et assignés si possible

---

## Ressources Externes

- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [NumPy Docstring Standard](https://numpydoc.readthedocs.io/en/latest/format.html)
- [Real Python - Documenting Python Code](https://realpython.com/documenting-python-code/)

---

## Conseils pour les Nouveaux Développeurs

1. **Lisez d'abord, codez ensuite**
   - Parcourez `README2.md` pour la vue d'ensemble
   - Explorez `src/classes/` pour comprendre le modèle métier
   - Regardez `model_V5_03_C.py` pour la logique d'optimisation

2. **Testez vos modifications**
   - Lancez l'interface: `python src/run.py`
   - Testez avec un petit dataset avant la prod
   - Vérifiez les logs d'optimisation

3. **Documentez au fur et à mesure**
   - N'attendez pas la fin pour documenter
   - Si vous ne comprenez pas un code, commentez-le après l'avoir compris
   - Mettez à jour les commentaires si vous changez la logique

4. **Demandez de l'aide**
   - Les issues GitHub sont là pour ça
   - Contactez les auteurs originaux si bloqué
   - Consultez la documentation OR-Tools si problème de contraintes

---

**Bonne continuation sur le projet!**

*Dernière mise à jour: Février 2026*
