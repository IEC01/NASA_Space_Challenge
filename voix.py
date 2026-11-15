"""Voix wolof : lecture à voix haute et écoute, avec les modèles MMS de Meta (licence CC-BY-NC : usage non commercial).

Trois niveaux, du plus simple au plus riche :
  1. Clips pré-enregistrés (assets/audio/*.wav, créés par generer_audios.py) : questions et phrases fixes,
     assemblés pour dire le conseil. Fonctionne sans internet ni modèle lourd au moment de la démo.
  2. Synthèse en direct (torch + transformers, modèle facebook/mms-tts-wol) : réponses libres de l'assistante.
  3. Reconnaissance de la parole (facebook/mms-1b-all, langue « wol ») : questions parlées. Modèle LOURD (~4 Go).
LES PHRASES WOLOF CI-DESSOUS SONT UNE PREMIÈRE VERSION : à faire relire et corriger par un locuteur.
Code généré avec l'aide de Claude (Anthropic) ; les parties modèle n'ont pas pu être testées par l'auteur.
"""
import functools
import importlib.util
import io
import os
import pathlib
import wave

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent
AUDIO_DIR = ROOT / "assets" / "audio"
TTS_MODEL = os.environ.get("TTS_MODEL", "facebook/mms-tts-wol")
STT_MODEL = os.environ.get("STT_MODEL", "facebook/mms-1b-all")
STT_LANG = "wol"
PAUSE_S = 0.18

PHRASES = {
    "welcome": "Nanga def ? Man mooy Yaxanal. Dinaa la dimbali ci sa tool.",
    "q_season": "Ci ban jamono nga bëgg a ji ? Nawet, jamono bu sedd, walla jamono bu tàng ?",
    "q_crop": "Lan ngay gën a ji ? Soble, kaani, walla ñebbe ?",
    "q_water": "Am nga ndox ngir ndoxal sa tool ? Waaw, tuuti rekk, walla déedéet ?",
    "q_prio": "Lan moo gën a am solo ci yaw ? Xaalis, ndox, suuf, walla at yu wow ?",
    "s_hiv": "Ci nawet", "s_fra": "Ci jamono bu sedd", "s_cha": "Ci jamono bu tàng",
    "c_oignon": "soble", "c_piment": "kaani", "c_niebe": "ñebbe",
    "advice_intro": "Lii mooy sa ndigal.",
    "best": "moo gën a baax.",
    "v_ok": "Baax na torop ci at yi weesu.", "v_mid": "Baax na tuuti ci at yi weesu.", "v_bad": "Baaxul ci at yi weesu.",
    "plan_intro": "Sunu ndigal ngir ñetti jamono yi ñëw :",
    "disclaimer": "Ndimbal rekk la. Bul fàtte laaj sa conseiller agricole.",
}
SEASON_KEY = {"Hivernage": "s_hiv", "Saison fraîche": "s_fra", "Saison chaude": "s_cha"}
CROP_KEY = {"Oignon": "c_oignon", "Piment": "c_piment", "Niébé": "c_niebe"}


def advice_keys(season, best_crop, cls, seq, seasons):
    """Suite de clips qui dit : « Voici ton conseil. [Saison] [culture] est la meilleure, [verdict]. Plan : ... »"""
    keys = ["advice_intro", SEASON_KEY[season], CROP_KEY[best_crop], "best", f"v_{cls}", "plan_intro"]
    for c, s in zip(seq, seasons):
        keys += [SEASON_KEY[s], CROP_KEY[c]]
    return keys + ["disclaimer"]


# ---------------- disponibilité ----------------
def live_available():
    if os.environ.get("VOIX_LIVE", "1") == "0":
        return False
    return all(importlib.util.find_spec(m) for m in ("torch", "transformers"))


def clips_count():
    return len(list(AUDIO_DIR.glob("*.wav"))) if AUDIO_DIR.is_dir() else 0


def available():
    return clips_count() > 0 or live_available()


def stt_available():
    return live_available()


# ---------------- audio ----------------
def wav_bytes(samples, sr):
    pcm = (np.clip(np.asarray(samples, dtype="float32"), -1, 1) * 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(int(sr)); w.writeframes(pcm.tobytes())
    return buf.getvalue()


def _read(b):
    with wave.open(io.BytesIO(b)) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype("float32") / 32768
    return sr, (x.reshape(-1, ch).mean(axis=1) if ch > 1 else x)


def concat(clips):
    parts, sr0 = [], None
    for c in clips:
        sr, x = _read(c)
        sr0 = sr0 or sr
        if sr != sr0:
            x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * sr0 / sr)), np.arange(len(x)), x)
        parts += [x, np.zeros(int(PAUSE_S * sr0), dtype="float32")]
    return wav_bytes(np.concatenate(parts), sr0)


@functools.lru_cache(maxsize=1)
def _tts():
    import torch
    from transformers import AutoTokenizer, VitsModel
    return AutoTokenizer.from_pretrained(TTS_MODEL), VitsModel.from_pretrained(TTS_MODEL).eval(), torch


def tts_live(text):
    """Texte wolof -> WAV (modèle MMS-TTS). Nécessite torch + transformers ; premier appel = téléchargement du modèle."""
    tok, model, torch = _tts()
    inputs = tok(text=text.lower(), return_tensors="pt")
    with torch.no_grad():
        wave_ = model(**inputs).waveform[0].cpu().numpy()
    return wav_bytes(wave_, model.config.sampling_rate)


def clip(key):
    p = AUDIO_DIR / f"{key}.wav"
    if p.exists():
        return p.read_bytes()
    if live_available():
        try:
            data = tts_live(PHRASES[key])
        except Exception:
            return None
        try:
            AUDIO_DIR.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        except Exception:
            pass
        return data
    return None


def compose(keys):
    clips = [clip(k) for k in keys]
    return None if not clips or any(c is None for c in clips) else concat(clips)


# ---------------- reconnaissance de la parole ----------------
@functools.lru_cache(maxsize=1)
def _asr():
    from transformers import pipeline
    return pipeline("automatic-speech-recognition", model=STT_MODEL,
                    model_kwargs={"target_lang": STT_LANG, "ignore_mismatched_sizes": True})


def stt_live(wav_data):
    """Enregistrement WAV (wolof) -> texte, avec MMS-ASR. Modèle lourd ; qualité à évaluer sur de vrais locuteurs."""
    sr, x = _read(wav_data)
    if sr != 16000:
        x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * 16000 / sr)), np.arange(len(x)), x)
    return _asr()({"raw": x.astype("float32"), "sampling_rate": 16000})["text"].strip()
