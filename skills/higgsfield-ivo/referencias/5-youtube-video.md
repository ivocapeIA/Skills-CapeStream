# Método 3.2 — Producción del episodio, prueba primero

Usa el `handoff.md` de la etapa 3.1 (si no existe, pedirlo o correr 3.1; nunca inventarlo). No rehacer la
investigación ni reescribir el guion. Resultado: un video reproducible, no un plan ni clips sueltos.

## Entradas opcionales
Tope total y tope de la prueba (ahorro: 140 / 30) · voz preferida o voz autorizada · referencias visuales · marca ·
resolución (default 1080p 16:9) · cambios al handoff.
**Narración: preguntar al principio si la graba el usuario o se genera** (`seed_audio`; la guía estima +60–65
créditos para un episodio). Si la graba el usuario: esperar el archivo antes de editar a su ritmo.

## Fase A — Preflight
1. Confirmar que están la narración completa, fuentes, plan de escenas, miniatura elegida y pasaje de prueba.
2. Decidir el camino real de armado antes de comprar nada: imágenes y clips del MCP + `armar.py` local.
3. Estilo único: una paleta, una tipografía, los mismos objetos recurrentes. En ahorro, `gpt_image_2_5` low para
   fondos simples y medium para cuadros clave; clips `seedance_2_0_mini` 720p 5 s sin audio. En calidad,
   `gpt_image_2_5` high y `seedance_2_5` 1080p.
4. Llevar registro de trabajos aceptados, terminados, fallidos y dudosos (`generado/registro.md`). Reintentar solo lo
   fallado; no reenviar algo con resultado incierto sin verificar primero.

## Fase B — La prueba (15–20 s)
- Del pasaje elegido: narración, visuales terminados, texto en pantalla sincronizado, música y export reproducible.
  Máximo 2 clips en ahorro.
- Tiene que entenderse sola: qué es el mecanismo, quiénes actúan, montos y consecuencias. Sin "como vimos" ni
  pronombres sueltos. Narración y texto en pantalla dicen lo mismo.
- Calidad de verdad, no "lujo" de fachada: composición clara, tipografía firme, cada visual muestra causa y
  efecto. Sin marcas inventadas, etiquetas ilegibles, interfaces falsas, manos deformes ni objetos que mutan.
  Las ilustraciones generadas se presentan como ilustraciones.
- **PARAR**: entregar la prueba con su duración real y preguntar "¿apruebo esta dirección para el episodio completo
  o qué cambio?". Si piden cambios, revisar solo la prueba. No producir el episodio en paralelo.

## Fase C — Episodio completo (después del sí)
- La prueba es el estándar, no una plantilla: variar encuadre, escala y forma de explicar.
- Voz: una sola interpretación, voz con licencia o autorizada (nunca imitar a una persona real sin permiso).
  Escuchar nombres, siglas, fechas, montos y negaciones. Editar los visuales al reloj REAL de la voz (medir con
  ffprobe), sin acelerar ni cambiar el tono.
- Visuales: registrar el origen de cada recurso (generado, licenciado, propio). Gráficos y cifras exactos como
  texto del armado; cuidar unidades, bases y que no aparenten más certeza que la evidencia.
- Edición y sonido: cambios con motivo, gráficos el tiempo justo para leerlos, sin zooms perpetuos ni cortes
  arbitrarios. Música baja debajo de la voz (`armar.py` la atenúa sola cuando hay voz).
- Subtítulos: archivo .srt aparte hecho sobre la voz final (no estimado por palabras). Quemarlos solo si se pidió.
- Miniatura: una, con el flujo `thumbnail-generation` del MCP (`get_workflow_instructions`), que prometa lo que el
  episodio cumple y se lea en chico.
- Título, descripción, capítulos reales (según el armado final), links de fuentes, créditos y aviso de IA.

## Fase D — Dos controles
1. Técnico y de hechos sobre el render completo: reproduce, duración/aspecto/resolución, sin cuadros negros ni
   cortes de audio, hechos y cifras bien dichos y bien escritos, texto legible, continuidad, subtítulos en
   sincronía, licencias.
2. Editorial: ¿alguien que lo ve por primera vez entiende qué pasa y por qué importa? ¿El gancho da razones para
   seguir? ¿Cada sección avanza? ¿Los visuales explican o decoran? ¿Se siente clase o presentación de diapositivas?
   ¿El final responde la pregunta inicial?
Informar con honestidad qué se revisó completo y qué por muestreo. No prometer retención, CTR ni ingresos.

## Entregables (`final/`)
1. `episodio.mp4` 16:9. 2. `miniatura.png`. 3. `episodio.srt`. 4. Título, descripción, capítulos, fuentes, créditos
y aviso. 5. Narración final. 6. `armar.json` + recursos (proyecto reproducible). 7. Informe breve: duración,
resolución/fps, controles hechos, derechos, limitaciones y créditos gastados.
