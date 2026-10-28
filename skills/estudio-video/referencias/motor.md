# Motor de la plantilla

## Archivos del proyecto (`videos/NN-nombre/proyecto/`)

| Archivo | Qué hace |
|---|---|
| `video.json` | Formato, audio, textos/colores base, variantes y clips. **Lo único que se toca para hacer variantes.** |
| `pieza.html` | La animación. Define `window.render(t)` y lee todo de `window.VAR`. |
| `motor/motor.js` | Helpers, variante activa (`?v=B`), precarga, subtítulos, vista previa (`?play`). |
| `render.mjs` | Arma el audio, captura los cuadros en Chrome y codifica con ffmpeg. |
| `frames.mjs` | Pasa los clips a secuencias de JPG (`out/frames/`) para que el render sea exacto. |
| `scripts/musica.py` | Música sintetizada (7 estilos), con la duración como parámetro. |
| `scripts/voz.py` | Voz neural provisoria con tiempos por palabra (una sola toma). |
| `scripts/locucion.py` | Voz neural **por escenas** (`base.textos.escenas`): una toma por escena, unidas con pausas. Escribe `dur`, `voz`, `subtitulos` y `base.tiempos.escenas = [[ini, fin], …]` en `video.json`. Cada escena dura lo que dura su voz. |
| `scripts/palabras.py` | Tiempos por palabra de una voz grabada (Whisper). |
| `motor/glsl.js` | Ruido simplex y `fbm` en GLSL, para las bases visuales. |

## Bases

`nuevo.mjs --base <nombre>` copia una de estas como `pieza.html`. Todas leen `textos` (hook, beats, cierre, botón, usuario), `tiempos` y `colores`.

| Base | Qué es | Opciones propias en `base` o en la variante |
|---|---|---|
| `texto` | Hook palabra por palabra, un concepto por golpe, CTA, subtítulos | — |
| `3d` | Three.js: protagonista que respira con la música, satélites en órbita, reflejos de estudio (RoomEnvironment), bloom | `forma`: `blob` \| `nudo` \| `anillo` · `satelites` (14) · `brillo` (0.3) · `exposicion` (0.85) · `camara` (1 = distancia normal; >1 más lejos) |
| `shader` | GLSL a pantalla completa con viñeta y grano | `shader`: `malla` \| `liquido` \| `ondas` · `velocidad` (1) · `grano` (0.035) |

Las dos visuales usan `M.golpe(t, M.bpm(VAR.musica))`: un pulso que vale 1 en cada golpe de la música y cae rápido. El blob se infla y el shader se ilumina al ritmo.

Para **sumar fotos o clips** a una base visual: un `<img>` encima del canvas, animado en `render(t)` como en la base `texto`. El canvas queda de fondo.

Requisitos: Node 18+, ffmpeg, Python 3 con `numpy scipy pillow` (+ `edge-tts` y `faster-whisper` si hay voz), y Chrome/Edge/Chromium (se busca solo; si no, `NAVEGADOR=/ruta`). En Windows el comando es `python`; en Linux y Mac, `python3` (`PYTHON=` para forzar).

## `video.json`

```jsonc
{
  "slug": "reel-hipico",            // nombre de los archivos de entregas/
  "titulo": "Reel hípico",
  "w": 1080, "h": 1920, "fps": 30, "dur": 20,
  "escala": 1,                      // 2 = render al doble (4K desde un diseño de 1920×1080)
  "lufs": -14,                      // -14 redes, -16 cartelería
  "musica": "house",                // estilo de musica.py, ruta a un archivo, o null
  "musica_db": -15,                 // opcional: volumen de la música (por defecto -15 con voz, 0 sin voz)
  "voz": "out/voz/locucion.wav",    // o null
  "voz_desde": 0.3,                 // segundos en los que entra la voz
  "subtitulos": true,
  "base": { "colores": {…}, "textos": {…}, "tiempos": {…} },   // lo que lee la pieza
  "variantes": { "A": {…}, "B": {…} },                         // solo lo que cambia
  "clips": { "salto": { "src": "../material/tomas/IMG_2207.MOV", "in": 1.2, "dur": 3, "cx": 0.6, "speed": 0.5, "interp": true } }
}
```

Cada variante se mezcla con `base` (en profundidad) y llega a la pieza como `window.VAR`, con `VAR.id`, `VAR.dur` y `VAR.palabras` (los tiempos de la voz, ya corridos por `voz_desde`).

## Contrato de la pieza

```html
<script src="out/datos.js"></script>   <!-- lo escribe render.mjs: VIDEO, VARIANTES, CLIPS -->
<script src="motor/motor.js"></script>
<script>
  const V = window.VAR, D = window.DUR;
  window.setup = async () => { /* opcional: preparar el DOM, precargar */ };
  window.render = t => { /* dejar el cuadro en el estado del instante t */ };
</script>
```

Reglas para que cada cuadro salga igual siempre:

- **Todo depende de `t`.** Nada de `transition`, `@keyframes`, `setTimeout`, `Date.now()` ni `Math.random()` (usá `M.hash(n)` / `M.noise1(x)`).
- `render(t)` tiene que poder llamarse en cualquier orden: `t = 12` y después `t = 3`.
- Escalá con `--u` (1 px de un diseño de 1080 de ancho): `font-size: calc(120 * var(--u))`.
- Lo que no se ve, `M.vis(el, false)`: ahorra pintado.
- Lo que más tarda en renderizar: `filter: blur()` y `backdrop-filter` de áreas grandes (mejor una imagen ya desenfocada), y en las bases visuales el bloom y el `fbm` de muchas octavas. Sin placa de video, 3D y shader tardan entre 25 y 35 s por segundo de video: usá `--hoja` y `--borrador`.

## Helpers (`window.M`)

| Helper | Uso |
|---|---|
| `k(t, a, b, ease)` | Progreso 0→1 entre a y b, con curva |
| `win(t, a, b, in, out)` | Entra en `[a, a+in]` y sale en `[b-out, b]` |
| `ease.out / in / inOut / expo / back / sine / elastic / lin` | Curvas |
| `lerp(a, b, p)`, `clamp(x)` | Interpolar, acotar |
| `css(el, {…})`, `vis(el, on)`, `$`, `$$` | DOM |
| `clip(img, id, tLocal, {speed, loop})` | Muestra el cuadro del clip que corresponde (después de `node frames.mjs`) |
| `splitChars(el)` | Parte el texto en letras para animarlas |
| `subtitulo(el, t)` | Escribe el renglón que suena, con la palabra actual en `<b>` |
| `hash(n)`, `noise1(x)` | Aleatorio determinista |

## Recetas

- **Cortes al ritmo:** `const b = 60 / BPM;` y cada escena dura un número entero de golpes (`2 * b`, `4 * b`). El BPM de cada estilo está en `menu.md`.
- **Fotos con Ken Burns:** `<img>` con `object-fit: cover` y `css(img, { transform: \`scale(${lerp(1.08, 1.18, p)}) translate(${lerp(0, -2, p)}%, 0)\` })`.
- **Clip vertical desde uno horizontal:** en `clips`, `cx` (0 = izquierda, 1 = derecha) marca dónde está la acción. Si es 720p, mejor como tarjeta sobre el mismo clip desenfocado (`filtro: "boxblur=20"` en otro clip con el mismo `src`) que estirado.
- **Cámara lenta suave:** `"speed": 0.5, "fps": 30, "interp": true` (interpola cuadros; tarda más en `frames.mjs`).
- **Logo:** `material/fotos/logo.png` → `<img src="../material/fotos/logo.png">`.
- **Placa final editable por cliente:** los datos (nombre, teléfono, mail) van en `base.textos` y cada cliente es una variante. Así se hace un reel por cliente sin tocar la pieza (como `09`).
- **Palabra con fondo** (resaltador) dentro de un texto animado: `display: inline-block` en la palabra. Con `inline`, Chrome a veces pinta una copia negra de la caja en otro lugar.
- **Three.js determinista:** nada de `clock.getDelta()` ni de física acumulada: posición, rotación y uniforms salen de `t`. `preserveDrawingBuffer: true` en el renderer.
- **Shader propio:** copiá `bases/shader.html` y cambiá el bloque del modo. `THREE.ColorManagement.enabled = false` para que los colores de la paleta salgan tal cual.
- **Lottie** (íconos e ilustraciones de LottieFiles, revisar la licencia): `npm i lottie-web`, `<script src="node_modules/lottie-web/build/player/lottie.min.js">`, `const a = lottie.loadAnimation({ container, renderer: "svg", autoplay: false, loop: false, path: "material/x.json" })` y en `render(t)`: `a.goToAndStop(t * 1000, false)`. Esperar el evento `DOMLoaded` en `window.setup`.
- **Blender** (producto 3D realista, gratis, hay que instalarlo): un script Python (`blender -b -P escena.py -- --salida out/blender/`) que arma la escena, anima con keyframes y renderiza una secuencia PNG con fondo transparente. Con fondo: pasala a video (`ffmpeg -framerate 30 -i out/blender/%04d.png -pix_fmt yuv420p out/blender/producto.mp4`) y entra como un clip más. Con transparencia (producto sobre un shader): mostrá la secuencia PNG directo, `img.src = "out/blender/" + String(Math.floor(t * 30) + 1).padStart(4, "0") + ".png"`, y esperá el `decode()`. Usá Eevee: Cycles sin placa de video tarda horas.
- **Demo de una app (interfaz recreada en HTML)** (visto en `videos/01-demo-app`): la app entera como DOM dentro de un `#mundo` con `transform: translate(…) scale(s)` = **cámara virtual** (claves `[t, cx, cy, s]` con `ease.inOut`); un cursor SVG con claves `[t, x, y]` y clics que hunden el botón y dibujan un anillo; todo en coordenadas del mundo. Las posiciones salen de `getBoundingClientRect()` **una vez en `window.setup`** (con la cámara en `none`), no a mano. Los momentos se anclan a palabras de la voz con un `W(escena, "palabra")` sobre `VAR.palabras`, no a segundos. Las filas de texto que "se escriben" van palabra por palabra (opacidad), no letra por letra. Trampas: (1) cabeceras con `flex` sin `flex-wrap` agrandan toda una grilla y cortan paneles; (2) con la cámara cerca del borde inferior de la ventana se ve el vacío de abajo: desplazá el contenido (scroll simulado con `translateY`) en lugar de bajar la cámara; (3) sobre una interfaz clara, los textos de apoyo van en píldoras oscuras y, si hay llamadas a un costado, una capa `dim` degradada.
- **Loop para cartelería:** el último cuadro tiene que empalmar con el primero, o terminar con un fundido al color de fondo (la plantilla lo hace con `#fin`).

## Comandos

```sh
npm install
node frames.mjs                    # si hay clips
node render.mjs --preview          # y abrir pieza.html?play&v=A (agregá &guias para ver las zonas seguras)
node render.mjs --stills 0,1.5,8 B # cuadros sueltos
node render.mjs --hoja             # hoja de revisión: una fila por variante
node render.mjs --audio A          # solo la mezcla, para escucharla
node render.mjs --borrador         # media resolución y rápido → out/borrador/ (para ver el movimiento)
node render.mjs                    # todas las variantes → ../entregas/
node render.mjs --portada 1.2      # portadas → ../entregas/
```

## Cuándo no usar la plantilla

- **Remotion** (`videos/_estudio-managerbnb`, `videos/11-legamaster-magic-chart/proyecto`): para muchas piezas de una marca con componentes compartidos (calendario, chat, logo) o cuando el usuario quiere el Studio con línea de tiempo. Las variantes se hacen con `inputProps` y una composición por variante.
- **Montaje en Python + overlay HTML** (`videos/09-promo-hipicos/proyecto`): mucho footage cortado al golpe (`timeline.json` en golpes de la música) y los textos encima.
- **Canva** (con el conector): cuando el entregable es un diseño que el usuario va a editar. Se genera, se le pasa el link y se exporta desde ahí.
