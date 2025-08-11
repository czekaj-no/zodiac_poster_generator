from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional, Tuple, Dict, Any, List
import json, os, math

SYNODIC = 29.530588  # dni
KNOWN_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

FALLBACK_WESTERN = [
    {"from":"03-21","to":"04-19","sign":"aries","element":"fire","pl":"Baran"},
    {"from":"04-20","to":"05-20","sign":"taurus","element":"earth","pl":"Byk"},
    {"from":"05-21","to":"06-20","sign":"gemini","element":"air","pl":"Bliźnięta"},
    {"from":"06-21","to":"07-22","sign":"cancer","element":"water","pl":"Rak"},
    {"from":"07-23","to":"08-22","sign":"leo","element":"fire","pl":"Lew"},
    {"from":"08-23","to":"09-22","sign":"virgo","element":"earth","pl":"Panna"},
    {"from":"09-23","to":"10-22","sign":"libra","element":"air","pl":"Waga"},
    {"from":"10-23","to":"11-21","sign":"scorpio","element":"water","pl":"Skorpion"},
    {"from":"11-22","to":"12-21","sign":"sagittarius","element":"fire","pl":"Strzelec"},
    {"from":"12-22","to":"01-19","sign":"capricorn","element":"earth","pl":"Koziorożec"},
    {"from":"01-20","to":"02-18","sign":"aquarius","element":"air","pl":"Wodnik"},
    {"from":"02-19","to":"03-20","sign":"pisces","element":"water","pl":"Ryby"}
]
FALLBACK_TOTEMS = [
    {"sign":"aquarius","totem":"otter","pl":"Wydra"},
    {"sign":"pisces","totem":"wolf","pl":"Wilk"},
    {"sign":"aries","totem":"falcon","pl":"Sokół"},
    {"sign":"taurus","totem":"beaver","pl":"Bóbr"},
    {"sign":"gemini","totem":"deer","pl":"Jeleń"},
    {"sign":"cancer","totem":"woodpecker","pl":"Dzięcioł"},
    {"sign":"leo","totem":"salmon","pl":"Łosoś"},
    {"sign":"virgo","totem":"bear","pl":"Niedźwiedź"},
    {"sign":"libra","totem":"raven","pl":"Kruk"},
    {"sign":"scorpio","totem":"snake","pl":"Wąż"},
    {"sign":"sagittarius","totem":"owl","pl":"Sowa"},
    {"sign":"capricorn","totem":"goose","pl":"Gęś"}
]
FALLBACK_CHINESE = [
    {"animal":"rat","pl":"Szczur"},{"animal":"ox","pl":"Wół"},{"animal":"tiger","pl":"Tygrys"},
    {"animal":"rabbit","pl":"Królik"},{"animal":"dragon","pl":"Smok"},{"animal":"snake","pl":"Wąż"},
    {"animal":"horse","pl":"Koń"},{"animal":"goat","pl":"Koza"},{"animal":"monkey","pl":"Małpa"},
    {"animal":"rooster","pl":"Kogut"},{"animal":"dog","pl":"Pies"},{"animal":"pig","pl":"Świnia"}
]
FALLBACK_PHASES = [
    {"key":"new_moon","pl":"Nów"},
    {"key":"waxing_crescent","pl":"Sierp przybywający"},
    {"key":"first_quarter","pl":"Pierwsza kwadra"},
    {"key":"waxing_gibbous","pl":"Garbaty przybywający"},
    {"key":"full_moon","pl":"Pełnia"},
    {"key":"waning_gibbous","pl":"Garbaty ubywający"},
    {"key":"last_quarter","pl":"Ostatnia kwadra"},
    {"key":"waning_crescent","pl":"Sierp ubywający"}
]

def _load_reference(base_dir: str) -> Dict[str, Any]:
    path = os.path.join(base_dir, "assets", "data", "reference.json")
    if not os.path.exists(path):
        return {
            "zodiac_western": FALLBACK_WESTERN,
            "totems": FALLBACK_TOTEMS,
            "china_zodiac": FALLBACK_CHINESE,
            "moon_phases": FALLBACK_PHASES,
            "celtic_tree_21": []
        }
    with open(path, "r", encoding="utf-8") as f:
        ref = json.load(f)

    ref.setdefault("zodiac_western", FALLBACK_WESTERN)
    ref.setdefault("totems", FALLBACK_TOTEMS)
    ref.setdefault("china_zodiac", FALLBACK_CHINESE)
    ref.setdefault("moon_phases", FALLBACK_PHASES)
    ref.setdefault("celtic_tree_21", [])
    return ref

def fixed_text_pairs(base_dir: str) -> list[tuple[str, str]]:
    ref = _load_reference(base_dir)
    raw = ref.get("texts", [])
    out = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        line1 = line2 = ""
        if isinstance(item, dict):
            if "line1" in item or "line2" in item:
                line1 = str(item.get("line1","")).strip()
                line2 = str(item.get("line2","")).strip()
            elif item:
                val = str(next(iter(item.values()))).strip().replace("\\n","\n")
                parts = [p.strip() for p in val.split("\n") if p.strip()]
                line1 = parts[0] if parts else ""
                line2 = parts[1] if len(parts)>1 else ""
        elif isinstance(item, str):
            val = item.strip().replace("\\n","\n")
            parts = [p.strip() for p in val.split("\n") if p.strip()]
            line1 = parts[0] if parts else ""
            line2 = parts[1] if len(parts)>1 else ""
        if line1 or line2:
            out.append((line1, line2))
    return out

def default_fixed_text_pair(base_dir: str) -> tuple[str, str]:
    pairs = fixed_text_pairs(base_dir)
    return pairs[0] if pairs else ("TO, KIM JESTEŚ, ZAPISANO W GWIAZDACH", "")



def _in_range(mm: int, dd: int, a: str, b: str) -> bool:
    am, ad = map(int, a.split("-"))
    bm, bd = map(int, b.split("-"))
    if (am, ad) <= (bm, bd):
        return (am, ad) <= (mm, dd) <= (bm, bd)
    return (mm, dd) >= (am, ad) or (mm, dd) <= (bm, bd)

def _index(lst: List[Dict[str, Any]], key: str, value: str) -> Optional[Dict[str, Any]]:
    for rec in lst:
        if rec.get(key) == value:
            return rec
    return None

def western_zodiac(ref: Dict[str, Any], m: int, d: int) -> Tuple[str, str, str]:
    for rec in ref["zodiac_western"]:
        if _in_range(m, d, rec["from"], rec["to"]):
            return rec["sign"], rec["element"], rec.get("pl", rec["sign"])
    cap = _index(ref["zodiac_western"], "sign", "capricorn")
    return "capricorn", cap.get("element","earth"), cap.get("pl","Koziorożec")

def totem_for_sign(ref: Dict[str, Any], sign: str) -> Tuple[str, str]:
    rec = _index(ref["totems"], "sign", sign)
    return rec["totem"], rec.get("pl", rec["totem"]) if rec else ("", "")

def chinese_animal(ref: Dict[str, Any], y: int, m: int, d: int) -> Tuple[str, str]:
    if (m, d) < (2, 4):
        y -= 1
    lst = ref["china_zodiac"]
    rec = lst[(y - 4) % 12]
    return rec["animal"], rec.get("pl", rec["animal"])

def moon_phase_8(dt: date) -> Tuple[int, str, float]:
    ref_dt = datetime(dt.year, dt.month, dt.day, 12, 0, tzinfo=timezone.utc)
    days = (ref_dt - KNOWN_NEW_MOON).total_seconds() / 86400.0
    age = days % SYNODIC
    idx = int((age / SYNODIC) * 8 + 0.5) % 8
    illum = 0.5 * (1 - math.cos(2 * math.pi * age / SYNODIC))
    return idx, float(illum)

def moon_phase_labels(ref: Dict[str, Any], idx: int) -> Tuple[str, str]:
    rec = ref["moon_phases"][idx]
    return rec["key"], rec.get("pl", rec["key"])

def celtic_tree_21_for(ref: Dict[str, Any], dt: date) -> Optional[Dict[str, str]]:
    lst = ref.get("celtic_tree_21", [])
    if not lst:
        return None
    mm, dd = dt.month, dt.day
    for rec in lst:
        for a, b in rec.get("ranges", []):
            if _in_range(mm, dd, a, b):
                return {"slug": rec["slug"], "en": rec.get("en"), "pl": rec.get("pl")}
    return None

def life_path_number(y: int, m: int, d: int, keep_masters: bool = True) -> int:
    s = sum(int(c) for c in f"{y:04d}{m:02d}{d:02d}")
    while s > 22:
        s = sum(int(c) for c in str(s))
    if keep_masters and s in (11, 22):
        return s
    while s > 9:
        s = sum(int(c) for c in str(s))
    return s

def birth_number(d: int) -> int:
    return d

@dataclass
class Profile:
    western_sign: str
    western_sign_pl: str
    element: str
    totem: str
    totem_pl: str
    chinese_animal: str
    chinese_animal_pl: str
    moon_phase_key: str
    moon_phase_pl: str
    birth_num: int
    life_path: int
    celtic_tree_slug: Optional[str]
    celtic_tree_en: Optional[str]
    celtic_tree_pl: Optional[str]

def build_profile(dt: date, base_dir: str) -> Profile:
    ref = _load_reference(base_dir)
    m, d, y = dt.month, dt.day, dt.year

    sign, element, sign_pl = western_zodiac(ref, m, d)
    totem, totem_pl = totem_for_sign(ref, sign)
    chi, chi_pl = chinese_animal(ref, y, m, d)
    idx, _illum = moon_phase_8(dt)
    phase_key, phase_pl = moon_phase_labels(ref, idx)
    tree = celtic_tree_21_for(ref, dt) or {"slug": None, "en": None, "pl": None}

    return Profile(
        western_sign=sign,
        western_sign_pl=sign_pl,
        element=element,
        totem=totem, totem_pl=totem_pl,
        chinese_animal=chi, chinese_animal_pl=chi_pl,
        moon_phase_key=phase_key, moon_phase_pl=phase_pl,
        birth_num=birth_number(d),
        life_path=life_path_number(y, m, d),
        celtic_tree_slug=tree["slug"], celtic_tree_en=tree["en"], celtic_tree_pl=tree["pl"],
    )

def icon_paths(profile: Profile, assets_dir: str) -> Dict[str, Optional[str]]:
    out = {
        "zodiac": os.path.join(assets_dir, "symbols", "zodiac", f"{profile.western_sign}.png"),
        "totem": os.path.join(assets_dir, "symbols", "animals", f"{profile.totem}.png"),
        "element": os.path.join(assets_dir, "symbols", "element", f"{profile.element}.png"),
        "china": os.path.join(assets_dir, "symbols", "china_zodiac", f"{profile.chinese_animal}.png"),
        "moon": os.path.join(assets_dir, "symbols", "moon_phases", f"{profile.moon_phase_key}.png"),
        "celtic": os.path.join(assets_dir, "symbols", "celtic_tree", f"{profile.celtic_tree_slug}.png") if profile.celtic_tree_slug else None,
        "digits_dir": os.path.join(assets_dir, "symbols", "numerology", "digits")
    }
    return out
