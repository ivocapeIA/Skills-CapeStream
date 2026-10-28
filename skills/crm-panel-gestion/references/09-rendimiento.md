# Rendimiento — que se sienta tan fluido como el sistema de referencia

Mismo stack (Next.js + Supabase + Vercel) puede sentirse **instantáneo** o **pesado** según
un puñado de decisiones. Casi todas son gratis si se toman en la Fase 1 y caras de
retrofitear. Leer en la **Fase 1** (para dejarlas configuradas) y en la **Fase 8** (como
checklist), y **antes** de dar por bueno un "anda lento".

Regla base: **medir, no adivinar** (§9). Pero el 90 % de los "va lento" en este stack es una
de estas cinco causas, en este orden de frecuencia:

1. Las funciones de Vercel y la base de Supabase están en **continentes distintos**.
2. Cada request paga el **round-trip de Auth** dos o tres veces.
3. Las **políticas RLS** escanean toda la tabla porque la función va sin envolver.
4. El server component hace las consultas **una atrás de otra** (waterfall) en vez de en
   paralelo, y trae **columnas y filas de más**.
5. Falta el andamiaje de Next 15: `loading.tsx`, `staleTimes`, deduplicación con `cache()`.

---

## 1. Co-locar funciones y base (la causa nº 1 de "no va fluido como el otro")

Con este stack, **cada** lectura o escritura de datos es una llamada HTTPS de la función de
Vercel al endpoint de Supabase (PostgREST). Si la función corre en EE.UU. este y la base en
Europa, esa llamada se va **150–250 ms** de ida y vuelta — y una pantalla que hace 4
consultas arranca con **1 segundo** perdido antes de pintar nada. Manager se siente rápido en
buena parte porque las dos cosas están en `us-east-1`.

- [ ] **Elegir la región de Supabase al crear el proyecto** cerca de los usuarios (para
      Argentina/LatAm: `us-east-1`). No se puede cambiar después sin migrar.
- [ ] **Fijar la región de las funciones de Vercel a la misma.** En `vercel.json`:

```json
{ "regions": ["iad1"] }
```

  `iad1` (Washington DC) ≈ `us-east-1` de Supabase. En Hobby solo se permite **una** región
  y por defecto Vercel usa la del deploy, que puede no ser la de la base.
- [ ] Verificar después del deploy: en los logs de una función, el tiempo de una consulta
      trivial (`select 1`) tiene que ser de **una** o dos decenas de ms, no cientos.
- [ ] Las **Server Actions y los Route Handlers** heredan esa región; los **Server
      Components** también. No hay que tocar nada más una vez puesto `regions`.

> Si además se usa un cliente que abre conexión directa a Postgres (Prisma, Drizzle, `postgres`)
> —Manager **no** lo hace, va todo por PostgREST/`supabase-js`— entonces hay que usar el
> **pooler** de Supabase (Supavisor, puerto `6543`, modo transacción) y no el `5432` directo:
> en serverless, abrir una conexión nueva por invocación agota la base.

---

## 2. Auth: no pagar el mismo round-trip tres veces

`supabase.auth.getUser()` **llama al servidor de Auth por la red** en cada invocación para
validar el token. En un request de Next, el `layout` y la `page` (y a veces un helper de
datos) lo llaman por separado: son 2–3 viajes a Auth **antes** de la primera consulta de
datos.

- [ ] **Deduplicar con `React.cache()`**: envolver el `createClient` de servidor y el
      `getPerfil()` (el que resuelve `id_org` y `nivel`) para que un request haga **un solo**
      chequeo de sesión y **una sola** lectura de perfil, aunque se los llame en cinco
      lugares.

```ts
// lib/supabase/server.ts
import { cache } from "react";
export const createClient = cache(async () => { /* ... crea el cliente con cookies ... */ });

// lib/perfil.ts
export const getPerfil = cache(async () => {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();   // Un viaje a Auth por request.
  if (!user) return null;
  const { data } = await supabase.from("usuario")
    .select("id_usuario, id_org, nivel")
    .eq("mail", user.email).is("fecha_baja", null).single();   // Una lectura por request.
  return data;
});
```

- [ ] **En el middleware, `getUser()` va una sola vez** y su única misión es refrescar la
      cookie (ver `03-seguridad.md` §2: la respuesta tiene que llevar las cookies frescas).
      No repetir la validación en cada layout: para eso está el `cache()`.
- [ ] Si la versión de `supabase-js` en uso ya expone verificación **local** del JWT
      (con las JWKS del proyecto, sin ir a la red — p. ej. `getClaims()`), preferirla para
      leer `sub`/`email` en el server, y dejar `getUser()` solo donde haga falta la garantía
      fuerte. Confirmar el nombre del método en la versión instalada antes de usarlo.
- [ ] **No** poner `export const dynamic = "force-dynamic"` "por las dudas" en el layout raíz:
      obliga a re-renderizar todo el árbol en cada navegación.

---

## 3. RLS que no escanea la tabla entera

Una policy `USING (id_org = current_user_org())` puede ejecutar `current_user_org()` **una
vez por fila** si el planificador no la trata como constante. En una tabla de 50 filas no se
nota; en una de 50 000 (un log de mensajes, transacciones históricas) la pantalla tarda
segundos.

- [ ] **Envolver la función en un subselect escalar** para que Postgres la evalúe **una vez
      por consulta**:

```sql
CREATE POLICY cosa_all ON cosa
  FOR ALL
  USING      ( (select public.current_user_org()) = id_org
               OR (select public.current_user_es_global()) )
  WITH CHECK ( (select public.current_user_org()) = id_org
               OR (select public.current_user_es_global()) );
```

- [ ] Las funciones auxiliares, **`STABLE` y `SECURITY DEFINER`** (ya está en
      `02-datos-rls-migraciones.md` §3): además de correcto, permite el cacheo.
- [ ] **Índice en toda columna que aparece en una policy o en un filtro frecuente**: siempre
      `id_org`, y las FKs (`id_apartamento`, `id_reserva`…). Sin índice, cada lectura con RLS
      es un *seq scan*.

```sql
CREATE INDEX idx_transaccion_org  ON transaccion (id_org);
CREATE INDEX idx_reserva_apart    ON reserva (id_apartamento) WHERE fecha_baja IS NULL;
```

- [ ] Medir una consulta lenta con `EXPLAIN (ANALYZE, BUFFERS)` desde el SQL editor de
      Supabase: si aparece `Seq Scan` sobre una tabla grande con un filtro que debería usar
      índice, falta el índice o la policy no está envuelta.

---

## 4. Consultas: en paralelo, y solo lo que se usa

- [ ] **Consultas independientes van con `Promise.all`**, no una atrás de otra. Tres `await`
      secuenciales de 60 ms son 180 ms; en paralelo son 60.

```ts
const [reservas, apartamentos, limpiezas] = await Promise.all([
  listarReservas(supabase, rango),
  listarApartamentos(supabase),
  listarLimpiezasPendientes(supabase),
]);
```

- [ ] **`select` con las columnas que se usan**, nunca `select("*")` en una tabla ancha o con
      un `text` grande (`info_huespedes`, cuerpos de mail, notas). Traer una columna de 8 KB
      por 500 filas es 4 MB por pantalla.
- [ ] **Traer las relaciones embebidas en una sola consulta** (`select("*, apartamento(nombre)")`),
      no una consulta por fila (N+1).
- [ ] **Paginar de verdad** lo que puede crecer (`.range()` + tope). Un listado sin límite
      que hoy trae 80 filas, en un año trae 8 000 y la pantalla se arrastra.
- [ ] Para analítica, el patrón de `01-stack-y-arquitectura.md` §5: el servidor manda filas
      crudas del **rango visible** y el navegador agrega; no traer todo el histórico.
- [ ] Contadores y agregados que se muestran siempre (KPIs del panel): resolverlos con **una
      función SQL** que devuelve la fila ya sumada, no trayendo todo para contar en JS.

---

## 5. Next 15: el andamiaje que hace que "cambiar de pantalla" sea instantáneo

(Esto es la falla **F8** de `07-errores-conocidos.md`, acá como configuración de Fase 1.)

- [ ] **`app/dashboard/loading.tsx`** con un esqueleto: da feedback inmediato mientras corren
      Auth + consultas. Sin esto, el clic "no hace nada" por 300–800 ms.
- [ ] **`staleTimes` para que el soft-nav no revalide todo cada vez:**

```ts
// next.config.mjs
const nextConfig = {
  experimental: { staleTimes: { dynamic: 30, static: 180 } },
};
```

  Las mutaciones ya fuerzan datos frescos con `router.refresh()`; sin `staleTimes`, **cada**
  navegación entre pantallas vuelve a pedir el RSC completo.
- [ ] **Barra de progreso de navegación** (ver `04-diseno-frontend.md` §6): aunque la carga
      sea corta, el ojo necesita la señal.
- [ ] **No revalidar de más**: `revalidatePath`/`revalidateTag` apuntando a la ruta puntual
      que cambió, no a `/dashboard` entero.
- [ ] Páginas y componentes que **no** dependen de la sesión (landing, vitrina): `export const
      revalidate = <segundos>` y que las sirva el CDN, no una función.

---

## 6. El bundle del navegador

- [ ] **Menos `"use client"`.** Un componente es de servidor salvo que necesite estado,
      efectos o eventos. Marcar de cliente un layout entero arrastra todo su árbol al bundle.
- [ ] **Librerías pesadas, solo donde se usan y con carga diferida:**

```ts
const GraficoBarras = dynamic(() => import("./GraficoBarras"), { ssr: false });
```

  `recharts`, editores de texto, mapas, lectores de PDF: nunca en el bundle de la primera
  pantalla.
- [ ] **Fechas sin `moment`.** `date-fns` con imports puntuales, o `Intl` nativo. `moment`
      pesa ~70 KB y no hace *tree-shaking*.
- [ ] **Íconos uno por uno** (`import { Check } from "lucide-react"`), nunca `import * as`.
- [ ] Revisar el output de `npm run build`: si la ruta más liviana del dashboard pasa de
      ~200 KB de *First Load JS*, hay una librería de cliente que no debería estar ahí.
- [ ] Fuentes con `next/font` (ya en Fase 1): evita el *layout shift* y el pedido extra a
      Google Fonts en runtime.

---

## 7. Imágenes y estáticos

- [ ] `next/image` siempre, con `width`/`height` o `fill` + `sizes`. Una foto de apartamento
      de 3 MB servida cruda tira abajo la métrica de la vitrina en celular.
- [ ] `priority` solo en la imagen "sobre el pliegue"; el resto, carga diferida (es el
      default de `next/image`).

---

## 8. Realtime y suscripciones (si se usan)

- [ ] Una suscripción de Supabase Realtime por pantalla que la necesita, **desuscribiéndose
      en el cleanup** del efecto. Suscripciones que se acumulan al navegar son *memory leak*
      y CPU en el cliente.
- [ ] No suscribir el panel entero a una tabla que cambia seguido "para que se vea vivo":
      `router.refresh()` tras las mutaciones propias alcanza en el 95 % de los casos.

---

## 9. Cómo medir (para no perseguir fantasmas)

| Síntoma | Dónde se mide | Qué buscar |
|---|---|---|
| "Cambiar de pantalla tarda" | DevTools → Network, filtro `Fetch/XHR`, mirar el doc `?_rsc=` | Cuánto tarda el RSC; si son cientos de ms, es servidor (§1–§4) |
| "La primera carga tarda" | Lighthouse / PageSpeed sobre la URL de producción | LCP, TBT, *First Load JS* (§6) |
| "Una consulta puntual vuela mal" | SQL editor de Supabase → `EXPLAIN (ANALYZE, BUFFERS)` | `Seq Scan` en tabla grande, función RLS por fila (§3) |
| "Algunas requests lentas y otras no" | Vercel → Observability / Logs de la función | Región de ejecución ≠ región de la base (§1); *cold starts* |
| "El navegador se traba con el uso" | DevTools → Performance, grabar una sesión | Re-renders, suscripciones sin cleanup (§8) |

Ruido que **no** es problema de la app (no tocar código por esto): ver `07-errores-conocidos.md`
**F7** (errores de consola de extensiones del navegador).

---

## 10. Checklist de rendimiento (Fase 1 y Fase 8)

- [ ] Región de Supabase elegida cerca de los usuarios; `vercel.json` con `regions` a la
      misma; verificado en logs que una consulta trivial son decenas de ms, no cientos.
- [ ] `createClient` de servidor y `getPerfil` envueltos en `React.cache()`; `getUser()` una
      sola vez en el middleware.
- [ ] Todas las policies RLS con la función **envuelta en `(select ...)`**; índice en
      `id_org` y en cada FK usada en filtros.
- [ ] Server components: consultas independientes con `Promise.all`; `select` de columnas
      puntuales; sin N+1; listados paginados con tope.
- [ ] `app/dashboard/loading.tsx` + `staleTimes.dynamic` ≥ 30 en `next.config`.
- [ ] `npm run build`: *First Load JS* de la ruta más liviana del dashboard < ~200 KB; sin
      `recharts`/editores en el bundle inicial (van con `dynamic`).
- [ ] `next/image` en toda foto; `next/font` para tipografías.
- [ ] Suscripciones de Realtime con cleanup (si hay).
- [ ] Medido en producción (Network del RSC + Lighthouse), no "a ojo".
