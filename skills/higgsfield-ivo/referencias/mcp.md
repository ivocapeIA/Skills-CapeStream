# Higgsfield por MCP: hoja de uso

Todas las herramientas son `mcp__claude_ai_Higgsfield__<nombre>` y vienen diferidas: cargarlas con ToolSearch en
UNA sola llamada al empezar, por ejemplo:
`select:mcp__claude_ai_Higgsfield__balance,mcp__claude_ai_Higgsfield__media_upload,mcp__claude_ai_Higgsfield__media_confirm,mcp__claude_ai_Higgsfield__generate_image,mcp__claude_ai_Higgsfield__generate_image_batch,mcp__claude_ai_Higgsfield__generate_video,mcp__claude_ai_Higgsfield__generate_video_batch,mcp__claude_ai_Higgsfield__generate_audio,mcp__claude_ai_Higgsfield__jobs_wait,mcp__claude_ai_Higgsfield__show_generation_by_ids,mcp__claude_ai_Higgsfield__models_explore,mcp__claude_ai_Higgsfield__list_voices`

## Herramientas que usa la skill

| Para qué | Herramienta | Notas |
|---|---|---|
| Saldo | `balance` | Antes y después, para informar el gasto real |
| Subir un archivo local | `media_upload` → `curl -X PUT --upload-file <archivo> "<upload_url>"` (con el `Content-Type` que indique) → `media_confirm` (`type: image/video/audio`) | Hasta 20 archivos por llamada (`files[]`). El `media_id` confirmado es lo que va en `medias[].value` |
| Media de una URL web | `media_import_url` | Nunca pasar una https:// en `medias` |
| Una imagen | `generate_image` | `params: { model, prompt, medias, aspect_ratio, quality, resolution, get_cost }` |
| Varias imágenes distintas | `generate_image_batch` | 2–12 pedidos independientes, sin widget; después `jobs_wait` |
| Un clip | `generate_video` | `params: { model, prompt, medias:[{value, role:"start_image"}], duration, resolution, aspect_ratio, generate_audio:false }` |
| Varios clips | `generate_video_batch` + `jobs_wait` | Grupos de hasta 12 |
| Voz | `list_voices` → `generate_audio` `{ model:"seed_audio", prompt:<texto exacto>, voice_type, voice_id, format:"mp3" }` | Una toma por guion aprobado |
| Esperar | `jobs_wait` (`timeout_seconds` ≤ 15) | Si `all_terminal` es false, volver a llamar a los `poll_after_seconds` |
| Mostrar resultados | `show_generation_by_ids` | Una sola vez al final de cada lote |
| Modelos y parámetros | `models_explore` `action:"get", model_id` | Confirmar duraciones, resoluciones y roles antes de cotizar |
| Analizar un video | `video_analysis_create` → `video_analysis_status` | Alternativa gratis: cuadros con ffmpeg + Read |
| Miniatura de YouTube | `get_workflow_instructions` `{ workflow:"thumbnail-generation" }` | Seguir ese flujo |

## Modelos verificados (2026-10-31)

- `gpt_image_2_5`: edición y generación con referencias (`medias` rol `image_references`). `quality`
  low|medium|high|xhigh|max, `resolution` 1k|2k|4k, `aspect_ratio` incluye `auto` (usarlo para respetar el de la
  foto).
- `seedance_2_0_mini`: 4–15 s, 480p|720p, roles `start_image`/`end_image`/`image_references`, `generate_audio`
  (default true: pasarlo en false).
- `seedance_2_0`: hasta 4k; `mode: "std"` (1080p/4k, plan Plus o superior) o `"fast"` (480p/720p).
- `seedance_2_5`: 4–30 s, 480p|720p|1080p, `mode: "omni_reference"` para usar la foto como referencia; `draft: true`
  hace un borrador a 480p que se puede pasar a 1080p después (`draft_job_id`): sirve para probar barato.
- `seed_audio`: voz (TTS) con voces preset o clonadas.
- Música: no hay modelo general en el catálogo actual (ver SKILL.md).

## Reglas del MCP que hay que respetar

- `get_cost: true` cotiza sin enviar. Cotizar SIEMPRE antes de gastar.
- No pasar `use_unlim` ni `use_free_gens` salvo que el usuario lo pida. Si la respuesta trae `unlim_choice`, hacerle
  esa pregunta al usuario.
- Si una llamada se corta por timeout, el trabajo puede haberse enviado igual: NO reenviar; buscar el job y
  esperarlo.
- Si la respuesta trae `recovery_tool`, llamarla enseguida.
- Carpeta de destino: antes de la primera generación, `get_preferences`; crear proyecto (`create_project`) solo si
  `auto_create_project` es true o el usuario lo pide, y reusar ese `folder_id` en todo el trabajo.

## Bajar los resultados

`jobs_wait` devuelve las URLs. Bajarlas a `generado/` con nombre de toma:
`curl -sL "<url>" -o generado/toma-03.mp4`. Revisar cada clip extrayendo cuadros de inicio, medio y final:
`ffmpeg -v error -ss 0 -i toma-03.mp4 -frames:v 1 c0.jpg` (repetir a la mitad y en el final) y mirarlos con Read
junto a la foto original.
