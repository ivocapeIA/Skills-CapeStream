# Seguridad — checklist y patrones

Cada punto de este archivo sale de un agujero real encontrado en una auditoría o de un
incidente. Se recorre entero en la Fase 8 y cada vez que se agrega una ruta pública.

---

## 1. Autorización

- [ ] **La UI no es una restricción.** Toda ruta que muta datos empieza con una guarda de
      servidor. Un helper único evita que una ruta nueva se olvide:

```ts
// lib/apiGuard.ts — "solo admin + módulo activo", en un solo lugar.
export async function guardAdmin(modulo?: ModuloKey) {
  const supabase = await createClient();                       // Cliente CON sesión.
  if (!(await esAdmin(supabase)))                              // Nivel del usuario.
    return { error: NextResponse.json({ error: "No tenés permiso." }, { status: 403 }) };
  if (modulo && !(await moduloActivo(modulo)))                 // Módulo habilitado.
    return { error: NextResponse.json({ error: "Módulo no habilitado." }, { status: 403 }) };
  return { supabase };
}
```

- [ ] **La página gatea la navegación; la API gatea la acción.** Las dos cosas, siempre.
- [ ] **El rol operativo tiene guarda propia** (`redirigirSiOperativo`) en cada página de
      gestión, y en la API solo puede hacer la transición concreta que le corresponde
      (ej. `pendiente → realizada`, sobre **sus** filas), nunca fijar un estado arbitrario.
- [ ] **Anti-escalación de privilegios:**
  - un admin común no puede editar ni cambiarle la contraseña al usuario `global`;
  - no se puede dar de baja al último admin/global de una organización;
  - el objetivo de una acción sobre otro usuario se lee con el **cliente de sesión**, así
    RLS ya lo acota a la organización de quien pide.
- [ ] **Cambio de contraseña propio: exige la contraseña actual.** Sin eso, quien agarre una
      sesión abierta se queda con la cuenta. La verificación se hace con un cliente de
      Supabase aparte que **no persiste sesión**, para que ese login de control no rote la
      cookie del navegador.

---

## 2. Sesión y middleware

- [ ] **Toda redirección del middleware lleva las cookies de sesión.** `getUser()` **rota el
      refresh token adentro** si estaba vencido, y el único lugar donde existe el token
      nuevo son las cookies de la respuesta. Devolver un `NextResponse.redirect()` recién
      creado (una respuesta vacía) tira esa rotación y **mata la sesión del dispositivo para
      siempre**. Síntoma real: 92 % de las sesiones no pasaban de una rotación y la gente
      tenía que loguearse cada vez que abría la app.

```ts
// Copia las cookies frescas a cualquier respuesta que se devuelva.
const conCookiesDeSesion = (respuesta: NextResponse) => {
  supabaseResponse.cookies.getAll().forEach((c) => respuesta.cookies.set(c));
  return respuesta;
};
return conCookiesDeSesion(NextResponse.redirect(url));
```

- [ ] **Rutas públicas: cuidado con `startsWith`.**
  - La raíz se compara **exacta** (`pathname === "/"`): toda ruta empieza con `/` y un
    prefijo deja el sitio entero sin protección.
  - El prefijo va **completo**: `"/api/ical/publico"` y no `"/api/ical"`, porque el segundo
    también abriría `/api/ical/sync`, que dispara una sincronización y debe exigir admin.
- [ ] **Los webhooks y crons van en la lista de rutas públicas** (no traen cookie) y se
      autentican por su cuenta. Sin la excepción, el middleware los redirige a `/login` con
      un 307 y el proveedor descarta el mensaje en silencio.
- [ ] **El callback de auth sanea el parámetro `next`** (anti open-redirect): solo rutas
      internas que empiecen con `/` y no con `//`.

---

## 3. Webhooks entrantes

- [ ] **Fail-closed siempre**: sin secreto configurado, el webhook **rechaza**. Nunca
      "si no hay firma, procesamos igual": el `From` lo controla quien envía, así que
      cualquiera que conozca la URL podría inyectar mensajes falsos.
- [ ] **Firma HMAC sobre el cuerpo CRUDO.** Leer `await req.text()` y validar **antes** de
      parsear; re-serializar el JSON cambia un byte y rompe la firma.

```ts
const crudo = await req.text();                        // Cuerpo tal cual lo firmó el proveedor.
if (!validarFirma(appSecret, crudo, req.headers.get("x-hub-signature-256")))
  return new NextResponse("Firma inválida", { status: 403 });
```

- [ ] **Si hace falta rutear antes de validar** (una URL compartida por varias
      organizaciones: hay que leer el payload para saber contra qué secreto comparar), es
      seguro **siempre que no haya ningún efecto de lado antes del chequeo de firma**. El
      atacante elige contra qué secreto lo comparamos, pero sigue sin poder producir una
      firma válida para ninguno. Dejarlo comentado en el código: es contraintuitivo y
      alguien lo va a "arreglar".
- [ ] **Deduplicación por id del proveedor** (`wamid`, `MessageSid`, `Message-ID`) en una
      tabla de vistos con purga automática. Un reintento del proveedor re-ejecutaría la
      acción.
- [ ] **Responder 200 al toque y trabajar en `after()`.** Si tardamos, el proveedor
      reintenta; con `maxDuration` explícito en la ruta.
- [ ] **Un mensaje que falla no frena a los demás** del mismo lote (try/catch por ítem).
- [ ] **La URL pública se deriva del pedido entrante** (`x-forwarded-host` / `-proto`), no de
      una constante. Incidente real: al cambiar de dominio, el viejo quedó como redirect 307;
      el proveedor **no sigue redirects** en webhooks y el bot quedó mudo 3 días. Además, la
      pantalla de configuración le mostraba al admin, para copiar y pegar, justo la URL
      muerta. La firma se valida contra varios orígenes candidatos (el del pedido primero).

---

## 4. Crons

- [ ] Protegidos con `CRON_SECRET`: `Authorization: Bearer <secreto>`; **sin la variable,
      401** (fail-closed).
- [ ] **Verificar después del deploy que el cron corre de verdad.** Incidente real: faltaba
      `CRON_SECRET` en el entorno y los crons devolvían 401 desde siempre — la
      funcionalidad "andaba" en el código y nunca había corrido una sola vez.
- [ ] El cron devuelve un JSON con lo que hizo y con **cada error explícito** (ver la trampa
      de `supabase-js` en `02-datos-rls-migraciones.md`).
- [ ] Reclamo atómico por fila antes de enviar algo (marcar `notificada_at` y revertir si el
      envío falla): evita el doble aviso.

---

## 5. Rutas públicas y tokens

- [ ] **Un recurso público se direcciona con un token aleatorio (UUID), nunca con el id.**
      Con el id se enumeran los recursos de todo el sistema.
- [ ] El contenido público es **genérico**: un feed de disponibilidad no dice quién es el
      huésped ni cuánto pagó.
- [ ] **Vitrina / catálogo público (opción recomendada): vistas en la MISMA base, leídas con
      la clave anónima.** La superficie pública se declara como un puñado de vistas
      (`vitrina_apartamento`, `vitrina_tramo`…) que proyectan **solo lo publicable** —sin
      dirección, sin claves, sin `info_huespedes`, sin montos ni datos de clientes— y filtran
      por `publicado = true AND fecha_baja IS NULL`. La página sin login las lee con la
      **clave anónima** (`NEXT_PUBLIC_SUPABASE_ANON_KEY`), **nunca** con `service_role`:
      verificar con `SET ROLE anon` que contra cualquier otra tabla (`reserva`, `usuario`,
      la tabla base) la RLS devuelve **0 filas**. Así el techo de lo que la página puede
      leer lo pone la base, y una consulta equivocada en el código no puede filtrar datos
      personales. Las vistas van con `security_invoker = off` (el default): aplican su filtro
      fijo en vez de la RLS de las tablas base. El linter de Supabase las marca como
      "security definer view" — es intencional y está acotado a proyecciones sin datos
      privados.
      Ventaja sobre la base separada: no hay copia, así la página muestra el estado **en
      vivo** (sin ventana de "todo libre") y no ocupa un segundo proyecto del plan free.
- [ ] **Base separada (alternativa, solo si se necesita aislamiento FÍSICO):** un proyecto
      aparte al que un sync copia solo lo publicable, con RLS activa y **cero políticas**
      (único acceso: `service_role` desde el servidor). Si se hace así, al republicar
      **no borrar y volver a insertar**: se estampa un `lote` nuevo y se borra el anterior
      *después* de escribir, o hay un instante en que la página pública muestra "todo libre".
      Y el sync tiene que mantener ese proyecto despierto (un free se pausa a los 7 días).

---

## 6. Descargas desde el servidor (SSRF)

Toda URL que carga un usuario y que el **servidor** va a descargar (feeds iCal, webhooks
salientes, importadores de páginas) se valida antes:

- [ ] Esquema `http`/`https` únicamente.
- [ ] Rechazar hosts obvios: `localhost`, `*.localhost`, `metadata`, `*.internal`.
- [ ] **Resolver DNS antes del fetch** y rechazar si *alguna* dirección cae en rango
      privado/loopback/link-local/CGNAT (v4 y v6, incluida la forma `::ffff:a.b.c.d`).
      El rango link-local `169.254.0.0/16` es el que expone la metadata de la nube.
- [ ] Límite de tamaño de la respuesta (OOM defensivo).
- [ ] Una sola implementación compartida por todos los llamadores: duplicarla es la forma
      segura de que una copia se quede vieja el día que haya un rango nuevo que bloquear.

---

## 7. Costo y abuso (rate limiting)

Todo endpoint que gasta plata (IA, SMS, WhatsApp) o que se puede tantear necesita tope:

- [ ] Tabla de contadores por (organización, identificador, acción, ventana) con
      **incremento atómico en una función SQL** — no "leer y escribir" desde la app, que
      compite consigo mismo entre mensajes concurrentes.
- [ ] Dos topes distintos: **intentos de verificación** (antes de gastar la consulta) y
      **llamadas al modelo** (por minuto y por día).
- [ ] Al frenar, **degradar en silencio**: no avisar a los administradores por cada mensaje
      bloqueado, o un flood de costo se convierte en un flood de spam interno.
- [ ] Login y formularios públicos: límite por IP/mail.

---

## 8. Secretos

- [ ] `service_role` solo en el servidor; jamás en una variable `NEXT_PUBLIC_*`.
- [ ] Credenciales de integraciones **por organización, en la base, protegidas por RLS de
      admin** (no por variables de entorno): así cada negocio conecta su propia cuenta sin
      tocar código ni redeploy. Las variables de entorno quedan como valor por defecto.
- [ ] **Lo mismo para los datos y textos del negocio, no solo para los secretos.** El nombre
      del titular, los horarios, la frase con la que un bot se presenta, su contexto general:
      todo en una tabla de config por organización, editable desde una pantalla. Un dato de
      negocio hardcodeado en un prompt o un componente, en multi-tenant, se lo lleva la
      segunda organización que se dé de alta (ver `07-errores-conocidos.md` **H6**).
- [ ] Nunca devolver un secreto al navegador. Las pantallas de configuración muestran
      "cargado / no cargado", no el valor.
- [ ] Nunca exponer credenciales por RPC. Caso real eliminado: una función que le entregaba
      el token del proveedor a `anon` con solo conocer un secreto de URL.
- [ ] `.gitignore` con `.env*` y una excepción explícita `!.env.example`. Verificar que
      ningún secreto entró al repo antes del primer push.
- [ ] Al cargar variables en el hosting, **verificar que quedaron con valor**: una clave
      guardada vacía se comporta igual que "no configurada" y el diagnóstico se va por otro
      lado. Las variables sensibles no se pueden releer: confirmar con una llamada real.

---

## 9. Trazabilidad

- [ ] Log de todos los mensajes entrantes y salientes, con estado y motivo del fallo
      (incluido "no enviado por baja"), visible en el panel: si falta un aviso, se tiene que
      poder ver **por qué** faltó.
- [ ] Registrar los pedidos de eliminación de datos y de baja de mensajes como filas, no
      como algo que alguien tiene que leer en un chat.
- [ ] Logs explícitos en los fallos de servicios externos (IA, correo, mensajería):
      `console.error("[IA] ...")` con status y cuerpo de la respuesta. Un `catch {}` mudo
      hace imposible el diagnóstico: pasó dos veces con el mismo síntoma.

---

## 10. Pendientes típicos (dejarlos anotados, no ocultos)

Cosas que este stack **no** trae resueltas y hay que decidir explícitamente:

- Cabeceras de seguridad HTTP (`CSP`, `X-Frame-Options`, `Referrer-Policy`) en
  `next.config.mjs`.
- Rate limiting del login.
- Rotación de las credenciales de integraciones guardadas en la base (hoy texto plano
  protegido por RLS; cifrarlas con una clave de entorno es la mejora natural).
- Retención/purga de logs de conversación.
