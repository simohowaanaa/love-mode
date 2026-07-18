import tkinter as tk
from tkinter import messagebox
import ctypes
import os
import sys
import json
import random
import winreg
import threading

try:
    import winsound            # intégré à Windows, pas une dépendance externe
except ImportError:
    winsound = None

# ============================================
# Réglages
# ============================================
DUREE_SECONDES = 600          # 10 minutes
MESSAGE = "Sorry but I love u"
PRENOM = "mon amour"          # <-- mets le prenom ici
HEARTS = ["❤️", "\U0001f495", "\U0001f497", "\U0001f496", "♥️"]

# Constantes API Windows
SPI_GETDESKWALLPAPER = 0x0073
SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATE = 0x03            # SPIF_UPDATEINIFILE | SPIF_SENDCHANGE

# Attributs de fichier
FILE_ATTRIBUTE_READONLY = 0x1
FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4
FILE_ATTRIBUTE_NORMAL = 0x80
INVALID_ATTRS = 0xFFFFFFFF

# Rafraîchissement du shell
SHCNE_ASSOCCHANGED = 0x08000000
SHCNE_UPDATEDIR = 0x00001000
SHCNE_UPDATEITEM = 0x00002000
SHCNF_IDLIST = 0x0000
SHCNF_PATHW = 0x0005

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
shell32 = ctypes.windll.shell32

# Emplacements des fichiers de travail
HEART_ICO = os.path.join(os.environ["TEMP"], "love_heart.ico")
BACKUP_JSON = os.path.join(os.environ["TEMP"], "love_icons_backup.json")
CREATED_JSON = os.path.join(os.environ["TEMP"], "love_created_folders.json")

# Dossiers "KNGHIK" à créer sur le bureau
NB_DOSSIERS = 100
NOM_AFFICHE = "KNBGHIK"


# ============================================
# 1. Changer les titres des fenêtres
# ============================================
def change_window_texts():
    """Remplace le titre de toutes les fenêtres visibles."""
    def callback(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                user32.SetWindowTextW(hwnd, MESSAGE + " ❤️")
        return True

    cb_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(cb_type(callback), 0)


# ============================================
# 2. Overlay de cœurs (plein écran, transparent)
# ============================================
def build_heart_overlay(root):
    """Crée une couche transparente avec des cœurs qui tombent. Retourne le Toplevel."""
    overlay = tk.Toplevel(root)
    overlay.title("❤️")
    overlay.attributes("-topmost", True)
    overlay.overrideredirect(True)          # sans bordure
    w, h = overlay.winfo_screenwidth(), overlay.winfo_screenheight()
    overlay.geometry(f"{w}x{h}+0+0")
    overlay.configure(bg="white")
    overlay.attributes("-transparentcolor", "white")

    # Chaque cœur : [label, x, y, vitesse, oscillation, phase]
    hearts = []
    for _ in range(70):
        lbl = tk.Label(
            overlay,
            text=random.choice(HEARTS),
            font=("Segoe UI Emoji", random.randint(15, 38)),
            bg="white",
        )
        x = random.randint(0, w - 50)
        y = random.randint(-h, 0)           # démarre au-dessus de l'écran
        lbl.place(x=x, y=y)
        hearts.append([lbl, float(x), float(y),
                       random.uniform(2.0, 7.0),      # vitesse de chute
                       random.uniform(0.5, 2.0),      # amplitude du balancement
                       random.uniform(0, 6.28)])      # phase

    def animate():
        for item in hearts:
            lbl, x, y, speed, amp, phase = item
            y += speed
            phase += 0.15
            x += amp * 0.6 * (1 if int(phase) % 2 else -1)  # petit balancement
            if y > h:                       # ressort en haut
                y = random.uniform(-60, -10)
                x = random.randint(0, w - 50)
            item[1], item[2], item[5] = x, y, phase
            lbl.place(x=int(x), y=int(y))
        overlay._anim_job = overlay.after(40, animate)      # ~25 img/s

    animate()
    return overlay


# ============================================
# 3. Popup message
# ============================================
def build_popup(root):
    """Crée la fenêtre popup rose. Retourne le Toplevel."""
    win = tk.Toplevel(root)
    win.title("❤️ COEUR ❤️")
    win.geometry("500x350")
    win.configure(bg="#FFB6C1")
    win.attributes("-topmost", True)

    tk.Label(
        win, text=f"{PRENOM},", font=("Segoe UI", 22, "italic"),
        bg="#FFB6C1", fg="#C71585",
    ).pack(pady=(25, 0))

    tk.Label(
        win, text=MESSAGE, font=("Segoe UI", 32, "bold"),
        bg="#FFB6C1", fg="#FF1493",
    ).pack(pady=(5, 20))

    frame = tk.Frame(win, bg="#FFB6C1")
    frame.pack()
    for i in range(20):
        tk.Label(
            frame, text=random.choice(HEARTS),
            font=("Segoe UI Emoji", random.randint(14, 28)), bg="#FFB6C1",
        ).grid(row=i // 5, column=i % 5, padx=10, pady=5)

    tk.Label(
        win, text="Ceci disparaitra dans 10 minutes ❤️",
        font=("Segoe UI", 12), bg="#FFB6C1", fg="#FF1493",
    ).pack(pady=20)
    return win


# ============================================
# 4. Fond d'écran (avec sauvegarde + restauration)
# ============================================
def get_current_wallpaper():
    buf = ctypes.create_unicode_buffer(260)
    user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 260, buf, 0)
    return buf.value


def set_wallpaper(path):
    user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, path, SPIF_UPDATE)


def make_love_wallpaper():
    """Génère l'image du fond d'écran. Retourne le chemin, ou None si Pillow absent."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow n'est pas installe : le fond d'ecran ne sera pas change.")
        return None

    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    img = Image.new("RGB", (w, h), color="#FFB6C1")
    draw = ImageDraw.Draw(img)

    def load_font(size):
        try:
            return ImageFont.truetype("arial.ttf", size)
        except OSError:
            return ImageFont.load_default()

    def centre(text, font, y):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) // 2, y), text, font=font, fill="#FF1493")

    big, small = load_font(70), load_font(46)
    centre(f"{PRENOM},", small, h // 2 - 90)
    centre(MESSAGE, big, h // 2 - 20)
    centre("<3", small, h // 2 + 70)

    path = os.path.join(os.environ["TEMP"], "love_wallpaper.bmp")
    img.save(path)
    return path


# ============================================
# 4bis. VRAI changement des icônes de dossiers du bureau
# ============================================
def make_heart_icon():
    """Génère un .ico en forme de cœur. Retourne le chemin, ou None si Pillow absent."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow n'est pas installe : les icones ne seront pas changees.")
        return None

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    red = (255, 20, 90, 255)
    # Deux cercles + un triangle = un cœur
    r = size // 4
    d.ellipse([size * 0.10, size * 0.15, size * 0.10 + 2 * r, size * 0.15 + 2 * r], fill=red)
    d.ellipse([size * 0.90 - 2 * r, size * 0.15, size * 0.90, size * 0.15 + 2 * r], fill=red)
    d.polygon(
        [(size * 0.08, size * 0.42), (size * 0.92, size * 0.42), (size * 0.5, size * 0.92)],
        fill=red,
    )
    img.save(HEART_ICO, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    return HEART_ICO


def get_desktop_path():
    """Chemin réel du bureau (gère la redirection OneDrive) via le registre."""
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
    ) as k:
        raw, _ = winreg.QueryValueEx(k, "Desktop")
    return os.path.expandvars(raw)


def refresh_shell():
    """Force Windows à recharger les icônes (global)."""
    shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)


def notify_folder(path):
    """Force Explorer à relire le desktop.ini d'un dossier précis."""
    shell32.SHChangeNotify(SHCNE_UPDATEDIR, SHCNF_PATHW, ctypes.c_wchar_p(path), None)


def _set_attrs(path, attrs):
    kernel32.SetFileAttributesW(ctypes.c_wchar_p(path), attrs)


def _get_attrs(path):
    a = kernel32.GetFileAttributesW(ctypes.c_wchar_p(path))
    return None if a == INVALID_ATTRS else a


def change_folder_icons():
    """Met une icône cœur sur chaque dossier du bureau. Sauvegarde l'état d'origine.

    Retourne True si au moins un dossier a été modifié."""
    ico = make_heart_icon()
    if not ico:
        return False

    desktop = get_desktop_path()
    backup = []  # liste de {folder, folder_attrs, ini_existed, ini_bytes(b64?), ini_attrs}

    ini_content = (
        "[.ShellClassInfo]\r\n"
        f"IconResource={ico},0\r\n"
        "[ViewState]\r\n"
        "Mode=\r\n"
        "Vid=\r\n"
        "FolderType=Generic\r\n"
    )

    for name in os.listdir(desktop):
        folder = os.path.join(desktop, name)
        if not os.path.isdir(folder):
            continue  # on ignore les fichiers et les raccourcis .lnk

        ini = os.path.join(folder, "desktop.ini")
        entry = {
            "folder": folder,
            "folder_attrs": _get_attrs(folder),
            "ini_existed": os.path.exists(ini),
            "ini_text": None,
            "ini_attrs": None,
        }
        try:
            if entry["ini_existed"]:
                entry["ini_attrs"] = _get_attrs(ini)
                # On enlève hidden/system pour pouvoir lire/écrire
                _set_attrs(ini, FILE_ATTRIBUTE_NORMAL)
                with open(ini, "r", encoding="utf-8", errors="replace") as f:
                    entry["ini_text"] = f.read()

            with open(ini, "w", encoding="utf-8") as f:
                f.write(ini_content)
            # desktop.ini doit être caché + système
            _set_attrs(ini, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
            # le dossier doit avoir le bit "read-only" ou "system" pour lire desktop.ini
            cur = entry["folder_attrs"] or 0
            _set_attrs(folder, cur | FILE_ATTRIBUTE_READONLY)
            notify_folder(folder)
            backup.append(entry)
        except OSError as e:
            print(f"Impossible de modifier {folder}: {e}")

    # Filet de sécurité : on écrit la sauvegarde sur disque
    with open(BACKUP_JSON, "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)

    refresh_shell()
    return bool(backup)


def restore_folder_icons(backup=None):
    """Remet chaque dossier dans son état d'origine à partir de la sauvegarde."""
    if backup is None:
        if not os.path.exists(BACKUP_JSON):
            print("Aucune sauvegarde d'icones a restaurer.")
            return
        with open(BACKUP_JSON, "r", encoding="utf-8") as f:
            backup = json.load(f)

    for entry in backup:
        folder = entry["folder"]
        ini = os.path.join(folder, "desktop.ini")
        try:
            if entry["ini_existed"]:
                # On restaure l'ancien contenu + ses attributs
                _set_attrs(ini, FILE_ATTRIBUTE_NORMAL)  # pour pouvoir réécrire
                with open(ini, "w", encoding="utf-8") as f:
                    f.write(entry["ini_text"] or "")
                if entry["ini_attrs"] is not None:
                    _set_attrs(ini, entry["ini_attrs"])
            else:
                # Il n'existait pas : on le supprime
                if os.path.exists(ini):
                    _set_attrs(ini, FILE_ATTRIBUTE_NORMAL)
                    os.remove(ini)
            # On remet les attributs d'origine du dossier
            if entry["folder_attrs"] is not None:
                _set_attrs(folder, entry["folder_attrs"])
            notify_folder(folder)
        except OSError as e:
            print(f"Impossible de restaurer {folder}: {e}")

    try:
        os.remove(BACKUP_JSON)
    except OSError:
        pass
    refresh_shell()
    print("Icones restaurees.")


# ============================================
# 4ter. Remplir le bureau de dossiers "KNGHIK" (icône cœur)
# ============================================
def create_knghik_folders():
    """Crée NB_DOSSIERS dossiers vides sur le bureau, tous affichés "KNGHIK"
    avec l'icône cœur. Retourne True si au moins un dossier a été créé."""
    ico = make_heart_icon()
    if not ico:
        return False

    desktop = get_desktop_path()
    created = []

    ini_content = (
        "[.ShellClassInfo]\r\n"
        f"IconResource={ico},0\r\n"
        f"LocalizedResourceName={NOM_AFFICHE}\r\n"
    )

    for i in range(1, NB_DOSSIERS + 1):
        # Nom réel unique sur le disque, mais nom affiché = "KNGHIK"
        folder = os.path.join(desktop, f"{NOM_AFFICHE}_{i:03d}")
        if os.path.exists(folder):
            continue  # on ne touche pas à un dossier déjà présent
        try:
            os.mkdir(folder)
            ini = os.path.join(folder, "desktop.ini")
            with open(ini, "w", encoding="utf-8") as f:
                f.write(ini_content)
            _set_attrs(ini, FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
            _set_attrs(folder, FILE_ATTRIBUTE_READONLY)
            notify_folder(folder)
            created.append(folder)
        except OSError as e:
            print(f"Impossible de creer {folder}: {e}")

    with open(CREATED_JSON, "w", encoding="utf-8") as f:
        json.dump(created, f, ensure_ascii=False, indent=2)

    refresh_shell()
    return bool(created)


def remove_created_folders(created=None):
    """Supprime uniquement les dossiers KNGHIK qu'on a créés (s'ils sont vides)."""
    if created is None:
        if not os.path.exists(CREATED_JSON):
            return
        with open(CREATED_JSON, "r", encoding="utf-8") as f:
            created = json.load(f)

    for folder in created:
        try:
            ini = os.path.join(folder, "desktop.ini")
            if os.path.exists(ini):
                _set_attrs(ini, FILE_ATTRIBUTE_NORMAL)
                os.remove(ini)
            # rmdir échoue si le dossier n'est pas vide -> sécurité
            if os.path.isdir(folder):
                _set_attrs(folder, FILE_ATTRIBUTE_NORMAL)
                os.rmdir(folder)
        except OSError as e:
            print(f"Impossible de supprimer {folder}: {e}")

    try:
        os.remove(CREATED_JSON)
    except OSError:
        pass
    refresh_shell()
    print("Dossiers KNGHIK supprimes.")


# ============================================
# 4quater. Petite mélodie (winsound, intégré à Windows)
# ============================================
def play_melody():
    """Joue une courte mélodie sans bloquer l'interface."""
    if winsound is None:
        return

    def _play():
        # (fréquence Hz, durée ms) — petit air doux
        notes = [(523, 220), (587, 220), (659, 260), (587, 220),
                 (523, 220), (659, 300), (784, 450)]
        for freq, dur in notes:
            try:
                winsound.Beep(freq, dur)
            except RuntimeError:
                break

    threading.Thread(target=_play, daemon=True).start()


# ============================================
# 5. Orchestration (tout dans le thread principal)
# ============================================
def launch_all():
    old_wallpaper = get_current_wallpaper()
    new_wallpaper = make_love_wallpaper()
    if new_wallpaper:
        set_wallpaper(new_wallpaper)

    icons_changed = change_folder_icons()
    folders_created = create_knghik_folders()

    root = tk.Tk()
    root.withdraw()

    overlay = build_heart_overlay(root)
    popup = build_popup(root)

    def tick_titles():
        change_window_texts()
        root._title_job = root.after(500, tick_titles)

    tick_titles()

    play_melody()  # petite mélodie au lancement

    def cleanup():
        play_melody()  # et une à la fin
        try:
            root.after_cancel(root._title_job)
        except Exception:
            pass
        try:
            overlay.after_cancel(overlay._anim_job)
        except Exception:
            pass
        if new_wallpaper and old_wallpaper:
            set_wallpaper(old_wallpaper)
        if icons_changed:
            restore_folder_icons()
        if folders_created:
            remove_created_folders()
        for w in (overlay, popup):
            try:
                w.destroy()
            except tk.TclError:
                pass
        root.destroy()
        print("✅ Fin de l'effet ! Tout est revenu a la normale.")

    root.after(DUREE_SECONDES * 1000, cleanup)
    root.mainloop()


# ============================================
# 6. Point d'entrée
# ============================================
def main():
    # Mode de secours : love_mode.py --restore
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        restore_folder_icons()
        remove_created_folders()
        return

    confirm = messagebox.askyesno(
        "❤️ Babe ❤️",
        "Juste un petit cadeau numérique pour illuminer ta journée autant que tu illumines la mienne. Prêt(e) pour un peu de magie ? ❤️"
    )
    if confirm:
        launch_all()
    else:
        print("Annule !")


if __name__ == "__main__":
    main()
