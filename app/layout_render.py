import os
from typing import Literal, Optional, List, Dict, Tuple
from datetime import date
from PIL import Image, ImageDraw, ImageFont
from app.rules import build_profile, icon_paths, default_fixed_text_pair

DPI = 300
SIZES_CM = {"21x30": (30.0, 21.0), "30x40": (40.0, 30.0)}  # landscape
SAFE_CM = 1

NAME_PT  = 55   # Allura
INFO_PT  = 10   # Open Sans
FIXED_PT = 11   # Open Sans Regular

NAME_Y_RATIO  = 0.115
FIXED_Y_RATIO = 0.78

# środkowe kółka
DRAW_CENTER_CIRCLE_OUTLINES = False  # nie rysuj obwódek
CENTER_CIRCLE_FIT_RATIO = 0.96       # jak mocno „wypychać” PNG w koło (0.90–1.00)


def _cm_to_px(cm: float) -> int:
    return int(round(cm / 2.54 * DPI))

def _pt_to_px(pt: float) -> int:
    return int(round(pt * DPI / 72.0))

def _load_font(fonts_dir: str, name_like: str, size_px: int):
    if os.path.isdir(fonts_dir):
        for fn in os.listdir(fonts_dir):
            if fn.lower().endswith(".ttf") and name_like.lower() in fn.lower():
                try:
                    return ImageFont.truetype(os.path.join(fonts_dir, fn), size=size_px)
                except Exception:
                    pass
    try:
        return ImageFont.truetype(os.path.join(fonts_dir, "Allura.ttf"), size=size_px)
    except Exception:
        return ImageFont.load_default()

def _paste_center(im: Image.Image, icon: Image.Image, center_xy):
    w, h = icon.size
    im.alpha_composite(icon, (int(center_xy[0]-w/2), int(center_xy[1]-h/2)))

def _load_icon(path: Optional[str], target_h: int) -> Optional[Image.Image]:
    if not path or not os.path.exists(path): return None
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    if h != target_h:
        scale = target_h / h
        im = im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    return im

def _compose_number(
        digits_dir: str,
        number: int,
        target_h: int,
        gap_px: int = 6,
        orientation: Literal["horizontal", "vertical"] = "horizontal",
        vertical_mode: Literal["fit_total", "stack_full", "stack_scaled"] = "fit_total",
        vertical_digit_scale: float = 1.0
) -> Optional[Image.Image]:

    s = str(number)
    tiles: List[Image.Image] = []
    for ch in s:
        p = os.path.join(digits_dir, f"{ch}.png")
        if not os.path.exists(p):
            return None
        tiles.append(Image.open(p).convert("RGBA"))

    if not tiles:
        return None

    if orientation == "horizontal" or len(tiles) == 1:
        resized = []
        for im in tiles:
            w, h = im.size
            if h != target_h:
                scale = target_h / h
                im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            resized.append(im)
        total_w = sum(im.size[0] for im in resized) + gap_px * (len(resized) - 1)
        out = Image.new("RGBA", (total_w, target_h), (255, 255, 255, 0))
        x = 0
        for i, imt in enumerate(resized):
            out.alpha_composite(imt, (x, 0))
            x += imt.size[0] + (gap_px if i < len(resized) - 1 else 0)
        return out

    n = len(tiles)
    if vertical_mode == "stack_full":
        each_h = target_h
    elif vertical_mode == "stack_scaled":

        each_h = int(round(target_h * (vertical_digit_scale if n > 1 else 1.0)))
    else:
        each_h = max(1, int((target_h - gap_px * (n - 1)) / n))
    resized = []
    max_w = 1
    for im in tiles:
        w, h = im.size
        if h != each_h:
            scale = each_h / h
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        resized.append(im)
        max_w = max(max_w, im.size[0])

    total_h = n * each_h + gap_px * (n - 1)
    out = Image.new("RGBA", (max_w, total_h), (255, 255, 255, 0))

    y = 0
    for i, imt in enumerate(resized):
        x = (max_w - imt.size[0]) // 2
        out.alpha_composite(imt, (x, y))
        y += each_h + (gap_px if i < n - 1 else 0)

    return out

def _draw_frame_with_gaps(
    d: ImageDraw.ImageDraw,
    W: int, H: int, frame: int,
    gaps: Dict[str, List[Tuple[int,int]]],
    line_w: int
):
    def _segments(total_len: int, holes: List[Tuple[int,int]]) -> List[Tuple[int,int]]:
        if not holes: return [(0, total_len)]
        segs = []
        holes = sorted([(max(0,a), min(total_len,b)) for a,b in holes if a<b])
        cur = 0
        for a,b in holes:
            if a > cur: segs.append((cur, a))
            cur = max(cur, b)
        if cur < total_len: segs.append((cur, total_len))
        return segs
    for a,b in _segments(W-2*frame, gaps.get("top", [])):
        d.line([(frame+a, frame), (frame+b, frame)], fill=(0,0,0,255), width=line_w)
    for a,b in _segments(H-2*frame, gaps.get("right", [])):
        d.line([(W-frame, frame+a), (W-frame, frame+b)], fill=(0,0,0,255), width=line_w)
    for a,b in _segments(W-2*frame, gaps.get("bottom", [])):
        d.line([(frame+a, H-frame), (frame+b, H-frame)], fill=(0,0,0,255), width=line_w)
    for a,b in _segments(H-2*frame, gaps.get("left", [])):
        d.line([(frame, frame+a), (frame, frame+b)], fill=(0,0,0,255), width=line_w)


# --- TRZY KÓŁKA W CENTRUM ---
def _triple_circles_spec(size_key: str, cm_w: float, cm_h: float) -> tuple[int,int]:
    """Zwraca (średnica_px, odstęp_px). 21x30: 7.5 cm i 0.5 cm; 30x40 skaluje się po krótszym boku (30/21)."""
    diam_cm, gap_cm = 7.5, 0.5
    if size_key == "30x40":
        scale = (min(cm_w, cm_h) / 21.0)  # 30/21
        diam_cm *= scale
        gap_cm  *= scale
    return _cm_to_px(diam_cm), _cm_to_px(gap_cm)

def _triple_circles_boxes(W: int, H: int, D_px: int, G_px: int) -> list[tuple[int,int,int,int]]:
    """Zwraca listę 3 bboxów (L,T,R,B) wycentrowanych w jednym rzędzie."""
    total_w = 3*D_px + 2*G_px
    x0 = (W - total_w) // 2
    y0 = (H - D_px) // 2
    return [(x0 + i*(D_px+G_px), y0, x0 + i*(D_px+G_px) + D_px, y0 + D_px) for i in range(3)]

def _draw_circle_outline(d: ImageDraw.ImageDraw, bbox: tuple[int,int,int,int], stroke: int):
    d.ellipse(bbox, outline=(0,0,0,255), width=stroke)

def _paste_center_fit(im: Image.Image, icon: Image.Image | None, bbox: tuple[int,int,int,int], fit_ratio: float = 0.88):
    """Wkleja obrazek wycentrowany w kole; skaluje do fit_ratio * średnica. Zakładamy PNG z przezroczystością."""
    if icon is None:
        return
    L, T, R, B = bbox
    D = min(R-L, B-T)
    target = int(D * fit_ratio)
    w, h = icon.size
    scale = target / max(w, h)
    icon2 = icon.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    cx, cy = L + D//2, T + D//2
    im.alpha_composite(icon2, (cx - icon2.size[0]//2, cy - icon2.size[1]//2))


# --- KONSTELACJE ---
def _constellation_slug(prof, paths: dict | None) -> str | None:
    """Preferuj prof.western_sign (np. 'aries'); fallback: slug z pliku ikony zodiaku."""
    s = getattr(prof, "western_sign", None)
    if isinstance(s, str) and s.strip():
        return s.strip().lower()
    if paths:
        p = paths.get("zodiac")
        if p:
            return os.path.splitext(os.path.basename(p))[0].lower()
    return None

def _load_constellation(assets_dir: str, prof_or_slug, paths: dict | None = None):
    """Szukaj w assets/symbols/constellation/: <slug>_constellation.png lub <slug>.png"""
    if isinstance(prof_or_slug, str):
        slug = prof_or_slug.strip().lower()
    else:
        slug = _constellation_slug(prof_or_slug, paths)
    if not slug:
        return None
    candidates = [
        os.path.join(assets_dir, "symbols", "constellation", f"{slug}_constellation.png"),
        os.path.join(assets_dir, "symbols", "constellation", f"{slug}.png"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return Image.open(p).convert("RGBA")
    return None



def create_poster(
    out_path: str,
    size_key: Literal["21x30","30x40"],
    name: str,
    birth_date_str: str,
    birth_date_iso: date,
    city_label: str,
    fixed_text: str,
    assets_dir: str,
    base_dir: str,
) -> str:
    if size_key not in SIZES_CM: raise ValueError("Zły rozmiar")
    cm_w, cm_h = SIZES_CM[size_key]
    W, H = _cm_to_px(cm_w), _cm_to_px(cm_h)

    im = Image.new("RGBA", (W, H), (255,255,255,255))
    d = ImageDraw.Draw(im)


    fonts_dir = os.path.join(assets_dir, "fonts")

    base_name_px = _pt_to_px(NAME_PT)
    base_info_px = _pt_to_px(INFO_PT)
    base_fixed_px = _pt_to_px(FIXED_PT)

    if size_key == "21x30":
        name_px, info_px, fixed_px = base_name_px, base_info_px, base_fixed_px
    elif size_key == "30x40":
        scale = (min(cm_w, cm_h) / 21.0)
        name_px = max(1, int(round(base_name_px * scale)))
        info_px = max(1, int(round(base_info_px * scale)))
        fixed_px = max(1, int(round(base_fixed_px * scale)))
    else:
        name_px, info_px, fixed_px = base_name_px, base_info_px, base_fixed_px

    name_font = _load_font(fonts_dir, "allura", name_px)
    info_font = _load_font(fonts_dir, "opensans", info_px)
    fixed_font = _load_font(fonts_dir, "opensans", fixed_px)

    prof  = build_profile(birth_date_iso, base_dir=base_dir)
    paths = icon_paths(prof, assets_dir=assets_dir)


    name_w, name_h = d.textbbox((0,0), name, font=name_font)[2:]
    name_y = int(H * NAME_Y_RATIO)
    d.text(((W - name_w)//2, name_y), name, fill=(0,0,0,255), font=name_font)

    line2 = birth_date_str + (", " + city_label if city_label.strip() else "")
    line2_w, line2_h = d.textbbox((0,0), line2, font=info_font)[2:]
    y2 = name_y + name_h + int(H * 0.015)
    d.text(((W - line2_w)//2, y2), line2, fill=(0,0,0,255), font=info_font)

    FIXED_Y_CENTER_RATIO = 0.80
    FIXED_LINE_SPACING = 0.30

    line1, line2 = default_fixed_text_pair(base_dir)

    lines = [ln for ln in (line1, line2) if ln]

    if lines:
        line_px = fixed_font.size
        gap_px = int(line_px * FIXED_LINE_SPACING)
        total_h = len(lines) * line_px + (len(lines) - 1) * gap_px
        y0 = int(H * FIXED_Y_CENTER_RATIO - total_h / 2)

        y = y0
        for ln in lines:
            lw = d.textbbox((0, 0), ln, font=fixed_font)[2]
            d.text(((W - lw) // 2, y), ln, fill=(0, 0, 0, 255), font=fixed_font)
            y += line_px + gap_px

    icon_h = int(min(W,H) * 0.04)
    line_w = max(2, int(min(W,H) * 0.003))
    frame  = _cm_to_px(SAFE_CM) + int(min(W,H) * 0.02)
    pad    = int(icon_h * 0.28)

    def _maybe(p): return _load_icon(p, icon_h)
    icons: Dict[str, Optional[Image.Image]] = {
        "zodiac":  _maybe(paths.get("zodiac")),
        "element": _maybe(paths.get("element")),
        "totem":   _maybe(paths.get("totem")),
        "moon":    _maybe(paths.get("moon")),
        "celtic":  _maybe(paths.get("celtic")),
        "china":   _maybe(paths.get("china")),
    }
    num_gap = max(4, int(icon_h * 0.10))  # odstęp między cyframi
    num_birth = _compose_number(
        paths["digits_dir"], prof.birth_num, icon_h,
        gap_px=num_gap, orientation="vertical",
        vertical_mode="stack_scaled", vertical_digit_scale=0.75
    )
    num_life = _compose_number(
        paths["digits_dir"], prof.life_path, icon_h,
        gap_px=num_gap, orientation="vertical",
        vertical_mode="stack_scaled", vertical_digit_scale=0.75
    )

    pos = {
        "top":    (W//2,       frame),         # EU zodiac
        "right":  (W - frame,  H//2),          # EU element
        "bottom": (W//2,       H - frame),     # life path
        "left":   (frame,      H//2),          # moon phase
        "tl":     (frame,      frame),         # celtic tree
        "tr":     (W - frame,  frame),         # totem
        "br":     (W - frame,  H - frame),     # birth number
        "bl":     (frame,      H - frame),     # chinese zodiac
    }

    gaps = {"top":[], "right":[], "bottom":[], "left":[]}
    def cut(edge: str, center_xy: Tuple[int,int], content_img: Optional[Image.Image]):
        if content_img is None: return
        w, h = content_img.size
        if edge in ("top","bottom"):
            cx = center_xy[0]; half = w//2 + pad
            gaps[edge].append((max(0, cx - frame - half), min(W - 2*frame, cx - frame + half)))
        else:
            cy = center_xy[1]; half = h//2 + pad
            gaps[edge].append((max(0, cy - frame - half), min(H - 2*frame, cy - frame + half)))

    cut("top", pos["top"], icons["zodiac"])  # 12:00  → zodiak (EU)
    cut("right", pos["right"], num_birth)  # 3:00   → liczba urodzenia
    cut("bottom", pos["bottom"], icons["moon"])  # 6:00   → księżyc
    cut("left", pos["left"], num_life)  # 9:00   → liczba życia

    cut("top", pos["tr"], icons["china"]); cut("right", pos["tr"], icons["china"])  # ~1:30 → zodiak chiński
    cut("bottom", pos["br"], icons["element"]); cut("right", pos["br"], icons["element"])  # ~4:30 → żywioł
    cut("bottom", pos["bl"], icons["celtic"]); cut("left", pos["bl"], icons["celtic"])  # ~7:30 → celtic
    cut("top", pos["tl"], icons["totem"]); cut("left", pos["tl"], icons["totem"])  # ~10:30→ totem

    _draw_frame_with_gaps(d, W, H, frame, gaps, line_w)

    if icons["zodiac"]:  _paste_center(im, icons["zodiac"], pos["top"])  # 12:00
    if num_birth:        _paste_center(im, num_birth, pos["right"])  # 3:00
    if icons["moon"]:    _paste_center(im, icons["moon"], pos["bottom"])  # 6:00
    if num_life:         _paste_center(im, num_life, pos["left"])  # 9:00

    if icons["china"]:   _paste_center(im, icons["china"], pos["tr"])  # 1:30
    if icons["element"]: _paste_center(im, icons["element"], pos["br"])  # 4:30
    if icons["celtic"]:  _paste_center(im, icons["celtic"], pos["bl"])  # 7:30
    if icons["totem"]:   _paste_center(im, icons["totem"], pos["tl"])  # 10:30

    # --- TRZY KÓŁKA W CENTRUM ---
    D_px, G_px = _triple_circles_spec(size_key, cm_w, cm_h)
    circle_boxes = _triple_circles_boxes(W, H, D_px, G_px)

    # (1) obrysy kół – WYŁĄCZONE domyślnie
    if DRAW_CENTER_CIRCLE_OUTLINES:
        circle_stroke = max(2, int(min(W, H) * 0.0028))
        for bb in circle_boxes:
            _draw_circle_outline(d, bb, circle_stroke)

    # (2) zawartość: #1 = konstelacja
    const_img = _load_constellation(assets_dir, prof, paths)
    _paste_center_fit(im, const_img, circle_boxes[0], fit_ratio=CENTER_CIRCLE_FIT_RATIO)

    # #2 i #3 zostają puste (na później)
    # _paste_center_fit(im, img2, circle_boxes[1], fit_ratio=CENTER_CIRCLE_FIT_RATIO)
    # _paste_center_fit(im, img3, circle_boxes[2], fit_ratio=CENTER_CIRCLE_FIT_RATIO)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    im.save(out_path, "PNG", dpi=(DPI, DPI))
    return out_path
