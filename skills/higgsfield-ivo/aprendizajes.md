# Aprendizajes de higgsfield-ivo

Anotar acá, con fecha, lo que se aprenda usando la skill: costos reales contra la estimación, modelos o parámetros
que fallaron, prompts que funcionaron mejor, problemas del MCP. Lo más nuevo arriba.

- 2026-10-31 — Creación. Verificado en el MCP: `gpt_image_2_5` (quality low…max, resolution 1k/2k/4k, rol
  `image_references`), `seedance_2_0_mini` (4–15 s, 480p/720p, `start_image`, `generate_audio` true por defecto),
  `seedance_2_5` (hasta 30 s y 1080p, `draft`). El catálogo no tiene modelo de música para uso general.
  `armar.py` probado con ffmpeg 9: ffmpeg 7+ ya no tiene `-filter_complex_script` (usa `-/filter_complex`), y
  drawtext necesita `expansion=none` para que un "%" en el texto no rompa el filtro.
