import streamlit
import streamlit.web.cli as stcli
import os, sys


def resolve_path(path):
    # Gérer à la fois le mode normal et le mode PyInstaller
    if getattr(sys, 'frozen', False):
        # Mode compilé (PyInstaller) - utiliser sys._MEIPASS
        script_dir = sys._MEIPASS
    else:
        # Mode script Python normal
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    resolved_path = os.path.join(script_dir, path)
    return resolved_path


if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("ui/Bienvenue.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())