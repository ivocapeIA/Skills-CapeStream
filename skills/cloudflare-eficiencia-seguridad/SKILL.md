---
name: cloudflare-eficiencia-seguridad
description: Buenas prácticas de Cloudflare (Workers, D1, R2, Durable Objects) para minimizar requests/CPU/memoria/storage dentro del plan gratis, y para mantener seguras las rutas /pub y /api/admin. Cargar al tocar server/src/*, wrangler.jsonc, schema.sql, panel/, app/App.js, o cuando se pregunte por costos, límites del plan gratis, o seguridad de Cloudflare.
---

# Cloudflare: consumir menos y romper menos

Este proyecto (`server/`) corre en Cloudflare Workers + D1 + R2 + Durable Objects,
apuntando a quedarse en el **plan gratis** (o el Workers Paid de $5/mes como techo)
todo lo posible. Este skill resume los límites reales del plan gratis, qué patrones
de este mismo repo ya los aprovechan, y un checklist para no romper esos ahorros al
agregar funcionalidad. Verificado contra developers.cloudflare.com en agosto 2026;
si algo no cierra, priorizá la documentación oficial sobre este archivo.

## 1 · Límites del plan gratis (lo que hay que cuidar)

| Recurso | Límite gratis | Nota |
|---|---|---|
| Workers — requests | 100.000/día | Resetea a medianoche UTC. Error 1027 al pasarse. |
| Workers — CPU | 10 ms/request | Solo cuenta tiempo de CPU real, no espera de red/D1/R2. |
| Workers — memoria | 128 MB | Compartida por request; ver sección Memoria. |
| Workers — subrequests | 50/request | fetch() + llamadas a D1/R2/DO cuentan como subrequest. |
| D1 — filas leídas | 5.000.000/día | Por cuenta, no por base. |
| D1 — filas escritas | 100.000/día | Un INSERT/UPDATE con columna indexada escribe 2 filas (tabla + índice). |
| D1 — storage | 5 GB total | Por cuenta. |
| Durable Objects — requests | 100.000/día | HTTP, RPC, mensajes WS entrantes (ver ratio abajo), alarms. |
| Durable Objects — duración | 13.000 GB-s/día | Solo corre mientras el objeto está activo, no mientras hiberna. |
| Durable Objects — storage SQLite | 5 GB total | Facturación de storage habilitada desde enero 2026. |
| R2 — storage | 10 GB-mes | Por cuenta. |
| R2 — Class A (PutObject, ListObjects, multipart...) | 1.000.000/mes | Operaciones que mutan estado. |
| R2 — Class B (GetObject, HeadObject...) | 10.000.000/mes | Lecturas. `DeleteObject` es **gratis siempre**, en cualquier plan. |
| R2 — egress (salida a Internet) | Siempre gratis | En cualquier plan, sin límite. Por eso R2 es la pieza clave de este proyecto para video 4K. |

Un mensaje WebSocket entrante a un Durable Object se factura a razón de **20:1**
para el conteo de requests (100 mensajes = 5 requests) — no aplica a mensajes
salientes ni a pings de protocolo WebSocket.

## 2 · Lo que este repo ya hace bien — no lo deshagas

- **WebSocket Hibernation API + auto-response de ping/pong**
  (`server/src/screen-session.ts:17` y `:33`): el Durable Object de cada pantalla
  sale de memoria cuando no pasa nada y no genera cargo de duración; el latido del
  monitor lo contesta la red de Cloudflare sin despertar el objeto. **Nunca agregues
  `setInterval`/`setTimeout` dentro de un Durable Object** — eso le impide hibernar y
  lo deja facturando duración todo el tiempo que el timer esté vivo.
- **Confirmación por versión + `304 Not Modified`** en `/pub/content`
  (`server/src/index.ts:233-236`): el monitor en modo respaldo (polling cada 15 s,
  `app/App.js:65`) casi nunca recibe cuerpo de respuesta, solo un 304. Si agregás
  otro endpoint de polling, replicá este patrón (`since`/versión + 304) en vez de
  devolver el objeto completo cada vez.
- **`last_seen` no se reescribe en cada poll**: `/pub/content` solo llama a
  `touch()` si `last_seen` tiene más de `TOUCH_MIN_INTERVAL_MS` (mitad de
  `ONLINE_WINDOW_MS`, hoy 30s) — ver caso resuelto más abajo. El panel también
  pausa su polling de 5s con `document.hidden` (`server/panel/src/App.tsx`).
- **Caché inmutable a nivel de navegador para medios** (`server/src/index.ts:280`):
  las claves de R2 son UUID (`crypto.randomUUID()` en `index.ts:500`), así que
  `Cache-Control: public, max-age=31536000, immutable` es seguro — el mismo archivo
  nunca cambia de contenido. Si algún día se permite *reemplazar* un archivo
  conservando la misma key, hay que bajar ese `max-age`.
- **Subida de archivos sin bufferear**: `/api/admin/upload` reenvía el body crudo
  (`c.req.raw.body`) directo a R2 en vez de parsear `multipart/form-data`, así el
  Worker nunca carga el archivo entero en sus 128 MB de memoria.
- **Consultas parametrizadas en todo D1** (`.prepare(...).bind(...)`), nunca
  interpolación de strings — además de evitar SQL injection, es lo que D1 necesita
  para reusar el plan de consulta.
- **Comparación en tiempo constante** (`safeEqual`, `server/src/shared.ts:74`) para
  tokens de dispositivo y `ADMIN_TOKEN` — evita filtrar el secreto por timing attack.
- **JWKS de Cloudflare Access cacheado 1 hora en memoria** (`server/src/access.ts:36-37`)
  en vez de pedirlo en cada request administrativo.
- **Índices ya definidos** en `schema.sql` para las columnas por las que se filtra u
  ordena (`pairing_code`, `group_name`, `last_seen`). Nota: `pairing_code` además es
  `UNIQUE`, lo que ya crea un índice implícito — no dupliques índices en columnas
  `UNIQUE`/`PRIMARY KEY` nuevas.

## 3 · Caso resuelto: escrituras de D1 en cada poll (2026-08-12)

Al mirar **Workers & Pages → Logs** aparecía, cada 5s, `GET /api/admin/screens` — el
polling normal del panel (`REFRESH_MS`), sin nada raro. Pero eso llevó a revisar el
consumo real de D1, y ahí apareció el problema de verdad, invisible en esos logs:

`/pub/content` (el canal de respaldo del monitor, poll cada 15s cuando el WebSocket
no puede abrirse — típico detrás de un proxy corporativo) llamaba a `touch()` **sin
condición** en cada consulta, y `touch()` hace `UPDATE screens SET last_seen = ?`.
Eso es una escritura a D1 cada 15s por pantalla en modo respaldo — **5.760
escrituras/día por pantalla** solo para refrescar una marca de tiempo. Con el límite
gratis de D1 en 100.000 filas escritas/día, ~17 pantallas en modo respaldo
simultáneo ya agotaban la cuota diaria — mucho antes que el límite de requests o el
de filas leídas, y sin ningún síntoma visible salvo un error de cuota en producción.

La corrección (ya aplicada en `server/src/index.ts`): antes de llamar a `touch()`,
comparar la antigüedad del `last_seen` que ya se tenía en memoria (viene de
`authenticateDevice`, no hace falta leerlo de nuevo) contra `TOUCH_MIN_INTERVAL_MS`
(mitad de `ONLINE_WINDOW_MS`, o sea 30s). Con poll cada 15s, esto escribe cada ~30s
en vez de cada 15s — mitad de las escrituras — y el dato nunca queda más viejo que
30s antes de refrescarse, con margen de sobra bajo los 60s que usa `isOnline()`
para considerar una pantalla en línea. No hizo falta tocar el modo WebSocket: el
"ping" de latido del monitor (`app/App.js`, `HEARTBEAT_MS`) nunca llega al Durable
Object porque lo contesta la red de Cloudflare vía `setWebSocketAutoResponse`.

**Lección para este proyecto**: en D1, mirá primero las escrituras periódicas
"invisibles" que actualizan solo una marca de tiempo o un estado — son casi siempre
más baratas de throttlear con un chequeo en memoria (comparar contra un dato que ya
tenías) que de eliminar. El límite de escritura (100k/día) es mucho más fácil de
pisar que el de requests (100k/día también, pero cada pantalla hace 1 solo request
por poll) o el de lectura (5M/día).

## 4 · Checklist al agregar funcionalidad

### Requests / Workers
- Preferí los bindings directos (`env.DB`, `env.MEDIA`, `env.SCREEN`) en vez de
  pegarle a una REST API por `fetch()`: son llamadas in-process, sin round-trip de
  red ni autenticación aparte.
- Antes de bajar el intervalo de polling del panel (`REFRESH_MS` en
  `server/panel/src/App.tsx:14`, hoy 5 s) o del monitor (`POLL_INTERVAL_MS` en
  `app/App.js:65`, hoy 15 s), pensá en el costo: cada tick es al menos un request y
  una lectura de D1. Con pocas pantallas no importa; si el proyecto crece a docenas
  de pantallas/paneles abiertos, subir el intervalo es más barato que gastar el
  límite diario. El panel ya pausa su polling con `document.hidden` (pestaña en
  segundo plano) — replicá esa idea en cualquier otro polling desde el navegador.
- No pongas `Cache-Control` público en nada bajo `/api/admin/*` (son respuestas con
  datos privados de estado); hoy no se hace, mantenelo así.
- Avanzado/opcional: como `/pub/*` está en `run_worker_first`
  (`server/wrangler.jsonc:14`), el Worker se ejecuta en cada pedido de medios aunque
  el objeto de R2 no cambie — el ahorro real hoy viene del `Cache-Control: immutable`
  a nivel navegador. Si el tráfico de video creciera mucho, se puede evaluar
  [Workers Caching](https://developers.cloudflare.com/workers/cache/) (`cache:
  {enabled: true}` por export) para que ni el Worker se ejecute en un HIT. No hace
  falta con la escala actual.

### CPU y memoria (límite: 10 ms CPU / 128 MB memoria en el plan gratis)
- Si en algún momento hay que procesar un archivo subido (generar miniatura,
  hashear, transcodificar), usá `TransformStream`/streams en vez de leer el `body`
  completo a memoria — un video de varios cientos de MB no entra en 128 MB.
- No guardes estado mutable a nivel de módulo (fuera de un handler o clase) salvo
  cachés explícitas con TTL como `jwksCache` — los Workers reusan el isolate entre
  requests de usuarios distintos, así que una variable de módulo persiste (y podría
  filtrar datos) entre pedidos.
- Siempre `await` o `ctx.waitUntil()` las promesas; una promesa "flotante" en un
  Worker puede cortarse a mitad de camino cuando termina el request.

### D1 (5M filas leídas/día, 100k escritas/día, 5 GB total — gratis)
- Seguí bindeando parámetros (`?` + `.bind()`), nunca template strings con SQL.
- Si una operación nueva necesita 2+ `INSERT`/`UPDATE` relacionados en secuencia,
  usá `env.DB.batch([...])` en vez de awaits sueltos: es una sola vuelta de red y,
  si un statement falla, se hace rollback de todo el lote.
- Usá `LIMIT 1` explícito en queries que uses con `.first()`.
- Cualquier columna nueva que aparezca en un `WHERE`/`ORDER BY` de una tabla que
  pueda crecer necesita su índice en `schema.sql` (migración, no en el hot path).
- Antes de escribir en D1 en cada request de un endpoint que se llama con polling
  (heartbeats, `last_seen`, contadores), preguntate si hace falta escribir *esta*
  vez o si alcanza con comparar contra un valor que ya tenés en memoria y saltear la
  escritura — ver el caso resuelto en la sección 3. El límite de escritura
  (100k filas/día) se agota mucho más rápido que el de lectura o el de requests.

### R2 (10 GB storage, 1M Class A/mes, 10M Class B/mes — gratis; egress siempre gratis)
- Si se agrega limpieza de medios huérfanos, borrá por `key` conocida (guardada en
  D1 al subir) en vez de `list()` + filtrar — `list()` es Class A y para un bucket
  grande puede consumir cuota rápido. `delete()` no tiene costo.
- Mantené las claves como contenido-direccionado (UUID) mientras el `Cache-Control`
  sea `immutable`; si se permite editar contenido de una key existente, hay que
  invalidar el caché (cambiar la key es más simple que purgar).

### Durable Objects
- El objeto por pantalla debe seguir usando `ctx.acceptWebSocket(server)` (nunca
  `server.accept()`) — es lo único que habilita la hibernación.
- No abras conexiones salientes de larga duración (`fetch` a un stream, TCP socket)
  desde dentro de un `ScreenSession`: una conexión saliente activa mantiene el
  objeto despierto (y facturando) hasta 15 minutos, aunque no haya nada que hacer.
- Si se agrega telemetría de alta frecuencia desde el monitor (por ejemplo, métricas
  cada 1 s), agrupá varios mensajes lógicos en un solo frame WebSocket antes de
  mandarlos — cada mensaje entrante individual tiene su propio costo de contexto y
  cuenta aparte para el límite de requests del Durable Object (ratio 20:1).

## 5 · Checklist de seguridad

- **Nunca** un secreto (tokens, claves) en `vars` de `wrangler.jsonc` — quedan en
  texto plano en el repo y el dashboard. Usá `wrangler secret put` (como ya se hace
  con `ADMIN_TOKEN`) o Secrets Store. `ACCESS_TEAM_DOMAIN`/`ACCESS_AUD` sí pueden ir
  en `vars` porque no son secretos (son identificadores públicos de la app de
  Access).
- Toda ruta nueva de administración va bajo `/api/admin/*` **con** el middleware
  `requireAdmin`, y tiene que declararse antes del catch-all
  `app.all('/api/*', ...)` al final de `index.ts`.
- Las rutas `/pub/*` **no** deben quedar nunca detrás de Cloudflare Access (rompe el
  emparejamiento: el monitor no puede loguearse con Google). Se autentican por
  `device_token` comparado con `safeEqual`, nunca con `===`.
- Si se agrega un endpoint público nuevo que reciba datos de cualquiera sin
  autenticar (como hoy `/pub/register`), sumale una regla de *rate limiting* en
  **Security → Security Rules** del dashboard — el plan gratis permite reglas
  simples por IP aunque no las reglas de conteo por status code (eso es Business+).
  Para formularios que dependan de humanos (no dispositivos), [Turnstile](https://developers.cloudflare.com/turnstile/)
  es la opción sin fricción para el usuario.
- Seguí acotando longitud/formato de todo input antes de guardarlo (como ya se hace:
  `name.slice(0, 80)`, `html.length <= 100_000`, `screenId` entre 16 y 64
  caracteres) — es la primera defensa contra payloads abusivos y contra vaciar la
  cuota de D1/R2 con basura.
- El fallback a `ADMIN_TOKEN` cuando Access no está configurado es válido para el
  día 1, pero en producción real conviene terminar de configurar Cloudflare Access
  (Parte 4 del README): sin eso, quien consiga ese único bearer token tiene control
  total del panel, sin registro de quién lo usó.
- Si se sirve HTML embebido de terceros (la pestaña "Incrustar código" ya asume
  HTML/iframes arbitrarios), cualquier CSP que se agregue al panel más adelante
  tiene que dejar espacio para eso — una CSP estricta global puede romper esa
  función; si hace falta endurecer, aislá esa vista con `sandbox` en el iframe en
  vez de una política global restrictiva.

## 6 · Medir antes de optimizar

No agregues cachés/batching especulativos sin ver primero qué límite se está por
pisar — con pocas pantallas este proyecto probablemente ni se acerca al plan
gratis.

- `cd server && npm run tail` (ya documentado en el README) para ver logs en vivo.
- Dashboard → **Workers & Pages** → tu Worker → **Metrics** (requests, CPU, errores).
- Dashboard → **D1** → tu base → **Metrics** (rows read/written).
- Dashboard → **Durable Objects** → **Metrics** (requests, duración, storage).
- Para automatizar el chequeo, la GraphQL Analytics API expone las mismas métricas.

## Referencias

- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/workers/platform/pricing/
- https://developers.cloudflare.com/workers/best-practices/workers-best-practices/
- https://developers.cloudflare.com/workers/cache/
- https://developers.cloudflare.com/d1/platform/pricing/
- https://developers.cloudflare.com/d1/best-practices/use-indexes/
- https://developers.cloudflare.com/r2/pricing/
- https://developers.cloudflare.com/durable-objects/platform/pricing/
- https://developers.cloudflare.com/durable-objects/best-practices/websockets/
- https://developers.cloudflare.com/durable-objects/best-practices/rules-of-durable-objects/
- https://developers.cloudflare.com/waf/rate-limiting-rules/best-practices/
- https://developers.cloudflare.com/turnstile/
- https://developers.cloudflare.com/workers/configuration/secrets/
