import os
import unicodedata
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from tkcalendar import DateEntry
from app.layout_render import create_poster
from app.rules import build_profile, icon_paths, fixed_text_pairs

# Ścieżki bazowe
BASE_DIR   = os.path.dirname(os.path.dirname(__file__)) if __file__.endswith(".py") else os.getcwd()
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

APP_TITLE  = "Generator plakatu – 300 DPI (poziomo)"

def _downloads_dir() -> str:
    # Windows najczęściej: C:\Users\<user>\Downloads
    d = os.path.join(os.path.expanduser("~"), "Downloads")
    return d if os.path.isdir(d) else os.path.expanduser("~")

def _slugify_name(name: str) -> str:
    # usuwanie polskich znaków i znaków specjalnych
    nfkd = unicodedata.normalize("NFKD", name)
    no_diac = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    safe = "".join(ch if (ch.isalnum() or ch in "-_ ") else "" for ch in no_diac)
    safe = "_".join(safe.split())
    return safe or "Imie"

def _collect_missing_assets(prof, paths) -> list[str]:
    """Lekki check – wypiszemy, czego brakuje (nie blokuje renderu)."""
    missing = []
    # pojedyncze ikony
    for key in ("zodiac","element","totem","moon","celtic","china"):
        p = paths.get(key)
        if not p or not os.path.exists(p):
            missing.append(f"{key}: {os.path.basename(p) if p else 'brak pliku'}")
    # cyfry
    ddir = paths.get("digits_dir")
    if ddir and os.path.isdir(ddir):
        for ch in str(prof.birth_num):
            f = os.path.join(ddir, f"{ch}.png")
            if not os.path.exists(f):
                missing.append(f"digit for birth_num: {ch}.png")
        for ch in str(prof.life_path):
            f = os.path.join(ddir, f"{ch}.png")
            if not os.path.exists(f):
                missing.append(f"digit for life_path: {ch}.png")
    else:
        missing.append("digits_dir: brak folderu z cyframi")
    # unikalne
    seen = set(); uniq = []
    for m in missing:
        if m not in seen:
            uniq.append(m); seen.add(m)
    return uniq

def run_app():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title(APP_TITLE)
    root.geometry("1024x680")

    frame = ctk.CTkFrame(root, corner_radius=8, fg_color="white")
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    # ——— Rozmiar ———
    size_label = ctk.CTkLabel(frame, text="Rozmiar (cm):")
    size_var = tk.StringVar(value="21x30")
    size_opt = ctk.CTkOptionMenu(frame, values=["21x30", "30x40"], variable=size_var, width=120)
    size_label.grid(row=0, column=0, sticky="e", padx=6, pady=(10,6))
    size_opt.grid(row=0, column=1, sticky="w", padx=6, pady=(10,6))

    # ——— Imię ———
    name_label = ctk.CTkLabel(frame, text="Imię (Allura):")
    name_entry = ctk.CTkEntry(frame, width=260, placeholder_text="np. Oliwia")
    name_label.grid(row=1, column=0, sticky="e", padx=6, pady=6)
    name_entry.grid(row=1, column=1, sticky="w", padx=6, pady=6)

    # ——— Data urodzenia ———
    date_label = ctk.CTkLabel(frame, text="Data urodzenia:")
    date_entry = DateEntry(frame, date_pattern="yyyy-mm-dd")
    date_label.grid(row=1, column=2, sticky="e", padx=6, pady=6)
    date_entry.grid(row=1, column=3, sticky="w", padx=6, pady=6)

    # ——— Miejscowość ———
    city_label = ctk.CTkLabel(frame, text="Miejscowość (Open Sans):")
    city_entry = ctk.CTkEntry(frame, width=260, placeholder_text="np. Włocławek")
    city_label.grid(row=2, column=0, sticky="e", padx=6, pady=6)
    city_entry.grid(row=2, column=1, columnspan=3, sticky="we", padx=6, pady=6)

    # ——— Tekst stały ———
    texts_pairs = fixed_text_pairs(BASE_DIR)  # lista (line1, line2)
    templ_values = ["(— wybierz —)"] + [f"{i+1}. {a} | {b}" if b else f"{i+1}. {a}"
                                        for i,(a,b) in enumerate(texts_pairs)]
    templ_var = tk.StringVar(value="(— wybierz —)")

    templ_label = ctk.CTkLabel(frame, text="Stały tekst (z listy):")
    templ_menu  = ctk.CTkOptionMenu(frame, values=templ_values, variable=templ_var, width=520)
    templ_label.grid(row=3, column=0, sticky="e", padx=6, pady=(16,6))
    templ_menu.grid(row=3, column=1, columnspan=3, sticky="w", padx=6, pady=(16,6))

    # Podgląd 2 linii – tylko do odczytu
    l1_var = tk.StringVar(value="")
    l2_var = tk.StringVar(value="")
    l1_lab = ctk.CTkLabel(frame, textvariable=l1_var, text_color="gray")
    l2_lab = ctk.CTkLabel(frame, textvariable=l2_var, text_color="gray")
    l1_lab.grid(row=4, column=1, sticky="w", padx=6, pady=(0,2))
    l2_lab.grid(row=5, column=1, sticky="w", padx=6, pady=(0,12))

    def on_pick_template(choice=None):
        sel = templ_var.get()
        if sel == "(— wybierz —)":
            l1_var.set(""); l2_var.set("")
            return
        idx = templ_values.index(sel) - 1
        if 0 <= idx < len(texts_pairs):
            a, b = texts_pairs[idx]
            l1_var.set(a); l2_var.set(b)
        else:
            l1_var.set(""); l2_var.set("")

    templ_menu.configure(command=on_pick_template)

    # ——— Własny tekst (opcjonalny) ———
    own_label = ctk.CTkLabel(frame, text="Własny tekst (opcjonalnie, wielolinijkowy):")
    own_box   = ctk.CTkTextbox(frame, width=520, height=70)
    own_label.grid(row=6, column=0, sticky="e", padx=6, pady=6)
    own_box.grid(row=6, column=1, columnspan=3, sticky="we", padx=6, pady=6)

    # ——— Zapis ———
    out_mode_var = tk.StringVar(value="downloads")  # 'downloads' lub 'custom'
    rb1 = ctk.CTkRadioButton(frame, text="Zapisz w Pobranych (domyślnie)", variable=out_mode_var, value="downloads")
    rb2 = ctk.CTkRadioButton(frame, text="Wybierz folder…", variable=out_mode_var, value="custom")
    rb1.grid(row=7, column=0, columnspan=2, sticky="w", padx=6, pady=(12,4))
    rb2.grid(row=8, column=0, sticky="w", padx=6, pady=(0,6))

    out_dir_var = tk.StringVar(value=_downloads_dir())
    pick_btn = ctk.CTkButton(frame, text="Zmień…", width=100,
                             command=lambda: out_dir_var.set(filedialog.askdirectory() or out_dir_var.get()))
    out_label = ctk.CTkLabel(frame, textvariable=out_dir_var, text_color="gray")
    pick_btn.grid(row=8, column=1, sticky="w", padx=(6,6), pady=(0,6))
    out_label.grid(row=8, column=2, columnspan=2, sticky="w", padx=(0,6), pady=(0,6))

    def _effective_out_dir() -> str:
        mode = out_mode_var.get()
        if mode == "custom":
            path = out_dir_var.get().strip()
            if not path:
                raise ValueError("Wybierz folder zapisu.")
            return path
        return _downloads_dir()

    status_var = tk.StringVar(value="Gotowe.")

    def on_generate():
        try:
            # 1) Dane wejściowe
            size = size_var.get()
            name = (name_entry.get() or "").strip()
            if not name:
                status_var.set("Podaj imię."); return
            dob  = date_entry.get_date()  # obiekt date
            city = (city_entry.get() or "").strip()

            # 2) Tekst stały – najpierw własny, jeśli wpisany
            own_text = own_box.get("1.0", "end").strip()
            if own_text:
                fixed_text = own_text
            else:
                sel = templ_var.get()
                if sel == "(— wybierz —)":
                    status_var.set("Wybierz stały tekst z listy lub wpisz własny."); return
                idx = templ_values.index(sel) - 1
                if not (0 <= idx < len(texts_pairs)):
                    status_var.set("Wybierz poprawny stały tekst."); return
                a, b = texts_pairs[idx]
                fixed_text = a if not b else (a + "\n" + b)

            # 3) Ścieżka zapisu + nazwa
            out_dir = _effective_out_dir()
            os.makedirs(out_dir, exist_ok=True)
            safe_name = _slugify_name(name)
            fname = f"poster_{size}_{safe_name}_{dob.strftime('%Y%m%d')}.png"
            out_path = os.path.join(out_dir, fname)

            # 4) Ostrzeżenia o ikonach (zbuduj profil i ścieżki)
            prof  = build_profile(dob, base_dir=BASE_DIR)
            paths = icon_paths(prof, assets_dir=ASSETS_DIR)
            missing = _collect_missing_assets(prof, paths)

            # 5) Render
            create_poster(
                out_path=out_path,
                size_key=size,
                name=name,
                birth_date_str=dob.strftime("%d.%m.%Y"),
                birth_date_iso=dob,
                city_label=city,
                fixed_text=fixed_text,
                assets_dir=ASSETS_DIR,
                base_dir=BASE_DIR,
            )

            if missing:
                status_var.set(f"Zapisano: {out_path}  (uwaga: {', '.join(missing)} – pominięto)")
            else:
                status_var.set(f"Zapisano: {out_path}")

        except Exception as e:
            status_var.set(f"Błąd: {e}")

    gen_btn = ctk.CTkButton(frame, text="Generuj plakat PNG (300 DPI)", command=on_generate)
    gen_btn.grid(row=10, column=0, columnspan=4, pady=(18,10))

    status = ctk.CTkLabel(frame, textvariable=status_var, text_color="gray")
    status.grid(row=11, column=0, columnspan=4, pady=(4,10), sticky="w")

    # layout expand
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_columnconfigure(2, weight=1)
    frame.grid_columnconfigure(3, weight=1)

    root.mainloop()

if __name__ == "__main__":
    run_app()
