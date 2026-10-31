# Créditos: modos, topes y los 6 consejos de la guía

## Modo calidad vs modo ahorro

| | Calidad | Ahorro (por defecto) |
|---|---|---|
| Fotos | `gpt_image_2_5`, `quality: "high"`, `resolution: "4k"` | `quality: "medium"`, `resolution: "2k"` (~1 crédito por foto) |
| Clips | `seedance_2_5` 1080p (hasta ~16 créditos/s) o `seedance_2_0` `mode: "std"` 1080p | `seedance_2_0_mini` 720p, 5 s, `generate_audio: false` (~1 crédito/s) |
| Reintentos | Los necesarios, dentro del tope | 1 por pieza; más, preguntando |
| Investigación | Más fuentes (15–25), ver videos completos | 12–15 fuentes, transcripciones, máx. 2 videos completos |

## Tope por defecto (estimaciones de la guía, modo ahorro)

Si el pedido no trae `tope=`, se toma este. En modo calidad no hay estimación: siempre mostrar la cotización y esperar
el sí.

| Método | Tope ahorro |
|---|---|
| Fotos | 1 × cantidad de fotos (+1 de prueba) |
| Recorrido | 60 |
| Anuncios | 135 por anuncio (405 los tres) |
| YouTube guion | 0 (Claude no gasta; la guía decía 5–15 en el SuperComputer) |
| YouTube video | 140 (máx. 30 en la prueba) + ~65 si se genera la voz |

Los números de la guía son estimaciones: manda `get_cost`. Si `get_cost` da más que el tope, mostrar y preguntar.

## Los 6 consejos, aplicados

1. **Modo Free del SuperComputer** → acá todo lo que no genera lo hace Claude: no cuesta créditos.
2. **Modelos y ajustes baratos** → Seedance 2.0 Mini 720p, clips cortos y sin sonido generado.
3. **Contestar las preguntas primero** → intake en una sola tanda antes de generar.
4. **Música y voz** → música libre de derechos o sintetizada, voz grabada por el usuario; armado local (CapCut en la
   guía, acá `armar.py` con ffmpeg).
5. **Probar antes de escalar** → una pieza primero; si todavía se está definiendo el estilo, probar a 480p (la mitad
   que 720p): `resolution: "480p"`.
6. **Iterar puntual** → si una toma falla, se regenera solo esa. Nunca todo el video por una toma.
