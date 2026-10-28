# Menú de opciones

Catálogo para la etapa 1. Cada opción dice **qué material le vas a tener que pedir**: eso define la lista de la etapa 2. Las carpetas `videos/NN-*` son ejemplos ya hechos en el repo, para mostrar o copiar.

## 1 · Tipo de contenido

| Tipo | Para qué sirve | Material que pide | Ejemplo |
|---|---|---|---|
| **Reel promo al ritmo** | Mostrar un lugar, producto o servicio con energía | 8–20 fotos o tomas cortas + textos | `09-promo-hipicos` |
| **Voz en off + subtítulos** | Contar algo (reseña, regalo de una marca, cómo funciona) | Voz grabada + tomas que ilustren cada frase | `11-legamaster-magic-chart` |
| **A cámara con zócalos** | Marca personal, opinión, tips | Tomas hablando a cámara (+ b-roll opcional) | `04-managerbnb-realista` |
| **Animación visual (no de texto)** | Frenar el scroll con imagen: 3D, fluidos, formas que respiran con la música | Nada (opcional: logo, foto del producto sin fondo) | bases `3d` y `shader` |
| **Motion graphics puro** | Explicar una idea o una app sin filmar nada | Nada (opcional: logo, capturas) | `05-curso-claude-code`, `10/03-managerbnb` |
| **Explainer / noticia con datos** | Datos, rankings, novedades | Fuentes verificables | `08-noticias-ia`, `10/06-noticias-ia` |
| **Spot comercial 30–45 s** | Vender un producto o una app | Capturas de la app, logo, voz | `02-managerbnb-comercial` |
| **Historias / carrusel** | Presentarse, destacados, paso a paso | Textos + 1 foto | `12-historias-quien-soy`, `06-jev-carrusel` |
| **Cartelería en loop** | Pantallas de local, tótems, video walls | Menú/precios/logo; sin audio crítico | `10-carteleria-monitor` |
| **Tutorial con pantalla** | Cursos, demos de software | Grabación de pantalla (o la web/app para grabarla) | `07-promo-cursos-niveles` |

## 2 · Plataforma y formato

| Destino | Medida | fps | Duración que rinde |
|---|---|---|---|
| Reels / TikTok / Shorts | 1080×1920 (9:16) | 30 | 7–30 s (hook en 2 s) |
| Historias | 1080×1920 | 30 | ≤ 15 s por historia |
| Feed Instagram/LinkedIn | 1080×1350 (4:5) | 30 | 15–45 s |
| Cuadrado | 1080×1080 | 30 | 15–30 s |
| YouTube / web | 1920×1080 (16:9) | 30 (60 si hay mucha interfaz) | lo que pida el contenido |
| Pantalla 4K | 1920×1080 con `"escala": 2` → 3840×2160 | 30 | 30–60 s en loop |
| Tótem vertical | 1080×1920 | 30 | 30–60 s en loop |
| Look cine | 1920×1080 con franjas 2,39:1 | 24 | — |

Para varios destinos, el formato maestro es 9:16 con el contenido en el centro. Después se recorta a 4:5 o se arma la versión 16:9 como una variante con otro `w`/`h`.

## 3 · Presupuesto y herramienta

El nivel de presupuesto y la matriz "qué se quiere ver → con qué" están en `presupuesto.md`. Resumen para la pregunta:

| Opción | Cuándo | Costo |
|---|---|---|
| **Base `texto`** | Textos cinéticos, promo con fotos o clips, voz con subtítulos | 0 |
| **Base `3d`** (Three.js) | Objeto protagonista brillante (blob, nudo, anillo), satélites, reflejos, bloom: "premium abstracto" | 0 (lento sin placa de video) |
| **Base `shader`** (GLSL) | Fondos vivos: mesh gradient (`malla`), mármol `liquido`, `ondas` de contorno | 0 (lento sin placa de video) |
| **Combinada** (recomendada si hay material) | Shader o 3D de fondo + fotos o clips del usuario + textos | 0 |
| **Remotion / montaje Python** | Muchas piezas de una marca / mucho footage al ritmo | 0 |
| **Canva** (si el conector está) | Que el usuario lo edite él después | Según su plan |
| **IA generativa por API** | Planos imposibles de filmar o de dibujar con código | Pago por uso · **no implementado todavía** (`ia-generativa.md`) |

## 4 · Estilo visual

| Estilo | Cómo se ve | Fuentes | Ejemplo |
|---|---|---|---|
| **Bold cinético** | Mayúsculas gigantes, cortes al golpe, alto contraste | Anton + Inter | `09`, plantilla |
| **Apple minimal** | Claro, mucho aire, tarjetas con sombra suave, sin color de acento | Inter (titulares 700, espaciado negativo) | `12` |
| **Editorial suizo** | Papel, grilla de 12 columnas, un solo rojo | Inter Tight + JetBrains Mono | `10/07` |
| **Neón synthwave** | Fondo violeta noche, magenta y cian, piso retro | Big Shoulders Display / Bebas Neue | `10/04` |
| **Cine** | Franjas negras, grano, cámara lenta, serif | Playfair Display / Fraunces | `10/05` |
| **Papel cálido** | Crema, notas a mano, fotos de producto | Fraunces + Caveat | `10/02` |
| **Noticiero** | Zócalos, reloj, titulares que pasan | Inter + IBM Plex Mono | `10/06` |
| **3D premium** | Objeto brillante iridiscente sobre fondo oscuro, satélites, luces de color | Anton + Inter | base `3d` |
| **Fluido / gradiente vivo** | Mesh gradient o mármol líquido a pantalla completa, grano, títulos grandes | Anton o Inter 800 | base `shader` |
| **Interfaz en movimiento** | La app real animada: tarjetas, cursor, notificaciones | Space Grotesk / Inter | `02`, `10/03` |
| **Lofi casero** | Tomas de celular, subtítulos grandes, carteles con los colores del producto | Big Shoulders + Inter | `11` |

## 5 · Paleta

Listas para pegar en `video.json` → `base.colores`. Para las bases `3d` y `shader`, sumá un `acento2` (segundo color de luz o de mancha); si falta, se usa `texto`. Contraste medido (texto/fondo, acento/fondo). El acento por debajo de 4,5 solo va en textos grandes.

| Nombre | fondo | fondo2 | texto | acento | Contraste | Va con |
|---|---|---|---|---|---|---|
| noche-ámbar | `#0d0d12` | `#23233a` | `#f5f5f7` | `#ffb020` | 17,8 / 10,6 | Bold cinético |
| apple-claro | `#f5f5f7` | `#ffffff` | `#1d1d1f` | `#1d1d1f` | 15,5 / 15,5 | Apple minimal |
| papel-editorial | `#f1efe9` | `#faf8f3` | `#121212` | `#e8401c` | 16,3 / 3,5 | Editorial |
| neón | `#0b0221` | `#2a0845` | `#f5f0ff` | `#ff2bd6` | 18,0 / 6,3 | Synthwave |
| cine | `#0a0a0a` | `#1c1814` | `#efe6d6` | `#c9a35b` | 16,0 / 8,4 | Cine |
| café-artesanal | `#f6efe3` | `#fffaf1` | `#3b2a20` | `#b5532c` | 11,9 / 4,3 | Papel cálido |
| noticiero | `#0a2540` | `#123a63` | `#ffffff` | `#ff4d5a` | 15,5 / 4,8 | Noticiero |
| verde-campo | `#0f2a1d` | `#1e4a33` | `#f3f1e7` | `#d4af37` | 13,5 / 7,3 | Hípico, campo, outdoor |
| menta-tech | `#06141b` | `#0e2a33` | `#e8fbf7` | `#2ee6b6` | 17,4 / 11,7 | Apps, IA, SaaS |
| coral-pop | `#fff4ee` | `#ffffff` | `#1b1b1f` | `#e8453c` | 15,9 / 3,6 | Gastronomía, retail |

**Colores de un logo** (los 5 que más aparecen, sin el fondo):

```sh
python -c "from PIL import Image; im=Image.open('material/fotos/logo.png').convert('RGBA'); px=[p[:3] for p in im.getdata() if p[3]>200]; q=Image.new('RGB',(len(px),1)); q.putdata(px); print(['#%02x%02x%02x'%c for n,c in sorted(q.quantize(6).convert('RGB').getcolors(),reverse=True)[:5]])"
```

Con los colores de la marca, el acento es el color de la marca y el fondo, un casi negro o un casi blanco teñido de ese color. Medí el contraste antes de proponer.

## 6 · Tipografía

Todas con licencia libre, se instalan con `npm i @fontsource/<nombre>` y se enlazan en `pieza.html`.

| Par | Carácter |
|---|---|
| Anton + Inter | Impacto, deportivo, promo |
| Bebas Neue + Inter | Parecido a Anton, más fino |
| Inter (opsz) sola | Apple, limpio, corporativo |
| Space Grotesk + Inter | Tech, startup |
| Inter Tight + JetBrains Mono | Editorial, técnico |
| Fraunces + Inter | Cálido, gastronómico, artesanal |
| Playfair Display + Inter | Elegante, cine, inmobiliario |
| Big Shoulders Display + Inter | Industrial, carteles de producto |
| + Caveat | Acento manuscrito (una o dos palabras, nunca un párrafo) |

Tamaños mínimos en 1080 de ancho: titulares 120 px o más, textos 48 px, subtítulos 56 px. En el celular, lo más chico se tiene que poder leer sin pausar.

## 7 · Voz

| Opción | Cuándo | Cómo |
|---|---|---|
| **Tu voz** (recomendada para la marca personal) | Confianza, cercanía | El usuario graba; ver `guion.md` |
| **Voz neural provisoria** | Armar todo antes de grabar, o probar textos de hook | `python scripts/voz.py <nombre> "texto" es-AR-ElenaNeural` |
| **Sin voz** | Cartelería; reels que se miran en silencio | Todo en texto + música |
| **Audio original de las tomas** | A cámara, selfies | Se usa tal cual; la música se agacha |

## 8 · Música

Sintetizada por `scripts/musica.py`, sin derechos de terceros: `python scripts/musica.py <estilo> salida.wav <segundos>`.

| Estilo | BPM | Clima |
|---|---|---|
| `house` | 122 | Promo, energía, moda |
| `synthwave` | 110 | Tech, gaming, noche |
| `noticiero` | 124 | Informativo, urgente |
| `marimba` | 104 | Apps, amable, "todo se resuelve" |
| `minimal` | 96 | Marca personal, corporativo |
| `lofi` | 84 | Relajado, café, detrás de escena |
| `cine` | 72 | Emotivo, premium, cámara lenta |

Con los BPM se calcula la grilla: un golpe dura 60/BPM s y un compás, 4 golpes. Los cortes tienen que caer en golpes.
También puede ser un archivo propio (`"musica": "material/musica.mp3"`), solo con licencia clara. **Audio en tendencia:** se exporta sin música (`"musica": null`) y se le agrega en la app al publicar.

## 9 · Subtítulos

| Opción | Cuándo |
|---|---|
| **Palabra resaltada** (karaoke, recomendado con voz) | Reels con voz: la mayoría los mira sin sonido |
| **Frase completa** | Tutoriales, contenido largo |
| **Sin subtítulos** | Sin voz, o cuando el texto en pantalla ya cuenta todo |

## 10 · Variantes

| Opción | Costo |
|---|---|
| **Una sola versión** | — |
| **A/B de hook** (recomendado) | Cambian 1–2 s de texto: casi nada |
| **A/B de portada** | Una imagen más |
| **A/B de duración** (corta/larga) | Reordenar escenas en `video.json` |
| **A/B/C** | Solo con alcance o presupuesto para repartir entre tres |

Más detalle en `variantes-ab.md`.
