"""Thèmes (auto, clair, sombre) et mise en page adaptative : téléphone, tablette, ordinateur."""
LIGHT = dict(bg="#f4f7f1", card="#ffffff", tx="#1b2a1f", mut="#5d6b60", ac="#1f8a4c", ac2="#e6f4ec", bd="#d9e2d6",
             okbg="#d8f3e3", oktx="#0f5a31", midbg="#fdebc8", midtx="#7a4a00", badbg="#fbdada", badtx="#8a1c1c")
DARK = dict(bg="#0f1a14", card="#17251c", tx="#e8efe9", mut="#9bb0a1", ac="#3ecf7a", ac2="#1f3326", bd="#2c3d32",
            okbg="#1c4a31", oktx="#aef0c9", midbg="#4a3a14", midtx="#ffd98a", badbg="#4d2222", badtx="#ffb4b4")

BASE = """
[data-testid="stMainBlockContainer"], .block-container {max-width: 1180px; padding: 3.6rem 1.2rem 5rem !important}
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
.q{font-weight:800;font-size:1.25rem;color:var(--tx);margin:14px 0 6px}
.welcome{text-align:center;padding:28px 18px}
.welcome .emo{font-size:4rem;line-height:1.1}
.welcome .wt{font-size:1.6rem;font-weight:800;margin:8px 0;color:var(--tx)}
.welcome .wp{font-size:1.15rem;color:var(--mut)}
.st-key-panel{background:var(--card);border:2px solid var(--bd);border-radius:24px;padding:10px 18px 18px}
[data-testid="stRadio"] [role="radiogroup"]{gap:10px}
[data-testid="stRadioOption"],[data-baseweb="radio"]{background:var(--card);border:2px solid var(--bd);border-radius:16px;padding:10px 16px;margin:0 !important;min-height:56px;align-items:center}
[data-testid="stRadioOption"][data-selected="true"],[data-baseweb="radio"]:has(input:checked){border-color:var(--ac);background:var(--ac2)}
[data-testid="stRadioOption"] > div > div:first-child,[data-baseweb="radio"] > div:first-child{display:none}
[data-testid="stRadio"] label p{font-size:1.1rem}
button[kind="primary"], [data-testid="stBaseButton-primary"]{background:var(--ac) !important;border:none !important;border-radius:18px !important;min-height:64px;width:100%}
button[kind="primary"] p, [data-testid="stBaseButton-primary"] p{font-size:1.35rem !important;font-weight:800 !important;color:#fff !important}
button[kind="secondary"], [data-testid="stBaseButton-secondary"]{min-height:56px;border-radius:16px;border:2px solid var(--bd);background:var(--card)}
[data-testid="stExpander"] details{background:var(--card);border:2px solid var(--bd);border-radius:18px}
[data-testid="stCaptionContainer"]{color:var(--mut)}
@media (max-width: 640px){
  [data-testid="stMainBlockContainer"], .block-container {padding: 3.4rem .6rem 5rem !important}
  .hero{padding:16px 16px;border-radius:20px} .hero .t{font-size:1.65rem} .hero .s{font-size:1rem}
  .big{font-size:1.45rem} .card{padding:14px 14px;border-radius:18px} .q{font-size:1.15rem}
}
@media (min-width: 641px) and (max-width: 1000px){ .hero .t{font-size:2.1rem} .big{font-size:1.6rem} }
@media (min-width: 1001px){ .hero .t{font-size:2.5rem} .big{font-size:1.9rem} .card{padding:20px 24px} }
"""


def css(mode, scale=1.0):
    v = lambda d: ";".join(f"--{k}:{x}" for k, x in d.items())
    zoom = f"html{{font-size:calc(16px * {scale})}}"
    if mode == "Auto":
        return zoom + f":root{{{v(LIGHT)}}}@media (prefers-color-scheme: dark){{:root{{{v(DARK)}}}}}" + BASE
    force = (".stApp{background:var(--bg)} [data-testid='stHeader']{background:transparent} "
             ".stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp span{color:var(--tx)} ")
    return zoom + f":root{{{v(DARK if mode == 'Sombre' else LIGHT)}}}" + force + BASE
