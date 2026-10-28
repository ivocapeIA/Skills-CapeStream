---
name: nfc-card
description: Tarjetas personales de contacto para tarjetas NFC de Cape Stream (cape.stream/perfil?c=<código>), con el estilo de tapa de revista: nombre gigante en color, la persona recortada delante de las letras, dato destacado, barra fija con "Guardar contacto". Usar cuando pidan una tarjeta NFC o personal, sumar a una persona, cambiar el diseño de esas tarjetas, o tocar src/nfc.ts, perfil.html o NfcProfileEditor.tsx.
---

# nfc-card — tarjetas personales en la tarjeta NFC

## Cómo funciona hoy (no hace falta código para una persona nueva)

1. Panel → **Tarjetas NFC** (sólo superadmin) → crear la tarjeta o usar una en blanco.
2. **Armar tarjeta personal**: nombre, apellido, qué hace, frase, dato destacado
   ("8+" / "años de experiencia"), teléfono (también es el WhatsApp), mail,
   Instagram, web, color, fondo claro u oscuro, y la foto.
3. **Publicar tarjeta**: se ve en `cape.stream/perfil?c=<código>`. Si la tarjeta no
   tenía destino, pasa a mandar ahí sola. Si ya mandaba a otro lado, no se toca
   (el aviso lo dice) y se cambia con "Cambiar destino".
4. El chip lleva `cape.stream/t/<código>` (botón "Copiar link"). Grabarlo como
   registro URL con NFC Tools y bloquearlo.

**La foto define el diseño.** Un PNG sin fondo (el panel lo detecta mirando si
el borde es transparente) pone a la persona *delante* del nombre gigante, como
en una tapa. Una foto con fondo ocupa la portada y el nombre baja encima de un
fundido. Para sacar el fondo: en el iPhone, mantener apretada la persona en
Fotos → Copiar sujeto; si no, remove.bg o Canva. El panel achica la foto (1400
px), la guarda en PNG sólo si tiene transparencia y arma aparte una cuadrada de
480 px en JPG para la vCard.

Son datos personales de un tercero: cargar sólo lo que la persona o el usuario
pasó. No inventar teléfono ni mail, no buscarlos en internet.

## Dónde está cada cosa

| Pieza | Archivo |
|---|---|
| Rutas, normalización, vCard | `server/src/nfc.ts` (`normalizeNfcProfile`, `buildVcard`, `/pub/nfc/:code`, `/pub/nfc/:code/vcf`, `PUT /api/admin/nfc/:code/profile`, `POST /api/admin/nfc/:code/photo`) |
| Columnas | `profile` (JSON), `photo_key`, `avatar_key`, `photo_cutout` en `nfc_cards` — migración `0024_nfc_profiles.sql` y `schema.sql` |
| Página pública | `server/panel/public/perfil.html` (estática, lee el JSON; `noindex` en `_headers` y `robots.txt`) |
| Formulario y foto | `server/panel/src/NfcProfileEditor.tsx`, montado desde `NfcSection.tsx`; estilos `.nfc-*` en `styles.css` |
| Pruebas | `server/scripts/test-nfc.ts` |

Las fotos van a R2 (`nfc/<código>/<uuid>`) y se sirven por `/pub/media/` con
`immutable`: cada subida usa una clave nueva y borra la anterior. Borrar la
tarjeta borra sus dos fotos.

## Si hay que tocar el diseño de perfil.html

Leer antes la skill `uxui-frontend`. Lo que no hay que romper:

- El nombre se ajusta por JS (`fitName`): cada renglón ocupa el ancho, con un
  tope de alto (34 % de la portada). Se mide después de `document.fonts.ready`
  (Anton), con 1,5 s como mucho.
- Capas de la portada: aura (z 0) → nombre (1) → persona (2) → fundido (3) →
  grano (4, y el nombre del modo foto) → dato (5) → botones de arriba (6).
- Todo dato del usuario entra con `textContent` o en `href` armados acá
  (`wa.me/<dígitos>`, `tel:+<dígitos>`, `mailto:`, Instagram validado). El color
  ya llega validado como `#rrggbb` porque va dentro de un `style`.
- Texto de los botones sobre el color: `onColor()` elige blanco o negro.
- Tiene que verse bien a 320, 360 y 390 px, sin scroll horizontal, y con
  `prefers-reduced-motion`.
- `og:*` no se puede personalizar: la página es estática y los datos llegan
  después. Si algún día hace falta la vista previa con foto en WhatsApp, eso
  pide que el Worker responda la página (y entonces `_headers` deja de aplicarse:
  ver CLAUDE.md, punto 3).

## Las tarjetas viejas

`nombre-apellido` (las tarjetas viejas) son HTML a mano en
`panel/public/`. Quedan funcionando; pasarlas al formato nuevo es el paso
`#app-nfc-migrar-viejas` de `docs/proyectos.md`. No crear tarjetas nuevas así.

## Verificar

- `cd server && npm test && npm run typecheck && npm run build`.
- En local: la D1 local se crea desde `schema.sql` sin registro de migraciones,
  así que una migración nueva se aplica con `wrangler d1 execute signage-db
  --local --file=migrations/00xx_….sql`. Si `wrangler dev` arrancó durante un
  build y `/panel` da 404, tocar `dist/panel.html` para que relea los archivos.
- Abrir `/perfil?c=<código>` a ancho de celular, bajar la vCard (que traiga la
  foto) y probar `/t/<código>` → 302 al perfil.
- Un push a master despliega y aplica la migración: no commitear ni pushear sin
  que el usuario lo pida.
