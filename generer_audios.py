"""Fabrique les clips audio wolof (assets/audio/*.wav) à partir des phrases de voix.py.
À lancer UNE FOIS sur un ordinateur avec :  pip install -r requirements-voix.txt   puis   python generer_audios.py
(Le premier lancement télécharge le modèle de voix, environ 150 Mo.) Écoutez ensuite chaque clip avec un locuteur wolof :
si une phrase sonne mal, corrigez-la dans voix.py (dictionnaire PHRASES), supprimez le clip et relancez.
Code généré avec l'aide de Claude (Anthropic) ; modèle MMS-TTS de Meta, licence CC-BY-NC (usage non commercial)."""
import voix

voix.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
for key, text in voix.PHRASES.items():
    out = voix.AUDIO_DIR / f"{key}.wav"
    if out.exists():
        print("déjà là :", key)
        continue
    print("synthèse :", key, "->", text)
    out.write_bytes(voix.tts_live(text))
print("Terminé :", voix.clips_count(), "clips dans", voix.AUDIO_DIR)
