# Fase 0 — Intake y plan

Única fase interactiva. Termina con `docs/PLAN.md` aprobado. Después: modo auto.

---

## 1. Cuestionario (una sola ronda)

No preguntar lo que el usuario ya dijo. Lo que falte se pide junto, en un solo bloque de
hasta 4 preguntas, cada una con opciones y **una marcada "(recomendada)"**.

### 1.1 Nombre del negocio — OBLIGATORIO

Si no lo dieron, es la primera pregunta y es abierta (no hay opciones que sugerir).
Pedir además: rubro en una línea y si el nombre comercial difiere de la razón social
(hace falta para el pie legal de la landing).

Se usa en: nombre del proyecto, `package.json`, marca del shell, `<title>`, `manifest.ts`,
JSON-LD, pie de la landing, correo del dominio, textos de `/privacy` y `/terms`.

### 1.2 Operatoria actual

Qué se pregunta y para qué sirve:

| Pregunta | Decide |
|---|---|
| ¿Quiénes usan el sistema y qué hace cada uno? | Niveles de usuario y gating de módulos |
| ¿Con qué trabajan hoy? (planilla, WhatsApp, papel, otro software) | Importadores necesarios (CSV, contactos) y qué migrar |
| ¿Cuáles son los 3 dolores principales? | Orden de las fases 4 y 6 |
| ¿Qué información se pierde o se carga dos veces hoy? | Dónde va la automatización de verdad |
| ¿Hay algo que hoy se hace a mano y NO quieren automatizar? | Respeto de los límites del negocio |
| ¿Cuál es el "día típico" de la persona que más lo va a usar? | Cuál es la pantalla de aterrizaje |

**Default si no contestan:** la pantalla de aterrizaje es el módulo operativo principal
(agenda/calendario/pipeline), no un panel de tarjetas. El panel de módulos queda en una ruta
aparte, accesible desde el logo.

### 1.3 Estilo del frontend

Ofrecer los 4 presets de `04-diseno-frontend.md` con una línea de descripción cada uno.
Preguntar además (si no lo dijeron):

- ¿Tienen colores de marca / logo? (hex, o "no").
- ¿Se usa más en celular o en escritorio? → decide si se diseña mobile-first o denso.

**Default:** preset `técnico neutro`, mobile-first con densidad alta en escritorio.

### 1.4 Aplicaciones a conectar

Menú (multi-selección):

- **WhatsApp** — Meta Cloud API (recomendado: es el canal directo y tiene plantillas) o
  Twilio (más rápido de arrancar, más caro por mensaje, sin verificación de empresa).
- **Correo** — lectura por IMAP (facturas, confirmaciones, notificaciones de plataformas)
  y/o envío transaccional.
- **Instagram / Messenger** — Instagram Messaging API (misma app de Meta que WhatsApp,
  webhook `messages` sobre la cuenta profesional vinculada a una página).
- **Calendarios** — iCal entrante (importar ocupación) y/o saliente (publicar el propio).
- **Pagos / facturación** — pasarela local, o solo registro manual.
- **IA** — clasificación de textos, chatbot, resúmenes.
- **Planillas** — importador CSV/Sheets de datos históricos.

Por cada una, anotar en el plan: **qué credencial hace falta, quién la consigue y cuánto
tarda el alta** (la verificación de empresa de Meta puede tardar días y bloquea la fase).

**Default:** WhatsApp por Meta Cloud API + IA con una sola clave (Anthropic o Gemini),
el resto en fases posteriores.

### 1.5 Escala y roles

- Cantidad de usuarios internos y si hay más de una organización/sucursal/franquicia.
- Si clientes finales interactúan (chat, formulario, link público sin login).
- Volumen aproximado de registros por mes (decide si algo necesita paginar de verdad).

**Default:** 3 niveles (`global` / `admin` / `operativo`), multi-tenant por `id_org` con una
sola organización al inicio.

### 1.6 Tecnología del frontend

Muchos usuarios **no saben** qué es React, Angular o Next.js — y está bien. La pregunta se
hace **con el beneficio de cada opción en una línea**, no como sigla suelta, y con una
recomendación explícita. Opciones a ofrecer (detalle y tabla comparativa en
`01-stack-y-arquitectura.md` §0):

| Opción | En una línea, para el intake |
|---|---|
| **Next.js + React (recomendada)** | La más usada para paneles; la pantalla llega ya armada del servidor (rápida en celular) y lee la base sin API intermedia. Es el stack de esta skill: los errores conocidos y las fases están hechos para él. |
| **React solo (Vite)** | Más simple de arrancar, todo en el navegador; sirve para apps chicas detrás de login, pero arranca más lento en móvil y hay que armar auth y ruteo a mano. |
| **Angular** | Muy estructurado, pensado para equipos grandes y apps corporativas de larga vida; más código y más curva para lo mismo. |
| **Vue / SvelteKit** | Livianos y agradables de escribir; ecosistema y material de ayuda más chicos. |
| **No sé / elegí vos** | Se usa la recomendada. |

**Default:** `Next.js + React`. Si el usuario elige otra, se anota en `docs/DECISIONES.md` y
**el plan lo dice explícito**: la skill deja de aplicar al pie de la letra (fases y errores
son de Next), pasa a ser orientativa, y hay que rehacer a mano lo que la skill da resuelto.
No hay que desalentar la elección, pero sí dejar claro el costo.

---

## 2. Cómo dar sugerencias

Regla: **nunca un menú neutro**. Cada punto abierto se presenta como
*"recomiendo X porque Y; la alternativa es Z, que conviene si W"*.

Sugerencias que casi siempre aplican y conviene ofrecer sin que las pidan:

1. **Multi-tenant desde el día 1** aunque hoy haya un solo negocio: RLS retrofiteada es una
   reescritura, y habilita vender/replicar el sistema después.
2. **Baja lógica en todo** (`fecha_baja`), nunca `DELETE` físico: los históricos sostienen
   las estadísticas y los borrados rompen FKs.
3. **Un log de comunicaciones unificado** (canal como columna, no una tabla por canal): la
   conversación con una persona es una sola aunque venga por WhatsApp, SMS o Instagram.
4. **Interruptores por tipo de mensaje saliente, default apagado**: evita el día en que una
   prueba manda 200 mensajes reales.
5. **Bandeja "Necesita atención"** como filtro por defecto en todo módulo que ingiera datos
   automáticos. El 80 % del uso es "¿qué tengo que decidir?", no scrollear historial.
6. **Pantalla única para el rol operativo**: quien limpia/entrega/atiende no navega un menú;
   ve su lista del día y un botón.
7. **Modo oscuro desde el principio** (es un sistema de tokens, no un `dark:` por clase; el
   costo de agregarlo después son cientos de clases).
8. **Cron diario + botón "actualizar ahora"**: el plan gratuito de Vercel solo permite crons
   diarios; el botón cubre el resto y además sirve para probar.
9. **Todo lo ajustable, en una tabla de configuración por organización, no en código**:
   textos de la landing, horarios, políticas, los datos del titular, el contexto de un
   chatbot. La prueba: dar de alta una organización nueva no debería tocar una línea de
   código. Un dato de negocio hardcodeado, en multi-tenant, termina saliéndole a otra
   organización.
10. **Región de Vercel = región de Supabase, decidido en la Fase 1.** Es gratis ahora y es
    la causa más común de que un proyecto con este mismo stack "se sienta lento". Va en el
    plan como decisión tomada, no como algo a revisar después (`09-rendimiento.md`).

---

## 3. Plantilla de `docs/PLAN.md`

```markdown
# Plan — <NOMBRE DEL NEGOCIO>

## 1. Qué es y cómo opera hoy
<2-3 párrafos: negocio, quién hace qué, herramientas actuales, dolores>

## 2. Qué resuelve el sistema (alcance v1)
- Dolor 1 → módulo/feature
- Dolor 2 → ...
- Fuera de alcance v1 (y por qué)

## 3. Modelo de dominio
Entidades, relaciones y cardinalidades.
### Invariantes duras (van a la base, no al código)
1. ...
2. ...

## 4. Módulos y navegación
| Sello | Módulo | Color | Rol que lo usa | Fase |
|---|---|---|---|---|

## 5. Roles y permisos
| Nivel | Ve | Puede |
|---|---|---|

## 6. Integraciones
| App | Proveedor | Credencial necesaria | Quién la consigue | Bloquea a |
|---|---|---|---|---|

## 7. Estilo visual
Preset elegido, paleta (hex), tipografías, densidad, referencia visual.

## 7b. Stack y hosting
Tecnología de frontend elegida (y, si no es Next.js + React, qué de esta skill deja de
aplicar). Región de Supabase y región de Vercel — **la misma** (`09-rendimiento.md` §1).
Plan de cada servicio (Vercel Hobby, Supabase free) y qué condiciona.

## 8. Automatizaciones — qué SÍ y qué NO
| Flujo | Automático | Manual con botón | Motivo |
|---|---|---|---|

## 9. Fases y criterios de aceptación
Fase 1 … Fase 8, con qué se considera terminada cada una.

## 10. Riesgos conocidos que aplican
Sacados de references/07-errores-conocidos.md, con la mitigación ya decidida.

## 11. Decisiones tomadas por default (sin preguntar)
Las que el modo auto va a asumir. El usuario puede vetarlas ahora; después se ejecutan.
```

---

## 4. Del intake al modelo de dominio

Método rápido y confiable:

1. **Sustantivos del relato** → entidades candidatas ("reserva", "depto", "limpieza",
   "gasto", "operaria").
2. **Verbos del relato** → transiciones de estado ("se confirma", "se realiza", "se paga").
   Cada verbo es un estado o una columna de fecha, no una tabla nueva.
3. **"¿Qué no puede pasar nunca?"** → invariantes. Esta pregunta es la más rentable de todo
   el intake: sale el doble booking, el pago duplicado, el solape de turnos.
4. **"¿Qué mira cada persona apenas abre el sistema?"** → pantalla de aterrizaje por rol.
5. **"¿Qué se rompe si dos personas hacen lo mismo a la vez?"** → dónde hace falta un
   reclamo atómico (ver `07-errores-conocidos.md`).

---

## 5. Catálogo de módulos (elegir del intake, no inventar)

| Sello | Módulo | Para qué | Señal de que hace falta |
|---|---|---|---|
| CLI | Clientes / Contactos | Ficha, historial, agrupación | "los tengo en la agenda del celular" |
| AGE | Agenda / Calendario | Reservas, turnos, entregas | El negocio tiene fechas |
| PIP | Pipeline / Oportunidades | Estados de venta | "no sé en qué quedó cada consulta" |
| TAR | Tareas / Operación | Trabajo asignado a personas | Hay personal que ejecuta |
| INV | Inventario / Catálogo | Stock, productos, unidades | Hay cosas contables |
| FIN | Finanzas / Transacciones | Ingresos, egresos, conciliación | "no sé cuánto gané" |
| GAS | Gastos | Egresos categorizados | Facturas de servicios |
| PER | Personal | Altas, asignaciones, pagos | Más de 2 personas |
| COM | Comunicaciones | Bandeja unificada de chats | Hay WhatsApp/IG |
| COR | Correo | Ingesta de mails con extractores | Llegan datos por mail |
| EST | Estadísticas | KPIs y cruces | "quiero ver cómo viene el mes" |
| CFG | Configuración | Credenciales, plantillas, toggles | Siempre |
| ORG | Organizaciones | Alta de tenants | Multi-negocio |

Cada módulo lleva: sello de 3 letras, color propio del sistema, familia
(operación diaria / base y configuración / finanzas y análisis) y un flag on/off por
organización.
