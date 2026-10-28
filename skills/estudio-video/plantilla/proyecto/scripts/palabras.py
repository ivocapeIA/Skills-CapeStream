"""Tiempo de cada palabra de una voz ya editada, con Whisper (faster-whisper).

    python scripts/palabras.py <voz.wav|m4a|mp3> <salida.json> [pista de vocabulario]

Sale una lista [{"w": palabra, "s": inicio, "e": fin}] que render.mjs pasa a la
pieza para los subtítulos. La pista ayuda con nombres propios y marcas
("Legamaster, Magic-Chart"). Requiere: pip install faster-whisper
Revisá el JSON a mano: Whisper a veces junta o parte palabras.
"""
import json
import pathlib
import sys

from faster_whisper import WhisperModel

voz, salida = sys.argv[1], pathlib.Path(sys.argv[2])
pista = sys.argv[3] if len(sys.argv) > 3 else None
modelo = WhisperModel("medium", device="cpu", compute_type="int8")
segs, _ = modelo.transcribe(voz, language="es", word_timestamps=True, initial_prompt=pista)
palabras = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps(palabras, ensure_ascii=False, indent=1), encoding="utf8")
print("ok", len(palabras), "palabras ->", salida)
print(" ".join(p["w"] for p in palabras))
