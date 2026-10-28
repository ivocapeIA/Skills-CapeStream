# Errores conocidos y cómo evitarlos

Catálogo de fallas **reales** de un sistema en producción. Formato: síntoma → causa → regla.
Leer **antes** de escribir parsers, crons, código que toca dinero o fechas, y en la Fase 8
como checklist.

---

## A. Fechas y zonas horarias

**A1. Un chequeo de día de la semana quedó invertido en producción (19 filas mal).**
Causa: se aplicó `AT TIME ZONE 'America/...'` a columnas **`DATE`**, que no tienen hora ni
zona; la conversión resta horas y corre la fecha al día anterior. Un domingo real se leía
sábado y un lunes se leía domingo.
→ **Regla:** `AT TIME ZONE` solo sobre `now()` y columnas `TIMESTAMPTZ`. Nunca sobre `DATE`.

**A2. La verificación del arreglo confirmó un resultado falso.**
Causa: la consulta de control tenía el mismo bug de A1.
→ **Regla:** verificar contra el **dato de origen** y con una consulta escrita distinto de la
que produjo el problema. Un backfill se valida contra la fuente, no contra lo que se acaba
de escribir.

**A3. Fechas que se corren un día al mostrarlas o al hacer aritmética en JS.**
Causa: `new Date("2026-08-24")` se interpreta en UTC y en husos negativos cae el día
anterior.
→ **Regla:** anclar a **mediodía local** (`new Date(y, m, d, 12)`) para toda aritmética de
fecha calendario, y un solo helper (`fechaISOaLocal`) usado en toda la app.

**A4. Un `TIMESTAMPTZ` de "fecha de gasto" cambiaba de día.**
→ **Regla:** si el dato es una fecha calendario, o es `DATE`, o se ancla a mediodía UTC al
guardar. Decidirlo una vez y documentarlo.

---

## B. Migraciones y despliegue

**B1. Módulos enteros caídos 3,5 h en producción.**
Causa: el deploy salió **antes** de aplicar la migración; el código nuevo consultaba columnas
inexistentes y cada consulta tiraba "column does not exist".
→ **Regla:** migración primero, deploy después. Y si el orden no se puede garantizar, el
código tiene que tolerar la ausencia de la columna.

**B2. Un bug "arreglado" seguía vivo.**
Causa: `CREATE OR REPLACE FUNCTION` con **distinta cantidad de parámetros** crea un
*overload* nuevo y deja la función vieja intacta; los llamadores viejos seguían pegándole a
esa.
→ **Regla:** cambiar la firma exige `DROP FUNCTION nombre(tipos_viejos);` explícito.

**B3. Una función de mantenimiento nunca corrió y nadie se enteró.**
Causa: faltaba un `GRANT EXECUTE ... TO service_role` y el error se tragaba (ver D1).
→ **Regla:** `GRANT` explícito a quien la llama, aunque la base actual funcione sin él:
recrear todo solo desde las migraciones tiene que andar.

**B4. Un `EXCLUDE` no se pudo aplicar.**
Causa: ya había filas que lo violaban.
→ **Regla:** verificar los datos existentes **antes** de agregar una restricción, e incluir
la limpieza o el backfill en la misma migración.

---

## C. Dinero y concurrencia

**C1. Un botón de pago cobró de más.**
Causa: la pantalla mostraba el total **ya filtrado por sucursal**, pero el endpoint solo
recibía la persona: la función SQL cerró y pagó **todas** las tareas pendientes de esa
persona en toda la organización.
→ **Regla:** el endpoint recibe **todos** los filtros que la pantalla muestra. Si la UI dice
"según X", X viaja al servidor.

**C2. Un gasto se creó dos veces.**
Causa: "leer estado → si corresponde, crear → marcar aplicado". Dos pestañas pasaron la
lectura antes de que cualquiera actualizara.
→ **Regla:** **reclamo atómico primero**
(`UPDATE ... SET estado='aplicado' WHERE estado='pendiente'`); si no afecta filas, alguien ya
lo hizo y se corta. Si el efecto posterior falla, revertir el estado.

**C3. Reimportar un CSV duplicaba movimientos.**
Causa: las filas **sin código** no entraban en la deduplicación.
→ **Regla:** la clave de dedup incluye todo lo que identifica la fila (código, tipo, monto
redondeado, moneda, ambas fechas) y se aplica también contra el propio archivo.

**C4. Doble conteo silencioso en los reportes.**
Causa: la misma plata entraba por dos caminos (detección automática + importación mensual).
→ **Regla:** una sola fuente de verdad por concepto. Si hay dos, una **detecta** y la otra
**carga**, y el pasaje de una a otra es un botón manual.

**C5. Un ingreso aparecía inflado.**
Causa: se sumaba el bruto y se restaba la comisión aparte, duplicando visualmente el
descuento.
→ **Regla:** definir por escrito el criterio contable (devengado vs. percibido, bruto vs.
neto), aplicarlo en un solo lugar y **aclararlo en la propia pantalla** con un subtítulo del
KPI. La mitad de los "bugs de plata" son diferencias de criterio, no errores de cálculo.

---

## D. Errores silenciosos

**D1. `try { await supabase.rpc(...) } catch {}` no atrapa nada.**
Causa: supabase-js **resuelve** con `{ data: null, error }` ante un error de Postgres; nunca
rechaza la promesa.
→ **Regla:** chequear `error` explícitamente y devolverlo en la respuesta del cron/endpoint.

**D2. El bot respondía en modo degradado y no había forma de saber por qué.**
Causa: todos los `catch` de la capa de IA se tragaban el error.
→ **Regla:** loguear cada fallo con contexto (status + cuerpo de la respuesta). La
degradación es correcta; la degradación **muda** no.

**D3. Una clave de API quedó guardada vacía en el hosting.**
Causa: el comando de alta no tomó el valor; la variable existía pero sin contenido.
→ **Regla:** después de cargar un secreto, verificar con una llamada real. Las variables
sensibles no se pueden releer: "existe" no es "tiene valor".

**D4. Un extractor cerraba mails como "aplicados" sin haber guardado el monto.**
Causa: el campo faltante no cambiaba el estado final. 10 registros quedaron sin monto durante
semanas.
→ **Regla:** si falta un campo crítico, el estado es `revisar_manual` con un texto claro, y
aparece en una bandeja "Necesita atención". Nunca cerrar en verde sin el dato.

**D5. Un cron nunca había corrido.**
Causa: faltaba `CRON_SECRET`; devolvía 401 desde el primer día.
→ **Regla:** después del deploy, **verificar que el cron corrió** (log o respuesta), no que
está declarado.

---

## E. Parsers e ingesta

**E1. Un parser calibrado contra un ejemplo falló con el segundo real.**
Causa: el mismo mail reenviado desde otro cliente traía la tabla HTML convertida en líneas
separadoras sueltas ("|"), y "el valor está en la línea siguiente" dejó de ser cierto.
→ **Regla:** normalizar (descartar líneas sin ningún carácter alfanumérico) y soportar los
tres formatos: valor en la misma línea, en la siguiente, y con ruido en el medio.

**E2. Un tercer formato dejó el monto en `null` en 10 de 13 casos.**
Causa: la fuente cambió (mails directos en vez de reenviados) y el valor pasó a venir pegado
a la etiqueta en la misma línea.
→ **Regla:** guardar el **cuerpo crudo** de todo lo que se ingiere. Permite recalibrar y
reprocesar sin volver a la fuente. Y ver D4.

**E3. Mails invisibles para el sistema.**
Causa: la búsqueda IMAP filtraba por "no leído"; el dueño de la casilla los había abierto.
→ **Regla:** buscar por **fecha**, con solape de margen; la idempotencia la da el `UNIQUE` de
`message_id`. Y no marcar como leído lo que se procesa: es la bandeja real de alguien.

**E4. Datos que nunca llegaban a destino.**
Causa: el mail llegaba **antes** que el registro con el que matchea y quedaba en `sin_match`
para siempre.
→ **Regla:** barrido de reintentos sobre el cuerpo guardado, disparado al final de cada sync
**y** apenas entran registros nuevos. Condición: **"todavía no escribió nada"**, no el
estado — un extractor que *acumula* sumaría dos veces al reprocesarse. Topes de ventana,
intentos y volumen por corrida.

**E5. Un import pisó una reserva cargada a mano.**
Causa: el match por fechas solo exigía que no tuviera código.
→ **Regla:** para completar un registro existente, exigir que el campo esté **vacío** y que
no sea un placeholder; si hay un candidato que no cumple, **reportar conflicto** en vez de
tocarlo. Y si el prefijo matchea más de una entidad: "sin mapear", nunca el primero.

---

## F. Sesión, red y navegador

**F1. La sesión se perdía al cerrar y abrir la app (92 % de las sesiones morían en la
primera rotación).**
Causa: `getUser()` **rota el refresh token adentro**; el token nuevo solo existe en las
cookies de esa respuesta. El middleware devolvía un `NextResponse.redirect()` nuevo (vacío) y
tiraba la rotación: el dispositivo quedaba con un token revocado.
→ **Regla:** copiar las cookies de sesión a **cualquier** respuesta que se devuelva.

**F2. El bot quedó mudo tres días.**
Causa: cambió el dominio; el viejo quedó como redirect 307 y el proveedor de webhooks **no
sigue redirects**. Encima la pantalla de configuración mostraba, para copiar y pegar, la URL
muerta.
→ **Regla:** derivar la URL pública del **pedido entrante**; validar la firma contra varios
orígenes candidatos; que la pantalla muestre el host por el que navega el admin.

**F3. `Cannot read properties of undefined (reading 'call')` que ni un hard-reload arregla.**
Causa: el service worker registrado en desarrollo cachea "caché primero" los chunks de
`/_next/static/`, que cambian de contenido sin cambiar de URL entre reinicios.
→ **Regla:** registrar el service worker **solo en producción**.

**F4. Una pestaña abierta durante un deploy se rompe (`ChunkLoadError`).**
Causa: el bundle viejo pide chunks con el hash anterior; el deploy nuevo no los tiene (404).
→ **Regla:** listener global de `error` y `unhandledrejection` que recarga **una vez** por
pestaña (guarda en `sessionStorage`).

**F5. "Functions cannot be passed directly to Client Components".**
Causa: un Server Component armaba la navegación con íconos de lucide (que son funciones) y se
la pasaba como prop al cliente.
→ **Regla:** entre servidor y cliente viajan **datos planos**. El cliente resuelve el ícono a
partir de una clave de texto.

**F6. Un `window.open()` bloqueado por el navegador.**
Causa: se llamaba después de un `await`, y ya no cuenta como gesto directo del usuario.
→ **Regla:** abrir la pestaña **antes** del `fetch` y escribirle el contenido después.

**F7. Consola llena de errores que "hay que reparar" y no son de la app.**
Síntomas típicos (juntos o sueltos):
- `contentscript.js` → `MaxListenersExceededWarning` / listeners `close` / `end`
- `ObjectMultiplex - orphaned data for stream "app-init-liveness"` / `"background-liveness"`
- `200.js` (u otro chunk corto) → `Cannot read properties of undefined (reading 'M_ID')`
- `VM##` / `et.reportAllChanges` → `reading 'startTime'`
Causa: **extensiones del navegador** (wallets tipo MetaMask, password managers, blockers,
herramientas de medición) inyectan scripts en la página. El stack no apunta a
`/_next/static/...` del dominio de la app ni a un módulo del repo.
→ **Regla:** antes de tocar código por un error de consola, clasificar el origen:
  1. ¿El archivo es `contentscript.js`, `chrome-extension://`, `VM##`, o un chunk **sin**
     path `/_next/` del host de la app? → **ignorar**; no es bug del producto.
  2. Confirmar en ventana **incógnito sin extensiones** (o perfil limpio): si desaparece,
     cerrar el ticket.
  3. Solo investigar si el stack cita un bundle propio (`/_next/static/chunks/...` del
     dominio) o un módulo del repo (`app/`, `components/`, `lib/`).
→ **Anti-patrón:** no "reparar" con `setMaxListeners`, polyfills ni guards inventados para
  apagar ruido de terceros. No inventar `M_ID` en el código de la app.

**F8. Cambiar de pantalla del panel se siente lento / "congelado".**
Causa típica (combinada):
1. Next 15 deja `staleTimes.dynamic = 0` → **cada** soft-nav revalida el RSC completo.
2. Layout + page llaman `getUser()` / `getPerfil()` **dos veces** en el mismo request.
3. No hay `loading.tsx` → la UI no da feedback hasta que termina Auth + DB (latencia a
   Supabase).
→ **Regla al armar el dashboard:**
  - `createClient` y `getPerfil` envueltos en `React.cache()` (un Auth+DB por request).
  - `experimental.staleTimes.dynamic` ≥ 30 s (las mutaciones ya hacen `router.refresh()`).
  - `app/dashboard/loading.tsx` (skeleton) + barra de progreso de navegación.
  - No volver a pedir el perfil en la page si el layout ya lo resolvió en el mismo request
    (el `cache()` lo deduplica).
→ **No confundir** con F7: lentitud real se mide en Network (documento RSC / `?_rsc=`), no
  en errores de `contentscript.js`.

**F9. `npx tsc --noEmit` pasa limpio y `npm run build` se cae con un error de `next/headers`.**
Causa: un componente de cliente (`"use client"`) importó —aunque sea solo para un **tipo** o
una **constante**— un módulo que en su cadena de imports llama a `cookies()` / `headers()` /
`next/headers`. El typecheck no lo ve; el build sí. Pasó con el módulo de config del chatbot:
la pantalla importaba de ahí los topes de largo y se traía `next/headers` al bundle.
→ **Regla:** los tipos y las constantes que comparten servidor y cliente viven en un módulo
**puro** (`lib/<x>/tipos.ts` o `configTipos.ts`), sin un solo import de servidor. El módulo
que toca la sesión importa **desde** el puro, nunca al revés. Y correr `npm run build`, no
solo `tsc`, antes de dar por cerrado un cambio que toca imports compartidos.

**F10. "Se mueve todo lento" con el mismo stack que otro proyecto que sí volaba.**
Causa (por frecuencia): (1) las funciones de Vercel y la base de Supabase quedaron en
**regiones distintas** → +150 ms por consulta, y una pantalla hace varias; (2) el `layout` y
la `page` validan la sesión con `getUser()` por separado → 2–3 viajes a Auth antes del primer
dato; (3) policies RLS con la función **sin envolver** en `(select ...)` → se evalúa una vez
por fila; (4) `await` secuenciales en el server component en vez de `Promise.all`; (5) falta
`loading.tsx` + `staleTimes` (ver F8).
→ **Regla:** `09-rendimiento.md` entero es config de **Fase 1**, no una optimización
posterior. Mínimo: `vercel.json` con `regions` = región de Supabase; `React.cache()` en
`createClient`/`getPerfil`; `(select public.current_user_org())` en toda policy + índice en
`id_org`; `Promise.all` para consultas independientes; `loading.tsx` + `staleTimes.dynamic`.
→ **Medir, no adivinar:** el tiempo del documento `?_rsc=` en la pestaña Network dice si el
cuello está en el servidor; `EXPLAIN (ANALYZE, BUFFERS)` dice si es la RLS/índice.

---

## G. Interfaz

**G1. Iconos y sellos invisibles en tema oscuro (1,7:1).**
Causa: un color pensado como **fondo** usado como **texto**. En claro coincidía por
casualidad con el token correcto.
→ **Regla:** tokens separados para fondo y para texto; barrer el código buscando ese patrón.

**G2. El velo de un modal aclaraba la pantalla en oscuro.**
Causa: `bg-ink/40`; `ink` es la tinta del tema y en oscuro vale casi blanco.
→ **Regla:** los velos van con `bg-black/40`.

**G3. Un elemento marcado `hidden sm:inline-block` se veía igual en celular.**
Causa: la clase propia estaba suelta al final del CSS, **después** de las utilidades de
Tailwind: a igual especificidad gana la última.
→ **Regla:** clases propias en `@layer components`.

**G4. Encabezados de tabla `sticky` que no se pegaban.**
Causa: la caja tenía `overflow-x-auto` (ya es contenedor de scroll) pero **sin alto
acotado**, así que nunca se desplazaba verticalmente.
→ **Regla:** el contenedor del `sticky` necesita alto máximo propio.

**G5. Una URL larga sacaba la pantalla de cuadro.**
Causa: hijo de un flex sin `min-w-0`: el `min-width: auto` usa la palabra más larga como
ancho mínimo.
→ **Regla:** `min-w-0` + `break-all` en todo contenedor de texto largo dentro de un flex.

**G6. El calendario se trababa en el celular y dejaba de responder.**
Causa: mostrar/ocultar la barra de direcciones dispara `resize` aunque **solo cambió el
alto**; el handler cortaba la transición en curso, `transitionend` no llegaba y un flag
"animando" quedaba en `true` para siempre.
→ **Regla:** ignorar los `resize` que no cambian el **ancho**; liberar el candado en el
recentrado en frío; y un `setTimeout` de respaldo por si `transitionend` nunca llega.

**G7. Barras de tamaño aleatorio en el calendario.**
Causa: el alto de la semana se repartía entre sus carriles: una semana con 8 solapes daba
barras de 9 px.
→ **Regla:** el carril mide siempre lo mismo y la fila crece; si no entra, scrollea la
grilla, nunca la página.

**G8. Un paso del tour desaparecía en celular.**
Causa: el ancla estaba en la tabla, que se oculta bajo `sm`.
→ **Regla:** el ancla va en el **envoltorio**, visible en las dos vistas.

**G9. Filtros que "no filtraban nada".**
Causa: al sacar la tabla, el filtro de estado solo afectaba a unos gráficos plegados, pero
seguía en el encabezado como si filtrara la pantalla.
→ **Regla:** un control vive **al lado de lo que afecta**. Si deja de afectar a lo principal,
se mueve o se saca.

---

## H. Reglas de negocio

**H1. Trabajo asignado a alguien dado de baja (23 tareas invisibles).**
Causa: la auto-asignación miraba el estado de la **asignación**, no si la **persona** seguía
activa. Como el personal dado de baja no figura en ninguna pantalla, esas tareas
desaparecieron de la operación.
→ **Regla:** una sola función resuelve "quién es el responsable" (asignación vigente **y**
persona activa) y la usan **todos** los caminos que asignan. Más un trigger que, al dar de
baja a alguien, libere o reasigne lo pendiente. El historial no se toca: sostiene las
estadísticas.

**H2. Una regla derivada no se recalculaba cuando cambiaba una fila vecina.**
Causa: el trigger solo miraba la fila modificada; la condición dependía de otra fila que
podía aparecer, moverse o darse de baja después.
→ **Regla:** si la regla mira vecinos, hace falta **también** un trigger sobre los vecinos.

**H3. Dos personas usando el mismo identificador pisaban los datos.**
Causa: no había regla de titularidad.
→ **Regla:** definirla explícitamente ("gana el primero"; a los demás se los atiende pero no
escriben nada) y **avisar al equipo**: es la única señal de que ese identificador circula.

**H4. Un lector automático inventaba nombres ("no anda el aire acondicionado" quedó como
nombre del cliente).**
Causa: heurística demasiado permisiva.
→ **Regla:** aceptar el dato solo si está marcado ("soy X", "me llamo X") o si el mensaje
**es** el dato (1–3 palabras con mayúscula inicial). Ante la duda, no escribir nada y volver
a preguntar **una** vez; después seguir de largo — alguien que escribe porque no puede entrar
no puede quedar trabado en un formulario.

**H5. Un cambio de precio reescribía la historia.**
→ **Regla:** el trabajo derivado guarda un **snapshot** del precio del momento, no una
referencia al precio vigente.

**H6. El nombre del titular estaba hardcodeado en el prompt del chatbot.**
Causa: el prompt escrito a mano mezclaba reglas del sistema con datos de ESTE negocio — la
frase con la que el bot se presenta si le preguntan si es una IA nombraba al titular en duro.
En una app multi-tenant, la segunda organización que activara el bot se habría presentado con
el nombre de la primera.
→ **Regla:** cero datos del negocio en el código. Nombre, teléfonos, horarios, políticas y
textos de presentación van a una tabla de config por organización, editable desde la app; el
código solo lleva las reglas que valen para todos los tenants. El contexto editable entra al
prompt como INFORMACIÓN y **antes** de las REGLAS, para que no pueda pisarlas. Ver
`05-integraciones.md` (chatbot en capas).

---

## I. Plataformas de terceros

**I1. Cuenta de WhatsApp Business dada de baja sin haber enviado un mensaje.**
Causa: identidad pública desalineada (marca ajena en el H1 y en la meta description; dos
razones sociales distintas entre la landing y la política de privacidad).
→ **Regla:** ver la checklist de alineación en `06-landing-y-legales.md`.

**I2. Un modelo de IA rechazaba **todos** los pedidos con 400.**
Causa: se mandaba un parámetro de configuración que el proveedor dejó de aceptar.
→ **Regla:** mandar el mínimo de parámetros; ante un 400 masivo, probar contra la API real
con un payload mínimo antes de suponer que es el modelo.

**I3. Un modelo "existente" no estaba disponible para cuentas nuevas.**
→ **Regla:** usar alias estables y tener fallback ante 404.

**I4. Riesgo de perder la cuenta del cliente por automatizar dentro del sitio de un tercero.**
→ **Regla:** nunca. Se copia el texto y se abre el link real; el humano confirma. Y las
descargas desde su web: una pasada, a pedido, nunca en cron ni con reintentos.

**I5. Sorpresas del plan gratuito.**
Causa: crons diarios (no por minuto) y proyectos que se pausan solos tras 7 días sin
actividad.
→ **Regla:** conocer los límites antes de diseñar. Frescura por tráfico (`revalidate` +
`after()`), cron diario que además mantiene despiertos los proyectos secundarios, y botón
manual para el resto.

---

## J. Datos públicos

**J1. Una ventana en la que la página pública mostraba "todo libre".**
Causa: el sync a la base separada borraba todo y volvía a insertar.
→ **Regla:** si hay sync, escribir el lote nuevo y **después** borrar el anterior. Mejor
todavía: sin sync (ver J3), esta ventana no puede existir.

**J2. Enumeración de recursos.**
Causa: la URL pública usaba el id.
→ **Regla:** token aleatorio (UUID) por recurso, contenido genérico.

**J3. Segunda base Supabase para la vitrina: dos costos que no se vieron venir.**
Causa: copiar las fichas publicables a un proyecto aparte ocupaba el segundo (y último) slot
del plan free y dejaba la página con el atraso del último sync.
→ **Regla:** por defecto, la superficie pública son **vistas en la misma base** que proyectan
solo lo publicable, leídas con la **clave anónima** — contra cualquier otra tabla la RLS
devuelve 0 filas, así que una consulta equivocada no puede filtrar datos personales. Sin
copia: estado en vivo, cero ventana de "todo libre" (J1 deja de poder pasar) y no gasta el
otro proyecto. La base separada queda como opción solo si hace falta aislamiento **físico**.
Detalle: `security_invoker = off` en las vistas (el linter las marca "security definer view",
es lo buscado). Ver `03-seguridad.md` §5.

---

## Checklist rápida de Fase 8

- [ ] Ningún `AT TIME ZONE` sobre columnas `DATE`; aritmética de fechas anclada a mediodía.
- [ ] Ningún `catch {}` mudo; todo error de supabase-js chequeado.
- [ ] Toda acción que toca plata: reclamo atómico + recibe todos los filtros de la UI.
- [ ] Toda ingesta: clave `UNIQUE` natural, cuerpo crudo guardado, `revisar_manual` cuando
      falta un campo crítico.
- [ ] Toda ruta que muta: `guardAdmin`. Toda ruta pública: prefijo revisado.
- [ ] Webhooks: firma, fail-closed, dedup, 200 + `after()`, URL derivada del pedido.
- [ ] Crons: `CRON_SECRET`, errores en la respuesta, **verificado que corrieron**.
- [ ] Tema oscuro: ningún color de fondo usado como texto; velos en `bg-black/xx`.
- [ ] 375 px: sin scroll horizontal, tablas en tarjetas, inputs 16 px, toques ≥ 40 px.
- [ ] Migración aplicada **antes** del deploy.
- [ ] Errores de consola clasificados: ruido de extensión (`contentscript`, `ObjectMultiplex`,
      `M_ID`, `reportAllChanges` en `VM##`) **no** se trata como bug de la app (ver F7).
- [ ] Soft-nav del panel: `React.cache` en cliente/perfil, `staleTimes.dynamic`, `loading.tsx`
      (ver F8).
- [ ] `npm run build` (no solo `tsc`) corrido tras tocar imports compartidos servidor/cliente;
      ningún componente de cliente importa un módulo que llega a `next/headers` (ver F9).
- [ ] Cero datos del negocio hardcodeados (nombre del titular, teléfonos, horarios, textos de
      presentación, contexto de un bot): todo en config por organización o `lib/empresa.ts`
      (ver H6).
- [ ] Vitrina pública: vistas en la misma base leídas con la clave anónima; verificado con
      `SET ROLE anon` que otras tablas devuelven 0 filas (ver J3).
- [ ] Rendimiento (ver F10 y `09-rendimiento.md` §10): región Vercel = región Supabase
      medida en logs; `React.cache` en sesión/perfil; policies RLS envueltas + índice en
      `id_org`; `Promise.all` sin waterfalls; `loading.tsx` + `staleTimes`.
