---
name: higgsfield-ivo
description: |
  Ejecuta de punta a punta, con el MCP de Higgsfield (claude_ai_Higgsfield) y sin abrir la web, los tres métodos de
  la guía "Higgsfield Prompts" (educateio): (1) Content Maxxing — mejorar fotos de una propiedad y armar el video
  recorrido para el anuncio; (2) AI Ads — convertir un anuncio existente en 3 anuncios nuevos para Facebook/Instagram;
  (3) Faceless YouTube — investigar nicho + guion completo y después producir el episodio (prueba primero). Cada uno en
  modo "calidad" o "ahorro" de créditos. Claude hace la parte que en la guía hace el SuperComputer (pensar,
  investigar, guionar, revisar, armar), así que solo se gastan créditos al generar imagen, video o voz.
  Usar cuando pidan: "mejorá estas fotos", "video del depto/propiedad", "video para el anuncio de Airbnb",
  "variantes de este anuncio", "3 anuncios a partir de este", "canal faceless", "video de YouTube sin cara",
  "higgsfield ivo", o /higgsfield-ivo <metodo>.
argument-hint: "<fotos|recorrido|anuncios|youtube-guion|youtube-video> [calidad|ahorro] [tope=<créditos>] [rutas o notas]"
---

# higgsfield-ivo

Fuente: https://app.notion.com/p/educateio/Higgsfield-Prompts-3f3cd6100a7b80a78fe0e15c27081763
La guía está pensada para pegar prompts en el SuperComputer de Higgsfield. Esta skill hace lo mismo **por MCP**:
Claude cumple el rol del SuperComputer (en su modo "Free": planifica, investiga, escribe y revisa sin costo) y
llama a las herramientas `mcp__claude_ai_Higgsfield__*` solo para generar. El armado final se hace **local con
ffmpeg** (`scripts/armar.py`), que no cuesta créditos: es exactamente lo que la versión de bajo costo pide
("armá solo si no cuesta créditos extra").

## Uso rápido

| Pedido | Método | Referencia a cargar |
|---|---|---|
| `/higgsfield-ivo fotos ahorro C:\fotos\depto` | 1.1 Mejora de fotos | `referencias/1-fotos.md` |
| `/higgsfield-ivo recorrido calidad` | 1.2 Video recorrido | `referencias/2-recorrido.md` |
| `/higgsfield-ivo anuncios ahorro anuncio.mp4` | 2. Variantes de anuncio | `referencias/3-anuncios.md` |
| `/higgsfield-ivo youtube-guion` | 3.1 Investigación y guion | `referencias/4-youtube-guion.md` |
| `/higgsfield-ivo youtube-video` | 3.2 Producción del episodio | `referencias/5-youtube-video.md` |

Si el pedido no nombra el método, deducirlo de lo que pasan (fotos de una propiedad → 1; un video publicitario →
2; un tema o canal → 3). Si nombran una propiedad sin decir más ("hacé el video del depto"), son 1.1 + 1.2 seguidos:
el recorrido siempre usa las fotos YA mejoradas.

**Modo por defecto: `ahorro`.** `calidad` solo si lo piden ("máxima calidad", "premium", "calidad"). Diferencias
en `referencias/creditos.md`.

**Antes de cualquier llamada al MCP, leer `referencias/mcp.md`** (herramientas, subida de archivos, esperas,
descargas) y la referencia del método.

## Flujo común (los cinco métodos)

0. **Preflight (gratis).** `balance` (créditos disponibles). Carpeta local de trabajo:
   `<carpeta actual>/higgsfield/<método>-<AAAA-MM-DD>/` (`entrada/`, `generado/`, `final/`). Si el MCP no
   responde o pide login, avisar que hay que reconectar el conector Higgsfield en claude.ai y parar.
1. **Intake mínimo.** Tomar lo que ya vino en el pedido. Preguntar en UNA sola tanda solo lo que bloquea (consejo
   #3 de la guía: preguntar todo primero ahorra reintentos). Lo que no bloquea se asume y se dice.
2. **Pensar todo gratis.** Análisis de las fotos o del anuncio, investigación, guiones, plan de tomas: lo hace
   Claude, sin generar nada. Las fotos se miran con Read; un video local se puede leer extrayendo cuadros con
   ffmpeg (gratis) en vez de `video_analysis_create`.
3. **Cotizar.** Cada generación prevista se cotiza con `get_cost: true` (no envía nada). Mostrar plan + cotización
   detallada (ítem × créditos) y el total contra el saldo.
4. **Aprobación por tope.** `tope=<N>` en el pedido = presupuesto aprobado. Sin tope, se toma como tope la
   estimación de la guía para ese método y modo (tabla en `creditos.md`). Si la cotización entra en el tope →
   seguir sin preguntar. Si no entra → mostrarla y esperar un sí. Nunca pasar el tope por reintentos.
5. **Una prueba primero.** Generar UNA imagen o UN clip, mirarlo (bajar el archivo y revisarlo) y recién después
   el resto, en lote (`generate_*_batch` + `jobs_wait`).
6. **Revisar cada salida contra su fuente** (checklist del método). Si una falla: regenerar SOLO esa, con
   instrucciones más acotadas; máximo 1 reintento por pieza sin preguntar.
7. **Armar local** con `scripts/armar.py` (cortes, música, voz, textos superpuestos) y verificar el archivo final
   con ffprobe (duración, resolución, que tenga audio).
8. **Entregar:** rutas de `final/`, qué se gastó (créditos reales, según `balance` antes y después), qué se revisó y
   qué limitación quedó. Anotar en `aprendizajes.md` de esta skill cualquier cosa nueva (costos reales, modelos
   que fallaron, prompts que funcionaron).

## Reglas que valen siempre (de la guía)

- **Prompt más específico → menos trabajo y más créditos; menos específico → más trabajo y menos créditos.** El
  modo elige de qué lado se juega.
- **No inventar contenido.** Fotos: misma escena, mismos objetos, mismo encuadre. Anuncios: nada de precios,
  reseñas, garantías, plazos ni datos de contacto que no estén confirmados. YouTube: ni fuentes, ni citas, ni cifras
  inventadas.
- **Solo se mueve la cámara** en los videos hechos desde fotos: los objetos no se desplazan, no aparecen personas ni
  ambientes que no se fotografiaron, no se pasa de un ambiente a otro.
- **Texto exacto, nunca generado:** nombre del negocio, logo, precios, teléfono, web, llamado a la acción, cifras y
  gráficos se superponen al armar (`armar.py` → `textos`), no se le piden al modelo.
- **Un zoom digital sobre una foto no reemplaza un clip generado.** Si un ambiente no sale bien, decirlo y pedir
  un video real de ese ambiente en vez de esconderlo.
- **Música:** el catálogo actual del MCP no tiene modelo de música para uso general (confirmar con
  `models_explore` tipo audio y query "music"; si aparece `suno_music`, usarlo con `instrumental: true`). Si no: la
  música sintetizada de la skill `estudio-video` (`plantilla/proyecto/scripts/musica.py`) o una pista libre de
  derechos que pase el usuario (Pixabay Music, YouTube Audio Library). Nunca canciones conocidas.
- **Voz:** `generate_audio` con `seed_audio` + una voz de `list_voices`; en modo ahorro preguntar antes si la va a
  grabar el usuario (la guía estima +60–65 créditos por voz generada en un episodio).
- Disclosures: imágenes generadas que ilustran algo no se presentan como trabajo, personal o clientes reales.
