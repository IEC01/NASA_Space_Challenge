"""Assistante Yaxanal : répond en wolof grâce à Claude (API Anthropic), à partir des résultats calculés."""
import os

import streamlit as st

from moteur import MY, ORDER, PRIO_FR, SEASONS, WATER_FR, crop_score

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
