"""Voz neural provisoria (Microsoft Edge TTS, gratis) con tiempos por palabra.
Sirve para armar el video antes de grabar la voz real, o para probar variantes de texto.

    python scripts/voz.py <nombre> "texto a decir" [voz] [velocidad]
    python scripts/voz.py hook-B "¿Sabías que el 80 % no mira más de 3 segundos?"
    python scripts/voz.py locucion "..." es-AR-TomasNeural +6%

Sale out/voz/<nombre>.mp3 y out/palabras/<nombre>.json. En video.json: "voz": "out/voz/<nombre>.mp3".
Voces útiles: es-AR-ElenaNeural, es-AR-TomasNeural, es-MX-DaliaNeural, es-ES-AlvaroNeural.
Requiere: pip install edge-tts (y conexión a internet).
"""
import asyncio
import json
import pathlib
import sys

import edge_tts

RAIZ = pathlib.Path(__file__).resolve().parent.parent
nombre, texto = sys.argv[1], sys.argv[2]
VOZ = sys.argv[3] if len(sys.argv) > 3 else "es-AR-ElenaNeural"
RATE = sys.argv[4] if len(sys.argv) > 4 else "+4%"


async def main():
    mp3 = RAIZ / "out" / "voz" / f"{nombre}.mp3"
    js = RAIZ / "out" / "palabras" / f"{nombre}.json"
    mp3.parent.mkdir(parents=True, exist_ok=True)
    js.parent.mkdir(parents=True, exist_ok=True)
    com = edge_tts.Communicate(texto, VOZ, rate=RATE, boundary="WordBoundary")
    palabras = []
    with open(mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                s = ch["offset"] / 1e7
                palabras.append({"w": ch["text"], "s": round(s, 3), "e": round(s + ch["duration"] / 1e7, 3)})
    js.write_text(json.dumps(palabras, ensure_ascii=False, indent=1), encoding="utf8")
    print(f"ok {mp3.relative_to(RAIZ)}  ({len(palabras)} palabras, termina en {palabras[-1]['e'] if palabras else 0:.1f} s)")


asyncio.run(main())
