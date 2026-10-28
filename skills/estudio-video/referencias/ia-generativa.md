# IA generativa por API (niveles 1 y 2)

> **Estado: documentado, no implementado.** Por ahora el presupuesto es bajo y la skill trabaja en nivel 0. Esta página existe para que la opción aparezca en el brief y para que, el día que haya presupuesto, la integración siga un plan y no se improvise.

## Cuándo ofrecerla

- En la ronda 2 del brief, como opción de **presupuesto**, nunca como recomendada mientras el nivel 0 cumpla.
- Siempre con la advertencia: los modelos escriben mal el texto, cambian el producto o el logo de un plano a otro, y cada intento se cobra. Hacen falta 3 a 5 intentos para tener un clip que sirva.
- Para lo que no se puede filmar ni dibujar con código. Nunca para textos, logos, datos ni la placa final: eso lo sigue haciendo el motor.

## Proveedores (verificar precios y modelos el día que se use: cambian cada mes)

| Para qué | Opciones | Nota |
|---|---|---|
| Video, varios modelos con una sola cuenta | **fal.ai** (Veo, Kling, Seedance, Wan, LTX…), Replicate | La forma más simple de probar varios modelos sin abrir cuentas en cada uno |
| Video, proveedor directo | Google AI Studio / Vertex (Veo), OpenAI (Sora), Runway, Luma, Kling | Mejor precio por volumen; una key por proveedor |
| Imagen (fondos, producto en escena) | fal.ai (Flux, Recraft), Google (Imagen), OpenAI (gpt-image) | Mucho más barata que el video: siempre se prueba primero en imagen |
| Voz | ElevenLabs | Clonar la voz de alguien solo con su permiso por escrito |
| Música | Suno, Udio | Revisar qué permite el plan para uso comercial. La sintetizada propia no tiene ese riesgo |
| Local, sin pagar por uso | ComfyUI con Wan / LTX-Video / Flux | Necesita una placa de video con mucha VRAM; no corre en este contenedor |

## Cómo se va a integrar (plan para cuando se implemente)

1. **Key fuera del repo:** variable de entorno (`FAL_KEY`, `GEMINI_API_KEY`…). Nunca en `video.json`, el código ni un commit. En una sesión en la nube, la red del entorno tiene que permitir el dominio de la API (consultar `read_documentation` con el tema `environment.network`).
2. **Tope de gasto en `video.json`:** `"ia": { "proveedor": "fal", "tope_usd": 5 }`. El script suma el costo estimado de cada pedido y se niega a pasar el tope sin una confirmación explícita del usuario.
3. **Script `scripts/ia.mjs`** (a crear), con este contrato:
   - `node scripts/ia.mjs imagen "<prompt>" --id fondo-1` → `../material/ia/fondo-1.png`
   - `node scripts/ia.mjs video "<prompt>" --desde ../material/ia/fondo-1.png --dur 5 --id hook` → `../material/ia/hook.mp4`
   - Cada pedido queda en `../material/ia/registro.json`: fecha, proveedor, modelo, prompt, seed, duración, costo estimado y archivo.
4. **Flujo barato:** imagen primero (centavos), aprobación, después imagen a video (un solo clip), aprobación, y recién entonces el resto. Nunca generar en lote sin ver el primero.
5. **El clip entra como un clip más:** se declara en `video.json` → `clips` y se usa con `M.clip()`. Así sirve para las variantes A/B (por ejemplo, hook con clip de IA contra hook con shader).
6. **Material de IA = material:** no se commitea (`material/` está en `.gitignore`), pero el `registro.json` se copia al README del proyecto para que se sepa qué se generó y cuánto costó.

## Prompts que funcionan para video

- Un plano, una acción y un movimiento de cámara: "Primer plano de una taza de café humeante sobre una mesa de madera, luz de ventana lateral, la cámara se acerca despacio, 5 segundos".
- Pedir **sin texto ni logos** y agregarlos después con el motor.
- Vertical en el pedido (9:16) si el destino es vertical: recortar después pierde calidad.
- Para que el producto se mantenga, partir de **una imagen** (imagen a video), no solo de texto.

## Al implementarlo

La primera vez que se use: armar `scripts/ia.mjs` siguiendo este contrato, probarlo con un pedido de imagen, anotar en `aprendizajes.md` el proveedor, el modelo, el costo real y qué funcionó, y cambiar el estado de esta página a "implementado".
