"""
Compile LoveEffect en un exe autonome (dist/LoveEffect.exe).
Utilise le vrai love_mode.py + launcher.py qui sont a cote de ce script.
"""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def install_dependencies():
    for dep in ["pyinstaller", "pillow"]:
        print(f"📦 Installation de {dep}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])


def build():
    # Verifie que les sources existent (pas de placeholder vide)
    for f in ["love_mode.py", "launcher.py"]:
        path = os.path.join(HERE, f)
        if not os.path.exists(path):
            raise SystemExit(f"Fichier manquant : {path}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",                 # mets --noconsole pour cacher le terminal
        "--name", "LoveEffect",
        "--distpath", os.path.join(HERE, "dist"),
        "--workpath", os.path.join(HERE, "build"),
        "--specpath", HERE,
        # love_mode est un vrai import du launcher : PyInstaller le suit tout seul.
        # On force les imports "paresseux" (faits dans des fonctions) :
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._imaging",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageDraw",
        "--hidden-import", "PIL.ImageFont",
        "--hidden-import", "winreg",
        "--paths", HERE,             # pour que love_mode soit trouvable
        os.path.join(HERE, "launcher.py"),
    ]
    subprocess.check_call(cmd)


if __name__ == "__main__":
    print("🚀 Compilation de LoveEffect...")
    install_dependencies()
    build()
    print("✅ Fini ! L'exe est dans dist/LoveEffect.exe")
