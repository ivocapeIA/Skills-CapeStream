# Aprendizajes de la skill

Memoria de la skill: se lee **al empezar** cada invocación y se escribe **al terminar** (etapa 6 del `SKILL.md`). Cada entrada, en una o dos líneas: fecha · proyecto · qué pasó → qué se hace ahora.

Reglas de higiene:
- Lo que se repite en 2 proyectos, o lo que el usuario confirma, se **promueve** a `SKILL.md` o a la referencia que corresponda y se borra de acá.
- Los bugs de los scripts no se anotan y se dejan: se **arreglan** en `plantilla/`, se prueban y se anota el arreglo.
- Más de ~150 líneas: consolidar (juntar las repetidas, borrar las ya promovidas).
- Nunca se borra una preferencia del usuario sin preguntarle.

## Preferencias del usuario
<!-- Se aplican desde la próxima invocación sin volver a preguntar (salvo que el pedido diga otra cosa). -->
- 2026-10-06 · Castellano rioplatense con voseo en guiones, textos y mensajes.
- 2026-10-07 · Presupuesto bajo: recomendar nivel 0. Las APIs de IA se mencionan como opción, no se implementan todavía.
- 2026-10-07 · Quiere animaciones muy visuales, no solo texto: ofrecer las bases `3d` y `shader` desde la primera ronda cuando el pedido sea "visual".
- 2026-10-07 · Cliente A (video de la app, 16:9, 60 s): para mostrar una app eligió **interfaz recreada en HTML** (no capturas reales), **voz neural provisoria con subtítulos** (no "sin voz", que era lo recomendado) y público profesional. Para una demo de app: recomendar primero la interfaz recreada y contar con voz + subtítulos.

## Resultados A/B
<!-- Variante ganadora, métrica, margen, base (reproducciones). Lo que gana se vuelve la opción recomendada. -->
- (todavía no hay resultados)

## Reglas confirmadas
<!-- Ya promovidas: quedan acá como historial de dónde salió cada regla. -->
- 2026-10-06 · Ya en SKILL.md: primer cuadro con el hook visible, zonas seguras, −14 LUFS, música sin derechos de terceros, permisos (sale de los proyectos 09, 10, 11 y 12).

## Observaciones (pendientes de confirmar)
- 2026-10-06 · prueba de la plantilla · Si la variante cambia el hook y hay voz, la voz y los subtítulos quedan diciendo el hook viejo → cada variante con voz necesita su propia toma del hook. (Ya está en `variantes-ab.md`; falta verlo en un proyecto real.)
- 2026-10-07 · prueba de bases visuales · Un mesh gradient que promedia colores queda gris y apagado → pintar cada mancha encima de la anterior (ya corregido en `bases/shader.html`).
- 2026-10-07 · prueba de bases visuales · Sin placa de video, 3D y shader tardan entre 25 y 35 s de render por segundo de video → revisar con `--hoja` y `--borrador`, y hacer un solo render final.

- 2026-10-07 · Cliente A · El texto de la voz se pasó de largo: 143 palabras dieron 73 s (la voz neural hace ~2,3 palabras/s y las pausas suman) → escribir ~2,0 palabras por segundo de video (corregido en `guion.md`) y generar la voz **por escenas** (`locucion.py`) antes de animar.
- 2026-10-07 · Cliente A · No pude escuchar la voz neural: la pronunciación de «Word» y «PDF» queda sin verificar → avisarlo siempre que la voz sea sintética.
- 2026-10-07 · Cliente A · El guion no se frenó para aprobación (pedido de video sin material): se entregó terminado con la voz provisoria → si pasa de nuevo, entregar la hoja de revisión primero.

## Arreglos hechos en la plantilla
- 2026-10-07 · `scripts/locucion.py` (nuevo) · Voz por escenas con tiempos por palabra y puntuación recuperada del texto (el servicio devuelve las palabras sin signos) → las escenas duran lo que dura su voz y la animación se ancla a palabras.
- 2026-10-07 · `render.mjs` · Con `"escala": 2` el video salía en 1080 en vez de 4K (Chrome no siempre escala la captura) → ahora ffmpeg fija el tamaño de salida.
- 2026-10-07 · `bases/shader.html` · `ShaderMaterial` convertía los colores de la paleta a espacio lineal y salían más oscuros → `ColorManagement` desactivado en la base shader.
- 2026-10-07 · `bases/shader.html` · El grano a 0,06 inflaba el archivo (19 MB cada 10 s) → bajado a 0,035.
- 2026-10-07 · `bases/3d.html`, `bases/shader.html` · La palabra en acento desaparecía cuando pasaba una mancha del mismo color (visto en la hoja de un proyecto recién creado) → el acento va como resaltador (fondo de acento, letra del color de fondo). Ojo: con `display: inline` Chrome pintaba una copia negra de la caja en otro lugar de la pantalla (span con fondo dentro de un `inline-block` con transform, sobre WebGL) → `display: inline-block`.
- 2026-10-07 · `nuevo.mjs` · Las bases visuales sin `acento2` usaban el blanco del texto como segunda mancha → el proyecto nuevo trae `acento2`.
