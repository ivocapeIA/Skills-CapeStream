# Diseño del frontend

El sistema de diseño es **una arquitectura de tokens**, no una paleta. El estilo elegido en
el intake cambia los valores; la estructura es siempre la misma.

---

## 1. Arquitectura de tokens (no negociable)

La alternativa —sembrar variantes `dark:` por clase— significa dos colores que mantener en
cada línea, en decenas de archivos. En su lugar:

```css
/* globals.css */
:root {
  --color-lienzo: 238 241 238;   /* Terna "R G B" sin coma: la consume rgb(var(--x)) */
  --color-paper: 255 255 255;
  --color-ink: 32 37 33;
  /* ... */
}
.dark {
  --color-lienzo: 18 20 19;
  --color-paper: 28 31 29;
  --color-ink: 233 237 234;
  /* ... el mismo set, otros valores */
}
```

```ts
// tailwind.config.ts — el <alpha-value> mantiene vivas las opacidades: bg-paper/60, text-ink/70.
const tema = (n: string) => `rgb(var(--color-${n}) / <alpha-value>)`;
colors: { lienzo: tema("lienzo"), paper: tema("paper"), ink: tema("ink") /* ... */ }
```

`darkMode: "class"`. Un **script inline en el `<head>`** (no un componente) aplica la clase
`dark` antes del primer pintado; si esperara a la hidratación la pantalla arrancaría clara y
saltaría. El `<html>` lleva `suppressHydrationWarning` porque su `class` difiere entre
servidor y cliente.

### La distinción que hace que nada se rompa

| Cambian con el tema | NO cambian con el tema |
|---|---|
| Superficies, textos, bordes, estados | Colores usados como **fondo con texto encima** |
| `lienzo` `paper` `superficie` | `marca`, los colores de módulo, tintas de familia |
| `ink` `inkSuave` `muted` `tenue` | `sobreClaro` (texto oscuro sobre chips claros) |
| `line` `lineFuerte` | |

Si un color se usara aclarado en oscuro, el texto blanco que lleva encima dejaría de
contrastar. Por eso los tres casos que necesitan las dos cosas tienen **tokens separados**:

- `marca` (fondo sólido) ↔ `marcaTinta` (texto/borde, se aclara en oscuro).
- `tintaFria`/`tintaCalida` (fondo) ↔ `selloFrio`/`selloNeutro`/`selloCalido` (texto).
- `ink` (texto de la app) ↔ `sobreClaro` (texto sobre chips claros en ambos temas).

**Error clásico:** usar como texto un color pensado como fondo. En tema claro "se ve bien de
casualidad" y en oscuro queda tinta oscura sobre papel oscuro: 1,7:1, invisible. Barrer el
código buscando ese patrón antes de cerrar.

**Otro error clásico:** un velo de modal con `bg-ink/40`. Como `ink` es la tinta del tema, en
oscuro vale casi blanco y el velo **aclara** la pantalla. Los velos van con `bg-black/40`.

---

## 2. Set completo de tokens

```
Superficies : lienzo (fondo) · paper (tarjeta) · superficie (input, hover, fila alterna)
Texto       : ink → inkSuave → muted → tenue   (escala de énfasis, todos medidos sobre su fondo)
Bordes      : line · lineFuerte
Estados UI  : exito|error|alerta × Tinta|Fondo|Borde
Estados op. : salvia (listo) · mostaza (pendiente) · humo (en curso), cada uno con su *Bg
Marca       : marca · marcaDeep (hover) · marcaTinta (texto/borde)
Módulos     : un color por módulo + tinta de familia + superficie de familia
```

**Dos paletas separadas a propósito**: "de qué módulo es" y "en qué estado está" nunca
comparten color. Si un chip verde puede significar "módulo Limpiezas" y también "tarea
lista", el color deja de informar.

---

## 3. Presets de estilo (elegidos en el intake)

Todos usan la misma arquitectura; cambian valores y tipografías.

### `editorial cálido`
Fondo apenas crema/frío, acento tierra (paprika `#b8451f`, terracota, bronce). Titulares en
condensada de alto contraste (Big Shoulders, Oswald), cuerpo humanista (Inter, Source Sans),
mono para códigos y montos (IBM Plex Mono). Sellos de 3 letras con leve rotación.
*Para:* negocios de servicio, hospitalidad, gastronomía, oficios.

### `técnico neutro` (default)
Grises fríos, un solo acento saturado (azul/índigo), bordes finos, densidad alta.
Tipografía: Inter / Geist + mono. Cero decoración; el color solo informa estado.
*Para:* operaciones internas, logística, soporte, backoffice.

### `corporativo sobrio`
Azul marino + gris, superficie blanca, sombras suaves, tipografía clásica (Source Sans,
Libre Franklin). Más aire, tarjetas grandes, KPIs prominentes.
*Para:* estudios profesionales, salud, financiero, cara al cliente.

### `vibrante moderno`
Fondo casi negro por default (con tema claro disponible), acentos saturados en degradado,
esquinas grandes (`rounded-2xl`), micro-animaciones.
*Para:* productos jóvenes, agencias, fitness, retail de nicho.
⚠️ Con acentos saturados hay que medir el contraste **de verdad**: los tonos neón vibran en
negativo y bajan de 4,5:1 sin que se note.

**Regla común a los cuatro:** un color por módulo, todos en la **misma banda de saturación**,
sin ningún neón, para que ninguna tarjeta grite más que las otras. Si hay 10+ módulos,
elegir los hex como sistema (no de a uno) y anotar el contraste sobre blanco al lado de cada
uno, en el comentario.

---

## 4. Contraste: medirlo, no estimarlo

- Texto normal ≥ **4,5:1**; el escalón más bajo (`tenue`) se reserva a placeholders y pistas.
- Ningún color de módulo se usa como **texto** salvo que supere 4,5:1; los vivos y los claros
  van solo como relleno, con texto blanco o `sobreClaro` según cuál contraste más.
- El degradado de las tarjetas se calibra **por color** (0,10 para un gris oscuro, 0,27 para
  un gris claro): con una opacidad única, un ocre grita y un gris claro no se ve.
- Los gráficos: **recharts pinta el SVG con props**, no lee variables CSS. La paleta se
  resuelve en JavaScript con un hook que observa la clase del `<html>` con un
  `MutationObserver`. Sin eso, los ejes salen con el gris por defecto (#666), ilegible sobre
  papel oscuro.

---

## 5. Celular (el 60 % del uso real en un panel operativo)

- **App shell**: `100dvh` (no `100vh`: en iPhone mide la ventana con la barra de direcciones
  oculta y corta el último tramo) + `env(safe-area-inset-*)` en shell y barra superior.
- **`<main>` es el único contenedor de scroll.** Cada pantalla es
  `flex h-full flex-col` → `header shrink-0` (título, filtros, acciones siempre visibles) →
  `div min-h-0 flex-1 overflow-auto` (lo único que scrollea).
- **Las tablas se vuelven tarjetas** bajo `sm`: la tabla pasa a `hidden sm:block` y debajo va
  una lista `sm:hidden` con el dato principal arriba, el contexto en `text-xs` y las acciones
  a la vista, reusando los mismos handlers. Una tabla de 6 columnas con scroll horizontal en
  375 px es inusable.
- **Inputs a 16 px en táctil**: por debajo de eso **iOS hace zoom solo al enfocarlos** y
  descuadra la pantalla.
- **`hover` restringido a `sm`**: en táctil el hover se queda pegado tras el toque. Feedback
  con `active:scale`.
- **Botones de fila con alto de toque** (~40 px), no `py-1`.
- **Los párrafos explicativos fijos van `hidden sm:block`.** Un renglón de texto que nunca
  cambia le roba una fila de datos a la pantalla; los contadores dinámicos se quedan.
- **`min-w-0` en los hijos de un flex** que contengan texto largo: una URL es UNA palabra, y
  el `min-width: auto` de flex la usa como ancho mínimo y saca la pantalla de cuadro.
- Barra superior más baja en celular; en pantallas tipo chat, borde a borde (sin margen del
  `main`, sin bordes ni esquinas redondeadas).

---

## 6. Capa de interacción (lo que hace que se sienta un producto)

Todo montado una sola vez desde el layout del dashboard:

- **Paleta de comandos (Ctrl/⌘+K)**: búsqueda difusa sobre módulos + acciones rápidas,
  navegación por flechas, trampa de foco. Las acciones navegan con `?nuevo=1` y el cliente
  abre su alta (y limpia el parámetro con `history.replaceState`, para que un refresco no
  reabra el modal).
- **Toasts** con store pub/sub (`useSyncExternalStore`, sin Provider): éxito/error/info. Toda
  acción que puede fallar **avisa**; nada falla en silencio.
- **Barra de progreso de navegación** fina arriba.
- **Indicador de conexión** para quien opera en la calle.
- **Tour guiado** por pantalla, con anclas `data-tour="..."`. Un paso cuyo elemento no está
  renderizado se saltea. El ancla va en el **envoltorio**, no en la tabla: si la tabla se
  oculta en celular, el paso desaparecería.
- **Recuperación de `ChunkLoadError`**: una pestaña abierta durante un deploy nuevo pide
  chunks con el hash viejo (404). Un listener global de `error` y `unhandledrejection` hace
  un `location.reload()` único por pestaña, con guarda en `sessionStorage` para no
  entrar en loop.
- **Service worker: registrar SOLO en producción.** En desarrollo, un SW "caché primero"
  sirve JS viejo contra un servidor ya arreglado y ni un hard-reload lo cura.

---

## 7. Detalles de CSS que ya mordieron

- **Clases propias en `@layer components`**, nunca sueltas al final del archivo: a igual
  especificidad gana la última, así que una clase suelta con `display: inline-block` le gana
  a `hidden` y el elemento aparece igual donde debía ocultarse.
- **`thead sticky` necesita un contenedor de scroll con alto acotado.** `overflow-x-auto` ya
  vuelve la caja un contenedor de scroll, pero sin alto máximo nunca se desplaza y el
  encabezado se va de pantalla.
- **Tailwind solo genera las clases que encuentra escritas literales**: una clase armada en
  runtime (`bg-${color}`) no existe en el CSS final. Se escriben literales en la definición
  de cada tarjeta/módulo.
- **`auto-rows-fr` + `max-h` fijo** dejan huecos muertos: la fila mide más que el tope de la
  tarjeta y lo que sobra queda como aire.
- **Barras de acciones con `flex-wrap`**: sin él, el tercer control se sale del viewport en
  402 px.
- **El `<meta name="theme-color">`** hay que reaplicarlo al montar cada pantalla si la
  navegación es con recargas completas; si no, queda pisado por el valor del layout raíz.

---

## 8. Reglas de contenido

- **Sin emojis en pantallas de gestión** (íconos lucide). Los emojis sí sirven en mensajes de
  WhatsApp, donde ayudan a escanear.
- Estados vacíos con texto útil y **en positivo** cuando corresponde: si el filtro por
  defecto es "necesita atención" y no hay nada, el mensaje es "Todo al día", no "sin
  resultados".
- Los textos de error se escriben para mostrarse tal cual al usuario, en castellano, sin
  jerga técnica ni códigos.
- Nombres cortos y memorables para las entidades que se repiten (deptos, sucursales,
  máquinas): una palabra, en tipografía condensada. Se vuelven el vocabulario del equipo y
  del bot.
