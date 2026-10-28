---
name: uxui-frontend
description: Criterio de UX/UI y frontend para que una pantalla se recuerde en vez de verse como plantilla. Usar al diseñar o rediseñar páginas, el panel, landings, apps (Expo) o tarjetas; al revisar una UI "plana", genérica o "hecha por IA"; o cuando pidan mejorar el diseño, la jerarquía, la tipografía o la accesibilidad.
---

# uxui-frontend — diseño que se recuerda, sin romper lo que funciona

Punto de partida: el layout por defecto (imagen centrada, título chico, estrellas,
botón "Add to cart") **funciona** pero no hace que nadie recuerde la marca. El
trabajo es decidir una idea visual y llevarla hasta el final, sin perder
usabilidad. Principios extraídos de un reel de diseño de producto (ayoships,
2025, una pantalla de auriculares "AURA" pasando de plana a editorial) y
combinados con las reglas del repo.

## Antes de dibujar

1. **Una frase de intención**: qué debe sentir quien abre esto y qué es lo único
   que tiene que hacer. Si no entra en una línea, no se sabe qué diseñar.
2. **Un elemento héroe** por pantalla (nombre, producto, número). Todo lo demás
   se subordina a él.
3. **Leer lo que ya existe**: tokens, fuentes y componentes del archivo que se
   toca. Una pantalla nueva suma al sistema, no inventa otro. Para Expo
   (`app/`, `vigia/app/`) leer la doc de SDK 57 antes de escribir.

## Lo que sale del video

- **Escala extrema.** El texto héroe va enorme (la marca ocupa el ancho de la
  pantalla) contra un texto de apoyo chico. El contraste de tamaños arma la
  jerarquía; los tamaños parecidos ("sizes" iguales) la matan. Escala
  tipográfica con saltos de ×2 o más entre héroe y cuerpo.
- **Superposición controlada (overlap).** Título, imagen y precio se pisan: el
  producto corta la palabra, la palabra queda detrás o delante. Profundidad con
  `z-index`, no con sombras. Condición: lo importante sigue legible.
- **Una tipografía con carácter** para el héroe (serif editorial o grotesca
  condensada) y una neutra para el resto. Máximo dos familias.
- **Color con intención**: un fondo de marca que sale del producto (verde salvia
  para unos auriculares verdes), no un gris por defecto. Una paleta de 3 a 5
  tokens y un único acento para la acción principal.
- **Sacar, no agregar.** La versión plana tenía estrellas, descripción larga y
  selectores a la vista; la versión final los baja de nivel. Cada elemento tiene
  que ganarse su lugar.
- **El botón principal no se esconde.** Aunque el héroe sea gigante, la acción
  sigue fija, contrastada y al alcance del pulgar.
- **Movimiento con sentido**: entrada escalonada (`translateY` + opacidad, 60-90
  ms entre elementos), una sola curva de easing en toda la pantalla.

## Checklist de implementación (web)

- Mobile primero: probar a 320, 360 y 390 px. Sin scroll horizontal
  (`overflow-x: clip`, `min-width: 0` en hijos de flex/grid, SVG con tamaño propio;
  ya hubo desbordes en header y QR por esto).
- Tipografía fluida con `clamp()`; el héroe nunca parte una palabra a la mitad.
- Tokens como variables CSS en `:root`; modo oscuro con `prefers-color-scheme`
  si la pantalla lo necesita.
- Áreas táctiles ≥ 44×44 px, foco visible, `:active` con feedback.
- Contraste ≥ 4,5:1 en texto de cuerpo y 3:1 en texto grande. Texto sobre imagen
  siempre con velo o zona despejada.
- `@media (prefers-reduced-motion: reduce)` apaga animaciones.
- `viewport-fit=cover` y `env(safe-area-inset-*)` en pantallas con notch.
- Imágenes con `width`/`height`, `alt` real y peso razonable; fuentes con
  `display=swap` y `preconnect`. Sin librerías nuevas si CSS alcanza.
- Estados completos: cargando, vacío, error, sin permisos. Textos en español
  rioplatense, como el resto del producto.
- `<img>` y no inline para cualquier SVG de terceros (regla del gestor de QR).

## Cartelería y TV

Pantallas de 4K a distancia: texto héroe aún mayor, ≥ 2 m de lectura, sin
hover ni cursor, sin dependencias externas, animaciones baratas (Tizen/Roku
rinden poco). Roku no tiene navegador: ver `roku/README.md`.

## Cómo trabajar

1. Mostrar primero el problema ("esto es la plantilla por defecto porque…") en
   dos o tres puntos concretos, no una lista de gustos.
2. Proponer **una** dirección visual con nombre, paleta, fuentes y el elemento
   héroe; si hay duda real entre dos, mostrar las dos, no cinco.
3. Implementar sobre el archivo existente, mínimo cambio que logre el efecto.
4. Verificar en navegador a ancho de celular (captura) antes de decir "listo".
5. No commitear ni desplegar sin pedido: un push a master despliega.

## Anti-patrones

Degradé violeta genérico, tarjetas con sombra y borde redondeado en todo,
emojis como íconos, tres columnas de "features" idénticas, centrar todo,
fuentes por defecto del sistema como decisión, texto gris claro sobre blanco,
animar todo a la vez, y copiar un look sin la idea que lo sostiene.
