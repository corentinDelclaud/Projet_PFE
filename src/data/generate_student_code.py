import pandas as pd
import os
import random
from collections import defaultdict

def generate_student_data(nb_dfas01: int, nb_dfas02: int, nb_dftcc: int, zlist: list):
    """
    Génère des données d'étudiants avec codes XYZAB
    
    Format du code:
    - X ∈ [4,6] : année (4=DFAS01, 5=DFAS02, 6=DFTCC)
    - Y ∈ [1,5] : jour de préférence (1=lundi, 2=mardi, 3=mercredi, 4=jeudi, 5=vendredi)
    - Z ∈ zlist : chiffre additionnel défini par l'utilisateur
    - AB ∈ [11,30] : numéro séquentiel
    
    Règles de binômes:
    1. 5ème année (DFAS02) ensemble en priorité
    2. 4ème année (DFAS01) avec 6ème année (DFTCC) en priorité
    3. Binômes de même année si reste
    
    Jour similaire:
    - 0,1 → lundi, 2,3 → mardi, 4,5 → mercredi, 6,7 → jeudi, 8,9 → vendredi
    - jour_similaire ≠ jour_preference (le jour équivalent, pas la valeur)
    """
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    
    print(f"\n{'='*60}")
    print(f"GÉNÉRATION DES DONNÉES ÉTUDIANTS")
    print(f"{'='*60}")
    print(f"DFAS01 (4ème année): {nb_dfas01} étudiants")
    print(f"DFAS02 (5ème année): {nb_dfas02} étudiants")
    print(f"DFTCC  (6ème année): {nb_dftcc} étudiants")
    print(f"TOTAL: {nb_dfas01 + nb_dfas02 + nb_dftcc} étudiants")
    print(f"{'='*60}\n")
    
    # Mappings
    annee_map = {4: 'DFAS01', 5: 'DFAS02', 6: 'DFTCC'}
    jour_map = {1: 'lundi', 2: 'mardi', 3: 'mercredi', 4: 'jeudi', 5: 'vendredi'}
    
    # Fonction pour convertir jour_similaire (0-9) en jour (1-5)
    def jour_similaire_to_jour(js):
        # 0,1→1(lundi), 2,3→2(mardi), 4,5→3(mercredi), 6,7→4(jeudi), 8,9→5(vendredi)
        return (js // 2) + 1
    
    # Créer des étudiants sans binômes ni jours pour l'instant
    students_pool = []
    for year_digit, count in [(4, nb_dfas01), (5, nb_dfas02), (6, nb_dftcc)]:
        for _ in range(count):
            students_pool.append({
                'annee': annee_map[year_digit],
                'annee_digit': year_digit,
                'periode_stage': random.randint(1, 4),
                'periode_stage_ext': 0
            })
    
    total_students = len(students_pool)
    print(f"Étudiants créés: {total_students}\n")
    
    # === CRÉATION DES BINÔMES ===
    print(f"{'='*60}")
    print(f"CRÉATION DES BINÔMES")
    print(f"{'='*60}\n")
    
    # Séparer par année
    dfas01_pool = [s for s in students_pool if s['annee_digit'] == 4]
    dfas02_pool = [s for s in students_pool if s['annee_digit'] == 5]
    dftcc_pool = [s for s in students_pool if s['annee_digit'] == 6]
    
    # Random shuffle pour éviter les biais
    random.shuffle(dfas01_pool)
    random.shuffle(dfas02_pool)
    random.shuffle(dftcc_pool)
    
    binomes = []
    stats = {
        'dfas02_dfas02': 0,
        'dfas01_dftcc': 0,
        'dfas01_dfas01': 0,
        'dftcc_dftcc': 0,
        'dfas02_dftcc': 0,
        'dfas02_dfas01': 0,
        'sans_binome': 0
    }
    
    # PRIORITÉ 1
    # 1. DFAS02 ensemble
    print("PRIORITÉ 1:")
    print("Étape 1: Binômes DFAS02-DFAS02")
    while len(dfas02_pool) >= 2:
        s1 = dfas02_pool.pop(0)
        s2 = dfas02_pool.pop(0)
        binomes.append((s1, s2))
        stats['dfas02_dfas02'] += 1
    print(f"  → {stats['dfas02_dfas02']} binômes créés\n")
    
    # 2. DFAS01 avec DFTCC
    print("Étape 2: Binômes DFAS01-DFTCC")
    while dfas01_pool and dftcc_pool:
        s1 = dfas01_pool.pop(0)
        s2 = dftcc_pool.pop(0)
        binomes.append((s1, s2))
        stats['dfas01_dftcc'] += 1
    print(f"  → {stats['dfas01_dftcc']} binômes créés\n")
    
    # PRIORITÉ 2
    print("PRIORITÉ 2:")
    # 3. DFAS01 ensemble (si reste)
    print("Étape 3: Binômes DFAS01-DFAS01 (restants)")
    while len(dfas01_pool) >= 2:
        s1 = dfas01_pool.pop(0)
        s2 = dfas01_pool.pop(0)
        binomes.append((s1, s2))
        stats['dfas01_dfas01'] += 1
    print(f"  → {stats['dfas01_dfas01']} binômes créés\n")
    
    # 4. DFTCC ensemble (si reste) - mais réserver 1 DFTCC si DFAS02 est impair
    print("Étape 4: Binômes DFTCC-DFTCC (restants)")
    reserve_dftcc = len(dfas02_pool)  # Réserver des DFTCC pour les DFAS02 restants
    while len(dftcc_pool) >= 2 + reserve_dftcc:
        s1 = dftcc_pool.pop(0)
        s2 = dftcc_pool.pop(0)
        binomes.append((s1, s2))
        stats['dftcc_dftcc'] += 1
    print(f"  → {stats['dftcc_dftcc']} binômes créés\n")
    
    # PRIORITÉ 3
    print("PRIORITÉ 3:")
    # 5. DFAS02 avec DFTCC (si DFAS02 impair)
    print("Étape 5: Binômes DFAS02-DFTCC (restants)")
    while dfas02_pool and dftcc_pool:
        s1 = dfas02_pool.pop(0)
        s2 = dftcc_pool.pop(0)
        binomes.append((s1, s2))
        stats['dfas02_dftcc'] += 1
    print(f"  → {stats['dfas02_dftcc']} binômes créés\n")
    
    # 6. DFAS02 avec DFAS01 (si DFAS02 encore restant)
    print("Étape 6: Binômes DFAS02-DFAS01 (restants)")
    while dfas02_pool and dfas01_pool:
        s1 = dfas02_pool.pop(0)
        s2 = dfas01_pool.pop(0)
        binomes.append((s1, s2))
        stats['dfas02_dfas01'] += 1
    print(f"  → {stats['dfas02_dfas01']} binômes créés\n")
    
    # Étudiants sans binôme
    alone = dfas01_pool + dfas02_pool + dftcc_pool
    stats['sans_binome'] = len(alone)
    
    # === RAPPORT STATISTIQUE ===
    print(f"{'='*60}")
    print(f"RAPPORT STATISTIQUE DES BINÔMES")
    print(f"{'='*60}")
    total_pairs = len(binomes)
    print(f"\nNombre total de binômes: {total_pairs}")
    print(f"\n{'Type de binôme':<25} {'Nombre':<10} {'Pourcentage'}")
    print(f"{'-'*60}")
    
    if total_pairs > 0:
        print(f"{'DFAS02-DFAS02':<25} {stats['dfas02_dfas02']:<10} {stats['dfas02_dfas02']/total_pairs*100:>5.1f}%")
        print(f"{'DFAS01-DFTCC':<25} {stats['dfas01_dftcc']:<10} {stats['dfas01_dftcc']/total_pairs*100:>5.1f}%")
        print(f"{'DFAS01-DFAS01':<25} {stats['dfas01_dfas01']:<10} {stats['dfas01_dfas01']/total_pairs*100:>5.1f}%")
        print(f"{'DFTCC-DFTCC':<25} {stats['dftcc_dftcc']:<10} {stats['dftcc_dftcc']/total_pairs*100:>5.1f}%")
        print(f"{'DFAS02-DFTCC':<25} {stats['dfas02_dftcc']:<10} {stats['dfas02_dftcc']/total_pairs*100:>5.1f}%")
        print(f"{'DFAS02-DFAS01':<25} {stats['dfas02_dfas01']:<10} {stats['dfas02_dfas01']/total_pairs*100:>5.1f}%")
    
    print(f"\n{'Étudiants sans binôme':<25} {stats['sans_binome']}")
    print(f"{'='*60}\n")
    
    # === ASSIGNATION DES JOURS DE PRÉFÉRENCE ===
    print(f"{'='*60}")
    print(f"ASSIGNATION DES JOURS DE PRÉFÉRENCE")
    print(f"{'='*60}\n")
    
    # Créer un pool de jours équilibré pour tous les binômes + individus seuls
    total_assignments = total_pairs + len(alone)
    jours_pool = []
    base_count = total_assignments // 5
    remainder = total_assignments % 5
    
    for day in range(1, 6):
        count = base_count + (1 if day <= remainder else 0)
        jours_pool.extend([day] * count)
    
    random.shuffle(jours_pool)
    
    jour_stats = {j: 0 for j in range(1, 6)}
    
    # Assigner aux binômes (les deux membres ont le même jour)
    for s1, s2 in binomes:
        day = jours_pool.pop(0)
        s1['jour_digit'] = day
        s1['jour_preference'] = jour_map[day]
        s2['jour_digit'] = day
        s2['jour_preference'] = jour_map[day]
        jour_stats[day] += 2
    
    # Assigner aux individus seuls
    for s in alone:
        day = jours_pool.pop(0) if jours_pool else random.randint(1, 5)
        s['jour_digit'] = day
        s['jour_preference'] = jour_map[day]
        jour_stats[day] += 1
    
    print("Répartition des jours de préférence:")
    for day in range(1, 6):
        print(f"  {jour_map[day].capitalize():<12} : {jour_stats[day]} étudiants ({jour_stats[day]/total_students*100:.1f}%)")
    print()
    
    # === ASSIGNATION DES JOURS SIMILAIRES ===
    print(f"{'='*60}")
    print(f"ASSIGNATION DES JOURS SIMILAIRES")
    print(f"{'='*60}\n")
    
    # Pool de jours similaires (uniquement les valeurs de zlist) équilibré
    jour_sim_pool = []
    nb_values_zlist = len(zlist)
    base_count_sim = total_students // nb_values_zlist
    remainder_sim = total_students % nb_values_zlist
    
    for idx, js in enumerate(zlist):
        count = base_count_sim + (1 if idx < remainder_sim else 0)
        jour_sim_pool.extend([js] * count)
    
    random.shuffle(jour_sim_pool)
    
    jour_sim_stats = {j: 0 for j in zlist}
    
    # Assigner aux binômes (jour_similaire ≠ jour_preference)
    for s1, s2 in binomes:
        jour_pref = s1['jour_digit']
        
        # Assigner jour_similaire à s1
        found = False
        attempts = 0
        while not found and attempts < 50:
            if not jour_sim_pool:
                jour_sim_pool = list(zlist)
                random.shuffle(jour_sim_pool)
            
            js = jour_sim_pool.pop(0)
            js_jour = jour_similaire_to_jour(js)
            
            if js_jour != jour_pref:
                s1['jour_similaire'] = js
                jour_sim_stats[js] += 1
                found = True
            else:
                jour_sim_pool.append(js)
            attempts += 1
        
        if not found:
            valid_js = [j for j in zlist if jour_similaire_to_jour(j) != jour_pref]
            s1['jour_similaire'] = random.choice(valid_js) if valid_js else zlist[0]
            jour_sim_stats[s1['jour_similaire']] += 1
        
        # Assigner jour_similaire à s2 (peut être le même que s1)
        found = False
        attempts = 0
        while not found and attempts < 50:
            if not jour_sim_pool:
                jour_sim_pool = list(zlist)
                random.shuffle(jour_sim_pool)
            
            js = jour_sim_pool.pop(0)
            js_jour = jour_similaire_to_jour(js)
            
            if js_jour != jour_pref:
                s2['jour_similaire'] = js
                jour_sim_stats[js] += 1
                found = True
            else:
                jour_sim_pool.append(js)
            attempts += 1
        
        if not found:
            valid_js = [j for j in zlist if jour_similaire_to_jour(j) != jour_pref]
            s2['jour_similaire'] = random.choice(valid_js) if valid_js else zlist[0]
            jour_sim_stats[s2['jour_similaire']] += 1
    
    # Assigner aux individus seuls
    for s in alone:
        jour_pref = s['jour_digit']
        
        found = False
        attempts = 0
        
        while not found and attempts < 50:
            if not jour_sim_pool:
                jour_sim_pool = list(zlist)
                random.shuffle(jour_sim_pool)
            
            js = jour_sim_pool.pop(0)
            js_jour = jour_similaire_to_jour(js)
            
            if js_jour != jour_pref:
                s['jour_similaire'] = js
                jour_sim_stats[js] += 1
                found = True
            else:
                jour_sim_pool.append(js)
            
            attempts += 1
        
        if not found:
            valid_js = [j for j in zlist if jour_similaire_to_jour(j) != jour_pref]
            s['jour_similaire'] = random.choice(valid_js) if valid_js else zlist[0]
            jour_sim_stats[s['jour_similaire']] += 1
    
    print(f"Répartition des jours similaires (zlist={zlist}):")
    for js in zlist:
        jour_equiv = jour_map[jour_similaire_to_jour(js)]
        print(f"  {js} ({jour_equiv})<12> : {jour_sim_stats[js]} étudiants ({jour_sim_stats[js]/total_students*100:.1f}%)")
    print()
    
    # Vérification
    violations = 0
    for s1, s2 in binomes:
        if jour_similaire_to_jour(s1['jour_similaire']) == s1['jour_digit']:
            violations += 1
        if jour_similaire_to_jour(s2['jour_similaire']) == s2['jour_digit']:
            violations += 1
    
    for s in alone:
        if jour_similaire_to_jour(s['jour_similaire']) == s['jour_digit']:
            violations += 1
    
    print(f"Contrainte vérifiée:")
    print(f"  Violations jour_similaire = jour_preference: {violations}")
    print()
    
    # === GÉNÉRATION DES CODES ===
    print(f"{'='*60}")
    print(f"GÉNÉRATION DES CODES ÉLÈVES")
    print(f"{'='*60}\n")
    
    code_counter = defaultdict(int)
    all_students = []
    
    for s1, s2 in binomes:
        all_students.extend([s1, s2])
    all_students.extend(alone)
    
    for s in all_students:
        year_digit = s['annee_digit']
        day = s['jour_digit']
        z_digit = random.choice(zlist)
        
        key = (year_digit, day, z_digit)
        code_counter[key] += 1
        seq_num = (code_counter[key] - 1) % 20 + 11
        
        if code_counter[key] > 20:
            # Changer de Z en prenant le suivant dans zlist
            z_idx = zlist.index(z_digit)
            z_digit = zlist[(z_idx + 1) % len(zlist)]
            key = (year_digit, day, z_digit)
            code_counter[key] = 1
            seq_num = 11
        
        s['id_eleve'] = f"{year_digit}{day}{z_digit}{seq_num}"
    
    # Lier les binômes
    for s1, s2 in binomes:
        s1['id_binome'] = s2['id_eleve']
        s2['id_binome'] = s1['id_eleve']
    
    for s in alone:
        s['id_binome'] = s['id_eleve']
    
    print(f"✓ {len(all_students)} codes générés")
    print()
    
    # Créer le DataFrame final
    df = pd.DataFrame(all_students)
    df = df[['id_eleve', 'id_binome', 'jour_preference', 'jour_similaire', 'annee', 'periode_stage', 'periode_stage_ext']]
    
    # Sauvegarder
    output_file = os.path.join(project_root, 'data', 'eleves_with_code.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"✓ Fichier généré: {output_file}")
    print(f"✓ {len(df)} étudiants enregistrés\n")
    
    # Afficher un échantillon
    print("Échantillon des données générées:")
    print(df.head(10).to_string(index=False))
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    # Configuration par défaut
    # Modifier ces valeurs pour changer le nombre d'étudiants par année
    NB_DFAS01 = 100  # 4ème année
    NB_DFAS02 = 81   # 5ème année (impair)
    NB_DFTCC = 80    # 6ème année (moins pour tester DFAS02-DFAS01)
    zlist = [0,4,5,6,8]
    
    generate_student_data(NB_DFAS01, NB_DFAS02, NB_DFTCC,zlist)
