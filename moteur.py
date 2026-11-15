"""Moteur de calcul : climat NASA POWER, bilan d'eau (inspiré de FAO-56/FAO-33), effet de la température,
classement des cultures par saison et plans de rotation. Aucune dépendance à Streamlit (testable seul).
Code généré avec l'aide de Claude (Anthropic) ; paramètres agronomiques = ordres de grandeur à valider."""
import itertools
import math
import pathlib
import time

import numpy as np
import pandas as pd
import requests

NIAYES = (14.85, -17.20)
YEARS = list(range(2006, 2026))
MY = ("Oignon", "Piment", "Niébé")
ICON = {"Oignon": "🧅", "Piment": "🌶️", "Niébé": "🫘"}
INFO = {  # revenu, azote (+ fixe / - épuise), matière organique, besoin en eau (mm)
    "Oignon": dict(inc=.9, n=-.8, org=.3, need=500),
    "Piment": dict(inc=.8, n=-.6, org=.3, need=600),
    "Niébé": dict(inc=.5, n=1.0, org=.7, need=300),
}
# durée du cycle (j), Kc initial / milieu / fin, profondeur racinaire (m), Ky (sensibilité du rendement à l'eau)
CROP_FAO = {"Oignon": (120, .70, 1.05, .75, .5, 1.1), "Piment": (120, .60, 1.05, .90, .7, 1.1),
            "Niébé": (70, .40, 1.05, .60, .8, .8)}
# températures moyennes (°C) : (minimum, début de l'optimum, fin de l'optimum, maximum)
CROP_T = {"Oignon": (6, 13, 24, 32), "Piment": (10, 20, 30, 36), "Niébé": (12, 22, 32, 40)}
TAW = 80  # eau utile du sol sableux (mm par m)
SEASONS = {  # fenêtre simulée (mois, jour), décalage d'année de fin, jours avant le semis, humidité initiale
    "Hivernage": dict(label="🌧️ Hivernage (juillet à octobre)", start=(6, 1), end=(11, 30), yoff=0, plant=30, dep0=.9),
    "Saison fraîche": dict(label="❄️ Saison fraîche (novembre à février)", start=(11, 1), end=(3, 5), yoff=1, plant=0, dep0=.4),
    "Saison chaude": dict(label="☀️ Saison chaude (mars à juin)", start=(3, 1), end=(7, 5), yoff=0, plant=0, dep0=.8),
}
ORDER = list(SEASONS)
PRIO_KEYS = ("Revenu", "Eau", "Sol", "Résilience")
WATER_BUDGET = {"Oui": 1e9, "Peu": 150.0, "Non": 0.0}  # mm d'arrosage par saison
PRIO_FR = {"Revenu": "gagner plus d’argent", "Eau": "économiser l’eau", "Sol": "garder la terre en bonne santé",
           "Résilience": "mieux résister aux années sèches"}
WATER_FR = {"Oui": "oui, assez d’eau", "Peu": "un peu d’eau seulement", "Non": "non, seulement la pluie"}

THR = 0.6  # une saison « réussit » si le rendement atteint 60 % du rendement possible


def month_season(m):
    return ORDER[0] if 7 <= m <= 10 else ORDER[1] if (m >= 11 or m <= 2) else ORDER[2]



# ---------------------------------------------------------------------------------------------
# CLIMAT NASA POWER ET BILAN D'EAU (inspiré de FAO-56 / FAO-33) + EFFET DE LA TEMPÉRATURE
# ---------------------------------------------------------------------------------------------
def ra_mm(lat, doy):
    phi = math.radians(lat)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    d = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(max(-1, min(1, -math.tan(phi) * math.tan(d))))
    ra = (24 * 60 / math.pi) * 0.0820 * dr * (ws * math.sin(phi) * math.sin(d) + math.cos(phi) * math.cos(d) * math.sin(ws))
    return ra / 2.45


POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
DATA_FILE = pathlib.Path(__file__).resolve().parent / "data" / "niayes_power.csv"  # copie locale (voir telecharger_donnees.py)
POWER_END = "20260310"


def _get(params, tries=4):
    """Requête NASA POWER avec nouvelles tentatives : l'API limite les requêtes répétées et rapides."""
    last = None
    for k in range(tries):
        try:
            r = requests.get(POWER_URL, params=params, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            time.sleep(3 * (k + 1))
    raise last


def _to_df(js):
    df = pd.DataFrame(js["properties"]["parameter"]).replace(-999, float("nan"))
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    return df[["PRECTOTCORR", "T2M_MAX", "T2M_MIN"]]


def power_daily(lat, lon):
    """Pluie et températures journalières 2006-2026 : fichier local s'il existe, sinon UNE requête NASA."""
    if DATA_FILE.exists():
        return pd.read_csv(DATA_FILE, index_col=0, parse_dates=True)
    base = dict(parameters="PRECTOTCORR,T2M_MAX,T2M_MIN", community="AG", latitude=lat, longitude=lon, format="JSON")
    try:
        df = _to_df(_get(dict(base, start="20060101", end=POWER_END)))
    except Exception:  # repli : une requête par an, espacées
        parts = []
        for y in range(2006, 2027):
            parts.append(_to_df(_get(dict(base, start=f"{y}0101", end=f"{y}1231" if y < 2026 else POWER_END))))
            time.sleep(1.5)
        df = pd.concat(parts)
    try:
        DATA_FILE.parent.mkdir(exist_ok=True)
        df.to_csv(DATA_FILE)
    except Exception:
        pass
    return df


def season_weather(lat, lon):
    d = power_daily(lat, lon).copy()
    d["rain"] = d["PRECTOTCORR"].fillna(0)
    d[["T2M_MAX", "T2M_MIN"]] = d[["T2M_MAX", "T2M_MIN"]].interpolate().bfill().ffill()
    d["tmean"] = (d["T2M_MAX"] + d["T2M_MIN"]) / 2
    ra = {k: ra_mm(lat, k) for k in range(1, 367)}
    d["et0"] = (0.0023 * (d["tmean"] + 17.8) * (d["T2M_MAX"] - d["T2M_MIN"]).clip(lower=0) ** 0.5
                * d.index.dayofyear.map(ra).to_numpy()).clip(lower=0)
    out = {}
    for sname, sp in SEASONS.items():
        (m1, d1), (m2, d2) = sp["start"], sp["end"]
        for y in YEARS:
            sub = d.loc[pd.Timestamp(y, m1, d1):pd.Timestamp(y + sp["yoff"], m2, d2), ["rain", "et0", "tmean"]]
            if len(sub) < 100:
                raise ValueError(f"données NASA incomplètes pour {sname} {y}")
            out[(sname, y)] = sub
    return out


def tfac(t, p):
    a, b, c, d = p
    return max(0.0, min(1.0, (t - a) / (b - a), (d - t) / (d - c)))


def simulate_season(df, crop, budget, season):
    """Rendement relatif (0-1) = effet de l'eau (FAO-33) x effet de la température."""
    L, k1, k2, k3, zr, ky = CROP_FAO[crop]; sp = SEASONS[season]; plant = sp["plant"]
    taw = TAW * zr; raw = .5 * taw; dep = sp["dep0"] * taw; left = budget
    rain, et0, tm = df["rain"].to_numpy(), df["et0"].to_numpy(), df["tmean"].to_numpy()
    etc_sum = eta_sum = 0.0; tf = []
    for i in range(len(rain)):
        if i >= plant + L:
            break
        if i < plant:
            kc = .2
        else:
            t = (i - plant) / L
            kc = k1 if t < .2 else k1 + (k2 - k1) * (t - .2) / .3 if t < .5 else k2 if t < .8 else k2 + (k3 - k2) * (t - .8) / .2
            if left > 0 and dep > raw:
                a = min(left, 20.0, dep); dep -= a; left -= a
        ks = 1.0 if dep <= raw else max(0.0, (taw - dep) / (taw - raw))
        etc = kc * et0[i]; eta = ks * etc
        dep = min(taw, max(0.0, dep - rain[i] + eta))
        if i >= plant:
            etc_sum += etc; eta_sum += eta; tf.append(tfac(tm[i], CROP_T[crop]))
    ratio = eta_sum / etc_sum if etc_sum else 0.0
    return max(0.0, 1 - ky * (1 - ratio)) * (sum(tf) / len(tf) if tf else 0.0)


def season_yields(lat, lon, budget, wx=None):
    wx = wx if wx is not None else season_weather(lat, lon)
    return {s: pd.DataFrame({c: [simulate_season(wx[(s, y)], c, budget, s) for y in YEARS] for c in MY}, index=YEARS)
            for s in ORDER}



# ---------------------------------------------------------------------------------------------
# CONSEILS
# ---------------------------------------------------------------------------------------------
def suitability(Ys, thr=THR):
    return {(s, c): dict(mean=float(Ys[s][c].mean()), ok=int((Ys[s][c] >= thr).sum()), n=len(Ys[s]))
            for s in ORDER for c in MY}


def crop_score(c, s, suit, prio):
    m = suit[(s, c)]; rel = m["ok"] / m["n"]; I = INFO[c]
    p = {"Revenu": I["inc"], "Eau": 1 - I["need"] / 700, "Sol": ((I["n"] + 1) / 2 + I["org"]) / 2, "Résilience": rel}[prio]
    return .6 * m["mean"] + .4 * p


def replay_plan(Ys, seq, start_idx, thr=THR):
    """Rejoue 3 saisons consécutives sur chaque année passée : tient si chaque saison atteint le seuil."""
    ok = n = 0
    for C in YEARS:
        vals = []
        for k in range(3):
            t = 3 * C + start_idx + k; idx = t % 3; cal = t // 3 + (1 if idx == 2 else 0)
            if cal < YEARS[0] or cal > YEARS[-1]:
                break
            vals.append(float(Ys[ORDER[idx]].loc[cal, seq[k]]))
        else:
            n += 1; ok += min(vals) >= thr
    return ok, n


def reasons(seq, seasons, budget):
    out = []
    for c, s in zip(seq, seasons):
        if c == "Oignon":
            out.append("✔ L’oignon préfère la saison fraîche pour bien grossir." if s == "Saison fraîche"
                       else "⚠ L’oignon grossit mal quand il fait chaud.")
        if c == "Piment":
            out.append("⚠ En hivernage, le piment craint l’excès d’eau et les maladies." if s == "Hivernage"
                       else "✔ Le piment pousse bien quand il fait 20 à 30 °C.")
    if "Niébé" in seq:
        out.append("✔ Le niébé nourrit la terre en azote : moins d’engrais à acheter.")
    if len(set(seq)) == 3:
        out.append("✔ Trois cultures différentes : moins de maladies et d’insectes.")
    elif any(seq[i] == seq[i + 1] for i in range(2)):
        out.append("⚠ Deux fois la même culture de suite : la terre se fatigue.")
    if budget <= 0 and any(s != "Hivernage" for s in seasons):
        out.append("⚠ Sans eau pour arroser, il est très difficile de cultiver hors de l’hivernage (il ne pleut presque pas).")
    return list(dict.fromkeys(out))


def build_plans(Ys, suit, start_idx, last, prio, budget):
    seasons = [ORDER[(start_idx + k) % 3] for k in range(3)]
    cand = []
    for seq in itertools.product(MY, repeat=3):
        sc = sum(crop_score(c, s, suit, prio) for c, s in zip(seq, seasons)) / 3
        pen = .15 * sum(a == b for a, b in zip((last,) + seq[:-1], seq))
        cand.append((sc - pen, seq))
    cand.sort(key=lambda r: -r[0])
    props = [s for _, s in cand if s != (last,) * 3][:2]
    plans = []
    for title, seq in [("Ce que vous faites aujourd’hui", (last,) * 3), ("Notre conseil n° 1", props[0]),
                       ("Notre conseil n° 2", props[1])]:
        ok, n = replay_plan(Ys, seq, start_idx)
        plans.append(dict(title=title, seq=seq, seasons=seasons, ok=ok, n=n, reasons=reasons(seq, seasons, budget)))
    return plans
