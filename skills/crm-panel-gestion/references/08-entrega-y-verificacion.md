# Entrega, verificación y documentación

---

## 1. Definición de "terminado"

Un cambio no está terminado hasta que:

1. `npx tsc --noEmit` sin errores.
2. `npm run build` sin errores.
3. Smoke test en navegador de las rutas tocadas, **en los dos temas** y en los dos anchos
   (375×812 y 1280×900).
4. Entrada en `HISTORIAL.md`.
5. Si hubo migración: aplicada **antes** del deploy y verificada contra datos reales.
6. Si el cambio agregó pantallas o consultas: el cambio de pantalla se siente inmediato
   (documento RSC < ~200 ms) y ninguna consulta nueva escanea tabla entera
   (`09-rendimiento.md`).

`tsc` y `build` **no detectan** los bugs de runtime de las rutas dinámicas (no se
prerrenderizan). Varios errores reales aparecieron recién con la app abierta. Si no hay forma
de abrir el navegador en la sesión, **decirlo explícitamente** en el historial en vez de dar
por verificado lo que no se probó.

Y al revés: `tsc` limpio **no** garantiza que el build pase. Un componente de cliente que
importa un módulo que llega a `next/headers` (aunque sea por un tipo) compila y no linka.
Correr `npm run build`, no solo `tsc`, siempre que se toquen imports compartidos entre
servidor y cliente (ver `07-errores-conocidos.md` F9).

### Consola del navegador (no perseguir fantasmas)

Al mirar DevTools en el smoke test, **filtrar ruido de extensiones** antes de declarar un
bug (detalle en `07-errores-conocidos.md` **F7**): `contentscript.js`, `ObjectMultiplex`,
`M_ID`, `reportAllChanges` / `startTime` en `VM##` no son de Next.js ni del CRM. Verificar
en incógnito sin extensiones. Solo cuentan stacks de `/_next/static/...` del dominio o
módulos del repo.

---

## 2. `HISTORIAL.md`

Es el activo más valioso del repositorio después del código: es lo que hace que la próxima
sesión —humana o de IA— no repita un error ya resuelto. Entrada más reciente **arriba**.

```markdown
## AAAA-MM-DD — Título en una línea, en criollo

**Tipo:** feature | fix | ui | seguridad | dato | refactor.
Archivos nuevos: ... Archivos modificados: ...

**Qué pasaba.** El síntoma como lo vio el usuario, y la causa real (no la que parecía).

**Qué cambia.** Las decisiones que NO se leen solas en el diff: por qué se eligió este
camino, qué alternativa se descartó y por qué, qué queda como limitación conocida.

Migración NNNN aplicada en producción. `npx tsc --noEmit` y `npm run build` sin errores.
**Pendiente:** lo que quedó sin hacer o sin verificar.
```

Lo que hay que escribir sí o sí: **el porqué**, las **limitaciones aceptadas a propósito**,
y los **pendientes**. Un diff explica el qué; nadie recuerda el porqué a los dos meses.

---

## 3. `CLAUDE.md` / `AGENTS.md` del proyecto nuevo

Se generan en la Fase 1 y se mantienen actualizados. Secciones:

- **Qué es** (2 líneas) · **Stack** · **Convenciones** (colores por token, comentarios en
  español, changelog) · **Comandos** · **Estructura** · **Patrones clave** (los que no se
  deducen del código: reglas de negocio, cómo funciona cada integración, decisiones
  contrarias a la intuición) · **Producción** (URLs, proyectos, variables de entorno,
  límites del plan) · **Estado y pendientes** · **Verificación antes de dar por terminado**.

Regla: si algo del código sorprende, va acá con el motivo. La sección "Patrones clave" es la
que evita que el siguiente cambio rompa una regla que costó un incidente.

`AGENTS.md` puede ser un archivo de una línea que apunte a `CLAUDE.md` (o al revés): así lo
leen Cursor, Codex y cualquier otro agente.

---

## 4. `docs/DECISIONES.md`

Registro de las decisiones tomadas **en modo auto**, sin preguntar. Una línea por decisión:

```
- 2026-08-29 · Baja lógica en todas las entidades (no DELETE). Motivo: histórico para stats.
- 2026-08-29 · Moneda única ARS en v1. Motivo: no salió multi-moneda en el intake.
```

Sirve para que el usuario revise de un vistazo qué se asumió y pueda vetar algo temprano.

---

## 5. Variables de entorno

`.env.example` versionado (con `!.env.example` en el `.gitignore`, porque la regla `.env*` lo
excluye), documentando **para qué sirve cada variable y qué pasa si falta**:

```bash
# Clave de servicio (service_role). SECRETA: solo servidor. Salta RLS.
# Sin ella: no funciona el alta de usuarios ni ningún cron.
SUPABASE_SERVICE_ROLE_KEY=
```

Al cargarlas en el hosting: marcar como *sensitive* las secretas, y **verificar con una
llamada real** que quedaron con valor (ver error D3).

---

## 6. Deploy

Orden invariable:

1. Aplicar migraciones a la base de producción.
2. Verificar que las variables de entorno nuevas están cargadas y con valor.
3. Deploy.
4. Smoke test de las rutas afectadas.
5. Verificar que los crons corrieron (no que están declarados).
5b. En el **primer** deploy: confirmar en los logs de una función que la región de ejecución
    coincide con la de Supabase y que una consulta trivial tarda decenas de ms
    (`09-rendimiento.md` §1).
6. Actualizar la URL de los webhooks si cambió el dominio — y recordar que un dominio viejo
   que queda como redirect **no sirve** para webhooks.

---

## 7. Revisiones recomendadas antes de cerrar una fase

- **Revisión de restricciones**: leer el código pensando en la operatoria diaria y buscar
  qué combinación de datos todavía no está contemplada (dos usuarios a la vez, una entidad
  dada de baja, un import que se repite, una fecha en el pasado, un monto en cero).
- **Revisión de seguridad**: recorrer `03-seguridad.md` entero.
- **Revisión de datos hardcodeados**: barrer el código buscando datos de ESTE negocio
  incrustados —nombre del titular, teléfonos, horarios, textos de presentación, el contexto
  de un bot—. Todo eso va a config por organización o a `lib/empresa.ts`. En multi-tenant es
  un bug esperando a la segunda organización (ver `07-errores-conocidos.md` H6).
- **Revisión de rendimiento**: recorrer `09-rendimiento.md` §10. Lo primero, medir en
  producción el tiempo del documento RSC (`?_rsc=`) al cambiar de pantalla y una consulta
  trivial en los logs de una función: si son cientos de ms, revisar región co-locada, RLS
  envuelta e índices, y waterfalls de `await`.
- **Revisión visual**: pantalla por pantalla, los dos temas, los dos anchos.
- **Advisors de la base**: correrlos después de cada migración que cree funciones o tablas.
  Una vitrina sobre vistas públicas dispara un aviso de "security definer view" que es
  esperado (ver `03-seguridad.md` §5); todo lo demás se revisa.

Las tres primeras encontraron, en el proyecto de referencia, bugs de dinero y de datos que ni
el typecheck ni el build ni las pruebas manuales habían mostrado.
