"""Tests du moteur (sans internet) : python -m pytest -q"""
import numpy as np
import pandas as pd
import pytest

import moteur as M


def synth(season, rain_total, tmean, et0, days=None):
    sp = M.SEASONS[season]
    n = days or {"Hivernage": 183, "Saison fraîche": 125, "Saison chaude": 127}[season]
    idx = pd.date_range("2025-01-01", periods=n)
    d = np.arange(n)
    shape = np.exp(-((d - 80) / 28) ** 2) if season == "Hivernage" else np.ones(n)
    r = shape / shape.sum() * rain_total
    return pd.DataFrame({"rain": r, "et0": np.full(n, et0), "tmean": np.full(n, tmean)}, index=idx)


@pytest.fixture(scope="module")
def Ys():
    clim = {"Hivernage": (450, 28, 5.0), "Saison fraîche": (10, 22, 3.6), "Saison chaude": (30, 26.5, 5.0)}
    rng = np.random.default_rng(1)
    out = {}
    for s, (rain, t, et0) in clim.items():
        out[s] = pd.DataFrame({c: [M.simulate_season(synth(s, max(0, rng.normal(rain, rain * .3)), t + rng.normal(0, 1), et0),
                                                      c, 1e9, s) for _ in M.YEARS] for c in M.MY}, index=M.YEARS)
    return out


def test_cultures_du_test():
    assert M.MY == ("Oignon", "Piment", "Niébé")
    assert set(M.CROP_FAO) == set(M.CROP_T) == set(M.INFO) == set(M.MY)


def test_rayonnement_plausible():
    assert 10 < M.ra_mm(14.85, 180) < 18


def test_effet_temperature():
    assert M.tfac(20, M.CROP_T["Oignon"]) == 1
    assert M.tfac(34, M.CROP_T["Oignon"]) == 0
    assert 0 < M.tfac(28, M.CROP_T["Oignon"]) < 1


def test_plus_d_eau_ne_baisse_jamais_le_rendement():
    df = synth("Hivernage", 150, 28, 5.0)
    assert M.simulate_season(df, "Niébé", 1e9, "Hivernage") >= M.simulate_season(df, "Niébé", 0, "Hivernage")


def test_oignon_prefere_la_saison_fraiche(Ys):
    assert Ys["Saison fraîche"]["Oignon"].mean() > Ys["Hivernage"]["Oignon"].mean()


def test_rejeu_compte_des_fenetres(Ys):
    for start in range(3):
        ok, n = M.replay_plan(Ys, ("Niébé", "Niébé", "Niébé"), start)
        assert 18 <= n <= 20 and 0 <= ok <= n


def test_trois_plans_dont_la_pratique_actuelle(Ys):
    suit = M.suitability(Ys)
    plans = M.build_plans(Ys, suit, 1, "Oignon", "Revenu", 1e9)
    assert len(plans) == 3 and plans[0]["seq"] == ("Oignon",) * 3
    assert plans[1]["seq"] != plans[2]["seq"] and all(len(p["seasons"]) == 3 for p in plans)


def test_sans_eau_pas_de_culture_hors_hivernage():
    for s in ("Saison fraîche", "Saison chaude"):
        assert M.simulate_season(synth(s, 5, 24, 4.5), "Oignon", 0, s) < M.THR
