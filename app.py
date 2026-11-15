"""Yaxanal Sunu Mbaaye – version TEST simplifiée : zone des Niayes, cultures oignon, piment et niébé, par saison.
Lancer :  streamlit run app.py
Code généré avec l'aide de Claude (Anthropic) et testé par l'équipe. Données : NASA POWER (pluie, températures).
"""
import datetime as dt
import itertools
import math
import os
import pathlib
import time

import numpy as np
import pandas as pd
import requests
import streamlit as st
try:
    import streamlit.components.v1 as components
except Exception:
    components = None

st.set_page_config(page_title="Yaxanal Sunu Mbaaye – Niayes", page_icon="🌱", layout="centered")
if components is not None:  # empêche la traduction automatique du navigateur
    try:
        components.html("""<script>
        const d = window.parent.document;
        d.documentElement.lang = 'fr'; d.documentElement.setAttribute('translate', 'no');
        </script>""", height=0)
    except Exception:
        pass
LIGHT = dict(bg="#f4f7f1", card="#ffffff", tx="#1b2a1f", mut="#5d6b60", ac="#1f8a4c", ac2="#e6f4ec", bd="#d9e2d6",
             okbg="#d8f3e3", oktx="#0f5a31", midbg="#fdebc8", midtx="#7a4a00", badbg="#fbdada", badtx="#8a1c1c")
DARK = dict(bg="#0f1a14", card="#17251c", tx="#e8efe9", mut="#9bb0a1", ac="#3ecf7a", ac2="#1f3326", bd="#2c3d32",
            okbg="#1c4a31", oktx="#aef0c9", midbg="#4a3a14", midtx="#ffd98a", badbg="#4d2222", badtx="#ffb4b4")
CSS = """
.card{background:var(--card);border:2px solid var(--bd);border-radius:22px;padding:18px 20px;margin:14px 0}
.card.rec{border-color:var(--ac);box-shadow:0 6px 20px rgba(31,138,76,.20)}
.ch{font-weight:800;font-size:1.15rem;color:var(--ac);margin-bottom:8px}
.big{font-size:1.7rem;font-weight:800;margin:6px 0 10px;color:var(--tx)}
.badge{display:inline-block;padding:8px 14px;border-radius:14px;font-weight:700;margin:6px 0}
.badge.ok{background:var(--okbg);color:var(--oktx)} .badge.mid{background:var(--midbg);color:var(--midtx)}
.badge.bad{background:var(--badbg);color:var(--badtx)}
.oth{margin-top:8px;color:var(--mut);font-size:1rem}
.tiles{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 12px}
.tile{flex:1 1 90px;border:2px solid var(--bd);border-radius:18px;padding:8px 4px;text-align:center;background:var(--ac2)}
.tile .sn{font-size:.8rem;color:var(--mut);font-weight:700}
.tile .ic{font-size:2.2rem;line-height:1.2}
.tile .cn{font-weight:800;font-size:1rem;color:var(--tx)}
.why{margin:6px 0 0 0;padding-left:20px;line-height:1.7;color:var(--tx)}
.ribbon{background:var(--ac);color:#fff !important;border-radius:999px;padding:2px 10px;font-size:.85rem;margin-left:8px}
.note{color:var(--mut);font-size:.95rem;margin-bottom:6px}
.hero{background:linear-gradient(135deg,#1f8a4c,#35b872);color:#fff;border-radius:26px;padding:22px 24px;margin:6px 0 14px}
.hero .t{font-size:2rem;font-weight:900;color:#fff} .hero .s{font-size:1.1rem;margin-top:4px;color:#fff}
.chip{display:inline-block;background:var(--ac2);color:var(--ac);border-radius:999px;padding:6px 14px;font-weight:700;margin:4px 0 10px}
[data-testid="stRadio"] label p{font-size:1.15rem}
[data-testid="stRadio"] > label p{font-weight:800;font-size:1.3rem}
[data-testid="stRadio"] [role="radiogroup"]{gap:10px}
[data-testid="stRadioOption"],[data-baseweb="radio"]{background:var(--card);border:2px solid var(--bd);border-radius:16px;padding:10px 16px;margin:0 !important}
[data-testid="stRadioOption"][data-selected="true"],[data-baseweb="radio"]:has(input:checked){border-color:var(--ac);background:var(--ac2)}
[data-testid="stRadioOption"] > div > div:first-child,[data-baseweb="radio"] > div:first-child{display:none}
[data-testid="stForm"]{border:2px solid var(--bd);border-radius:24px;background:var(--card);padding:18px}
[data-testid="stFormSubmitButton"]{width:100%}
[data-testid="stForm"] button{background:var(--ac) !important;border:none !important;border-radius:18px !important;padding:.9rem 1rem !important;width:100% !important}
[data-testid="stForm"] button p{font-size:1.4rem !important;font-weight:800 !important;color:#fff !important}
[data-testid="stExpander"] details{background:var(--card);border:2px solid var(--bd);border-radius:18px}
[data-testid="stCaptionContainer"]{color:var(--mut)}
h1{font-size:2.1rem !important}
.st-key-topbar [data-testid="stHorizontalBlock"]{flex-wrap:nowrap !important;align-items:center;gap:8px}
.st-key-topbar [data-testid="stColumn"]{min-width:0 !important}
.st-key-topbar [data-testid="stColumn"]:not(:first-child){flex:0 0 auto !important;width:auto !important}
.st-key-topbar [data-testid="stPopover"] button{min-height:52px;min-width:64px;padding:0 10px !important;border-radius:16px;border:2px solid var(--bd);background:var(--card);padding:0}
.st-key-topbar [data-testid="stPopover"] button p{font-size:1.4rem}
[data-testid="stPopoverBody"]{background:var(--card) !important;border:2px solid var(--bd);border-radius:18px}
"""


def theme_css(mode):
    v = lambda d: ";".join(f"--{k}:{x}" for k, x in d.items())
    if mode == "Auto":
        return f":root{{{v(LIGHT)}}}@media (prefers-color-scheme: dark){{:root{{{v(DARK)}}}}}" + CSS
    force = (".stApp{background:var(--bg)} [data-testid='stHeader']{background:transparent} "
             ".stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp span{color:var(--tx)} ")
    return f":root{{{v(DARK if mode == 'Sombre' else LIGHT)}}}" + force + CSS


MODE_ICON = {"Auto": "🌓", "Clair": "☀️", "Sombre": "🌙"}
MODE_LABEL = {"Auto": "🌓 Auto (selon l’appareil)", "Clair": "☀️ Clair", "Sombre": "🌙 Sombre"}
LANG_CODE = {"Français": "FR", "Wolof": "WO"}
mode = st.session_state.get("mode", "Auto")  # lus avant les widgets pour que les boutons montrent le choix en cours
lang = st.session_state.get("lang", "Français")
with st.container(key="topbar"):
    _sp, _cl, _c = st.columns([4, 1, 1])
    with _cl:
        with st.popover(f"🌐 {LANG_CODE[lang]}", help="Langue / Làkk"):
            lang = st.radio("Langue", list(LANG_CODE), key="lang")
    LANG = lang
    with _c:
        with st.popover(MODE_ICON[mode], help="Mode d’affichage : auto, clair ou sombre"):
            mode = st.radio("Mode d’affichage", list(MODE_ICON), format_func=MODE_LABEL.get, key="mode")
st.markdown(f"<style>{theme_css(mode)}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------------------------
# DONNÉES DE RÉFÉRENCE (ordres de grandeur ESTIMÉS, à valider avec un technicien agricole)
# ---------------------------------------------------------------------------------------------
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
# TEXTES WOLOF = PREMIÈRE VERSION, à faire relire par un locuteur wolof avant usage auprès des producteurs.
TXT = {
    "Français": dict(
        sub="Quelle culture planter, et quand ? · Zone des Niayes · version test", chip="📅 Nous sommes en {s}",
        q1="1. Pour quelle saison voulez-vous planter ?", q2="2. Que cultivez-vous le plus souvent ?",
        q3="3. Avez-vous de l’eau pour arroser (puits, forage, goutte-à-goutte) ?",
        q4="4. Qu’est-ce qui compte le plus pour vous ?", btn="👉 Voir mon conseil",
        h1="1. Quelle culture en priorité ?", h2="2. Votre plan pour les 3 prochaines saisons", prio="Priorité",
        wins="a bien réussi {ok} fois sur {n}", pwins="aurait bien marché {ok} fois sur {n}", rec="⭐ Recommandé",
        today="Ce que vous faites aujourd’hui", c1="Notre conseil n° 1", c2="Notre conseil n° 2",
        assume="Nous supposons que vous cultivez la même culture à chaque saison.",
        ok="✅ Solide", mid="🟠 Moyen", bad="🔴 Fragile", others="Voir les autres saisons de l’année",
        disc="Ce conseil est une aide. Il ne remplace pas l’avis de votre conseiller agricole : parlez-en avec lui, "
             "surtout pour les prix du marché, les maladies et les semences.",
        tech="Pour le conseiller agricole : détails techniques", ask_h="🗣️ Yaxanal, l’assistante (répond en wolof)",
        q_explain="Explique-moi mon conseil", q_why="Pourquoi ces cultures ?",
        ph="Écrivez votre question (en wolof ou en français)…", wait="Yaxanal réfléchit…"),
    "Wolof": dict(
        sub="Lan lañuy ji, ak kañ ? · Niayes · jéem", chip="📅 Léegi nekk nanu ci {s}",
        q1="1. Ci ban jamono nga bëgg a ji ?", q2="2. Lan ngay gën a ji ?",
        q3="3. Am nga ndox ngir ndoxal sa tool ? (pus, forage, goutte-à-goutte)",
        q4="4. Lan moo gën a am solo ci yaw ?", btn="👉 Wone ma ndigal bi",
        h1="1. Lan moo gën a baax ?", h2="2. Sa pexe ngir 3 jamono yu ñëw yi", prio="Jëkkal",
        wins="baax na {ok} yoon ci {n} at", pwins="dafa baax woon {ok} yoon ci {n} at", rec="⭐ Ndigal bu baax",
        today="Li ngay def tey", c1="Sunu ndigal bu njëkk", c2="Sunu ndigal bu ñaareel",
        assume="Danuy jàpp ne yaa ngi ji li ngay def tey ci jamono yépp.",
        ok="✅ Baax na torop", mid="🟠 Baax na tuuti", bad="🔴 Baaxul", others="Seetal yeneen jamono yi ci at mi",
        disc="Ndimbal rekk la. Bul fàtte laaj sa conseiller agricole, rawatina ci njëg ak feebar yi.",
        tech="Ngir conseiller agricole bi : xibaar yu teknik", ask_h="🗣️ Laaleel Yaxanal (dafay wax Wolof)",
        q_explain="Leeral ma ndigal bi", q_why="Lu tax ?", ph="Bind sa laaj fii…", wait="Yaxanal mi ngi xalaat…"),
}
CROP_NAME = {"Français": {c: c for c in MY}, "Wolof": {"Oignon": "Soble", "Piment": "Kaani", "Niébé": "Ñebbe"}}
SLAB = {"Français": {s: SEASONS[s]["label"] for s in SEASONS},
        "Wolof": {"Hivernage": "🌧️ Nawet (juillet ba octobre)", "Saison fraîche": "❄️ Jamono bu sedd (novembre ba février)",
                  "Saison chaude": "☀️ Jamono bu tàng (mars ba juin)"}}
SSHORT = {"Français": {"Hivernage": "🌧️ Hivernage", "Saison fraîche": "❄️ Saison fraîche", "Saison chaude": "☀️ Saison chaude"},
          "Wolof": {"Hivernage": "🌧️ Nawet", "Saison fraîche": "❄️ Sedd", "Saison chaude": "☀️ Tàng"}}
SNAME = {"Français": {"Hivernage": "hivernage", "Saison fraîche": "saison fraîche", "Saison chaude": "saison chaude"},
         "Wolof": {"Hivernage": "nawet", "Saison fraîche": "jamono bu sedd", "Saison chaude": "jamono bu tàng"}}
WLAB = {"Français": {"Oui": "Oui, j’en ai assez", "Peu": "Un peu seulement", "Non": "Non, seulement la pluie"},
        "Wolof": {"Oui": "Waaw, am naa ndox bu doy", "Peu": "Tuuti rekk", "Non": "Déedéet, taw rekk"}}
PLAB = {"Français": {"Revenu": "💰 Gagner plus d’argent", "Eau": "💧 Économiser l’eau",
                     "Sol": "🌍 Garder la terre en bonne santé", "Résilience": "☀️ Mieux résister aux années sèches"},
        "Wolof": {"Revenu": "💰 Am xaalis", "Eau": "💧 Wattu ndox", "Sol": "🌍 Wattu suuf si",
                  "Résilience": "☀️ Dëgër ci at yu wow"}}
ERR = ("Nous n’arrivons pas à joindre les données de la NASA. Vérifiez votre connexion internet et réessayez "
       "dans un instant.")


def T(k):
    return TXT[LANG][k]


THR = 0.6  # une saison « réussit » si le rendement atteint 60 % du rendement possible


def lab(c):
    return f"{ICON[c]} {CROP_NAME[LANG][c]}"


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


@st.cache_data(ttl=86400 * 7, show_spinner=False)
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


@st.cache_data(ttl=86400)
def season_yields(lat, lon, budget):
    wx = season_weather(lat, lon)
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


def badge(ok, n):
    r = ok / n if n else 0
    return ("ok", T("ok")) if r >= .8 else ("mid", T("mid")) if r >= .5 else ("bad", T("bad"))


# ---------------------------------------------------------------------------------------------
# ASSISTANTE EN WOLOF (Claude, via l'API Anthropic) : appuyée sur les résultats calculés ci-dessus
# ---------------------------------------------------------------------------------------------
MODEL = "claude-sonnet-5-5"
SYSTEM = """Tu es « Yaxanal », une assistante agricole bienveillante qui aide des producteurs des Niayes (Sénégal).
Réponds TOUJOURS en wolof (orthographe latine standard), avec des phrases très courtes et simples, comme on parle à un voisin agriculteur. Pour les mots techniques sans équivalent courant, garde le mot français (comme le font les locuteurs wolof) plutôt que d'inventer un mot.
Appuie-toi UNIQUEMENT sur les données du CONTEXTE ci-dessous. N'invente jamais de prix, de doses de produits chimiques, de variétés ni de dates précises. Si la question sort du contexte (maladies, pesticides, marché), dis honnêtement que tu n'en es pas sûre et invite à demander au conseiller agricole.
Rappelle de temps en temps que ce conseil est une aide et ne remplace pas le conseiller agricole. Si tu hésites sur un mot wolof, dis-le et ajoute le mot français entre parenthèses.
Maximum 5 phrases, sans tableau ni jargon."""


def get_client():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        try:
            key = st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            key = None
    if not key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=key)
    except Exception:
        return None


def ask_assistant(history, context, client):
    resp = client.messages.create(model=MODEL, max_tokens=600, system=SYSTEM + "\n\nCONTEXTE :\n" + context,
                                  messages=history[-8:])
    return "".join(getattr(b, "text", "") for b in resp.content).strip() or "…"


def build_context(sidx, usual, water_key, prio_key, suit, plans):
    rows = [f"Zone : Niayes. Saison choisie : {SEASONS[ORDER[sidx]]['label']}. Culture habituelle : {usual}.",
            f"Eau pour arroser : {WATER_FR[water_key]}. Priorité du producteur : {PRIO_FR[prio_key]}."]
    for s_ in ORDER:
        rk = sorted(MY, key=lambda c: -crop_score(c, s_, suit, prio_key))
        rows.append(f"{SEASONS[s_]['label']} : culture prioritaire {rk[0]} (réussie {suit[(s_, rk[0])]['ok']} années sur "
                    f"{suit[(s_, rk[0])]['n']}) ; autres : " + ", ".join(
                        f"{c} ({suit[(s_, c)]['ok']}/{suit[(s_, c)]['n']})" for c in rk[1:]))
    for p in plans:
        rows.append(f"{p['title']} : " + " puis ".join(f"{c} ({SEASONS[s_]['label']})" for c, s_ in zip(p["seq"], p["seasons"]))
                    + f" ; aurait bien marché {p['ok']} fois sur {p['n']} ; points : " + " ".join(p["reasons"]))
    return "\n".join(rows)


# ---------------------------------------------------------------------------------------------
# INTERFACE
# ---------------------------------------------------------------------------------------------
st.markdown(f'<div class="hero"><div class="t">🌱 Yaxanal Sunu Mbaaye</div><div class="s">{T("sub")}</div></div>',
            unsafe_allow_html=True)
now_idx = ORDER.index(month_season(dt.date.today().month))
st.markdown(f'<div class="chip">{T("chip").format(s=SNAME[LANG][ORDER[now_idx]])}</div>', unsafe_allow_html=True)

with st.form("questions"):
    sidx = st.radio(T("q1"), range(3), index=now_idx, format_func=lambda i: SLAB[LANG][ORDER[i]], key="q_season")
    usual = st.radio(T("q2"), MY, format_func=lab, horizontal=True, key="q_crop")
    water = st.radio(T("q3"), list(WATER_BUDGET), format_func=lambda k: WLAB[LANG][k], key="q_water")
    prio = st.radio(T("q4"), PRIO_KEYS, format_func=lambda k: PLAB[LANG][k], key="q_prio")
    go = st.form_submit_button(T("btn"), type="primary")
if go:
    st.session_state["inp"] = (sidx, usual, water, prio)
    st.session_state["chat"] = []

if "inp" in st.session_state:
    sidx, usual, water, prio = st.session_state["inp"]
    budget = WATER_BUDGET[water]
    try:
        with st.spinner("Nous consultons 20 ans de données de la NASA… (la première fois, cela peut durer une minute)"):
            lat, lon = round(NIAYES[0], 2), round(NIAYES[1], 2)
            Ys = season_yields(lat, lon, budget)
        suit = suitability(Ys)
        plans = build_plans(Ys, suit, sidx, usual, prio, budget)
    except Exception as e:
        st.error(ERR)
        with st.expander("Détails pour l’équipe technique"):
            st.code(f"{type(e).__name__}: {e}")
            st.caption("Astuce : lancez « python telecharger_donnees.py » une fois pour enregistrer les données "
                       "NASA dans le dossier data/ ; l’app les lira ensuite sans internet.")
        st.stop()
    titles = [T("today"), T("c1"), T("c2")]

    st.header(T("h1"))

    def season_card(s_):
        ranked = sorted(MY, key=lambda c: -crop_score(c, s_, suit, prio))
        best = ranked[0]; m = suit[(s_, best)]; cls, t = badge(m["ok"], m["n"])
        oth = " &nbsp;·&nbsp; ".join(f"{lab(c)} {badge(suit[(s_, c)]['ok'], suit[(s_, c)]['n'])[1].split(' ')[0]} "
                                     f"{suit[(s_, c)]['ok']}/{suit[(s_, c)]['n']}" for c in ranked[1:])
        st.markdown(f'<div class="card"><div class="ch">{SLAB[LANG][s_]}</div>'
                    f'<div class="big">🥇 {T("prio")} : {lab(best)}</div>'
                    f'<div class="badge {cls}">{t} · {T("wins").format(ok=m["ok"], n=m["n"])}</div>'
                    f'<div class="oth">{oth}</div></div>', unsafe_allow_html=True)
    season_card(ORDER[sidx])
    with st.expander(T("others")):
        for s_ in ORDER:
            if s_ != ORDER[sidx]:
                season_card(s_)

    st.header(T("h2"))
    for k, p in enumerate(plans):
        cls, t = badge(p["ok"], p["n"])
        tiles = "".join(f'<div class="tile"><div class="sn">{SSHORT[LANG][s_]}</div><div class="ic">{ICON[c]}</div>'
                        f'<div class="cn">{CROP_NAME[LANG][c]}</div></div>' for c, s_ in zip(p["seq"], p["seasons"]))
        why = "".join(f"<li>{r}</li>" for r in p["reasons"])
        note = f'<div class="note">{T("assume")}</div>' if k == 0 else ""
        ribbon = f'<span class="ribbon">{T("rec")}</span>' if k == 1 else ""
        st.markdown(f'<div class="card {"rec" if k == 1 else ""}"><div class="ch">{titles[k]}{ribbon}</div>{note}'
                    f'<div class="tiles">{tiles}</div>'
                    f'<div class="badge {cls}">{t} · {T("pwins").format(ok=p["ok"], n=p["n"])}</div>'
                    f'<ul class="why">{why}</ul></div>', unsafe_allow_html=True)
    st.caption(T("disc"))

    # --- assistante en wolof ---
    st.header(T("ask_h"))
    history = st.session_state.setdefault("chat", [])
    b1, b2 = st.columns(2)
    pending = None
    if b1.button(T("q_explain"), use_container_width=True):
        pending = "Explique-moi mon conseil, simplement."
    if b2.button(T("q_why"), use_container_width=True):
        pending = "Pourquoi ces cultures pour ces saisons ?"
    q = st.chat_input(T("ph")) or pending
    if q:
        history.append(dict(role="user", content=q))
        client = get_client()
        if client is None:
            ans = ("L’assistante n’est pas encore activée : il manque la clé API Claude. Ajoutez-la dans la variable "
                   "d’environnement ANTHROPIC_API_KEY ou dans le fichier .streamlit/secrets.toml, puis relancez l’application "
                   "(étapes détaillées dans README_assistante.md).")
        else:
            try:
                with st.spinner(T("wait")):
                    ans = ask_assistant(history, build_context(sidx, usual, water, prio, suit, plans), client)
            except Exception as e:
                ans = f"L’assistante est momentanément indisponible ({type(e).__name__}). Réessayez dans un instant."
        history.append(dict(role="assistant", content=ans))
    for m in history:
        with st.chat_message("user" if m["role"] == "user" else "assistant", avatar="🧑🏾‍🌾" if m["role"] == "user" else "🌱"):
            st.write(m["content"])
    st.caption("Les textes et réponses en wolof peuvent contenir des erreurs : faites-les relire par un locuteur. "
               "L’assistante ne remplace pas le conseiller agricole.")
    with st.expander(T("tech")):
        st.markdown(
            "- **Zone** : Niayes, point de référence 14.85, -17.20 ; sol sableux supposé ; semis au début de chaque saison (début juillet pour l’hivernage).\n"
            "- **Données** : NASA POWER, pluie et températures journalières 2006-2025 (résolution d’environ 50 km).\n"
            "- **Méthode** : bilan d’eau journalier inspiré de FAO-56 (évapotranspiration de Hargreaves-Samani), réponse du rendement à l’eau FAO-33, "
            "multipliée par un effet de la température moyenne propre à chaque culture. Une saison « réussit » si le rendement atteint 60 % du rendement possible.\n"
            "- **Limites** : coefficients des cultures et seuils de température = ordres de grandeur, **ceux du piment sont estimés** ; les maladies ne sont pas modélisées ; "
            "rien n’est validé sur le terrain. « Assez d’eau » est supposé illimité, « un peu » = 150 mm par saison. Prix, maladies, érosion et dates de semis réelles ne sont pas pris en compte.")
        for s_ in ORDER:
            st.caption(f"{SEASONS[s_]['label']} : rendement relatif (% du rendement possible) par année")
            st.dataframe((Ys[s_] * 100).round(0).astype(int).rename_axis("Année"))
