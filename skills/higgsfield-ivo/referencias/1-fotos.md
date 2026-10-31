# Método 1.1 — Mejora de fotos (Content Maxxing)

Objetivo: que cada foto parezca tomada por un fotógrafo de interiores de revista. Se mejora la FOTOGRAFÍA, no el
lugar: sin redecorar, sin ordenar, sin restaurar.

## Entrada
Carpeta o lista de fotos, o el link de un anuncio de Airbnb (ver `aprendizajes.md`: etiquetas por ambiente y
`?im_w=2560`). Si son muchas, elegir las importantes: una o dos por ambiente, sin ángulos repetidos, priorizando lo
que vende (vistas, luz, la cama, el living) y armar una hoja de contactos con ffmpeg para mirarlas juntas.
Subirlas en una tanda (`media_upload` con `files[]` → PUT de cada una desde un archivo con las URLs → `media_confirm`).
En exteriores (vistas, atardeceres) sumar al prompt: "Keep the sky colours exactly as in the source".

## Ejecución
- Una generación por foto, cada una con su propia foto como `image_references` (nunca varias fotos en un mismo
  pedido: la guía las mejora de a una).
- Modelo `gpt_image_2_5`, `aspect_ratio: "auto"`. Ahorro: `quality: "medium"`, `resolution: "2k"`. Calidad:
  `quality: "high"` (o `xhigh` para la foto principal), `resolution: "4k"`.
- Probar con la foto más difícil (contraluz o ventanas quemadas), revisarla, y recién después lanzar el resto con
  `generate_image_batch`.
- Bajar a `generado/<nombre-original>-mejorada.png`.

## Prompt (ahorro). Completar `{ambiente}` si se sabe; si no, borrar esa línea.

```
Edit this photograph. Improve only the photography; it must stay the exact same scene.
Scene: {ambiente}.
Keep unchanged: every object, its position, size, shape, colour and material; framing, crop, camera angle,
perspective and aspect ratio; artwork, patterns, text and small details; real wear and imperfections.
Do not add, remove, move, tidy, restage or straighten anything. No new lamps, windows, people or props.
Improve: soft, balanced, directional light built from the light already in the room (same direction, same time
of day); open muddy shadows without flattening them; bright but detailed highlights, clean midtones, natural
dark anchors; clean whites and true-to-life colours with gentle cast correction; the room's main feature (bed,
sofa, island) quietly brighter than the rest; less noise and compression, sharpening only where real detail exists.
Avoid: HDR look, grey whites, crushed blacks, orange wood, oversaturation, filters, spotlight effect, vignette,
invented texture or lettering.
If an improvement would require changing the scene, leave that area as it is.
Output one full-frame photorealistic photo that looks professionally shot, not AI-edited. No border, caption or watermark.
```

## Prompt (calidad): el de ahorro, más estos bloques al final

```
Priorities, in order: preserve content and geometry; coherent photographic lighting; tonal balance and visual
hierarchy; material rendering and technical quality; a restrained editorial finish.
Materials, only those present: fabric keeps its folds, seams and patterns without exaggerated weave; wood keeps
its grain and tone without extra orange; stone and tile keep every grout line and patina; walls get smooth light
gradients without plastic smoothing; curtains keep translucency without showing invented scenery; metal and glass
keep their reflections where they are.
Do not invent scenery in blown-out windows or detail in unreadable shadows; leave ambiguous detail ambiguous.
Do not correct converging verticals, widen the room or change furniture proportions.
Final pass: quiet anything that became conspicuous (orange floors, crunchy fabric, harsh window highlights,
distracting floor reflections, over-bright secondary objects).
```

## Revisión (mirar original y mejorada lado a lado con Read)
- ¿Están todos los objetos, en el mismo lugar y del mismo tamaño? ¿Cuadros, almohadones y textos iguales?
- ¿Encuadre, perspectiva y proporción iguales?
- ¿Luz más prolija pero creíble (sin efecto teatral, sin HDR)? ¿Colores reales?
- Si algo cambió: regenerar esa foto sola, agregando al prompt la línea "Keep exactly as in the source: <lo que
  cambió>". Máximo un reintento por foto sin preguntar.

## Entrega
Las mejoradas en `final/fotos/`, con el mismo nombre que el original. Si después viene el recorrido, se usan esas.
