"""Fin de phrase « à l'oreille » avec deux modèles (Arthur, 12/10/2026 : « installe-les si c'est pertinent et que ça peut
tourner sur mon PC sans le faire laguer ») — trouvés par la recherche du 12/10 (voir CLAUDE.md, « Boucle intransigeante ») :

- **Smart Turn v3.2** (pipecat-ai, BSD-2, ONNX int8 8 Mo, ~20 ms par appel sur CPU) : probabilité que la personne ait FINI
  de parler (intonation, allongement final), d'après les 8 s de son qui précèdent l'instant. Entraîné sur des tours de
  parole avec un assistant vocal, pas sur des podcasts : un VOTE, à combiner avec la ponctuation et les pauses.
- **Alignement forcé CTC** (`bofenghuang/asr-wav2vec2-ctc-french`, Apache-2.0, 315 M paramètres, ~1 s par fenêtre de 6 s sur
  CPU) : position exacte de chaque lettre / mot entendu (trames de 20 ms), là où Whisper se trompe de 0,1–0,3 s et colle les
  « euh » aux mots. Viterbi en numpy (pas de torchaudio, introuvable pour torch 2.14).

Modèles dans `models/hf/` (non versionnés), téléchargés par `python -m clipper doctor --models` ou au premier usage.
"""
from __future__ import annotations

import re
import subprocess
import unicodedata
from functools import lru_cache
from pathlib import Path

import numpy as np

from .media import FFMPEG

ROOT = Path(__file__).resolve().parent.parent
TURN_DIR = ROOT / "models" / "hf" / "smart-turn-v3"
TURN_FILE = "smart-turn-v3.2-cpu.onnx"
CTC_DIR = ROOT / "models" / "hf" / "wav2vec2-ctc-french"
SR = 16000


def ensure_models() -> None:
    """Télécharge les deux modèles s'ils manquent (Hugging Face, ~1,2 Go au total)."""
    from huggingface_hub import hf_hub_download, snapshot_download
    if not (TURN_DIR / TURN_FILE).exists():
        hf_hub_download("pipecat-ai/smart-turn-v3", TURN_FILE, local_dir=str(TURN_DIR))
    if not (CTC_DIR / "model.safetensors").exists():
        snapshot_download("bofenghuang/asr-wav2vec2-ctc-french", local_dir=str(CTC_DIR),
                          allow_patterns=["config.json", "model.safetensors", "preprocessor_config.json", "vocab.json",
                                          "tokenizer_config.json", "special_tokens_map.json", "added_tokens.json"])


def load_pcm(wav: Path, a: float, b: float) -> np.ndarray:
    a = max(0.0, a)
    out = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{a:.4f}", "-t", f"{max(0.0, b - a):.4f}", "-i", str(wav),
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(out, np.float32).copy()


# ------------------------------------------------------------------------------------------------- Smart Turn v3

@lru_cache(maxsize=1)
def _turn():
    import onnxruntime as ort
    from transformers import WhisperFeatureExtractor
    ensure_models()
    so = ort.SessionOptions()
    so.intra_op_num_threads = 2          # léger : ne fait pas laguer le PC
    sess = ort.InferenceSession(str(TURN_DIR / TURN_FILE), so, providers=["CPUExecutionProvider"])
    return sess, WhisperFeatureExtractor(chunk_length=8)


def turn_complete(wav: Path, t: float) -> float:
    """Probabilité (0–1) que l'orateur ait fini sa phrase / sa pensée à l'instant t (son des 8 s précédentes)."""
    sess, fe = _turn()
    x = load_pcm(wav, t - 8.0, t)[-8 * SR:]
    if len(x) < 8 * SR:
        x = np.concatenate([np.zeros(8 * SR - len(x), np.float32), x])   # complété AU DÉBUT, comme l'entraînement
    feats = fe(x, sampling_rate=SR, return_tensors="np", padding="max_length", max_length=8 * SR, truncation=True,
               do_normalize=True).input_features.astype(np.float32)
    y = float(np.ravel(sess.run(None, {"input_features": feats})[0])[0])
    return y if 0.0 <= y <= 1.0 else float(1 / (1 + np.exp(-y)))


# ------------------------------------------------------------------------------------------------- alignement CTC

@lru_cache(maxsize=1)
def _ctc():
    import torch
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
    ensure_models()
    torch.set_num_threads(4)
    proc = Wav2Vec2Processor.from_pretrained(str(CTC_DIR))
    model = Wav2Vec2ForCTC.from_pretrained(str(CTC_DIR)).eval()
    return proc, model


def _norm_text(text: str, vocab: dict) -> str:
    t = unicodedata.normalize("NFC", text.lower()).replace("’", "'")
    t = re.sub(r"\s+'", "'", t)          # « qu 'il » (découpage de Whisper) -> « qu'il » : UN mot
    t = re.sub(r"[^\w' -]", " ", t).replace("-", " ")
    t = "".join(ch if (ch in vocab or ch == " ") else " " for ch in t)
    return re.sub(r"\s+", " ", t).strip()


def emissions(wav: Path, a: float, b: float) -> tuple[np.ndarray, float, dict]:
    """Log-probabilités CTC (trames de 20 ms) sur [a, b] ; renvoie (logp, durée d'une trame, vocabulaire)."""
    import torch
    proc, model = _ctc()
    x = load_pcm(wav, a, b)
    inp = proc(x, sampling_rate=SR, return_tensors="pt")
    with torch.inference_mode():
        logits = model(inp.input_values).logits[0]
    logp = torch.log_softmax(logits, dim=-1).numpy()
    return logp, (len(x) / SR) / max(1, logp.shape[0]), proc.tokenizer.get_vocab()


def align(wav: Path, a: float, b: float, text: str) -> list[dict]:
    """Alignement forcé de `text` sur le son [a, b] : [{w, s, e}] en temps absolus (début de la 1re lettre, fin de la
    dernière). Viterbi CTC classique (tutoriel torchaudio), en numpy."""
    logp, dt, vocab = emissions(wav, a, b)
    proc, _m = _ctc()
    blank = proc.tokenizer.pad_token_id if proc.tokenizer.pad_token_id is not None else vocab.get("[PAD]", 0)
    sep = vocab.get("|", vocab.get(" "))
    t = _norm_text(text, vocab)
    if not t:
        return []
    toks, owner = [], []          # jetons à aligner + index du mot de chaque jeton (-1 = séparateur)
    words = t.split(" ")
    for wi, w in enumerate(words):
        if wi and sep is not None:
            toks.append(sep)
            owner.append(-1)
        for ch in w:
            toks.append(vocab[ch])
            owner.append(wi)
    T, J = logp.shape[0], len(toks)
    if J == 0 or T < J:
        return []
    # trellis[t, j] : meilleur score en ayant émis les j premiers jetons après t trames
    trellis = np.full((T + 1, J + 1), -np.inf)
    trellis[0, 0] = 0.0
    trellis[1:, 0] = np.cumsum(logp[:, blank])
    tk = np.array(toks)
    for i in range(T):
        stay = trellis[i, 1:] + logp[i, blank]
        move = trellis[i, :-1] + logp[i, tk]
        trellis[i + 1, 1:] = np.maximum(stay, move)
    # retour arrière : trame où chaque jeton est émis
    j, frames = J, [[] for _ in range(J)]
    for i in range(T, 0, -1):
        if j == 0:
            break
        stay = trellis[i - 1, j] + logp[i - 1, blank]
        move = trellis[i - 1, j - 1] + logp[i - 1, tk[j - 1]]
        if move >= stay:          # jeton j émis à la trame i-1 (CTC « pointu » : une trame par lettre)
            frames[j - 1].append(i - 1)
            j -= 1
    out = []
    for wi, w in enumerate(words):
        fr = [f for k, o in enumerate(owner) if o == wi for f in frames[k]]
        if fr:
            out.append({"w": w, "s": round(a + min(fr) * dt, 3), "e": round(a + (max(fr) + 1) * dt, 3)})
    return out


def heard_text(wav: Path, a: float, b: float) -> str:
    """Ce que le modèle CTC entend sur [a, b] (décodage glouton) : texte brut, hésitations comprises."""
    proc, _ = _ctc()
    logp, _dt, _v = emissions(wav, a, b)
    ids = logp.argmax(-1)
    return proc.decode(ids)
