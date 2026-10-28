# Landing pública y páginas legales

La landing **no es decorativa**. Es lo que revisan Meta, Google y cualquier plataforma antes
de habilitar una integración, y lo que define la identidad pública del negocio. Un
desalineamiento entre lo que dice la web y lo que dice el registro fiscal alcanza para que
te den de baja una cuenta ya aprobada — pasó.

---

## 1. Qué lleva la landing

**Obligatorio:**

1. **Nombre del negocio** (el que se pidió en el intake) como marca visible y en el `<title>`.
2. **Qué hace, en una frase**, en el H1. Sin marcas ajenas (ver §4).
3. **Prueba de que el producto existe**: capturas o, mejor, **réplicas funcionales** de dos
   pantallas reales del producto (un calendario clickeable, una conversación con su ritmo).
   Usan los mismos tokens y colores de módulo que la app, así que lo que ve el visitante es
   el producto y no una ilustración genérica.
4. **Contacto**: WhatsApp o formulario, teléfono, correo **del mismo dominio del sitio**.
5. **Pie con la ficha legal en texto plano**: nombre legal, identificación fiscal, condición
   fiscal, domicilio completo (con código postal), teléfono y correo del dominio.
6. **JSON-LD `LocalBusiness`** con `legalName`, `taxID`, `address`, `telephone`, `url`: un
   revisor automático lo lee sin depender de la maqueta.
7. **Enlaces a `/privacy` y `/terms`** (y a `/eliminar-datos` si hay mensajería).
8. **Acceso al panel** (botón "Ingresar" → `/login`).

**Fuente única**: todos esos datos viven en `lib/empresa.ts` y de ahí los toman el pie, el
JSON-LD, `/privacy` y `/terms`. Si cambia uno, cambia en todos lados.

> Detalle real que costó un rato: el teléfono en el enlace `tel:` y los dígitos de `wa.me`
> pueden no ser la misma cadena (el "9" argentino). Mismo número, distinta representación:
> dos constantes.

**Comportamiento:** un visitante sin sesión ve la landing; uno con sesión va directo al
dashboard. La raíz se agrega a las rutas públicas del middleware con **comparación exacta**
(`pathname === "/"`), nunca por prefijo.

---

## 2. `/privacy`

Secciones mínimas (redactadas para el país del negocio; para Argentina, Ley 25.326 y la
mención de la AAIP):

- Ficha del responsable arriba de todo (los mismos datos del pie).
- Qué datos se recopilan: de usuarios internos, de clientes finales, de la operación.
- **Finalidad y base del tratamiento.**
- Uso de la plataforma de mensajería (si aplica) y qué se guarda de esas conversaciones.
- Proveedores con los que se comparten datos, nombrados (hosting, base de datos,
  mensajería, IA) y **transferencia internacional de datos**.
- Cookies (aunque sean solo sesión y tema).
- **Retención con plazos reales**, no "el tiempo necesario".
- **Cómo eliminar tus datos**: canal concreto y plazo de respuesta.
- Derechos, menores, cambios de la política.
- Fecha de última actualización.

Regla: **no prometer lo que el sistema no cumple.** Si la política dice que se puede pedir la
baja escribiendo una palabra, esa palabra tiene que estar implementada; si todavía la procesa
una persona, decir eso.

---

## 3. `/terms` y `/eliminar-datos`

**`/terms`** (Meta lo pide junto con la privacidad): para quién es el servicio, uso
aceptable, propiedad de los datos de cada organización, disponibilidad, tarifas (y dónde se
acuerdan), limitación de responsabilidad, baja de cuentas, ley aplicable y jurisdicción.

**`/eliminar-datos`** + su callback: las plataformas de Meta piden una "Data Deletion Request
URL". Llega un `signed_request` firmado con el app secret (`<firma>.<payload>` en base64url,
HMAC-SHA256 sobre el payload) y se espera `{ url, confirmation_code }`. Si el sistema no
guarda identificadores de esa red social, la respuesta honesta es "sin datos asociados a ese
ID" y el código de confirmación se **deriva** del user_id (HMAC con el mismo secreto) en vez
de guardarse en una tabla. Las dos rutas van en las rutas públicas del middleware.

---

## 4. Alineación de identidad (esto da de baja cuentas)

Aprendido a la mala: una cuenta de WhatsApp Business recién dada de alta fue dada de baja
—y la apelación rechazada— **sin haber enviado un solo mensaje**. No se evaluó la conducta,
se evaluó el alta. Las dos causas encontradas al auditar el sitio:

1. **Marca ajena usada como propia.** El H1 decía "Tu *Airbnb*, administrado de verdad" y la
   meta description lo repetía. Una marca de terceros en el título, la descripción o el H1 es
   exactamente lo que las políticas llaman *misrepresent your affiliation*. Corrección: el H1
   habla del producto propio y los canales de terceros se nombran solo como integraciones
   ("venga del canal que venga — X, Y o una reserva directa"), que es **uso nominativo
   legítimo**.
2. **Dos negocios distintos en el mismo sitio.** La landing se presentaba como la empresa que
   opera, y `/privacy` como una plataforma SaaS usada por otras organizaciones. Un revisor que
   cruza sitio ↔ información de negocio ↔ constancia fiscal ve una contradicción. Corrección:
   **un solo negocio en todo el sitio**; si además la plataforma la usan terceros, se aclara
   que cada organización conecta **sus propias** cuentas de mensajería y responde por los
   datos de sus clientes (esto es lo que mantiene al proyecto fuera de la categoría
   "Solution Provider", que tiene otro régimen de alta).

Checklist de alineación antes de pedir cualquier verificación:

- [ ] Nombre legal, domicilio, teléfono y correo del sitio **coinciden exactamente** con la
      información de negocio cargada en la plataforma y con la constancia fiscal.
- [ ] El correo de contacto es del **mismo dominio** del sitio (no Gmail/Yahoo).
- [ ] Ninguna marca ajena en `<title>`, meta description, H1, `manifest` ni nombre de la app.
- [ ] Ninguna otra razón social ni otro rubro alojado en el mismo dominio (una landing vieja
      de otro emprendimiento en una ruta olvidada es una contradicción directa).
- [ ] La política de privacidad y los términos son alcanzables **sin sesión** y sin JS.
- [ ] Lo que la política promete (baja, borrado, retención) está implementado.
- [ ] Si el dominio contiene una palabra que evoca una marca ajena, saberlo y decidirlo
      explícitamente: es un vector que queda en pie.

---

## 5. PWA y metadatos

- `manifest.ts` con `display: "standalone"` (es lo correcto para una app de gestión:
  saca el navegador y deja la barra de estado del sistema; `fullscreen` es para juegos y en
  iOS ni siquiera se soporta).
- `theme_color` y `background_color` **de la paleta real** (el color de marca y el fondo del
  body), o la barra de estado y el splash quedan de otro color.
- `start_url` al dashboard, no a la raíz: la app instalada no debería abrir la landing.
- `id`, `display_override`, `categories` y accesos directos (mantener presionado el ícono).
- El `<meta name="theme-color">` se reaplica al montar cada pantalla si la navegación
  recarga la página entera.
