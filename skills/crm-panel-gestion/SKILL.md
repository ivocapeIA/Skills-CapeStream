---
name: crm-panel-gestion
description: Construye de punta a punta un CRM o panel de gestión multi-tenant (Next.js 15 + Supabase + Tailwind + Vercel) con landing pública, páginas legales, integraciones (WhatsApp, correo IMAP, Instagram, calendarios, IA) y endurecimiento de seguridad. Arranca SIEMPRE en modo plan pidiendo nombre del negocio, operatoria actual, estilo visual e integraciones deseadas; después ejecuta en modo auto sin volver a preguntar. Usar cuando pidan crear un CRM, panel administrativo, sistema de gestión interno, backoffice o dashboard de operación desde cero (o migrar uno de planillas/WhatsApp a una app).
---

# CRM / Panel de gestión — de la intake al deploy

Esta skill es el destilado de un sistema real en producción (gestión de alquileres
temporarios: multi-tenant, WhatsApp bidireccional con chatbot, lectura de correo,
calendarios, finanzas, vitrina pública). Incluye **lo que funcionó, lo que se rompió y por
qué**. Seguirla evita repetir ~50 errores que ya costaron incidentes en producción.

Funciona igual en **Claude Code** y en **Cursor** (ver `README.md` de esta carpeta para
la instalación en cada uno). No depende de ninguna herramienta propietaria: las fases se
pueden ejecutar leyendo y escribiendo archivos.

---

## 0. Reglas no negociables

1. **Fase 0 SIEMPRE en modo plan.** Nada de código, migraciones ni `npm install` antes de
   que el plan esté aprobado. En el plan se dan **sugerencias con recomendación explícita**
   en cada punto abierto, no un menú neutro.
2. **Pedir el nombre del negocio.** Es obligatorio: nombra el proyecto, la marca de la
   landing, el `manifest`, los metadatos, los mails legales. Sin nombre no se arranca.
3. **Después del plan aprobado: modo auto, cero preguntas.** Toda duda se resuelve con el
   default documentado en las referencias y se anota en `docs/DECISIONES.md`. Solo se
   interrumpe si falta un **secreto** que solo el usuario puede dar (API key, credencial)
   o si una acción es destructiva sobre datos reales.
4. **Landing pública obligatoria** (más `/privacy` y `/terms`; más `/eliminar-datos` si hay
   mensajería). No es opcional ni "para después": las plataformas (Meta, Google) la exigen
   y define la identidad pública del negocio.
5. **RLS desde la migración 1.** Multi-tenant por `id_org` aunque hoy haya una sola
   organización. Retrofitear aislamiento es una reescritura.
6. **Colores solo por tokens semánticos.** Nunca `slate-*`, `bg-white`, `red-500` sueltos:
   la app tiene modo oscuro desde el día 1.
7. **Cero datos del negocio hardcodeados — todo lo ajustable es editable desde la app.**
   Nombre del titular, teléfonos, horarios, políticas, textos de una landing, la frase con
   la que un bot se presenta, el contexto general de un bot: nada de eso vive en un prompt,
   un componente ni un helper. Va a una tabla de configuración por organización (editable
   desde una pantalla) o a `lib/empresa.ts` como fuente única. En una app multi-tenant, un
   dato de un negocio metido en el código se lo come la segunda organización que se dé de
   alta (caso real: el nombre del titular hardcodeado en el prompt del chatbot). Regla
   práctica: dar de alta una organización nueva no debería tocar una línea de código.
8. **Comentarios línea por línea en español** en todo el código, y `HISTORIAL.md` con una
   entrada por cambio (la más reciente arriba). El changelog es lo que hace que la próxima
   sesión —humana o de IA— no repita un error ya resuelto.
9. **La app tiene que sentirse instantánea desde la Fase 1.** Las funciones de Vercel y la
   base de Supabase, en la **misma región** (causa nº 1 de "va lento" con este stack);
   `React.cache()` en el chequeo de sesión y el perfil; policies RLS con la función envuelta
   en `(select ...)` e índice en `id_org`; `loading.tsx` y `staleTimes`. Todo en
   `references/09-rendimiento.md` — no es una optimización posterior, es configuración de
   arranque.
10. **Nada se da por terminado sin**: `npx tsc --noEmit` limpio, `npm run build` OK, entrada
    en `HISTORIAL.md` y smoke test de las rutas tocadas.

### Equivalencias por entorno

| Acción | Claude Code | Cursor | Otro agente |
|---|---|---|---|
| Modo plan | `EnterPlanMode` / `ExitPlanMode` | Modo *Plan* del chat | Escribir `docs/PLAN.md` y esperar "aprobado" |
| Preguntas de intake | `AskUserQuestion` (1 sola ronda) | Preguntar en el chat (1 sola ronda) | Idem |
| Ejecución | Auto / `--permission-mode acceptEdits` | Modo *Agent* | Idem |

En todos los casos el plan se **escribe además a `docs/PLAN.md`**: sobrevive al cambio de
sesión, de herramienta y de modelo.

---

## Fase 0 — Intake y plan (única fase interactiva)

Leer `references/00-intake-y-plan.md` para el cuestionario completo, los defaults y las
plantillas de sugerencia.

Se necesitan **seis** datos. Si el usuario ya los dio en su mensaje, no se vuelven a
preguntar. Lo que falte se pide en **una sola ronda** de preguntas (máximo 4 por bloque,
con opciones y una marcada "(recomendada)"):

1. **Nombre del negocio** (obligatorio) + rubro en una línea.
2. **Qué es el negocio y cómo opera hoy**: quién hace qué, con qué herramientas
   (WhatsApp, Excel, cuaderno, otro software), cuáles son los 3 dolores principales.
3. **Estilo del frontend buscado**: se ofrecen presets (`editorial cálido`,
   `técnico neutro`, `corporativo sobrio`, `vibrante moderno`) — ver
   `references/04-diseno-frontend.md`.
4. **Aplicaciones a conectar**: WhatsApp (Meta Cloud API / Twilio), correo (IMAP/Gmail),
   Instagram, calendarios (iCal/Google), pasarelas de pago, planillas, IA.
5. **Escala y roles**: cuántas personas lo usan, qué niveles (global / admin / operativo),
   si hay clientes finales que interactúan (por chat, por link público).
6. **Tecnología del frontend**: ofrecer las opciones **con el beneficio de cada una en una
   línea** (`Next.js + React` recomendado, `React solo`, `Angular`, `Vue/SvelteKit`,
   `no sé / elegí vos`) — tabla comparativa y recomendación en `references/01-stack-y-arquitectura.md`
   §0. Si el usuario no sabe qué es cada una, es tarea del asistente explicárselo ahí mismo y
   recomendar. El default es `Next.js + React`: es el único stack en el que esta skill sirve
   como manual literal (fases y ~50 errores conocidos calibrados para él). Cualquier otra
   elección se anota en `docs/DECISIONES.md` y la skill pasa a ser orientativa.

Con eso se produce el plan, que **siempre** incluye:

- **Modelo de dominio**: entidades, relaciones y las 3–5 invariantes de negocio duras
  (ej. "no puede haber dos reservas solapadas del mismo depto").
- **Mapa de módulos** elegidos del catálogo (ver `references/01-stack-y-arquitectura.md`),
  con el color y el sello de 3 letras de cada uno.
- **Qué se automatiza y qué NO** (con el motivo). Regla de oro: lo que toca plata o una
  cuenta de terceros arranca **manual con botón**, no automático.
- **Integraciones por fase** y qué secreto/credencial hace falta para cada una, con el
  camino de alta (verificación de empresa, número, app secret…).
- **Cronograma por fases 1→8** y criterios de aceptación de cada una.
- **Riesgos conocidos** que aplican a este negocio, sacados de `references/07-errores-conocidos.md`.

Salida de la fase: `docs/PLAN.md` + aprobación. A partir de acá, **no se pregunta más**.

---

## Fase 1 — Esqueleto y sistema de diseño

Referencias: `01-stack-y-arquitectura.md`, `04-diseno-frontend.md`, `09-rendimiento.md`.

- `create-next-app` (App Router, TS, Tailwind) + `lucide-react`, `recharts`,
  `@supabase/supabase-js`, `@supabase/ssr`.
- **Región co-locada (hacerlo ahora, no después):** proyecto de Supabase en la región de los
  usuarios (LatAm: `us-east-1`) y `vercel.json` con `{ "regions": ["iad1"] }` a esa misma
  región. Es la causa nº 1 de "se mueve todo lento" con este stack (`09-rendimiento.md` §1).
- `globals.css` con **la paleta completa en variables CSS** (`:root` y `.dark`) y
  `tailwind.config.ts` mapeándolas con `rgb(var(--color-x) / <alpha-value>)`.
- Tipografías con `next/font` (display condensada / cuerpo / mono para códigos y montos).
- Script anti-parpadeo del tema en el `<head>` + `suppressHydrationWarning` en `<html>`.
- App shell: `100dvh`, `safe-area-inset-*`, `<main>` como único contenedor de scroll.
- **Andamiaje de rendimiento base:** `app/dashboard/loading.tsx` (esqueleto),
  `experimental.staleTimes.dynamic ≥ 30` en `next.config`, y el `createClient` de servidor
  envuelto en `React.cache()` desde el primer día (`09-rendimiento.md` §2 y §5).
- `CLAUDE.md` + `AGENTS.md` del proyecto nuevo (mismas convenciones) y `HISTORIAL.md` vacío.

**Aceptación:** build OK; se ve una pantalla vacía en claro y oscuro sin parpadeo; cero
clases de color crudas en el repo; en los logs de una función, una consulta trivial a la base
tarda **decenas** de ms, no cientos.

## Fase 2 — Base de datos, RLS y migraciones

Referencia: `02-datos-rls-migraciones.md`.

- Migraciones numeradas `NNNN_nombre.sql` en `supabase/migrations/`, **inmutables una vez
  aplicadas** (todo cambio es una migración nueva).
- Esquema base + tabla `organizacion` + `usuario` (vinculado a Auth **por email**) +
  `modulo` (on/off por organización).
- Migración de RLS: `current_user_org()`, `current_user_es_admin()`,
  `current_user_es_global()` (SECURITY DEFINER, `SET search_path = public`) y políticas en
  **todas** las tablas. En las policies, la función va **envuelta en `(select ...)`** y hay
  **índice en `id_org`** y en cada FK: sin eso, la RLS escanea la tabla entera y las
  pantallas con historial se arrastran (`09-rendimiento.md` §3).
- Restricciones e invariantes en la base: `CHECK`, `EXCLUDE` con `btree_gist` para solapes,
  índices únicos parciales, FKs. **Las reglas que tienen más de un camino de escritura
  (UI + cron + import + webhook) van en triggers, no en el código de la app.**
- `REVOKE EXECUTE ... FROM anon, authenticated` en cada función auxiliar; `GRANT` explícito
  solo a quien la usa.

**Aceptación:** los advisors de seguridad de Supabase sin hallazgos; una consulta con la
anon key desde otra organización devuelve 0 filas.

## Fase 3 — Auth, shell y navegación

- Login/registro con Server Actions; el alta valida el email contra la tabla `usuario` con
  el **cliente admin** (server-side), nunca dejando que el navegador pregunte "¿este mail
  existe?".
- Middleware: refresco de sesión + rutas públicas. Ojo con `startsWith` y con la raíz
  (comparación exacta) — ver `03-seguridad.md`.
- Tres clientes de Supabase: `client` (browser), `server` (con sesión, RLS), `admin`
  (service_role, solo servidor y solo donde no hay sesión).
- Shell: sidebar en escritorio + drawer en celular, paleta de comandos (Ctrl/K), toasts,
  barra de progreso de navegación, indicador de conexión, tour guiado.
- Catálogo de navegación en **un solo archivo** (`lib/navegacion.ts`) que consumen panel,
  sidebar y paleta: duplicarlo garantiza que se desincronicen.
- Soft-nav rápido (ver `07-errores-conocidos.md` **F8**): `React.cache()` en
  `createClient`/`getPerfil`, `loading.tsx` del dashboard, `experimental.staleTimes.dynamic`
  ≥ 30 s (las mutaciones refrescan con `router.refresh()`).

**Aceptación:** un usuario operativo no puede entrar a ningún módulo de gestión (guarda en
la página **y** en la API).

## Fase 4 — Módulos del negocio (CRUD)

Referencia: `01-stack-y-arquitectura.md` (patrón de módulo).

Por cada módulo del plan, en este orden: capa de datos (`lib/<modulo>.ts`, con validación y
normalización) → API routes (`guardAdmin(modulo)`) → página server component → cliente
(`<Modulo>Client.tsx`) con tabla en escritorio y **tarjetas en celular**.

**Aceptación por módulo:** alta, edición, baja lógica, filtros, estado vacío con texto útil,
sin scroll horizontal a 375 px, y errores que se ven (toast), nunca fallos silenciosos.

## Fase 5 — Estadísticas y analítica

- El servidor devuelve **filas crudas** del rango; el navegador agrega y cruza-filtra.
- Cálculo en un módulo **puro** (`lib/stats-core.ts`, sin imports de servidor) para que
  corra en el navegador y se pueda testear suelto.
- Recharts pinta el SVG con props: la paleta del tema se resuelve en JS con un hook
  (`useTemaActual`), no con clases.

## Fase 6 — Integraciones

Referencia: `05-integraciones.md` (WhatsApp/Meta, Twilio, IMAP, Instagram, iCal, IA, pagos).

Orden recomendado: primero la que resuelve el dolor #1 del intake. Cada integración se
entrega con: credenciales **por organización** cargadas desde una pantalla (no por env),
webhook firmado y fail-closed, log de entrantes/salientes, interruptor on/off por tipo de
mensaje (default apagado) y opt-out real. Todo texto que el negocio necesite ajustar —el
contexto de un chatbot incluido— es un campo editable en una tabla de config por
organización, nunca una constante en el código (ver `05-integraciones.md`, chatbot en capas).

## Fase 7 — Landing pública y legales

Referencia: `06-landing-y-legales.md`.

Landing con el nombre del negocio, propuesta de valor, prueba (capturas o réplicas
funcionales del producto), contacto y **pie con datos legales verificables**
(razón social, identificación fiscal, domicilio, teléfono y correo del mismo dominio) +
JSON-LD `LocalBusiness`. Más `/privacy`, `/terms` y, si hay mensajería, `/eliminar-datos`
y el callback de borrado de datos.

Si además hay una **vitrina / catálogo público** (páginas sin login), la superficie pública
se declara **en la misma base** como vistas que proyectan solo lo publicable y se leen con
la **clave anónima**, no con `service_role` ni con una segunda base (ver `03-seguridad.md`
§5: contra cualquier otra tabla la RLS devuelve 0 filas, así una consulta equivocada no
puede filtrar datos de clientes).

## Fase 8 — Endurecimiento, verificación y deploy

Referencias: `03-seguridad.md`, `08-entrega-y-verificacion.md`, `09-rendimiento.md`.

- Pasada completa de la checklist de seguridad.
- Pasada de la checklist de rendimiento (`09-rendimiento.md` §10): región co-locada medida en
  logs, `React.cache` en sesión/perfil, policies RLS envueltas + índices, `Promise.all` sin
  waterfalls, `loading.tsx` + `staleTimes`, *First Load JS* bajo control.
- Pasada de la checklist de errores conocidos (`07-errores-conocidos.md`) sobre el código
  escrito: zona horaria, atomicidad, idempotencia, contraste, celular, **cero datos del
  negocio hardcodeados**, ningún componente de cliente que importe `next/headers`.
- `npx tsc --noEmit`, `npm run build`, smoke test en navegador (375×812 y 1280×900, tema
  claro y oscuro).
- **Orden de deploy: migraciones primero, código después.** Al revés tira abajo módulos
  enteros en producción (ya pasó, 3,5 h caído).
- `HISTORIAL.md`, `CLAUDE.md` y `docs/DECISIONES.md` actualizados.

---

## Índice de referencias

| Archivo | Leer cuando |
|---|---|
| `references/00-intake-y-plan.md` | Fase 0: cuestionario, defaults, plantilla de `PLAN.md` |
| `references/01-stack-y-arquitectura.md` | Fases 1, 4, 5: stack, capas, patrón de módulo, catálogo de módulos |
| `references/02-datos-rls-migraciones.md` | Fase 2 y cualquier cambio de esquema |
| `references/03-seguridad.md` | Fases 3, 6, 8 y antes de exponer cualquier ruta pública |
| `references/04-diseno-frontend.md` | Fases 1, 4: tokens, presets de estilo, celular, accesibilidad |
| `references/05-integraciones.md` | Fase 6: WhatsApp, correo, Instagram, iCal, IA, pagos |
| `references/06-landing-y-legales.md` | Fase 7 |
| `references/07-errores-conocidos.md` | Fase 8 y **antes de escribir** parsers, crons, dinero o fechas |
| `references/08-entrega-y-verificacion.md` | Cierre de cada fase y deploy |
| `references/09-rendimiento.md` | **Fase 1** (dejarlo configurado), Fase 8 y ante cualquier "va lento" |

---

## Criterio transversal: qué NO automatizar

Vale más que cualquier feature. En el sistema de referencia, cada uno de estos costó un
incidente antes de convertirse en regla:

- **Plata**: cargar un movimiento a finanzas siempre es un botón manual si la fuente puede
  duplicarse (un CSV mensual, una resolución de la plataforma). Detectar sí, cargar no.
- **Cuentas de terceros**: nunca automatizar acciones dentro del sitio de otro (publicar una
  reseña, aceptar un reclamo). Se copia el texto y se abre el link real: el humano confirma.
- **Escribir un campo cuando el dato no se pudo leer con certeza**: se marca
  `revisar_manual` y aparece en una bandeja "Necesita atención". Cerrar como "aplicado" sin
  el dato es el agujero silencioso más caro: 10 reservas sin monto durante semanas.
- **Adivinar un match ambiguo**: si el candidato no es único, se reporta el conflicto. Nunca
  se toma el primero.
- **Reintentar contra un tercero que puede banear** (scraping, login): una pasada, a pedido,
  nunca en cron.
