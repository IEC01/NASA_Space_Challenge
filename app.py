"""AgriSpace Dakar – Assistant de rotation culturale (NASA Space Apps)
Lancer :  pip install -r requirements.txt  &&  streamlit run app.py
Données : NASA POWER (https://power.larc.nasa.gov/docs/services/api/)
  PRECTOTCORR = pluie corrigée (mm/j, basée sur GPM IMERG/MERRA-2)
  T2M         = température à 2 m (°C)
  GWETROOT    = humidité de la zone racinaire (0-1, MERRA-2)
"""
import itertools
import math
from concurrent.futures import ThreadPoolExecutor
import folium
import numpy as np
import pandas as pd
import requests
import streamlit as st
try:
    import streamlit.components.v1 as components
except Exception:  # API retirée dans une future version : on s'en passe
    components = None
from streamlit_folium import st_folium

st.set_page_config(page_title="Yaxanal Sunu Mbaaye ", page_icon="🌱", layout="wide")

# Empêche la traduction automatique du navigateur (ex. « parcelle » -> « colis »)
if components is not None:
    try:
        components.html("""<script>
        const d = window.parent.document;
        d.documentElement.lang = 'fr'; d.documentElement.setAttribute('translate', 'no');
        if (!d.querySelector('meta[name=google]')) {
          const m = d.createElement('meta'); m.name = 'google'; m.content = 'notranslate'; d.head.appendChild(m);
        }
        </script>""", height=0)
    except Exception:
        pass

ZONES = {  # lat, lon, solutions de sol, valeurs de repli (pluie, T, humidité, NDVI) si l'API est indisponible
    "Niayes (maraîchage)": (14.85, -17.20, ["Sableux"], (350, 26, .22, .45)),
    "Bassin arachidier (Kaolack)": (14.15, -16.07, ["Sableux", "Sablo-argileux"], (600, 28, .18, .38)),
    "Vallée du fleuve (Podor)": (16.65, -14.96, ["Argileux", "Sablo-argileux"], (250, 30, .20, .35)),
    "Sénégal oriental (Tambacounda)": (13.77, -13.67, ["Sablo-argileux", "Argileux"], (850, 29, .25, .55)),
    "Casamance (Ziguinchor)": (12.56, -16.27, ["Sablo-argileux", "Argileux"], (1100, 27, .32, .68)),
}
SOL_F = {"Sableux": .85, "Sablo-argileux": 1.0, "Argileux": 1.1}
CROPS = {  # famille, besoin eau (mm), azote, tolérance sécheresse, revenu, matière organique
    "Mil": ("Céréale", 350, -.5, .9, .4, .5), "Sorgho": ("Céréale", 400, -.5, .85, .4, .5),
    "Maïs": ("Céréale", 550, -1, .4, .6, .6), "Arachide": ("Légumineuse", 450, .8, .6, .7, .6),
    "Niébé": ("Légumineuse", 300, 1, .9, .5, .7), "Sésame": ("Oléagineux", 350, -.2, .8, .7, .4),
    "Oignon": ("Maraîchère", 500, -.8, .3, .9, .3),
}


@st.cache_data(ttl=86400, show_spinner="Récupération des données NASA POWER…")
def nasa_climato(lat, lon, years=(2023, 2024, 2025)):
    """Moyenne de la saison des pluies (juin-octobre) sur plusieurs années."""
    rows = []
    for y in years:
        r = requests.get(
            "https://power.larc.nasa.gov/api/temporal/daily/point",
            params=dict(parameters="PRECTOTCORR,T2M,GWETROOT", community="AG",
                        latitude=lat, longitude=lon, start=f"{y}0601", end=f"{y}1031", format="JSON"),
            timeout=60)
        r.raise_for_status()
        p = r.json()["properties"]["parameter"]
        df = pd.DataFrame(p).replace(-999, pd.NA).dropna()
        rows.append((df.PRECTOTCORR.sum(), df.T2M.mean(), df.GWETROOT.mean()))
    d = pd.DataFrame(rows, columns=["rain", "temp", "sm"])
    return d.mean().to_dict(), d


ORNL = "https://modis.ornl.gov/rst/api/v1/MOD13Q1"


@st.cache_data(ttl=86400, show_spinner="Récupération du NDVI MODIS…")
def nasa_ndvi(lat, lon, years=(2023, 2024, 2025)):
    """NDVI MODIS (MOD13Q1, 250 m, composites de 16 jours), saison juin-octobre.
    Retourne (série temporelle, moyenne par année)."""
    base = dict(latitude=lat, longitude=lon)
    dates = requests.get(f"{ORNL}/dates", params=base, timeout=60).json()["dates"]
    recs = []
    for y in years:
        sel = [d["modis_date"] for d in dates
               if f"{y}-06-01" <= d["calendar_date"] <= f"{y}-10-31"]
        for i in range(0, len(sel), 10):  # l'API limite à 10 pas de temps par requête
            chunk = sel[i:i + 10]
            r = requests.get(f"{ORNL}/subset", params=dict(
                base, band="250m_16_days_NDVI", startDate=chunk[0], endDate=chunk[-1],
                kmAboveBelow=0, kmLeftRight=0), timeout=60)
            r.raise_for_status()
            for e in r.json()["subset"]:
                v = e["data"][0]
                if v > -2000:  # -3000 = valeur manquante
                    recs.append((pd.to_datetime(e["calendar_date"]), v / 10000))
    ts = pd.DataFrame(recs, columns=["date", "NDVI"]).set_index("date").sort_index()
    return ts, ts.groupby(ts.index.year).NDVI.mean()


# ---------------------------------------------------------------------------
# REJEU SUR 20 ANS : bilan hydrique journalier inspiré de FAO-56 (ET0 de Hargreaves-Samani,
# coefficient cultural Kc, stress hydrique Ks) et réponse du rendement à l'eau (FAO-33, Ky).
# Les paramètres ci-dessous sont des ordres de grandeur à valider avec des agronomes.
# ---------------------------------------------------------------------------
YEARS = list(range(2006, 2026))  # 20 saisons des pluies
# durée du cycle (j), Kc initial, Kc milieu, Kc fin, profondeur racinaire (m), Ky
CROP_FAO = {
    "Mil": (90, .30, 1.00, .30, 1.0, .8), "Sorgho": (110, .30, 1.00, .55, 1.2, .9),
    "Maïs": (100, .30, 1.20, .60, 1.0, 1.25), "Arachide": (110, .40, 1.15, .60, .6, .7),
    "Niébé": (70, .40, 1.05, .60, .8, .8), "Sésame": (90, .35, 1.10, .25, 1.0, .8),
    "Oignon": (120, .70, 1.05, .75, .5, 1.1),
}
TAW_M = {"Sableux": 80, "Sablo-argileux": 120, "Argileux": 160}  # eau utile du sol, mm par m
PLANT_OFFSET = {"15 juin": 14, "1er juillet": 30, "15 juillet": 44}  # jours après le 1er juin


def ra_mm(lat, doy):
    """Rayonnement extraterrestre (mm/j équivalent), FAO-56 éq. 21."""
    phi = math.radians(lat)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    d = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(max(-1, min(1, -math.tan(phi) * math.tan(d))))
    ra = (24 * 60 / math.pi) * 0.0820 * dr * (ws * math.sin(phi) * math.sin(d)
                                              + math.cos(phi) * math.cos(d) * math.sin(ws))
    return ra / 2.45


def _fetch_year(lat, lon, y):
    r = requests.get(
        "https://power.larc.nasa.gov/api/temporal/daily/point",
        params=dict(parameters="PRECTOTCORR,T2M_MAX,T2M_MIN", community="AG", latitude=lat,
                    longitude=lon, start=f"{y}0601", end=f"{y}1130", format="JSON"), timeout=60)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["properties"]["parameter"]).replace(-999, float("nan"))
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df["rain"] = df["PRECTOTCORR"].fillna(0)
    df[["T2M_MAX", "T2M_MIN"]] = df[["T2M_MAX", "T2M_MIN"]].interpolate().bfill().ffill()
    tmean = (df["T2M_MAX"] + df["T2M_MIN"]) / 2
    ra = np.array([ra_mm(lat, d) for d in df.index.dayofyear])
    df["et0"] = (0.0023 * (tmean + 17.8) * (df["T2M_MAX"] - df["T2M_MIN"]).clip(lower=0) ** 0.5 * ra).clip(lower=0)
    return y, df[["rain", "et0"]]


@st.cache_data(ttl=86400 * 7, show_spinner="Téléchargement de 20 ans de climat NASA POWER (première fois seulement)…")
def nasa_daily20(lat, lon):
    with ThreadPoolExecutor(max_workers=6) as ex:
        return dict(ex.map(lambda y: _fetch_year(lat, lon, y), YEARS))


def simulate(wx, crop, taw_m, irr, plant_off):
    """Rendement relatif (0-1) d'une culture pour une saison : 1 - Ky * (1 - ETa/ETc)."""
    L, k1, k2, k3, zr, ky = CROP_FAO[crop]
    taw = taw_m * zr; raw = 0.5 * taw
    dep = 0.9 * taw                      # sol sec au 1er juin
    irr_left = 250.0 if irr else 0.0     # même hypothèse que le score d'eau : +250 mm
    etc_sum = eta_sum = 0.0
    for i, (rain, et0) in enumerate(zip(wx["rain"].to_numpy(), wx["et0"].to_numpy())):
        if i >= plant_off + L:
            break
        if i < plant_off:
            kc = 0.2                     # jachère
        else:
            t = (i - plant_off) / L
            kc = k1 if t < .2 else k1 + (k2 - k1) * (t - .2) / .3 if t < .5 else k2 if t < .8 else k2 + (k3 - k2) * (t - .8) / .2
            if irr_left > 0 and dep > raw:
                a = min(irr_left, 20.0, dep); dep -= a; irr_left -= a
        ks = 1.0 if dep <= raw else max(0.0, (taw - dep) / (taw - raw))
        etc = kc * et0; eta = ks * etc
        dep = min(taw, max(0.0, dep - rain + eta))
        if i >= plant_off:
            etc_sum += etc; eta_sum += eta
    ratio = eta_sum / etc_sum if etc_sum else 0.0
    return max(0.0, 1 - ky * (1 - ratio))


@st.cache_data(ttl=86400)
def rel_yields(lat, lon, sol, irr, off):
    wx = nasa_daily20(lat, lon)
    return pd.DataFrame({c: [simulate(wx[y], c, TAW_M[sol], irr, off) for y in YEARS] for c in CROP_FAO}, index=YEARS)


def replay(Y, seq, thr):
    """Rejoue la rotation sur chaque cycle de 3 saisons consécutives (2006-08, 2007-09, ...)."""
    rows = []
    for s0 in YEARS[:-2]:
        vals = [float(Y.loc[s0 + i, c]) for i, c in enumerate(seq)]
        j = int(np.argmin(vals))
        rows.append(dict(start=s0, min=min(vals), mean=sum(vals) / 3, worst_crop=seq[j],
                         worst_year=s0 + j, held=min(vals) >= thr))
    return pd.DataFrame(rows).set_index("start")


def score(seq, last, water, sf):
    fam = [CROPS[last][0]] + [CROPS[c][0] for c in seq]
    w = dr = inc = n = org = pen = 0
    for i, c in enumerate(seq):
        _, need, nn, d, rev, o = CROPS[c]
        ok = water >= need
        w += min(1, water / need); dr += d * (.9 if ok else 1) + (.1 if ok else 0)
        inc += rev * min(1, water / need + .15); n += nn; org += o
        pen += fam[i] == fam[i + 1]
    div = len(set(fam[1:]))
    w_use = 1 - sum(CROPS[c][1] for c in seq) / 1800
    return dict(
        Eau=max(0, min(1, w / 3 * .6 + w_use * .4 + .1)),
        Sol=max(0, min(1, .35 + n / 3 * .3 + org / 3 * .25 + (div - 1) * .1 - pen * .3)) * sf,
        Revenu=min(1, inc / 3), Résilience=min(1, dr / 3), pen=pen, div=div, n=n)


@st.cache_data(ttl=86400, show_spinner="Analyse du sol (SoilGrids)…")
def soilgrids(lat, lon):
    """Texture du sol (0-30 cm) via SoilGrids / ISRIC. Retourne sable, limon, argile en %."""
    r = requests.get("https://rest.isric.org/soilgrids/v2.0/properties/query", params=[
        ("lon", lon), ("lat", lat), ("property", "sand"), ("property", "silt"), ("property", "clay"),
        ("depth", "0-5cm"), ("depth", "5-15cm"), ("depth", "15-30cm"), ("value", "mean")], timeout=60)
    r.raise_for_status()
    return parse_soilgrids(r.json())


def parse_soilgrids(js):
    out = {}
    for layer in js["properties"]["layers"]:
        d = layer["unit_measure"].get("d_factor", 10) or 10
        vals = [x["values"]["mean"] for x in layer["depths"] if x["values"].get("mean") is not None]
        out[layer["name"]] = sum(vals) / len(vals) / d  # g/kg -> %
    return out


def texture_class(t):
    """Regroupe la texture en 3 classes utilisées par le modèle."""
    if t["clay"] >= 35: return "Argileux"
    if t["sand"] >= 70 and t["clay"] < 15: return "Sableux"
    return "Sablo-argileux"


BBOX = (12.2, 16.8, -17.6, -11.3)  # lat min/max, lon min/max : Sénégal (approx.)


def nearest_zone(lat, lon):
    """Zone agro-écologique la plus proche (sol, valeurs de repli)."""
    return min(ZONES, key=lambda z: (ZONES[z][0] - lat) ** 2 + (ZONES[z][1] - lon) ** 2)


st.title("🌱 YAXANAL SUNU MBAAYE – Votre Assistant Agricole ")
st.caption("Observations NASA (POWER, MODIS) + sol local + priorités de l’agriculteur → rotations sur 3 saisons")

with st.sidebar:
    mode = st.radio("Localisation", ["Zone prédéfinie", "Cliquer sur la carte"])
    if mode == "Zone prédéfinie":
        zone = st.selectbox("Zone", list(ZONES), key="zone")
        lat, lon, sols, fb = ZONES[zone]
    else:
        base = ZONES[st.session_state.get("zone", list(ZONES)[0])]
        lat, lon = st.session_state.get("pt", (base[0], base[1]))
        zone = nearest_zone(lat, lon)
        sols, fb = ZONES[zone][2], ZONES[zone][3]
        st.caption(f"📍 {lat:.3f}, {lon:.3f} · zone la plus proche : {zone}")
    auto_sol = st.checkbox("Détecter le sol (SoilGrids)", value=True)
    sol = None
    if auto_sol:
        try:
            tex = soilgrids(round(lat, 3), round(lon, 3))
            sol = texture_class(tex)
            st.caption(f"🧪 Sol détecté : **{sol}** (sable {tex['sand']:.0f} %, "
                       f"limon {tex['silt']:.0f} %, argile {tex['clay']:.0f} %)")
        except Exception as e:
            st.warning(f"SoilGrids indisponible ({type(e).__name__}) : choisissez le sol à la main.")
    if sol is None:
        sol = st.selectbox("Type de sol", sols)
    last = st.selectbox("Dernière culture", list(CROPS))
    irr = st.checkbox("Irrigation disponible")
    clim = st.slider("Scénario pluie (%)", -40, 20, 0)
    st.subheader("Priorités")
    W = {k: st.slider(k, 0, 10, v) for k, v in
         {"Eau": 7, "Sol": 8, "Revenu": 5, "Résilience": 7}.items()}

st.subheader("Localisez votre parcelle")
fmap = folium.Map(location=[lat, lon], zoom_start=7 if mode == "Cliquer sur la carte" else 6,
                  tiles="OpenStreetMap")
for zn, (zlat, zlon, *_r) in ZONES.items():
    folium.CircleMarker([zlat, zlon], radius=5, color="#888", fill=True, tooltip=zn).add_to(fmap)
folium.Marker([lat, lon], tooltip="Parcelle analysée", icon=folium.Icon(color="green", icon="leaf")).add_to(fmap)
out = st_folium(fmap, height=360, use_container_width=True, returned_objects=["last_clicked"], key="map")
click = (out or {}).get("last_clicked")
if click and mode == "Cliquer sur la carte":
    new_pt = (round(click["lat"], 3), round(click["lng"], 3))
    fresh = new_pt != st.session_state.get("last_click")  # n'alerter qu'au moment du clic
    st.session_state["last_click"] = new_pt
    if not (BBOX[0] <= new_pt[0] <= BBOX[1] and BBOX[2] <= new_pt[1] <= BBOX[3]):
        if fresh:
            st.warning("Point hors du Sénégal ignoré : l’analyse reste sur le dernier point valide.")
    elif new_pt != st.session_state.get("pt"):
        st.session_state["pt"] = new_pt
        st.rerun()
elif mode == "Zone prédéfinie":
    st.caption("Passez en mode « Cliquer sur la carte » (barre latérale) pour choisir une parcelle précise.")

try:
    m, detail = nasa_climato(lat, lon)
    src = "NASA POWER (moyenne saisons 2023-2025, juin-octobre)"
except Exception as e:
    m = dict(rain=fb[0], temp=fb[1], sm=fb[2]); detail = None
    src = f"valeurs de repli (API NASA indisponible : {type(e).__name__})"

try:
    ndvi_ts, ndvi_yr = nasa_ndvi(lat, lon)
    ndvi_last, ndvi_norm = float(ndvi_yr.iloc[-1]), float(ndvi_yr.mean())
    src_n = "NASA MODIS MOD13Q1 (via ORNL DAAC)"
except Exception as e:
    ndvi_ts = ndvi_yr = None
    ndvi_last = ndvi_norm = fb[3]
    src_n = f"valeur de repli (API MODIS indisponible : {type(e).__name__})"

# Anomalie de végétation : < 1 = végétation en retard sur la normale -> stress hydrique supposé
anom = ndvi_last / ndvi_norm if ndvi_norm else 1.0
stress = min(1.0, max(.6, anom / .95))  # tolérance de 5 % avant de pénaliser

rain = m["rain"] * (1 + clim / 100)
water_raw = rain + (250 if irr else 0)
water = water_raw * stress
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Pluie saison (mm)", round(rain)); c2.metric("Température (°C)", round(m["temp"], 1))
c3.metric("Humidité racinaire", f"{m['sm']:.2f}")
c4.metric("NDVI (dernière saison)", round(ndvi_last, 2), f"{(anom - 1) * 100:+.0f} % vs normale")
c5.metric("Eau utile (mm)", round(water), f"{round(water - water_raw)} mm (stress NDVI)" if stress < 1 else None)
st.caption(f"Sources : {src} · {src_n}")
if stress < 1:
    st.warning("Végétation en retard sur la normale : un stress hydrique est supposé, "
               "l’eau utile est réduite et les cultures gourmandes en eau sont pénalisées.")
if ndvi_ts is not None:
    with st.expander("Courbe NDVI saison des pluies (MODIS, 250 m)"):
        st.line_chart(ndvi_ts)
if detail is not None:
    st.dataframe(detail.round(2).rename(index=lambda i: 2023 + i, columns={"rain": "Pluie (mm)", "temp": "Température (°C)", "sm": "Humidité racinaire"}), use_container_width=False)

tot = sum(W.values()) or 1
res, seen, top_rots = [], set(), []
for s in itertools.product(CROPS, repeat=3):
    sc = score(s, last, water, SOL_F[sol])
    g = sum(sc[k] * W[k] for k in W) / tot
    res.append((g, s, sc))
res.sort(key=lambda r: -r[0])
st.subheader("Rotations recommandées")
shown = 0
for g, s, sc in res:
    key = tuple(sorted(s))
    if key in seen: continue
    seen.add(key); shown += 1; top_rots.append(s)
    with st.container(border=True):
        st.markdown(f"**Après {last} → " + " › ".join(f"S{i+1} : {c}" for i, c in enumerate(s)) + f"**  —  score **{round(g*100)}**")
        cols = st.columns(4)
        for col, k in zip(cols, W): col.progress(float(sc[k]), text=f"{k} {round(sc[k]*100)}%")
        notes = []
        if sc["n"] > .8: notes.append("légumineuses : restauration de l’azote")
        if sc["div"] == 3: notes.append("3 familles : moins de maladies")
        if sc["pen"]: notes.append("⚠ même famille consécutive")
        lourds = [c for c in s if CROPS[c][1] > water]
        if lourds: notes.append("⚠ eau insuffisante pour " + ", ".join(lourds))
        st.caption(" · ".join(notes))
    if shown == 5: break

# ---------------------------------------------------------------------------
st.divider()
st.header("Rejouer ma rotation sur 20 ans de climat NASA")
st.caption("Choisissez ou ajustez trois rotations (par défaut : les 3 premières du classement). L'outil les rejoue "
           "sur chaque cycle de 3 saisons consécutives (2006-2025) et compte combien auraient tenu.")
labels = ["Rotation A", "Rotation B", "Rotation C"]
seqs = []
for k, col in enumerate(st.columns(3)):
    with col:
        st.markdown(f"**{labels[k]}**")
        seqs.append([st.selectbox(f"Saison {j + 1}", list(CROPS), index=list(CROPS).index(top_rots[k][j]),
                                  key=f"rot{k}_{j}") for j in range(3)])
p1, p2 = st.columns(2)
plant = p1.select_slider("Date de semis", list(PLANT_OFFSET), value="1er juillet")
thr = p2.slider("Une saison « tient » si le rendement relatif est d'au moins", 0.3, 0.9, 0.6, 0.05,
                help="Rendement relatif = rendement obtenu / rendement potentiel sans stress hydrique.")
if st.button("▶ Lancer le rejeu sur 20 ans", type="primary"):
    st.session_state["replay_on"] = True
if st.session_state.get("replay_on"):
    try:
        Y = rel_yields(round(lat, 2), round(lon, 2), sol, bool(irr), PLANT_OFFSET[plant])
        R = [replay(Y, sq, thr) for sq in seqs]
        n = len(R[0])
        st.subheader("Résultat")
        for k, col in enumerate(st.columns(3)):
            r = R[k]; w = r["min"].idxmin()
            with col:
                st.markdown(f"**{labels[k]}** : " + " › ".join(seqs[k]))
                st.metric("Cycles de 3 ans qui tiennent", f"{int(r['held'].sum())} / {n}")
                st.metric("Rendement relatif moyen", f"{r['mean'].mean():.0%}")
                st.caption(f"Pire cycle : {w}–{w + 2} ({r['min'].min():.0%})")
        st.line_chart(pd.DataFrame({labels[k]: R[k]["min"] for k in range(3)}).rename_axis("Cycle commençant en"))
        st.caption("Courbe : rendement relatif de la saison la plus touchée de chaque cycle de 3 ans (plus haut = plus sûr).")
        st.markdown("**Pourquoi la rotation A échoue, quand elle échoue**")
        fails = R[0][~R[0]["held"]]
        if fails.empty:
            st.success("Aucun cycle sous le seuil sur 2006-2025.")
        else:
            for s0, row in fails.sort_values("min").head(6).iterrows():
                st.write(f"• {s0}–{s0 + 2} : {row['worst_crop']} en {row['worst_year']} → "
                         f"{row['min']:.0%} du rendement potentiel (stress hydrique).")
        with st.expander("Rendement relatif par culture et par année"):
            st.dataframe((Y * 100).round(0).astype(int).rename_axis("Année"))
        st.caption("Méthode : bilan hydrique journalier inspiré de FAO-56 (ET0 de Hargreaves-Samani, Kc, Ks), réponse du "
                   "rendement à l'eau de FAO-33. Pluie et températures : NASA POWER, juin à novembre. Coefficients "
                   "approximatifs, non validés sur le terrain ; POWER a une résolution d'environ 50 km.")
    except Exception as e:
        st.error(f"Rejeu impossible ({type(e).__name__}) : les données NASA POWER n'ont pas pu être téléchargées. Réessayez.")
