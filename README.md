# Zodiac Poster Generator (300 DPI, Landscape)

A simple Python app (CustomTkinter + Pillow) that generates minimalist zodiac posters ready for high-quality print.

> **Note:** This repository **does not** include any graphics, fonts, or private text content.
> All assets live in `assets/` locally and are ignored via `.gitignore`.

---

## ✨ Features

- Landscape formats: **21×30 cm** and **30×40 cm** (300 DPI).
- Name (Allura), birth date & city (Open Sans).
- 8 icons around the frame (4 corners + 4 edge centers) in this order (clockwise starting at 12 o’clock):
  - **12:00** Western zodiac  
  - **~1:30** Chinese zodiac  
  - **3:00** Birth number (digits stacked **vertically**)  
  - **~4:30** Element  
  - **6:00** Moon phase  
  - **~7:30** Totem animal  
  - **9:00** Life path number (digits stacked **vertically**)  
  - **~10:30** Celtic tree
- Fixed text: choose from `reference.json` (two explicit lines) **or** type your own (multi-line).

---

## 🧰 Requirements

- Python **3.10+**
- Windows (tested with PyCharm)

Install packages:

```bash
pip install -r requirements.txt
requirements.txt (minimal):

Pillow>=10
customtkinter>=5.2
tkcalendar>=1.6

📁 Project Structure

.
├── app/
│   ├── __init__.py
│   ├── gui.py          # GUI (CustomTkinter)
│   ├── layout_render.py     # PNG rendering / layout
│   ├── rules.py             # date → zodiac/element/totem/etc.
├── assets/                  # (ignored in git; local only)
│   ├── fonts/               # Allura.ttf, OpenSans-Regular.ttf
│   ├── symbols/
│   │   ├── zodiac/          # aries.png ... pisces.png
│   │   ├── animals/         # otter.png ... goose.png
│   │   ├── element/         # fire.png, earth.png, air.png, water.png
│   │   ├── china_zodiac/    # rat.png ... pig.png
│   │   ├── moon_phases/     # new_moon.png ... waning_crescent.png
│   │   ├── celtic_tree/     # 21 trees (slugs)
│   │   └── numerology/digits/  # 0.png ... 9.png
│   └── data/
│       ├── reference.json               # your private data (ignored)
│       └── reference.example.json       # public example (committed)
├── main.py                 # entry point
├── requirements.txt
└── README.md
To keep folder structure in git without assets, add empty .gitkeep files under each assets/** subfolder.

🔐 Private Assets
All files under assets/ are ignored by git (see .gitignore).
You should commit only a public example data file:

Commit: assets/data/reference.example.json

Local private copy: assets/data/reference.json (ignored)

Example assets/data/reference.example.json

json
{
  "version": 1,
  "texts": [
    { "id": "fixed_text1", "line1": "text,", "line2": "text" },
    { "id": "fixed_text2", "line1": "text", "line2": "text" }
  ],
  "zodiac_western": [],
  "totems": [],
  "chinese_zodiac": [],
  "moon_phases": [],
  "celtic_tree_21": []
}
The app uses its own rules in rules.py for calculations; you mainly need texts (line1, line2).
Icons must be named exactly by their slugs (e.g., zodiac/aries.png, numerology/digits/3.png).

▶️ Run
python main.py
# or
python -m app.main_gui

Output folder (GUI):

Default: your Downloads directory

Or: choose a custom folder (session-only)

Filename format:
poster_{SIZE}_{NAME}_{YYYYMMDD}.png (name normalized without diacritics)

⚙️ Tuning (in code)
Open app/layout_render.py:

Icon size: icon_h = int(min(W, H) * 0.07) (relative)
or set a fixed physical height: icon_h = _cm_to_px(1.8)

Frame thickness: line_w = max(2, int(min(W, H) * 0.003))

Safe frame margin (for framing): SAFE_CM = 0.5

Fonts (21×30 fixed, 30×40 scaled): see the size_key == "30x40" block scaling

Vertical stacked digits size: vertical_digit_scale = 0.75 (¾ of icon height)

Name ↔ date gap: search NAME_TO_INFO_GAP_RATIO or the line name_h + int(H * ...)

Bottom text vertical position: FIXED_Y_CENTER_RATIO

🧩 Troubleshooting
ModuleNotFoundError: customtkinter/tkcalendar/PIL → pip install -r requirements.txt

Tk errors on Windows → ensure Python installed with Tk support.

Missing icons on output → check filenames and slugs; the renderer skips absent icons and shows a warning in the GUI status bar.

🪪 License & Assets

Code: **Personal Use Only (Non-Commercial)** – see [LICENSE.md](./LICENSE.md).  
**Assets under `assets/` are not included in the license** (all rights reserved).

