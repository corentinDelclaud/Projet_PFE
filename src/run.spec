# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, copy_metadata
import sys
import os
from pathlib import Path

python_env = sys.prefix

# Collecter les données Streamlit
datas = [(f"{python_env}/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/streamlit/runtime", "./streamlit/runtime")]
datas += collect_data_files("streamlit")
datas += copy_metadata("streamlit")

# Chemin de base du projet
spec_root = Path(SPECPATH)  # Dossier contenant run.spec (src/)
project_root = spec_root.parent  # Dossier parent (Projet_PFE/)

print(f"SPECPATH: {spec_root}")
print(f"Project root: {project_root}")

ui_path = spec_root / 'ui'
if ui_path.exists():
    datas += [(str(ui_path), 'ui')]
    print(f"✓ Added ui from: {ui_path}")

# AJOUTER le dossier utils
utils_path = spec_root / 'utils'
if utils_path.exists():
    datas += [(str(utils_path), 'utils')]
    print(f"✓ Added utils from: {utils_path}")

# NOTE: Le dossier 'data' n'est PAS inclus dans le bundle car il doit être
# modifiable (lecture/écriture des CSV). L'utilisateur doit placer le dossier
# 'data' à côté de l'exécutable dans dist/
print(f"ℹ️  INFO: Le dossier 'data' doit être placé à côté de l'exécutable")
print(f"   Emplacement attendu: dist/data/ (à côté de l'exécutable)")

# NOTE: Le dossier 'resultat' sera créé automatiquement par l'application
# à côté de l'exécutable si nécessaire
print(f"ℹ️  INFO: Le dossier 'resultat' sera créé automatiquement")


# Ajouter les autres dossiers (chercher dans project_root/src/)
folders_to_add = ['classes', 'formatters', 'OR-TOOLS']
for folder in folders_to_add:
    # Essayer dans src/ d'abord
    folder_path = spec_root / folder
    if folder_path.exists():
        datas += [(str(folder_path), folder)]
        print(f"✓ Added {folder} from: {folder_path}")
    # Sinon essayer dans le parent
    else:
        folder_path = project_root / folder
        if folder_path.exists():
            datas += [(str(folder_path), folder)]
            print(f"✓ Added {folder} from: {folder_path}")
        else:
            print(f"✗ {folder} not found at: {folder_path}")

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[str(spec_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Streamlit
        'streamlit', 
        'streamlit.web.cli',
        # Data processing
        'pandas',
        'openpyxl',
        # OR-Tools
        'ortools',
        'ortools.sat',
        'ortools.sat.python',
        'ortools.sat.python.cp_model',
        # OR-TOOLS modules (nouveau modèle optimizer)
        'optimizer',
        'loaders',
        'config_manager',
        'exporter',
        'app',
        # Classes
        'classes',
        'classes.affectation',
        'classes.binome',
        'classes.calendar',
        'classes.cours',
        'classes.discipline',
        'classes.eleve',
        'classes.jour_preference',
        'classes.periode',
        'classes.stage',
        'classes.vacation',
        # Enums
        'classes.enum',
        'classes.enum.demijournee',
        'classes.enum.niveaux',
        'classes.enum.types_binome',
        # Formatters
        'formatters',
        'formatters.generate_formatted_fiche_appel',
        'formatters.generate_formatted_fiche_appel_custom',
        'formatters.generate_formatted_student_TT',
        'formatters.generate_formatted_student_TT_custom',
        # Utils
        'utils',
        'utils.logger',
        'utils.paths',
        # Data generators
        'data',
        'data.generate_student_code',
        'data.generate_mock_students_csv',
        'data.generate_mock_calendar_csv',
        'data.generate_mock_stages_csv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PlanningStagesDentaires',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)