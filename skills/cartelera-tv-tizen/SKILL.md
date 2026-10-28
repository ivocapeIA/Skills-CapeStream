---
name: cartelera-tv-tizen
description: Construye páginas HTML autocontenidas de cartelería digital (digital signage) para pantallas de TV Smart TV / Samsung Tizen embebidas en el navegador del televisor — carteles de local, menús, vidrieras digitales. Usar siempre que el usuario pida una página para "incrustar en el navegador de una Smart TV / Samsung TV", una "cartelería digital", una "vidriera digital", o un cartel de local (heladería, panadería, bar, tienda, etc.) pensado para quedar prendido sin interacción humana. Cubre restricciones de rendimiento de navegadores Tizen, cursor oculto, carrusel de fotos, WiFi+QR sin dependencias externas, y sonido ambiente con Web Audio API.
---

# Cartelería digital para TV (Samsung / Tizen)

Guía para armar páginas HTML de un solo archivo, pensadas para quedar **incrustadas y desatendidas** en el navegador de una Smart TV (típicamente Samsung Tizen). Es el mismo tipo de pantalla que usarías como vidriera digital, cartel de horarios, o menú animado de un local.

Esta skill nació de construir cuatro ejemplos reales (panadería, escuela de quesos, vinoteca, heladería) y corregir en el camino varios problemas específicos de TV. **Los ejemplos completos y funcionando están en `../../ejemplos/`** — la forma más rápida de arrancar un caso nuevo es copiar el que más se parezca y adaptar paleta/motivo/contenido, no partir de cero.

## Restricciones que definen todo lo demás

Antes de escribir una línea de código, tené esto en la cabeza — son la razón de casi todas las decisiones de abajo:

1. **No hay mouse.** El único input es el control remoto (D-pad + Enter/OK), o directamente nada (pantalla 100% desatendida). Esto implica: cursor oculto siempre, sin scroll (todo entra en un viewport), y cualquier elemento interactivo tiene que funcionar con foco + tecla, no solo con click.
2. **El hardware es de gama baja.** Los navegadores Tizen (sobre todo en TVs de unos años) tienen CPU/GPU mucho más débil que un navegador de escritorio. Animaciones que no pesan nada en Chrome pueden trabar una TV.
3. **La página puede quedar corriendo horas sin recargar.** Nada de memory leaks evidentes (intervals que se acumulan, listeners que no se limpian).
4. **La conectividad no está garantizada.** No asumas que vas a poder pegarle a un CDN externo cada vez que la página cargue.

## Checklist de arranque

- [ ] `html, body, *` con `cursor: none !important` — nunca se ve el puntero.
- [ ] Un solo `viewport` 100vw × 100vh, `overflow: hidden`. Sin scroll.
- [ ] Todo en **un solo archivo HTML** (CSS y JS inline). Es lo que se "incrusta" en el navegador de la TV; no hay build step ni carpeta de assets que la TV pueda resolver.
- [ ] Paleta y motivo animado **propios del rubro**, no una plantilla reciclada con el texto cambiado (ver "Identidad por rubro" más abajo).

## Rendimiento: qué evitar y por qué

Esto es lo que más nos hizo dar marcha atrás durante el desarrollo real. En orden de impacto:

| Evitar | Por qué | Alternativa |
|---|---|---|
| `ConvolverNode` (reverb por convolución) en Web Audio | Es, con diferencia, la operación más cara de CPU en audio en tiempo real | Envolvente de ganancia simple (`linearRampToValueAtTime` / `exponentialRampToValueAtTime`) para simular cola de sonido |
| `backdrop-filter: blur()` | Muy mal soportado / muy pesado en WebKit de Tizen | Fondo semitransparente sólido (`rgba(...)`) sin blur |
| `transform: scale()` animado continuo sobre imágenes full-screen (efecto Ken Burns) | Fuerza recomposición constante de capas grandes | Crossfade de solo `opacity` entre slides — mismo carrusel, mucho más liviano |
| `filter: blur()` por elemento, repetido en muchos nodos (ej. 20 partículas con blur individual) | Cada filtro es su propio costo de render | Sacar el blur, o aplicarlo una sola vez a un contenedor si hace falta |
| Muchos nodos de audio siempre activos (osciladores + LFOs de sobra) | Suma silenciosa de CPU incluso con el sonido "de fondo" | Ir al mínimo que logre el efecto: 2 notas de pad alcanzan, no hacen falta 6 |
| Demasiadas partículas DOM animadas | Cada una es un elemento + una animación corriendo | 10–15 partículas es un punto razonable; 20+ empieza a notarse |

Regla general: si algo se ve bien en el navegador de tu computadora pero no estás seguro de si una TV lo banca, sacalo o abaratalo — en cartelería desatendida nadie va a extrañar un blur, pero sí van a notar que la página tartamudea.

## Carrusel de fotos reales

- Fondo compuesto por 3–4 `<div class="slide">` apilados con `background-image`, cada uno con su propio `animation-delay` sobre una `@keyframes slideShow` que solo anima `opacity` (nunca `transform`).
- Overlay (`.scrim`) con gradiente oscuro encima para que el texto sea legible sobre cualquier foto.
- **De dónde sacar las fotos:**
  - Fotos de banco libre (Unsplash) → sí se pueden usar directo por URL (`images.unsplash.com/photo-...`), son de licencia libre y no requieren atribución.
  - Fotos reales de un negocio puntual (ej. "la heladería real de tal ciudad") → **no** hay forma de bajarlas automáticamente a un HTML descargable. Google Places solo las expone a través de su propio visor con atribución obligatoria, no da URLs crudas para incrustar. Si el usuario quiere fotos reales de su local, tienen que subirlas ellos y vos las insertás directo — es la única vía limpia.
- Riesgo a mencionar siempre: si la URL de la foto (o de Google Fonts) no carga por falta de red en el momento, esa capa queda vacía pero el resto de la página sigue funcionando (por eso el overlay + fondo de color de respaldo en `body` importan).

## WiFi + código QR (pre-generado, sin JS en el navegador)

Esta fue la parte que más iteraciones tuvo. La versión que termina funcionando bien en todos los casos:

1. **Nunca generar el QR contra una API externa** (tipo `api.qrserver.com`) ni cargarlo de un CDN en tiempo de ejecución (tipo `cdnjs.cloudflare.com/.../qrcodejs`). Ambas fallan en silencio si la TV no tiene esa red disponible en el momento justo.
2. **Tampoco conviene generarlo con JavaScript propio en el navegador de destino**, aunque esté todo incrustado sin depender de red — probamos esa versión y falló apenas alguien insertó el HTML copiado en un sistema que sanitiza `<script>` (muy común en editores de CMS o widgets "seguros" de HTML): sin script, el QR nunca se dibuja y queda en blanco.
3. **La solución que sí es robusta: pre-generar el QR como SVG estático, una sola vez, en tiempo de build (con Node, no en el navegador), y pegar el resultado literal dentro del HTML.** Así el QR se ve incluso si el destino bloquea scripts, incluso si no hay red, e incluso si alguien copia solo el `<body>` sin los `<script>`. La librería `assets/qrcode.js` (misma de Kazuhiko Arase, MIT) se usa como herramienta de build, no como dependencia de runtime:

```bash
node -e "
var fs = require('fs');
eval(fs.readFileSync('assets/qrcode.js', 'utf8'));
var qr = qrcode(0, 'L');
qr.addData('WIFI:T:WPA;S:MiRed;P:miclave;;');
qr.make();
console.log(qr.createSvgTag({ scalable: true, margin: 2 }));
"
```

Pegar el `<svg>...</svg>` que imprime directo adentro de `<div id="qrcode">...</div>` en el HTML final. `createSvgTag` ya resuelve solo el tamaño exacto (es múltiplo perfecto del número de módulos, sin sobrante que quede desfasado) y el margen de silencio.

4. **Recolorear vía CSS**, no vía opciones de la librería: `#qrcode svg rect { fill: var(--cream); }` y `#qrcode svg path { fill: <color oscuro de marca>; }` — funciona igual con el SVG estático porque sigue siendo SVG real en el DOM, solo que ya no depende de que corra ningún script para existir.
5. **Formato del string WiFi:** `WIFI:T:WPA;S:<nombre_red>;P:<contraseña>;;` — la mayoría de los celulares lo reconocen y ofrecen conectarse solos al escanear.


## Sonido ambiente

- **Ningún navegador deja que una página reproduzca audio sin gesto del usuario primero** — ni siquiera en modo kiosco. No prometas autoplay real; lo más honesto es:
  1. Intentar arrancar el audio apenas carga la página (`startAmbience()` al final del script).
  2. Si el navegador lo bloquea, dejarlo armado para arrancar con el primer `click`, `keydown` o `touchstart` en cualquier parte de la página (el primer toque del control remoto ya sirve).
  3. Tener además un botón `<button>` real y focuseable (no un `<div onclick>`) para prender/apagar a mano — así funciona también con navegación por control remoto (foco + Enter).
- **Sintetizar el sonido con Web Audio API en vez de usar archivos de audio.** Cero problemas de copyright, cero peso de archivo, cero dependencia de red. Un pad de 2 notas (osciladores triangulares + LFO lento) más algún arpegio ocasional alcanza para dar ambiente; ver la tabla de rendimiento para lo que NO conviene sumarle (reverb por convolución, de más).
- **Tono según el rubro:** un pad grave y lento funciona para cava/bodega; un arpegio rápido en escala mayor pentatónica con onda triangular da un jingle alegre para heladería/local infantil. Ajustá tempo y registro al mood del lugar, no reuses el mismo patrón para todo.

## Identidad por rubro (evitar la sensación de plantilla reciclada)

Cuando el usuario pide una página nueva para otro tipo de local, no alcanza con cambiar el texto sobre la misma base visual. Como mínimo, cambiá:

- **Paleta de color**, derivada del producto real (ej: bordó/dorado para vino, celeste/pastel para heladería, verde cava oscuro para quesos) — evitar el default genérico crema+terracota si no tiene que ver con el rubro.
- **El motivo animado central**, propio del producto (pan con vapor / rueda de queso con cuña / copa de vino que se mece y gotea / cucurucho con bochas que rebotan) — no reciclar el mismo ícono con otro color.
- **La cinta de texto en loop** con ítems reales del rubro (variedades, sabores, productos).
- **El texto** ancla el lugar/contexto real (ej. mencionar la ciudad) sin afirmar que las fotos de stock son del local real si no lo son — avisale al usuario esa diferencia explícitamente.

## Cómo llega la página a la TV (esto es lo que realmente importa)

**El botón de "copiar código" (ver más abajo) no es un método de despliegue.** Es tentador pensar que alguien puede copiar el HTML y pegarlo directo en la barra de direcciones de la TV como `data:text/html,...`, pero las barras de direcciones de los navegadores de TV tienen un límite de caracteres bastante bajo (unos pocos miles, varía por modelo) — y estas páginas, con la librería de QR incrustada y el resto, pesan entre 10.000 y 80.000 caracteres. No entra, y no hay forma de comprimir el código lo suficiente sin sacrificar funcionalidad. Si alguien intenta este camino, el navegador va a rechazar el pegado por "demasiado largo".

**El método que sí funciona: alojar el archivo y que la TV cargue una URL corta.** Opciones de más simple a más permanente:

1. **Netlify Drop** (`app.netlify.com/drop`) — arrastrás el `.html` a la página y te da una URL pública al instante, sin cuenta. Ideal para probar rápido.
2. **GitHub Pages** — un poco más de configuración (subir a un repo, activar Pages), pero la URL queda fija para siempre sin depender de que nadie la mantenga activa.
3. **Servidor local en la misma red** — `python3 -m http.server` en una compu o Raspberry Pi conectada a la misma red que la TV, y la TV apunta a la IP local (ej. `192.168.1.20:8000/heladeria.html`). Sirve si no querés depender de internet externo, pero esa compu tiene que quedar prendida todo el tiempo.

Para qué sirve entonces el botón de copiar código: para que alguien se lleve el HTML a un editor, a otro proyecto, o lo suba a mano al hosting elegido — no para pegarlo directo en la TV.



Útil para que quien esté manejando la TV con el control remoto pueda llevarse el código completo de la página (por ejemplo, para pegarlo en otra pantalla, en un editor, o compartirlo) sin necesitar una compu conectada al mismo archivo.

- Botón real (`<button>`, focuseable), no un `<div onclick>`, para que funcione con foco + Enter del control remoto igual que el botón de sonido.
- Copia `document.documentElement.outerHTML` (con el `<!DOCTYPE html>` agregado a mano, porque `outerHTML` no lo incluye) usando `navigator.clipboard.writeText`, con un *fallback* a `document.execCommand('copy')` vía un `<textarea>` oculto para navegadores Tizen más viejos que no tengan la Clipboard API.
- Da feedback visual breve ("¡Copiado!") por 2 segundos y vuelve al estado original — así confirma que la acción funcionó sin agregar un modal ni interrumpir la pantalla.
- Ubicación sugerida: arriba a la izquierda (el resto de las esquinas ya están ocupadas por WiFi, sonido, y los puntos del carrusel).

**Trampa real que nos pasó: no copiar `document.documentElement.outerHTML` directamente en el momento del click.** Para cuando alguien toca el botón, otros scripts de la página (el que genera el QR, el que inyecta partículas) ya mutaron el DOM — el QR en particular, al generarse como SVG, agrega varios KB de más (un `<path>` con un tramo por cada módulo oscuro: en nuestros ejemplos, ~8,7 KB solo de eso) que no existen en el archivo original. Si el botón copia el DOM tal cual está en ese momento, termina copiando el archivo real *más* toda esa gordura generada — y como esos KB de más no aportan nada útil (es contenido que cualquier copia del archivo va a regenerar sola al cargar), el único efecto es inflar innecesariamente lo que se copia.

**Fix:** sacar una "foto" del `outerHTML` como la primerísima línea de JS que corre en toda la página — antes de que el script del QR o el de partículas tengan chance de tocar el DOM — y guardarla en una variable global. El botón de copiar usa esa foto, no el DOM en vivo:

```html
<script>
  // Debe ser el PRIMER <script> de la pagina, antes que cualquier otro
  // que mute el DOM (QR, particulas, etc.)
  window.__SOURCE_SNAPSHOT__ = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
</script>
<!-- ... resto de los scripts que generan QR, particulas, etc ... -->
<script>
  btn.addEventListener('click', function(){
    var source = window.__SOURCE_SNAPSHOT__ || ('<!DOCTYPE html>\n' + document.documentElement.outerHTML);
    // ... copiar `source` al portapapeles ...
  });
</script>
```

```js
function fallbackCopy(text){
  var ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.left = '-9999px';
  document.body.appendChild(ta);
  ta.focus(); ta.select();
  var ok = false;
  try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
  document.body.removeChild(ta);
  return ok;              // no asumir exito: devolver el resultado real
}

function showResult(ok){
  label.textContent = ok ? '¡Copiado!' : 'No se pudo copiar';
  setTimeout(function(){ label.textContent = 'Copiar código'; }, 2500);
}

btn.addEventListener('click', function(){
  var source = window.__SOURCE_SNAPSHOT__ || ('<!DOCTYPE html>\n' + document.documentElement.outerHTML);
  if (navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(source).then(function(){ showResult(true); },
      function(){ showResult(fallbackCopy(source)); });
  } else {
    showResult(fallbackCopy(source));
  }
});
```

**Otra trampa: probar el botón dentro de una vista previa en iframe (por ejemplo, la vista previa de archivos de un chat) puede dar resultados falsos.** Los iframes de vista previa suelen correr con permisos restringidos y pueden bloquear el acceso al portapapeles en silencio — ni `navigator.clipboard.writeText` ni el `execCommand('copy')` de respaldo tiran error necesariamente, simplemente no copian nada, y quien prueba el botón termina viendo en su portapapeles lo último que sí se copió por otra vía, dando la falsa sensación de que "copia otra cosa". Por eso el botón tiene que verificar el resultado real de `execCommand('copy')` (devuelve `true`/`false`) y mostrar un estado distinto si falla ("No se pudo copiar") en vez de asumir éxito siempre — y hay que probarlo con la página ya desplegada o al menos abierta en una pestaña de navegador común, no solo dentro de una vista previa en sandbox.

**Por qué NO hay un QR equivalente que "copie" el código:** un código QR tiene una capacidad física máxima de unos ~3.000 caracteres en el mejor de los casos (modo alfanumérico, máxima corrección de errores más baja). Estas páginas pesan entre 10.000 y 80.000 caracteres. No hay forma de codificar el HTML completo en un QR — es una limitación del estándar QR, no algo que se pueda resolver con más código. Si en algún momento se necesita ese flujo, la única vía real es subir el archivo a algún hosting (un Gist, un bucket, lo que sea) y que el QR apunte a esa URL en vez de contener el código — pero eso ya requiere un lugar donde alojar el archivo, cosa que esta skill no asume por defecto.



De abajo hacia arriba en capas (z-index):

0. `.photo-carousel` — fondo, crossfade de fotos
1. `.scrim` — gradiente oscuro para legibilidad
2. `.grain` (opcional, textura sutil estática) + partículas animadas del rubro
3. `.content` — logo/nombre (con rotación opcional de candidatos si el usuario todavía no decidió), tagline, motivo animado, cinta de texto en loop
4. Elementos fijos de esquina: horas (abajo centro), indicadores de carrusel (abajo derecha), panel WiFi+QR (abajo izquierda), botón de sonido (arriba derecha)

## Antes de entregar

- ¿Cursor oculto en todo el documento?
- ¿Cero `backdrop-filter`, cero zoom continuo en el carrusel, cero reverb por convolución?
- ¿El QR está pre-generado como SVG estático (no depende de ningún script para dibujarse, no depende de CDN ni API externa)?
- ¿El botón de sonido es un `<button>` real, focuseable, con intento de autoplay + fallback en primer toque?
- ¿Hay un botón real (focuseable) para copiar el código fuente completo, con fallback si no hay Clipboard API?
- ¿La paleta y el motivo animado son propios del rubro, no reciclados de otro ejemplo?
- Si el usuario mencionó un local real: ¿le aclaraste que las fotos son de banco genérico salvo que suba las suyas?
