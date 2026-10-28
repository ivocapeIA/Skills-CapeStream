"""Locución por escenas: una toma de voz neural por escena (Edge TTS, gratis), unidas con
pausas controladas. Cada escena dura lo que dura su voz, así que la animación se ancla a
palabras reales y no a tiempos inventados.

    python scripts/locucion.py [voz] [velocidad]
    python scripts/locucion.py es-AR-ElenaNeural +6%

Lee base.textos.escenas de video.json. Escribe:
  out/voz/locucion.wav          la locución completa
  out/palabras/locucion.json    tiempos por palabra (con su puntuación)
  video.json                    dur, voz, subtitulos y base.tiempos.escenas = [[inicio, fin], ...]
Requiere: pip install edge-tts (y conexión a internet) y ffmpeg.
"""
import asyncio
import json
import pathlib
import re
import subprocess
import sys
import unicodedata

import edge_tts

RAIZ = pathlib.Path(__file__).resolve().parent.parent
VJ = RAIZ / "video.json"
VOZ = sys.argv[1] if len(sys.argv) > 1 else "es-AR-ElenaNeural"
RATE = sys.argv[2] if len(sys.argv) > 2 else "+6%"
ENTRADA = 0.25      # silencio antes de la voz en cada escena
COLA = 0.50         # silencio después (el último se pisa abajo)
COLA_FINAL = 2.2    # el cierre se queda un rato con el logo


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def duracion(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


async def toma(i, texto):
    mp3 = RAIZ / "out" / "voz" / f"escena-{i}.mp3"
    mp3.parent.mkdir(parents=True, exist_ok=True)
    com = edge_tts.Communicate(texto, VOZ, rate=RATE, boundary="WordBoundary")
    crudas = []
    with open(mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                s = ch["offset"] / 1e7
                crudas.append({"w": ch["text"], "s": s, "e": s + ch["duration"] / 1e7})
    # el servicio devuelve las palabras sin puntuación: se la devolvemos desde el texto original
    fichas = texto.split()
    j = 0
    for p in crudas:
        for k in range(j, len(fichas)):
            if norm(fichas[k]) == norm(p["w"]):
                p["w"] = fichas[k]
                j = k + 1
                break
    return mp3, crudas


async def main():
    cfg = json.loads(VJ.read_text(encoding="utf8"))
    textos = cfg["base"]["textos"]["escenas"]
    tomas = [await toma(i, t) for i, t in enumerate(textos)]

    escenas, palabras, t = [], [], 0.0
    for i, (mp3, crudas) in enumerate(tomas):
        voz_dur = duracion(mp3)
        cola = COLA_FINAL if i == len(tomas) - 1 else COLA
        ini = t
        fin = ini + ENTRADA + voz_dur + cola
        escenas.append([round(ini, 3), round(fin, 3)])
        for p in crudas:
            palabras.append({"w": p["w"], "s": round(ini + ENTRADA + p["s"], 3), "e": round(ini + ENTRADA + p["e"], 3)})
        t = fin

    # mezcla: cada toma entra en el inicio de su escena
    ins, filtros, etiquetas = [], [], []
    for i, (mp3, _) in enumerate(tomas):
        ms = int(round((escenas[i][0] + ENTRADA) * 1000))
        ins += ["-i", str(mp3)]
        filtros.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=mono,adelay={ms}[a{i}]")
        etiquetas.append(f"[a{i}]")
    filtros.append("".join(etiquetas) + f"amix=inputs={len(tomas)}:normalize=0,apad,atrim=0:{round(t, 3)}[o]")
    salida = RAIZ / "out" / "voz" / "locucion.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(filtros), "-map", "[o]", str(salida)], check=True)

    js = RAIZ / "out" / "palabras" / "locucion.json"
    js.parent.mkdir(parents=True, exist_ok=True)
    js.write_text(json.dumps(palabras, ensure_ascii=False, indent=1), encoding="utf8")

    cfg["dur"] = round(t + 0.1, 1)
    cfg["voz"] = "out/voz/locucion.wav"
    cfg["voz_desde"] = 0
    cfg["subtitulos"] = True
    cfg["base"].setdefault("tiempos", {})["escenas"] = escenas
    VJ.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf8")

    print(f"ok {salida.relative_to(RAIZ)}: {len(palabras)} palabras, {t:.1f} s")
    for i, (a, b) in enumerate(escenas):
        print(f"  escena {i}: {a:6.2f} -> {b:6.2f}  ({b - a:4.1f} s)  {textos[i][:60]}")


asyncio.run(main())
