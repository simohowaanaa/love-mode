"""
Launcher : vérifie les dépendances puis lance l'effet (avec la confirmation).
"""
import subprocess
import sys
import importlib


def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", package])


def check_dependencies():
    # nom pip -> nom d'import
    dependencies = {"Pillow": "PIL"}
    missing = []
    for pip_name, import_name in dependencies.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print(f"📦 Installation de {', '.join(missing)}...")
        for pip_name in missing:
            install_package(pip_name)
    return True


if __name__ == "__main__":
    # Dans l'exe figé (PyInstaller), les dépendances sont déjà embarquées :
    # pas de pip au runtime (sys.executable = l'exe, pas Python).
    if not getattr(sys, "frozen", False):
        check_dependencies()
    import love_mode          # PyInstaller embarque ce module automatiquement
    love_mode.main()          # main() = confirmation + launch_all
