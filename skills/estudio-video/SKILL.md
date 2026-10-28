---
name: estudio-video
description: Hace videos y animaciones de punta a punta (reels, TikTok, shorts, historias, spots, motion graphics, animaciones 3D y abstractas, fondos líquidos, explainers, cartelería digital, carruseles con portada animada). Primero ofrece opciones según el requerimiento y el presupuesto (tipo de contenido, formato, herramienta, estilo, paleta, tipografía, voz, música, subtítulos y variantes A/B), después escribe el guion y la lista exacta de material, espera a que el usuario suba voz, tomas o fotos, y recién entonces arma, revisa y renderiza, con variantes A/B de bajo costo. Aprende de cada uso. Usar cuando pidan "hacé un video", "un reel", "una animación", "algo 3D", "un spot", "una historia animada", "contenido para redes", "variantes para testear", o al retomar un proyecto de videos/.
---

# Estudio de video

Cinco principios, en este orden:

1. **El usuario decide antes de que se produzca nada.** Opciones primero, guion después, render al final.
2. **La opción más barata que cumple.** Se elige por lo que tiene que verse y por el presupuesto, no por moda.
3. **Material real antes de pulir.** No se inventan voces, tomas ni datos para "ir avanzando".
4. **Mirar cuadros antes que renderizar.** Una hoja de revisión cuesta segundos; un render, minutos.
5. **Una variante es una diferencia en `video.json`.** Por eso las variantes A/B salen casi gratis.

La plantilla (`plantilla/`) es el motor de `videos/10-carteleria-monitor` generalizado: una pieza HTML que se dibuja en función de `t`, se captura cuadro a cuadro en Chrome y se codifica con ffmpeg. Trae tres bases: `texto` (textos cinéticos, fotos, clips), `3d` (Three.js: objeto protagonista, reflejos, bloom) y `shader` (GLSL: mesh gradient, líquido, ondas). Además: música sintetizada sin derechos, voz con duck, loudness normalizado y subtítulos palabra por palabra.

## Etapa 0 · Leer lo aprendido

Antes de la primera pregunta, leé [aprendizajes.md](aprendizajes.md) entero. Aplicá las **preferencias** sin volver a preguntarlas, usá los **resultados A/B** para elegir qué recomendar y tené en cuenta las **observaciones** pendientes. Si una de ellas cambia tu recomendación, decilo en una línea.

## Etapa 1 · Brief con opciones

Lo que el pedido ya dice no se pregunta. Preguntá con `AskUserQuestion`, en hasta tres rondas de no más de 4 preguntas. Cada pregunta lleva primero la opción recomendada, con "(Recomendado)". Usá `preview` para mostrar paletas (hex) y bocetos de estilo. Catálogo en [referencias/menu.md](referencias/menu.md).

| Ronda | Preguntas |
|---|---|
| 1 · Qué y para qué | Tipo de contenido · Plataforma y formato · Duración · Objetivo / llamada a la acción |
| 2 · Cómo se ve y con qué | **Presupuesto** · Herramienta / base · Estilo visual · Paleta (+ tipografía si queda lugar) |
| 3 · Cómo suena y cuántas versiones | Voz · Música · Subtítulos · Variantes A/B (cuántas y qué cambia, `multiSelect`) |

- **Presupuesto y herramienta:** seguí [referencias/presupuesto.md](referencias/presupuesto.md). Ofrecé siempre el nivel 0 (código, sin costo). Los niveles con IA por API aparecen como opción, marcados "no implementado todavía" ([referencias/ia-generativa.md](referencias/ia-generativa.md)). Si lo pedido no se logra con el presupuesto (por ejemplo, personajes animados a costo cero), decilo antes de seguir.
- Si el pedido es "visual" o "no de texto", la base recomendada es `3d` o `shader`, combinada con fotos o clips si los hay.
- "Decidí vos" → decidí todo, mostralo en una tabla de una línea por tema y seguí.
- Si una elección le va a jugar en contra, decilo antes de seguir.

## Etapa 2 · Guion y lista de material → **esperar**

1. Creá el proyecto desde la raíz del repo donde se trabaja; crea `videos/` si no existe (`--base texto|3d|shader`):
   `node ~/.claude/skills/estudio-video/scripts/nuevo.mjs "<nombre>" --base 3d --dur 20 --musica house --variantes A,B`
2. Escribí `videos/NN-nombre/guion.md` con la plantilla de [referencias/guion.md](referencias/guion.md).
3. Mostrá en el chat la tabla del guion y la **lista de material** concreta: qué, cómo, cuántas tomas y en qué carpeta.
4. Si el estilo es nuevo o la base es `3d` o `shader`, mostrá antes una hoja de revisión con textos provisorios (`node render.mjs --hoja`) para que apruebe el estilo.
5. **Terminá el turno pidiendo el material y la aprobación del guion.** No sigas con material inventado. Si no hace falta material (3D, shader, motion), igual esperá a que apruebe el guion.

## Etapa 3 · Recibir y revisar el material

- `ffprobe` de cada archivo: resolución, fps, duración, orientación y audio. Avisá cada problema con su consecuencia.
- Voz: `python scripts/palabras.py <voz> out/palabras/<nombre>.json "<marcas>"`. Ajustá el guion a lo que se grabó.
- Clips: declaralos en `video.json` → `clips` y corré `node frames.mjs`.
- Si falta algo, pedilo y esperá.

## Etapa 4 · Armar, revisar y renderizar

1. Adaptá `pieza.html` y `video.json` ([referencias/motor.md](referencias/motor.md)).
2. `node render.mjs --hoja` → **mirala vos primero** (Read), corregí y recién ahí mandala (`SendUserFile`). Esperá el OK.
3. Para el movimiento en 3D o shader sin placa de video: `node render.mjs --borrador` (media resolución, ~3 veces más rápido).
4. `node render.mjs` → `entregas/<slug>-<variante>.mp4`. `--portada <t>` para la portada.
5. Mandá los videos con una tabla de qué cambia en cada variante.

## Etapa 5 · Control de calidad y entrega

Seguí [referencias/entrega.md](referencias/entrega.md): checklist técnico, README, fila en `videos/README.md`, texto de la publicación, pendientes antes de publicar y `git status` (solo entregas y código).

## Etapa 6 · Retro: la skill aprende

Al cerrar cada invocación (cuando se entrega, cuando el usuario corta, o cuando se espera material después de una corrección), antes del último mensaje:

1. **Anotá en [aprendizajes.md](aprendizajes.md)** de 1 a 3 entradas, en la sección que corresponda:
   - **Preferencias:** lo que eligió o corrigió y va a querer de nuevo (estilo, tono, duración, colores).
   - **Resultados A/B:** si trajo métricas, la ganadora con su margen y su base.
   - **Observaciones:** lo que salió mal o tardó de más, con la causa y qué hacer distinto.
2. **Bug en un script o en una base:** arreglalo en `plantilla/`, probalo con `--stills` o `--hoja` y anotalo en "Arreglos". No lo dejes anotado sin arreglar.
3. **Promové:** si una observación aparece por segunda vez, o el usuario la confirma, pasala como regla a este archivo o a la referencia que corresponda y movela a "Reglas confirmadas".
4. **Higiene:** este `SKILL.md` no pasa de ~200 líneas y `aprendizajes.md`, de ~150. Si se pasan, consolidá. Nunca borres una preferencia sin preguntar.
5. **Contale al usuario** en 1 a 3 líneas qué aprendió la skill.
6. **Commit aparte:** `Actualizar la skill estudio-video con lo aprendido en NN`. En una sesión en la nube, si no se commitea y pushea, lo aprendido se pierde.

No anotes trivialidades ni lo que ya está escrito. Lo que importa es lo que cambia la próxima vez.

## Variantes A/B

Detalle en [referencias/variantes-ab.md](referencias/variantes-ab.md):

- **Una sola variable por test.**
- Por impacto y costo: **hook > portada > duración > CTA > música > paleta**. En las bases visuales también: `forma` (3D) o `shader`.
- 2 o 3 variantes por test.
- Publicar A un día y B otro no es un test: hacen falta Reels de prueba de Instagram o un experimento A/B de Meta Ads.

## Reglas que salen de los proyectos anteriores

- **El primer cuadro ya muestra el hook**, nada de fundido desde negro.
- **Zonas seguras en 9:16:** nada importante en los 250 px de arriba ni en los 340 de abajo (de 1920).
- **Loudness:** −14 LUFS en redes, −16 en cartelería.
- **Música:** sintetizada o con licencia clara. El audio en tendencia se agrega en la app al publicar.
- **Fuentes con licencia libre** (@fontsource / Google Fonts).
- **Personas, menores y marcas:** permiso antes de publicar. Producto regalado → etiqueta de colaboración paga.
- **Datos verificables o fuera.**
- **Sobre fondos que se mueven** (3D, shader, clips): texto claro con sombra; el acento, solo en una o dos palabras.
- **Cartelería:** loop sin corte y sin depender del audio.

## Otras herramientas

Remotion (`videos/_estudio-managerbnb`, `videos/11-*`) para muchas piezas de una marca con componentes compartidos. El montaje en Python de `videos/09-promo-hipicos` para mucho footage al ritmo. Canva (si el conector está) cuando el usuario lo va a editar él. Blender y Lottie, como recetas en `referencias/motor.md`.
