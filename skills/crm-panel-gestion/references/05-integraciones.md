# Integraciones

Regla transversal: **el código de negocio nunca sabe quién manda el mensaje**. Una fachada
de envío y una función de "qué contestar"; cada proveedor es un adaptador. Cambiar de
proveedor tiene que ser una pantalla de configuración, no un refactor.

---

## 1. WhatsApp

### Elegir proveedor

| | Meta Cloud API | Twilio (u otro BSP) |
|---|---|---|
| Costo | Más barato | Más caro por mensaje |
| Alta | Verificación de empresa (días) | Minutos |
| Ventana de 24 h | Sí, obligatoria | Sí, pero el BSP la abstrae |
| Plantillas | Aprobadas por Meta | Idem |
| Webhook | GET de alta + firma `X-Hub-Signature-256` | Firma `X-Twilio-Signature` |
| Respuesta | Por API | TwiML en la misma respuesta HTTP |

Recomendación: arquitectura **multi-proveedor desde el principio** aunque se arranque con
uno. Cuesta poco al inicio y evita quedarse sin canal si una cuenta se cae.

### Arquitectura

```
lib/whatsapp/
├── tipos.ts        # Cuenta (credenciales de ambos + cuál está activo), MensajeEntrante, ResultadoEnvio
├── enviar.ts       # FACHADA: elige proveedor, resuelve ventana 24 h, chequea baja y tipo, loguea
├── entrante.ts     # TODA la lógica del bot. Devuelve QUÉ contestar; el transporte lo decide el webhook
├── meta.ts         # Adaptador Meta (firma, envío, marcar leído, "escribiendo…")
├── twilio.ts       # Adaptador Twilio
├── cuenta.ts       # Resolución de credenciales por secreto de URL / phone_number_id / organización
├── plantillas.ts   # Ventana de 24 h y elección de plantilla
├── tiposEnvio.ts   # On/off por tipo de saliente, por organización
└── optout.ts       # BAJA / ALTA / eliminación de datos
```

### La ventana de 24 h (Meta)

Fuera de las 24 h del último mensaje **de la persona**, no se puede mandar texto libre.
Por eso **todo mensaje proactivo declara un "uso"** (`aviso_operativo`, `resumen_semanal`,
`aviso_urgente`, `aviso_admin`) y la fachada decide: dentro de la ventana va texto libre;
fuera, la plantilla aprobada que el admin cargó para ese uso. Si Meta rechaza por ventana
justo en el medio, se reintenta con la plantilla.

Los usos son una **unión fija en el código**, no una lista editable desde la UI: cada uno
tiene su disparador ya escrito en un punto concreto de la app. Agregar un aviso nuevo
requiere programar ese disparador primero — la pantalla no puede inventar un quinto.

Las plantillas se pueden **sincronizar** (traer las `APPROVED` de la cuenta) y **crear**
desde la app (`POST /{waba_id}/message_templates`, un componente BODY, variables `{{1}}`
correlativas, categoría `UTILITY` para avisos operativos). Queda `PENDING` en Meta; la
aprobación tarda de minutos a días y no depende de la app.

### Interruptores por tipo, default apagado

Tabla `whatsapp_tipo_envio` (organización × tipo × habilitado). La fachada omite el envío si
el tipo está apagado y deja un skip tipado en el log. Esto es lo que evita que una prueba
mande 200 mensajes reales.

Además: **kill switch global** por constante, para cortar todo lo saliente en un deploy
cuando algo se descontrola.

### Opt-out real (obligación legal y de plataforma)

- "BAJA" corta los mensajes proactivos a ese número; "ALTA" los devuelve. "ELIMINAR MIS
  DATOS" registra el pedido como fila y avisa al equipo.
- **La detección compara frases contra el mensaje COMPLETO**, no por substring: buscar
  "baja" adentro del texto daría de baja a quien escriba "la baja presión del agua". Una
  frase inconfundible ("eliminar mis datos") sí puede ir por substring.
- La fachada de envío consulta la baja **antes de cada mensaje proactivo** y deja el intento
  en el log con estado `no_enviado_baja`, para que en el panel se vea por qué faltó ese
  aviso.
- Excepción `ignorarBaja` **solo** en las respuestas a un mensaje entrante: la conversación
  la inició la otra persona, y sin esa excepción la propia confirmación de la baja quedaría
  bloqueada.
- Ojo con el ciclo de imports: si `enviar.ts` importa `optout.ts`, el aviso a los admins va
  en `entrante.ts`, no en `optout.ts`.

### Teléfonos

Canonizar a **E.164** (solo dígitos, 8–15) al guardar y antes de enviar, **sin adivinar el
código de país**. Comparar siempre por dígitos: `+54 9 11 5555-1234` cargado a mano y
`5491155551234` del webhook son el mismo número.

### Chatbot de atención (si aplica)

Reglas duras **por código, no por prompt** (un prompt no es un control de seguridad):

- Sin sesión verificada no responde nada: pide el identificador (código de reserva, DNI,
  número de pedido) y lo busca **solo dentro de la organización del webhook**.
- Al contexto del modelo entra **solo** el registro verificado y su entidad relacionada:
  filtrar datos de otro cliente es imposible porque nunca están en el prompt.
- Los datos sensibles (claves de acceso, direcciones) se inyectan al contexto **solo en la
  ventana temporal correcta** (ej. desde las 13:00 del día de check-in). Antes de eso el
  modelo ni los conoce.
- Tope de intentos de verificación y de llamadas al modelo (ver `03-seguridad.md`).
- Degradación: sin clave de IA o si el modelo falla, responde "lo reviso y te confirmo" y
  **avisa al equipo**; el cliente nunca queda sin respuesta.
- **Si le preguntan si es un bot, lo confirma.** Negarlo es una mala práctica y en varias
  plataformas es incumplimiento.
- Ritmo humano: demora antes de contestar, proporcional al largo de la respuesta
  (~18 caracteres/segundo simulados, piso ~1,2 s, techo ~20 s, con ruido aleatorio) y una
  demora mayor en el primer contacto. Con Meta, marcar "leído" + indicador "escribiendo…"
  **cuando arranca a escribir**, no al recibir: un visto instantáneo seguido de una
  respuesta que tarda dos minutos delata el sistema igual que una respuesta instantánea.
- Poder **pausar el bot en un chat puntual** desde el panel (una tabla de presencia), además
  del interruptor global: el mensaje se sigue viendo, lo contesta una persona.
- Los mensajes que llegan durante la demora se **anexan al mismo lote sin reiniciar el
  reloj**: se contesta todo junto.

### Contexto en capas — y CERO datos del negocio en el prompt de código

Lo que el bot sabe sale de **tres niveles con límites claros**. Mezclarlos es el error:

1. **Reglas duras** — en el prompt escrito a mano, y **no editables desde la app**: cuándo
   puede entregar datos sensibles (claves, direcciones) y en qué ventana temporal, qué hace
   ante una urgencia, no contestar temas ajenos al servicio. Son las que protegen al cliente
   y al negocio; en un textarea, un error de tipeo las apaga.
2. **Contexto general de la organización** — una tabla de config (`chatbot_config`: un campo
   de texto libre que vale para todo + cómo se presenta si le preguntan si es una IA),
   **editable desde una pantalla**. Acá va TODO lo que es de este negocio: horarios,
   políticas, el nombre con el que se presenta. Vacío = una frase genérica armada con el
   nombre de la organización, **nunca** con el de otra.
3. **Banco por entidad** (`info_huespedes` del apartamento, ficha del cliente…) — lo
   específico de cada unidad, y **manda** si contradice al general. Decírselo al modelo
   explícito en el prompt.

Reglas que salen de un bug real (el nombre del titular hardcodeado en el prompt, que en
multi-tenant se le habría mostrado a otra organización):

- **Ni un dato del negocio en el prompt de código.** Nombre, teléfono, horarios, frase de
  presentación: todo sale del nivel 2. El código solo lleva reglas que valen para todos los
  tenants.
- **El contexto editable entra como INFORMACIÓN y ANTES del bloque de REGLAS**, nunca
  después: es texto que escribe un admin, y detrás de las reglas podría pisarlas. El orden
  del prompt es la defensa.
- **Tope de largo del texto libre en la BASE** (`CHECK`), no solo en la UI: el prompt se
  arma en el webhook y un texto gigante ahí es costo y latencia en cada mensaje.
- **La lectura de la config nunca tira**: si falla, devuelve vacío y el bot sigue con el
  banco por entidad. Degradar, no romper.
- **El módulo con el tipo y los topes de esa config es puro** (sin imports de servidor): la
  pantalla es un componente de cliente, e importar el módulo que hace `cookies()` /
  `next/headers` le arrastra eso al bundle — `tsc` pasa y `npm run build` se cae (ver
  `07-errores-conocidos.md` **F9**).

---

## 2. Correo entrante (IMAP)

Sirve para ingerir lo que hoy llega por mail: facturas de servicios, confirmaciones de
plataformas, notificaciones. `imapflow` + `mailparser`.

- Credenciales por organización (usuario + **contraseña de aplicación**) cargadas desde una
  pantalla. Al guardar, **sacar TODOS los espacios de la contraseña**: los proveedores la
  muestran agrupada de a 4 caracteres para leerla mejor y no son parte del valor real.
- **Buscar por fecha (`since`), nunca por "no leído".** El flag de leído lo toca cualquier
  cliente que abra la casilla; un mail que el dueño abrió queda invisible para siempre. La
  idempotencia la da el `UNIQUE` de `message_id`, así que reprocesar una ventana es
  inofensivo y barato. Y **no marcar los mails como leídos**: es la bandeja real de alguien.
- **Pipeline en cascada por confianza:** 1) extractor determinístico por asunto conocido →
  2) extractor por header de plantilla del remitente (más estable que el asunto y ajeno al
  idioma) → 3) patrón ya aprobado para esa organización → 4) clasificación con IA, que queda
  `pendiente_revision` → 5) degradación por palabras clave.
- **Separación de seguridad clave:** "aprobar un patrón" decide solo si un mail necesita que
  un humano lo mire la próxima vez. **Nunca habilita que la IA escriba sola campos de
  negocio** (montos, fechas, cancelaciones): esa escritura es exclusiva de extractores
  determinísticos calibrados a mano.
- **Si falta un campo crítico, el mail NO se cierra como aplicado**: queda
  `revisar_manual` con un aviso claro y aparece en "Necesita atención". Cerrar como
  "aplicado" un mail sin monto dejó 10 registros vacíos durante semanas sin que nadie se
  enterara.
- **Reintentos**: un mail suele llegar **antes** de que exista el registro con el que
  matchea. Barrido que reprocesa el cuerpo ya guardado (no hace falta volver a IMAP) al
  final de cada sync y apenas entren registros nuevos. La condición de reintento es
  **"todavía no escribió nada"** (`id_relacion IS NULL`), **no el estado**: si un extractor
  *acumula* (suma a un total), reprocesarlo sumaría dos veces. Topes: ventana de días,
  intentos por mail y cantidad por corrida.
- Calibrar los parsers contra **mails reales** y guardar el cuerpo crudo: el mismo mail
  reenviado desde otro cliente llega con la tabla HTML convertida a líneas separadoras
  sueltas, y "el valor está en la línea siguiente" deja de ser cierto. Un extractor de
  etiqueta→valor tiene que cubrir: valor en la misma línea, valor en la siguiente, y ruido
  de tabla en el medio.
- Papelera con borrado en dos pasos + purga automática a los N días, respetando las
  categorías que alimentan otros módulos.

---

## 3. Instagram / Messenger

Misma app de Meta que WhatsApp; el webhook es el mismo endpoint con otro campo suscripto.

- La cuenta de Instagram tiene que ser **profesional y estar vinculada a una página**.
- Webhook: firma `X-Hub-Signature-256` igual que WhatsApp; el payload trae `entry[].messaging[]`
  en vez de `entry[].changes[]`.
- **Ventana de 24 h** también (con etiquetas de mensaje para casos puntuales), y los mismos
  límites: nada de mensajería masiva.
- Encaja en la misma bandeja unificada: el canal es una **columna** del log, no una tabla
  aparte. La conversación con una persona es una sola aunque salte de canal.
- Permisos que requieren App Review: planificar el tiempo antes de prometer la fecha.

---

## 4. Calendarios (iCal)

**Entrante**: importar la ocupación de plataformas externas.
- Feed por URL cargada por el admin → validación anti-SSRF obligatoria (`03-seguridad.md`).
- Dedup por `UID`; guardar además el **código externo** en su propia columna: si solo se usa
  como clave de dedup, después nada permite cruzar ese registro con el resto del sistema
  (bug real: ninguna reserva tenía código y el bot rechazaba a todos los clientes).
- **Detección de cancelaciones** (lo que desapareció de todos los feeds), con guardas
  defensivas: no cancelar nada si algún feed falló al leerse, ni si vinieron 0 eventos
  (glitch), y solo dar de baja lo futuro.
- Insertar **después** de dar de baja: un evento que corrió sus fechas choca contra el
  constraint de solape con su propia versión vieja.
- Inserción resiliente fila a fila: un evento que solapa no puede abortar el feed entero; se
  reporta el conflicto.

**Saliente**: publicar el propio calendario.
- Ruta pública con **token aleatorio**, sin sesión (los agregadores lo leen anónimos).
- `SUMMARY` genérico (nada de nombres de clientes).
- CRLF y plegado de líneas a **75 octetos, no caracteres**: una "ñ" ocupa dos y plegar mal
  corta la línea.

---

## 5. Capa de IA

Una sola capa (`lib/ia/proveedor.ts`) con **salida estructurada** (`generarJSON` con
esquema). Orden: proveedor primario si hay clave; si no hay o falla, el secundario; si
tampoco, **degradación explícita**.

- **Loguear TODOS los fallos** con `console.error("[IA] ...")`: clave inválida, cuota, red,
  status y cuerpo de la respuesta, negativa del modelo, 200 sin texto, JSON inválido. Un
  `catch {}` mudo hizo imposible diagnosticar el mismo síntoma dos veces.
- Los nombres de modelo caducan y algunos **no están disponibles para cuentas nuevas** aunque
  figuren en el listado: preferir alias estables y tener fallback ante 404.
- No mandar campos de configuración que el proveedor pueda dejar de aceptar (un parámetro
  obsoleto tiró 400 en **todos** los modelos).
- Costo: ver rate limiting en `03-seguridad.md`. Y las funciones caras (resumir una
  conversación) van **bajo demanda con un botón**, nunca precalculadas para todos.
- Cuando el resultado tiene que ser siempre positivo y humano (un texto que se publica),
  evaluar **formatos fijos elegidos al azar** en vez de IA: no depende de una clave, no
  inventa nada y el tono está garantizado.

---

## 6. Importadores (CSV / planillas)

- Parsear el archivo **real** del cliente, no el ideal: separador `;`, decimales con coma,
  fechas `MM/DD/YYYY`, columnas truncadas.
- **Dedup por clave natural completa** (código + tipo + monto + moneda + fechas), con el
  monto redondeado a los decimales de la columna. Las filas **sin** código también se
  deduplican: si no, cada reimport las duplica.
- El match contra entidades propias exige **candidato único**; si el prefijo matchea dos,
  queda "sin mapear" y se reporta. Nunca tomar el primero.
- Al completar un registro existente, exigir que esté **vacío** (`monto IS NULL`) y que no
  sea un placeholder: un registro cargado a mano que se superponga no se pisa, se reporta
  como conflicto.
- Reimportar tiene que ser **idempotente y corregir**: recalcular sobre todas las filas ya
  guardadas de esa clave, no sumar las del archivo actual.
- Una fila inválida se descarta y se cuenta; no aborta el import.
- **Modo "carga histórica"**: al dar de alta un cliente se importan períodos viejos, y cada
  registro dispararía el trabajo derivado automático (cientos de tareas "pendientes" con
  fechas de años atrás). Un checkbox marca esos derivados como ya realizados.

---

## 7. Pagos y facturación

- Registrar el movimiento **detectado** automáticamente, pero **cargarlo a finanzas con un
  botón manual** si la misma plata puede llegar por otra vía (un CSV mensual, una
  conciliación bancaria). Evita el doble conteo, que es el error más caro y el más difícil
  de detectar.
- Emitir un comprobante = **una sola transacción SQL** que junta lo pendiente, crea el
  movimiento y marca lo cobrado. Y que **respete todos los filtros que la pantalla muestra**:
  si la UI dice "según el filtro de sucursal", el endpoint tiene que recibir la sucursal, o
  paga de más (bug real).
- El botón de reimpresión **no se deshabilita** cuando ya está todo pagado: si hay pendiente,
  cobra y después imprime; si no, imprime desde lo que ya está en pantalla, sin tocar la
  base. Se puede apretar las veces que haga falta sin riesgo de cobrar dos veces.
- La impresión abre una pestaña con HTML autocontenido y dispara `window.print()`. La pestaña
  se abre **antes** del `fetch`: un `window.open()` después de un `await` ya no cuenta como
  gesto del usuario y el navegador lo bloquea.
