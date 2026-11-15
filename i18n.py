"""Textes de l'interface en français et en wolof. LES TEXTES WOLOF SONT UNE PREMIÈRE VERSION : à faire relire."""
from moteur import MY, SEASONS

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


TXT["Français"].update(
    listen="Écouter", listen_advice="🔊 Écouter mon conseil", welcome_h="Bienvenue 👋",
    welcome_p="Répondez aux 4 questions, puis appuyez sur le gros bouton vert.",
    mic="🎙️ Parlez à Yaxanal (wolof)", voice_h="Réglages de la voix")
TXT["Wolof"].update(
    listen="Dégglu", listen_advice="🔊 Dégglu ndigal bi", welcome_h="Dalal ak jàmm 👋",
    welcome_p="Tontul ñeent yi laaj, ba noppi nga bësal butoŋ bu wert bi.",
    mic="🎙️ Wax ak Yaxanal", voice_h="Réglages de la voix")
SIZES = {1.0: "Aa", 1.15: "Aa+", 1.3: "Aa++"}  # taille du texte
