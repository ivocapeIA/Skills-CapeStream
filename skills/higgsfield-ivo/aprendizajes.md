# Aprendizajes de higgsfield-ivo

Anotar acá, con fecha, lo que se aprenda usando la skill: costos reales contra la estimación, modelos o parámetros
que fallaron, prompts que funcionaron mejor, problemas del MCP. Lo más nuevo arriba.

- 2026-10-31 — Primer uso real (método 1.1, calidad, 8 fotos de un anuncio de Airbnb). Costo REAL = cotización:
  `gpt_image_2_5` con referencia cuesta 4,25 (high 4k), 2,75 (high 2k) y 1 (medium 2k) por foto; 8 × 4,25 = 34.
  Tarda ~1 min por tanda. Resultado fiel en interiores (no movió objetos, respetó vistas reales). En el atardecer
  "corrigió" el cielo gris a azul: en exteriores pedir explícitamente "keep the sky colours exactly as in the source".
  Fotos de un anuncio de Airbnb: la página pública trae `"accessibilityLabel":"Imagen de <ambiente> N"` junto a
  cada `baseUrl`; sin parámetro baja a 1200 px, con `?im_w=2560` baja a 2560. Las URLs de subida de `media_upload`
  son larguísimas: escribirlas a un archivo y subir en bucle (pegadas en un solo comando bash rompen el comillado).
  `aspect_ratio: "auto"` respetó la proporción de cada foto (salidas 3312×2480, 2480×3312, 1664×3744, 3840×2160).
- 2026-10-31 — Creación. Verificado en el MCP: `gpt_image_2_5` (quality low…max, resolution 1k/2k/4k, rol
  `image_references`), `seedance_2_0_mini` (4–15 s, 480p/720p, `start_image`, `generate_audio` true por defecto),
  `seedance_2_5` (hasta 30 s y 1080p, `draft`). El catálogo no tiene modelo de música para uso general.
  `armar.py` probado con ffmpeg 9: ffmpeg 7+ ya no tiene `-filter_complex_script` (usa `-/filter_complex`), y
  drawtext necesita `expansion=none` para que un "%" en el texto no rompa el filtro.
