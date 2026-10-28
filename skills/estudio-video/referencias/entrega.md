# Control de calidad y entrega

## Checklist técnico (para cada archivo de `entregas/`)

```sh
# formato, fps, duración, códecs
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of compact entregas/x.mp4
# loudness integrado (−14 redes / −16 cartelería, ±1)
ffmpeg -hide_banner -i entregas/x.mp4 -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1
# cuadros negros o congelados que no deberían estar
ffmpeg -hide_banner -i entregas/x.mp4 -vf "blackdetect=d=0.2:pix_th=0.05,freezedetect=n=0.003:d=1.5" -an -f null - 2>&1 | grep -E "black_start|freeze_start"
```

- [ ] Medida, fps y duración como en el guion.
- [ ] Loudness dentro del objetivo. La voz se entiende por encima de la música (escuchar con el celular, no con auriculares).
- [ ] **Primer cuadro** con el hook visible (`--stills 0`).
- [ ] Nada importante en las zonas que tapa la interfaz (`pieza.html?guias`).
- [ ] Textos: sin errores de tipeo, sin palabras cortadas, legibles en el celular sin pausar.
- [ ] Subtítulos sincronizados y con las marcas bien escritas (Whisper se equivoca con los nombres propios).
- [ ] Datos de contacto exactos (teléfono, mail, usuario): probados, no copiados de memoria.
- [ ] Final: CTA de 3 s o más. En cartelería, el loop empalma sin salto.
- [ ] Peso razonable: menos de 30 MB cada 30 s en redes.

Mirá vos los cuadros (`--hoja`, `--stills`) antes de decir que está listo. Si algo no se pudo verificar, decilo.

## Mostrarlo

- `SendUserFile` con los `.mp4` (y la hoja de revisión si hay variantes), con una tabla de qué cambia en cada uno.
- Para verlos en el celular está la galería del repo (`videos/_galeria`, `node server.mjs`).

## README del proyecto (`videos/NN-nombre/README.md`)

Mismo formato que los anteriores (`09`, `11`, `12`):

```markdown
# NN · <Título>

<Qué es, para quién y dónde se publica, en 2 líneas>

## Estado (<fecha>)
**<Listo para publicar / falta X>**

| Entrega | Duración | Qué cambia |
|---|---|---|
| `entregas/<slug>-A.mp4` | 20 s | Control |
| `entregas/<slug>-B.mp4` | 20 s | Hook con dato |

## Texto de la publicación
<copy + hashtags> · Portada sugerida: <segundo / archivo>

## Test A/B
<tabla de variantes-ab.md>

## Pendientes antes de publicar
1. <permiso, dato a verificar, etiqueta de colaboración paga…>

## Regenerar
cd proyecto && npm install && pip install numpy scipy pillow
node frames.mjs && node render.mjs
<qué material hace falta y dónde va: el material no está en git>
```

Y una fila en la tabla de `videos/README.md`: `| \`NN-nombre/\` | Qué es | Estado |`.

## Antes de publicar (avisar siempre lo que aplique)

- **Personas:** permiso de quien aparece (y de sus padres si es menor).
- **Marcas:** producto regalado o pago → etiqueta de colaboración paga. Confirmar el usuario de la marca para etiquetarla.
- **Negocios de ejemplo:** si el nombre o el teléfono son inventados, que se note que es una muestra ("TU HÍPICO") o que no se publique como si fuera real.
- **Música:** sintetizada o con licencia. Nunca un tema comercial quemado en el archivo.
- **Contenido que vence** (noticias, precios, promos): anotar hasta cuándo sirve.
- **Sticker de enlace / CTA tocable:** lo que en el video parece un botón no se puede tocar. Hay que poner el sticker al subirlo.

## Git

1. `git status`: solo `entregas/`, el código de `proyecto/`, `guion.md`, `README.md`, `.gitignore`.
2. Nada de `material/`, `out/`, `node_modules/`, `.wav`, `.m4a`, `.mov` ni variantes descartadas.
3. Mensaje de commit en castellano y en infinitivo ("Agregar el reel de X con dos variantes de hook"), como los anteriores.
