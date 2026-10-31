"""Arma el video final con ffmpeg, local y sin gastar créditos de Higgsfield.

Uso:  python armar.py proyecto.json

proyecto.json (las rutas son relativas al propio json):
{
  "salida": "final/recorrido.mp4",
  "ancho": 1080, "alto": 1920, "fps": 24,
  "tomas": [
    {"archivo": "generado/toma-01.mp4", "desde": 0, "hasta": 4.5},
    {"imagen": "generado/escena-02.png", "duracion": 5, "movimiento": "acercar"}
  ],
  "musica": {"archivo": "entrada/musica.mp3", "volumen": 0.35},
  "voz": {"archivo": "generado/voz.mp3"},
  "textos": [{"texto": "Reservá en managerbnb.com.ar", "desde": 26, "hasta": 30, "pos": "abajo", "tam": 64}],
  "fundido": 0.6
}
- "tomas" con "archivo" son clips (se recortan entre desde/hasta); con "imagen" son fotos fijas a las que se les da
  movimiento ("acercar", "alejar", "izquierda", "derecha" o "quieta").
- Todo se escala y recorta para LLENAR el cuadro (sin barras negras).
- Si hay voz y música, la música baja sola mientras habla la voz.
"""
import json
import os
import subprocess
import sys
import tempfile

# Fuente para los textos superpuestos (Windows primero; si no existe, la que tenga el sistema)
FUENTES = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
           "/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def escapar_ruta(ruta):
    # Dentro de un filtergraph los ":" y "\" de una ruta hay que escaparlos
    return ruta.replace("\\", "/").replace(":", "\\:")


def duracion_de(archivo):
    # Pregunta la duración real del archivo a ffprobe
    salida = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=nw=1:nk=1", archivo], capture_output=True, text=True)
    return float(salida.stdout.strip() or 0)


def main():
    # Lee el proyecto y resuelve las rutas contra la carpeta del json
    ruta_json = os.path.abspath(sys.argv[1])
    base = os.path.dirname(ruta_json)
    with open(ruta_json, encoding="utf-8") as f:
        p = json.load(f)
    ruta = lambda r: os.path.join(base, r)
    ancho, alto, fps = p.get("ancho", 1920), p.get("alto", 1080), p.get("fps", 24)

    entradas, filtros, etiquetas = [], [], []
    total = 0.0
    # Ajuste común: llenar el cuadro, recortar el sobrante, fps fijo y píxeles cuadrados
    llenar = (f"scale={ancho}:{alto}:force_original_aspect_ratio=increase,crop={ancho}:{alto},"
              f"fps={fps},setsar=1,format=yuv420p")

    for i, toma in enumerate(p["tomas"]):
        if "imagen" in toma:
            # Foto fija: se agranda al doble y se le aplica un movimiento lento con zoompan
            dur = float(toma.get("duracion", 5))
            cuadros = int(dur * fps)
            mov = toma.get("movimiento", "acercar")
            z = {"acercar": f"1+0.12*on/{cuadros}", "alejar": f"1.12-0.12*on/{cuadros}"}.get(mov, "1.08")
            x = {"izquierda": f"(iw-iw/zoom)*(1-on/{cuadros})", "derecha": f"(iw-iw/zoom)*on/{cuadros}"}.get(
                mov, "(iw-iw/zoom)/2")
            entradas += ["-loop", "1", "-t", str(dur), "-i", ruta(toma["imagen"])]
            filtros.append(f"[{i}:v]scale={ancho*2}:{alto*2}:force_original_aspect_ratio=increase,"
                           f"crop={ancho*2}:{alto*2},zoompan=z='{z}':x='{x}':y='(ih-ih/zoom)/2':d={cuadros}:"
                           f"s={ancho}x{alto}:fps={fps},setsar=1,format=yuv420p,trim=duration={dur}[v{i}]")
        else:
            # Clip: se recorta entre desde y hasta, y se ajusta al cuadro
            desde = float(toma.get("desde", 0))
            hasta = float(toma.get("hasta", duracion_de(ruta(toma["archivo"]))))
            dur = hasta - desde
            entradas += ["-i", ruta(toma["archivo"])]
            filtros.append(f"[{i}:v]trim=start={desde}:end={hasta},setpts=PTS-STARTPTS,{llenar}[v{i}]")
        etiquetas.append(f"[v{i}]")
        total += dur

    # Une todas las tomas una detrás de otra (cortes limpios)
    filtros.append(f"{''.join(etiquetas)}concat=n={len(etiquetas)}:v=1:a=0[vcat]")
    ultimo = "vcat"

    # Textos exactos superpuestos (nombre, precio, CTA, cifras): nunca generados por el modelo
    fuente = next((f for f in FUENTES if os.path.exists(f)), None)
    tmp = tempfile.mkdtemp()
    for j, t in enumerate(p.get("textos", [])):
        # El texto va en un archivo para no pelear con el escapado de comillas y dos puntos
        archivo_txt = os.path.join(tmp, f"t{j}.txt")
        with open(archivo_txt, "w", encoding="utf-8") as f:
            f.write(t["texto"])
        y = {"arriba": "h*0.10", "centro": "(h-text_h)/2"}.get(t.get("pos", "abajo"), "h*0.80-text_h")
        fuente_opt = f"fontfile='{escapar_ruta(fuente)}':" if fuente else ""
        filtros.append(f"[{ultimo}]drawtext={fuente_opt}textfile='{escapar_ruta(archivo_txt)}':expansion=none:"
                       f"fontsize={t.get('tam', 56)}:fontcolor=white:box=1:boxcolor=black@0.45:boxborderw=24:"
                       f"x=(w-text_w)/2:y={y}:enable='between(t,{t['desde']},{t['hasta']})'[vt{j}]")
        ultimo = f"vt{j}"

    # Fundido a negro al final
    fundido = float(p.get("fundido", 0.5))
    if fundido > 0:
        filtros.append(f"[{ultimo}]fade=t=out:st={max(total - fundido, 0)}:d={fundido}[vfin]")
        ultimo = "vfin"

    # Audio: música en loop recortada al largo del video, voz encima y la música baja cuando hay voz
    n = len(p["tomas"])
    pistas = []
    if p.get("musica"):
        entradas += ["-stream_loop", "-1", "-i", ruta(p["musica"]["archivo"])]
        filtros.append(f"[{n}:a]atrim=duration={total},volume={p['musica'].get('volumen', 0.35)},"
                       f"afade=t=out:st={max(total - 1.5, 0)}:d=1.5[mus]")
        pistas.append("mus")
        n += 1
    if p.get("voz"):
        entradas += ["-i", ruta(p["voz"]["archivo"])]
        filtros.append(f"[{n}:a]apad,atrim=duration={total},volume={p['voz'].get('volumen', 1.0)}[voz]")
        if pistas:
            # La voz comprime a la música (ducking) y después se mezclan las dos
            filtros.append("[voz]asplit=2[voz1][voz2]")
            filtros.append("[mus][voz1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[musb]")
            filtros.append("[musb][voz2]amix=inputs=2:duration=first:normalize=0[afin]")
        else:
            filtros.append("[voz]anull[afin]")
        pistas = ["afin"]
    audio = pistas[0] if pistas else None

    # El filtergraph va en un archivo: evita los problemas de comillas de cada shell
    script = os.path.join(tmp, "filtros.txt")
    with open(script, "w", encoding="utf-8") as f:
        f.write(";\n".join(filtros))
    salida = ruta(p["salida"])
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    resto = ["-map", f"[{ultimo}]"]
    if audio:
        resto += ["-map", f"[{audio}]", "-c:a", "aac", "-b:a", "192k"]
    resto += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(fps), "-movflags", "+faststart",
              "-t", str(total), salida]
    # ffmpeg 7+ lee el filtergraph de un archivo con "-/filter_complex"; las versiones viejas, con -filter_complex_script
    for opcion in ("-/filter_complex", "-filter_complex_script"):
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", *entradas, opcion, script, *resto],
                           capture_output=True, text=True)
        if r.returncode == 0:
            break
        if "Unrecognized option" not in r.stderr and "Option not found" not in r.stderr:
            sys.exit(r.stderr)
    else:
        sys.exit(r.stderr)
    print(f"Listo: {salida} ({total:.1f} s, {ancho}x{alto}, {fps} fps)")


if __name__ == "__main__":
    main()
