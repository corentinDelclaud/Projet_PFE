import sys
import os
import csv
import random

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def generate_calendar():
    # Définition du chemin vers le dossier data
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    os.makedirs(output_dir, exist_ok=True)
    csv_file = os.path.join(output_dir, 'mock_calendrier.csv')

    # Définition des colonnes
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    moments = ["Matin", "ApresMidi"]
    
    # Construction de l'en-tête: Semaine, Lundi_Matin, Lundi_ApresMidi, ...
    header = ["Semaine"]
    for j in jours:
        for m in moments:
            header.append(f"{j}_{m}")

    print(f"Génération du calendrier dans : {csv_file}")

    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        # Génération des 52 semaines
        for semaine in range(1, 53):
            # Création d'une ligne vide pour chaque vacation (ou valeur par défaut si besoin)
            # Ici on laisse vide pour que l'utilisateur puisse remplir, ou "Disponible" par défaut
            row = [semaine] + [""] * 10
            writer.writerow(row)

    print("Fichier calendrier.csv généré avec succès.")

if __name__ == "__main__":
    generate_calendar()



