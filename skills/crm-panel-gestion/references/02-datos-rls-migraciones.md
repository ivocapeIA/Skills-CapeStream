# Base de datos, RLS multi-tenant y migraciones

---

## 1. Convenciones de migraciones

- Archivos `supabase/migrations/NNNN_nombre_descriptivo.sql`, numerados y **en español**.
- **Una migración aplicada es inmutable.** Todo cambio posterior es una migración nueva,
  aunque sea para arreglar la anterior.
- Cada migración lleva un encabezado con qué hace y por qué; los comentarios línea por línea
  también aplican al SQL.
- Toda migración que cambia datos existentes incluye su **backfill** en el mismo archivo.
- **Orden de deploy: migración primero, código después.** Al revés, el código nuevo consulta
  columnas que no existen y tira abajo pantallas enteras (incidente real: 3,5 h de módulos
  caídos porque el deploy salió antes que la migración).

### Trampa: cambiar la firma de una función ya aplicada

`CREATE OR REPLACE FUNCTION` con **distinta cantidad de parámetros no reemplaza nada**:
crea un *overload* nuevo y deja la versión vieja viva, con el bug intacto. Agregar o quitar
un parámetro exige un `DROP FUNCTION nombre(tipos_viejos);` explícito en la misma migración.

---

## 2. Esquema base multi-tenant

```sql
-- Organización = tenant. Todo cuelga de acá, directa o indirectamente.
CREATE TABLE organizacion (
    id_org      SERIAL PRIMARY KEY,
    nombre      TEXT NOT NULL,
    fecha_alta  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_baja  TIMESTAMPTZ                          -- Baja lógica: nunca DELETE físico.
);

-- Usuario de la app. Se vincula al usuario de Auth POR EMAIL (no por uuid):
-- el esquema auth no está expuesto por PostgREST y el email es el dato compartido.
CREATE TABLE usuario (
    id_usuario  SERIAL PRIMARY KEY,
    id_org      INTEGER NOT NULL REFERENCES organizacion(id_org),
    mail        TEXT NOT NULL,
    nivel       TEXT NOT NULL CHECK (nivel IN ('global','admin','operativo')),
    telefono    TEXT,
    fecha_baja  TIMESTAMPTZ
);
-- El mail tiene que ser único entre usuarios activos: si no, current_user_org()
-- devuelve cualquiera de los dos y el aislamiento se vuelve aleatorio.
CREATE UNIQUE INDEX usuario_mail_unico ON usuario (lower(mail)) WHERE fecha_baja IS NULL;

-- Módulos on/off por organización: permite vender/activar por partes.
CREATE TABLE modulo (
    id_modulo  SERIAL PRIMARY KEY,
    id_org     INTEGER NOT NULL REFERENCES organizacion(id_org),
    clave      TEXT NOT NULL,          -- mod_clientes, mod_agenda, ...
    habilitado BOOLEAN NOT NULL DEFAULT TRUE
);
```

Niveles: `global` (ve todas las organizaciones; es el dueño de la plataforma),
`admin` (gestiona su organización), `operativo` (una sola pantalla, solo lo suyo).

---

## 3. Funciones auxiliares de RLS

```sql
-- Devuelve el id_org del usuario autenticado, leyendo el email del JWT de Supabase Auth.
CREATE OR REPLACE FUNCTION public.current_user_org()
RETURNS INTEGER
LANGUAGE sql
STABLE                       -- No modifica datos; estable dentro de la consulta.
SECURITY DEFINER             -- Necesita leer "usuario" saltando la RLS de esa tabla.
SET search_path = public     -- Obligatorio en SECURITY DEFINER: evita secuestro por search_path.
AS $$
    SELECT id_org FROM public.usuario
    WHERE mail = auth.jwt() ->> 'email' AND fecha_baja IS NULL
    LIMIT 1;
$$;

-- Igual para current_user_es_admin() (nivel IN ('admin','global'))
-- y current_user_es_global() (nivel = 'global').
```

**Después de crear cada función auxiliar, revocar permisos de más:**

```sql
REVOKE EXECUTE ON FUNCTION public.helper_interno(...) FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.helper_interno(...) TO service_role;
```

Motivo real: un helper pensado para triggers quedó ejecutable por `anon` y permitía
resolver datos de cualquier organización **sin sesión**, por RPC. Los advisors de seguridad
de Supabase lo detectan: correrlos después de cada migración que cree funciones.

> Ojo: en algunas bases `service_role` funciona igual sin el `GRANT` explícito. Ponerlo de
> todos modos: recrear la base solo desde las migraciones tiene que funcionar.

---

## 4. Políticas RLS

Patrón para tabla **con** `id_org`:

```sql
ALTER TABLE cosa ENABLE ROW LEVEL SECURITY;

CREATE POLICY cosa_all ON cosa
    FOR ALL
    USING      (id_org = public.current_user_org() OR public.current_user_es_global())
    WITH CHECK (id_org = public.current_user_org() OR public.current_user_es_global());
```

Patrón para tabla **sin** `id_org` (cuelga de otra):

```sql
CREATE POLICY detalle_all ON detalle
    FOR ALL
    USING (
        public.current_user_es_global() OR
        id_padre IN (SELECT id_padre FROM padre WHERE id_org = public.current_user_org())
    )
    WITH CHECK ( ... la misma condición ... );
```

### Reglas que evitan los agujeros reales

1. **Toda tabla con credenciales o secretos exige admin, no solo pertenencia.**
   Error real: la tabla de configuración de correo (contraseña IMAP en texto plano) quedó
   con políticas que solo pedían la organización; cualquier usuario **operativo** podía leer
   la contraseña pegándole directo a PostgREST con la anon key, salteando el chequeo de la
   API route. La política correcta:
   `USING (id_org = current_user_org() AND current_user_es_admin())`.
   Y sin bypass para el usuario global en escritura: que sea dueño de la plataforma no lo
   habilita a escribir credenciales de un tercero (SELECT sí, para auditoría).
   La misma política (`org AND admin`) va en las tablas de **configuración editable** —el
   contexto de un chatbot, plantillas de mensajes, toggles— aunque no guarden secretos: un
   `operativo` no configura el negocio, y copiar de `whatsapp_config` una policy que pedía
   solo la organización dejó un agujero real.
2. **Tablas que solo escribe el servidor** (logs de mensajería, mails ingeridos, contadores
   de límite) llevan únicamente policy de `SELECT`. El `INSERT`/`UPDATE` lo hace
   `service_role`, que salta RLS. Si después hace falta escribir desde un endpoint con
   sesión, se valida admin con el cliente de sesión y se escribe con el admin.
3. **La RLS no reemplaza la autorización de la API.** RLS aísla *organizaciones*; no
   distingue `admin` de `operativo` en la mayoría de las tablas. Eso lo hace `guardAdmin`.
4. **`WITH CHECK` siempre**, no solo `USING`: sin él se pueden insertar filas de otra
   organización aunque no se puedan leer.

---

## 5. Invariantes en la base

Las que más valor dieron en el sistema real:

```sql
-- 1) Nada de solapes (doble booking, doble turno, doble asignación).
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE reserva ADD CONSTRAINT reserva_sin_solape
    EXCLUDE USING gist (
        id_apartamento WITH =,
        daterange(fecha_inicio, fecha_fin, '[)') WITH &&
    ) WHERE (fecha_baja IS NULL);

-- 2) Rangos coherentes y montos sanos.
ALTER TABLE reserva ADD CONSTRAINT reserva_fechas CHECK (fecha_fin > fecha_inicio);
ALTER TABLE reserva ADD CONSTRAINT reserva_monto CHECK (monto IS NULL OR monto >= 0);

-- 3) Catálogos cerrados en vez de texto libre.
ALTER TABLE transaccion ADD CONSTRAINT transaccion_tipo
    CHECK (tipo IN ('ingreso','egreso','comision','servicio','sena'));

-- 3b) Texto libre de configuración que después se inyecta en un prompt o un mensaje:
--     tope de largo en la BASE, no solo en la UI. El prompt se arma en el webhook y un
--     texto gigante ahí es costo y latencia en CADA mensaje.
ALTER TABLE chatbot_config ADD CONSTRAINT chatbot_config_contexto_largo
    CHECK (char_length(contexto) <= 8000 AND char_length(identidad) <= 300);

-- 4) Unicidad parcial: el código externo es único ENTRE FILAS ACTIVAS.
CREATE UNIQUE INDEX reserva_codigo_unico
    ON reserva (id_apartamento, codigo_reserva)
    WHERE fecha_baja IS NULL AND codigo_reserva IS NOT NULL;

-- 5) Coherencia entre tablas que la FK no cubre (la FK corre como owner y salta RLS):
--    un trigger valida que la categoría elegida sea de la misma organización.
```

Antes de agregar un `EXCLUDE` a una tabla con datos: **verificar que no haya filas que ya lo
violen** (la migración falla, o peor, hay que limpiar datos en producción a las apuradas).

---

## 6. Triggers: cuándo sí

Un trigger cuando la regla tiene que valer **sin importar quién escribe**:

- Crear el trabajo derivado al insertar el hecho (alta de reserva → limpieza pendiente, con
  *snapshot* de los precios vigentes en ese momento).
- Recalcular ese derivado cuando cambian los campos de los que depende.
- Liberar/reasignar trabajo cuando se da de baja a una persona.
- Cancelar el derivado cuando el hecho se da de baja.

Detalles que se aprendieron a golpes:

- **Snapshot de precios**: el derivado guarda el precio del momento, no una FK al precio
  actual. Si no, cambiar la tarifa reescribe la historia.
- **El trigger de la fila que cambió no alcanza** cuando la regla depende de filas vecinas.
  Ejemplo: una regla que mira si el día siguiente está bloqueado necesita *además* un
  trigger sobre los bloqueos, que barra la fila vecina cuando el bloqueo aparece, se mueve o
  se da de baja después.
- **`SECURITY DEFINER`** en las funciones que usan los triggers: la regla tiene que
  resolverse igual la dispare un admin con sesión, un cron o un import.
- Documentar en la migración si la regla es **best-effort** (se aplica al escribir, no es
  retroactiva entre filas distintas). Si no se documenta, alguien lo va a reportar como bug.

---

## 7. Fechas: la trampa más cara

Regla dura, salida de un bug que dejó 19 filas mal en producción:

> **`AT TIME ZONE` se aplica a `now()` y a columnas `TIMESTAMPTZ`. NUNCA a una columna
> `DATE`.**

Una columna de fecha calendario no tiene hora ni zona; convertirla resta horas y la corre al
día anterior. En el caso real, eso **invirtió** un chequeo de día de la semana: los domingos
se leían como sábado y los lunes como domingo. Además, la consulta con la que se "verificó"
el arreglo tenía el mismo bug, así que confirmó un resultado falso.

Corolarios:

- Verificar los backfills **contra el dato de origen**, no contra lo que se acaba de
  escribir, y con una consulta escrita distinto de la que causó el problema.
- En JavaScript, para hacer aritmética con fechas calendario, anclarlas a **mediodía local**
  (`new Date(y, m, d, 12)`): evita que un cambio de huso corra el día.
- Guardar la zona horaria del negocio en una variable (`NEXT_PUBLIC_TZ`) y usarla en todo
  cálculo de "hoy".

---

## 8. supabase-js no lanza excepciones

```ts
// MAL: el catch nunca se ejecuta; el error se pierde para siempre.
try { await supabase.rpc("tarea_de_mantenimiento"); } catch {}

// BIEN: supabase-js RESUELVE con { data, error } ante un error de Postgres.
const { error } = await supabase.rpc("tarea_de_mantenimiento");
if (error) resultado.errores.push(`tarea_de_mantenimiento: ${error.message}`);
```

Un permiso faltante en una función de mantenimiento quedó indetectable durante semanas por
este motivo. Todo cron devuelve en su respuesta JSON qué hizo y qué falló.

Otra trampa de PostgREST: **`.neq("col", "X")` descarta también las filas con `col IS NULL`**
(semántica SQL de NULL). Para "todo lo que no sea X, incluidos los nulos":
`.or("col.is.null,col.neq.X")`.
