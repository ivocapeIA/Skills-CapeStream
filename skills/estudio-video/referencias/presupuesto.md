# Herramientas según lo que se pide y el presupuesto

Se elige en la ronda 2 del brief. Primero el **requerimiento** (qué tiene que verse), después el **nivel de presupuesto**. Siempre se ofrece la opción más barata que cumple. Si el requerimiento no se puede cumplir con el presupuesto, se dice antes de empezar, no después.

## Niveles

| Nivel | Qué incluye | Estado en la skill |
|---|---|---|
| **0 · Sin costo** | Plantilla HTML (texto, fotos, clips), **base 3D** (Three.js), **base shader** (GLSL), Lottie, Blender, stock libre (Mixkit, Pexels), música sintetizada, voz neural provisoria | **Listo y probado** (Blender y Lottie, como receta) |
| **0 + GPU propia** | Modelos abiertos de video e imagen corriendo en la PC (Wan, LTX-Video, Flux en ComfyUI) | Documentado, no armado. Necesita una placa con mucha VRAM |
| **1 · Bajo** | Pocas imágenes generadas con IA (fondos, texturas, un producto en escena) que el motor anima en 2,5D; 1 o 2 clips de IA de 3 a 5 s solo para el hook | **Documentado, no implementado**: ver `ia-generativa.md` |
| **2 · Medio** | Varios clips de IA (un plano por escena), voz clonada o de estudio con IA | Documentado, no implementado |
| **3 · Alto** | Video de IA en todo el video, modelado 3D a medida, animador o editor humano | Fuera de la skill: se arma el brief para contratarlo |

Mientras el presupuesto sea bajo, **se recomienda nivel 0** y se ofrece el 1 solo para un plano que no se pueda lograr de otra forma.

## Qué herramienta para qué

| Lo que tiene que verse | Nivel 0 (recomendado hoy) | Si hay presupuesto |
|---|---|---|
| Textos cinéticos, promo con fotos o clips | Plantilla `texto` | — |
| Objeto 3D protagonista, formas brillantes, abstracto premium | Base `3d` (blob, nudo, anillo, satélites, bloom) | Modelo 3D a medida (nivel 3) |
| Fondos líquidos, mesh gradients, auroras, ondas | Base `shader` (malla, liquido, ondas) | — (no hace falta) |
| Producto real girando con luz de estudio | Blender con script, a partir de un modelo o de una caja/botella simple | Modelo 3D fiel del producto (nivel 3) |
| Íconos e ilustraciones animadas | Lottie de LottieFiles (revisar la licencia de cada uno) | Ilustración a medida (nivel 3) |
| Escena fotorrealista imposible de filmar | Stock libre (Mixkit, Pexels) | Clip de IA (nivel 1–2) |
| Producto en un escenario | Foto del producto sin fondo + escena con shader o 3D | Imagen de IA del producto en escena + animación 2,5D (nivel 1) |
| Persona hablando | El usuario se graba | Avatar o voz de IA (nivel 2): avisar que baja la confianza |
| Personajes animados | No hay buena opción a costo cero: decirlo | Imagen a video con IA (nivel 2) o animador (nivel 3) |
| Logo que se arma | Plantilla (SVG + `splitChars`) o base `3d` | — |

## Combinar en lugar de elegir una sola

Lo que más rinde casi siempre es una **mezcla**: shader o 3D de fondo, fotos o clips del usuario en el medio y textos con la plantilla. Todo queda en la misma `pieza.html`. Las bases `3d` y `shader` ya traen el hook, los beats y el CTA, así que se pueden usar solas o con fotos encima.

## Costo en tiempo (nivel 0)

Medido en el contenedor sin placa de video (el peor caso), a 1080×1920 y 30 fps:

| Base | Render final | `--borrador` |
|---|---|---|
| `texto` | ~2 s por segundo de video | — |
| `3d` | ~25 s por segundo de video | ~9 s por segundo |
| `shader` (`liquido`) | ~35 s por segundo de video | ~10 s por segundo |

Con una placa de video, 3D y shader quedan cerca del tiempo real. Sin placa: revisar con `--hoja` y `--borrador`, y hacer un solo render final.
