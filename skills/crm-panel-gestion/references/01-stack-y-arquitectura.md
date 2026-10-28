# Stack y arquitectura

Stack probado en producción. Se puede cambiar, pero cada pieza está acá por un motivo que
conviene conocer antes de reemplazarla.

---

## 0. ¿Por qué este stack? (para quien no conoce los nombres)

Un panel de gestión interno tiene un perfil muy concreto: **mucho celular**, equipo chico,
multi-tenant, datos sensibles, y la necesidad de que "cambiar de pantalla" se sienta
instantáneo. Sobre ese perfil, las opciones reales:

| Opción | Qué es | Le conviene a | Contra para este caso |
|---|---|---|---|
| **Next.js + React** *(elegido)* | React es la librería de UI más usada: se arma la pantalla con "componentes" reutilizables. Next.js le agrega **render en el servidor** (la página llega ya armada → arranca rápida en el celular), ruteo, y lectura de datos en el servidor **sin una API intermedia** (el Server Component habla con Supabase y la RLS aísla). | Paneles, back-office, apps con SSR/SEO, equipos que quieren un solo framework para front y "back liviano". **Es el stack de esta skill: los ~50 errores conocidos y las 8 fases están calibrados para él.** | Curva propia (Server vs Client Components). Aceptable: es lo que evita construir una API a mano. |
| **React "solo"** (Vite + React Router / TanStack) | Solo la librería, sin servidor: todo corre en el navegador (SPA). Se le suma a mano lo que Next trae de fábrica. | Apps internas chicas, dashboards detrás de login donde el SEO no importa y el primer render lento se tolera. | Arranque más lento en móvil (el navegador baja todo y recién ahí pinta); hay que montar auth, ruteo y capa de datos por separado. Esta skill aplica ~60 %. |
| **Angular** | Framework completo y muy estructurado (todo viene decidido: inyección de dependencias, RxJS, módulos). | Organizaciones grandes, apps corporativas de larga vida con muchos devs que necesitan que "todo se haga igual". | Más ceremonia y más código para lo mismo; curva alta; comunidad de componentes más chica que React. Para un equipo chico es sobrepeso. Esta skill **no** aplica como guía paso a paso. |
| **Vue / SvelteKit** | Alternativas livianas y muy agradables de escribir; SvelteKit además tiene SSR como Next. | Quien ya las conoce y valora escribir menos. | Ecosistema y contrataciones más chicos; menos material cuando algo raro falla. Esta skill **no** aplica en detalle (fases y errores son de Next). |

**Recomendación:** Next.js + React, salvo que el equipo ya domine otra cosa. No por moda:
porque es el único camino en el que esta skill sirve como manual completo, con los errores de
producción ya documentados y las medidas de rendimiento (`09-rendimiento.md`) ya resueltas.
Si se elige otra tecnología, decirlo en `docs/DECISIONES.md` y asumir que la skill pasa a ser
orientativa, no literal.

**Las otras dos piezas** son casi ortogonales a esa elección:

- **Supabase** = Postgres (base de datos SQL de verdad) + Auth + **RLS** (el aislamiento
  entre organizaciones lo hace la base, no el código) + API automática. Alternativa directa:
  Postgres propio + una capa de auth. Se elige Supabase porque la RLS multi-tenant y el Auth
  ya vienen hechos y bien hechos.
- **Vercel** = el hosting que ejecuta Next.js sin configurar nada, con deploy por `git`,
  `cron` y `after()`. Alternativas: Netlify, un servidor propio, Cloudflare. Se elige Vercel
  porque es donde Next corre con menos fricción.

> "Se mueve todo lento" con **este mismo stack** casi nunca es culpa del stack: es
> configuración. La causa más común es que las funciones y la base quedaron en regiones
> distintas. Ver `09-rendimiento.md` — es lectura obligada de la Fase 1.

---

## 1. Stack

| Pieza | Elección | Por qué |
|---|---|---|
| Framework | **Next.js 15 (App Router) + React 19 + TypeScript** | Server Components para leer datos con RLS sin API intermedia; `after()` para trabajo en segundo plano en webhooks |
| Estilos | **Tailwind CSS 3** con tokens semánticos en variables CSS | Modo oscuro en un solo lugar; ver `04-diseno-frontend.md` |
| Backend/datos | **Supabase** (Postgres + Auth + RLS) | El aislamiento multi-tenant lo hace la base, no el código de la app |
| Hosting | **Vercel** | Deploy por git, crons, `after()`, variables por entorno |
| Gráficos | **recharts** | Pinta SVG con props (ojo: no lee variables CSS) |
| Íconos | **lucide-react** | Monocromáticos, sin emojis en pantallas de gestión |
| Correo | **imapflow** + **mailparser** | IMAP directo a la casilla del negocio |
| IA | **@anthropic-ai/sdk** y/o Gemini por REST | Capa propia con degradación, ver `05-integraciones.md` |

**Decisión de Fase 1 que define si la app "va fluida" (gratis ahora, cara después):**

- **La región de las funciones de Vercel tiene que ser la misma que la del proyecto de
  Supabase.** Cada consulta es una llamada de red función→base; si están en continentes
  distintos son +150 ms por consulta y la app se siente pesada con este mismo stack. Elegir
  la región de Supabase al crearlo (LatAm: `us-east-1`) y fijar `vercel.json` →
  `{ "regions": ["iad1"] }`. Es la causa nº 1 de "no va fluido como el otro proyecto".
  Detalle completo en **`09-rendimiento.md` §1** (lectura obligada de esta fase).

**Restricciones del plan gratuito que condicionan el diseño (conocerlas de entrada):**

- **Vercel Hobby: los crons corren una vez por día** y a hora aproximada. Todo lo que
  necesite más frecuencia se engancha al cron diario, se dispara desde el tráfico
  (`revalidate` + `after()`) o queda en un botón "actualizar ahora".
- **Supabase free: 2 proyectos activos** y un proyecto se pausa solo tras 7 días sin
  actividad. Por eso una vitrina/catálogo público conviene resolverlo con **vistas públicas
  en la misma base** leídas con la clave anónima (ver `03-seguridad.md` §5), no con una
  segunda base: no gasta el otro slot, no hay sync que mantener despierto y la página muestra
  el estado en vivo. (En el sistema de referencia la vitrina arrancó en una base aparte y se
  integró después, migración `0059`.)

---

## 2. Estructura de carpetas

```
src/
├── app/
│   ├── api/                  # Route handlers: mutaciones, webhooks, crons
│   │   ├── <modulo>/route.ts
│   │   ├── cron/<tarea>/route.ts
│   │   └── <canal>/[secret]/route.ts
│   ├── auth/                 # callback + signout
│   ├── dashboard/            # área privada, una carpeta por módulo
│   ├── login/                # Server Actions de acceso
│   ├── (públicas)/           # landing, privacy, terms, eliminar-datos
│   ├── layout.tsx · page.tsx · globals.css · manifest.ts
├── components/               # <Modulo>Client.tsx, shell, gráficos
├── lib/
│   ├── supabase/             # client · server · admin · (secundaria)
│   ├── <modulo>.ts           # capa de datos por módulo (con RLS)
│   ├── <modulo>-core.ts      # cálculo PURO reutilizable en el navegador
│   ├── apiGuard.ts · org.ts · format.ts · navegacion.ts
│   └── <integracion>/        # whatsapp/ · correo/ · ia/ · ical
middleware.ts
supabase/migrations/          # NNNN_nombre.sql, inmutables
docs/                         # PLAN.md · DECISIONES.md
HISTORIAL.md · CLAUDE.md · AGENTS.md
```

---

## 3. Los tres clientes de Supabase (regla de oro)

```ts
// lib/supabase/server.ts  → CON SESIÓN. RLS activa. Es el default para todo.
// lib/supabase/client.ts  → navegador. Solo lecturas públicas o realtime.
// lib/supabase/admin.ts   → service_role. SALTA RLS. Solo servidor, solo donde NO hay sesión.
```

**El cliente admin se usa exclusivamente en:** webhooks (no traen sesión), crons, y
escrituras a tablas que a propósito no tienen policy de `UPDATE`/`INSERT` para
`authenticated` (log de mensajes, mails ingeridos). En esos casos el endpoint **primero
valida con el cliente de sesión** que quien pide sea admin de la organización, y recién
después usa el admin para escribir. Ese doble paso es lo que deja la auditoría intacta.

Nunca exponer `SUPABASE_SERVICE_ROLE_KEY` al navegador ni ponerla en una variable
`NEXT_PUBLIC_*`.

---

## 4. Patrón de módulo (repetir igual para cada uno)

**1. Capa de datos** — `lib/<modulo>.ts`, con el cliente de sesión:

```ts
// Valida, normaliza y devuelve datos ya listos para la pantalla.
// Toda la validación de negocio vive acá: la API route solo autoriza y delega.
export async function crearCosa(supabase: SupabaseClient, entrada: EntradaCosa) {
  // Normalización primero (recortes de longitud, trims, canonicalización de teléfonos).
  // Después validación con mensajes en castellano, pensados para mostrarse tal cual.
  // Al final el insert, con el id_org resuelto por lib/org.ts#getOrgId.
}
```

**2. API route** — `app/api/<modulo>/route.ts`:

```ts
export async function POST(req: Request) {
  const g = await guardAdmin("mod_cosas");   // Autorización: admin + módulo activo.
  if (g.error) return g.error;               // La UI NO es una restricción real.
  // ... parseo del body y llamada a la capa de datos.
}
```

**3. Página** — Server Component: lee con el cliente de sesión y pasa datos planos al
cliente. **Nunca pasar funciones ni componentes** (los íconos de lucide son funciones:
React Server Components no los puede serializar). El cliente arma los íconos adentro, a
partir de una clave de texto.

**4. Cliente** — `<Modulo>Client.tsx`: estado local, `fetch` a la API, `router.refresh()`
para recargar los datos del server component. Tabla en escritorio (`hidden sm:block`) y
lista de tarjetas en celular (`sm:hidden`), compartiendo handlers y estado vacío.

---

## 5. Analítica: el servidor no agrega, el navegador sí

Patrón que hace que el cruce de filtros sea instantáneo:

1. `GET /api/stats?desde&hasta` devuelve **filas crudas** del rango (más el período de
   comparación). No calcula KPIs.
2. `lib/stats-core.ts` es **puro**: sin un solo import de servidor, así corre en el
   navegador y se puede probar aislado. Recibe filas + filtros y devuelve todas las
   agregaciones.
3. El componente hace **un fetch por cambio de rango**; cada clic de filtro recalcula en
   memoria con `useMemo` → cero latencia y cero lecturas extra a la base.

Contra: el payload crece con el rango. Por eso se trae solo el rango visible y se topea la
amplitud del rango personalizado (ej. 366 días).

Detalles que evitan bugs conocidos:
- Convertir moneda **por mes del movimiento**, no sobre el total (meses con tipo de cambio
  distinto se distorsionan).
- Los avisos ("sin tipo de cambio", "estimado") se cuentan sobre el conjunto **ya filtrado**,
  no sobre todo el rango.
- Un delta porcentual con base negativa no se muestra (pasar de pérdida a ganancia no es
  "▼ 300 %").

---

## 6. Reglas de negocio: ¿app o base de datos?

**Van a la base (trigger o función)** cuando hay más de un camino de escritura: UI, cron,
importador, webhook, script manual, cliente admin. Ejemplo real: la asignación de la persona
responsable la resuelve **una sola función SQL** que usan los tres triggers que asignan; en
el código de la app estaría duplicada en cinco lugares y se desincronizaría al primer
cambio.

**Van a la app** las validaciones de entrada, los mensajes al usuario y todo lo que necesite
llamar a un servicio externo.

Ambos lados: los `CHECK` y `EXCLUDE` de la base son la red de seguridad; la app los traduce
a mensajes legibles capturando el código de error (`23505` duplicado, `23P01` exclusión).

---

## 7. Idempotencia y concurrencia (patrones obligatorios)

- **Ingesta externa**: clave natural `UNIQUE` (`message_id` de un mail, `wamid` de un
  mensaje). Reprocesar una ventana tiene que ser inofensivo y barato.
- **Reclamo atómico** antes de un efecto de lado que no se puede repetir:

```sql
-- Reclama la fila: si no afecta ninguna, alguien ya lo hizo y se corta ahí.
UPDATE mensaje SET estado = 'aplicado' WHERE id = $1 AND estado = 'revisar_manual';
```

  Si el efecto posterior falla, se revierte el estado para no perder el candidato.
- **Colas de trabajo**: reclamo por `DELETE ... RETURNING` para que dos despachadores nunca
  tomen el mismo lote, más auto-reparación de lotes vencidos.
- **Webhooks**: responder 200 al instante y hacer el trabajo en `after()`; el proveedor
  reintenta si tardamos, y el reintento re-ejecutaría la acción.
- **Contadores**: incrementar con una función SQL, no con "leer y escribir" desde la app.

---

## 8. Fuente única de verdad

Cada vez que un formato, un catálogo o un cálculo se duplicó "porque era chiquito", se
desincronizó. Casos reales: el texto de un mensaje que se armaba en dos lados y quedó con
formatos distintos; el catálogo de navegación repetido entre el panel y la paleta de
comandos; helpers de fecha duplicados entre el servidor y un componente.

Regla: si dos lugares tienen que decir lo mismo, se extrae a un módulo puro y lo importan
los dos. Vale también para los datos legales del negocio (`lib/empresa.ts`) que aparecen en
la landing, en `/privacy` y en el JSON-LD.

**Fuente única no es lo mismo que hardcodear.** `lib/empresa.ts` centraliza datos que casi
nunca cambian y son de UN solo negocio (una plataforma multi-tenant que quiera cambiarlos
por organización los sube a una tabla de config). Pero un texto que el operador va a querer
ajustar —el contexto de un chatbot, un horario, una política— no es "fuente única": es
**configuración**, y va a una tabla por organización editable desde una pantalla, no a un
módulo del código. En el sistema de referencia esto se aprendió con el prompt del chatbot,
que mezclaba reglas del sistema con el nombre del titular en duro (migración `0060`): ver
`05-integraciones.md` (chatbot en capas) y `07-errores-conocidos.md` **H6**.
