# Método 1.2 — Video recorrido de la propiedad (Content Maxxing)

Objetivo: UN video terminado, con música, que muestre la propiedad ambiente por ambiente, como lo filmaría y editaría
un director de fotografía de hoteles boutique. No es un recorrido continuo ni un vuelo de IA ni una presentación de
fotos: son tomas separadas unidas con cortes limpios.

## Entrada
Fotos YA mejoradas (método 1.1; si no lo están, hacerlo primero). Notas opcionales del usuario: tipo y carácter de
la propiedad, uso y orientación, duración, fotos o ambientes obligatorios, orden, qué fotos son del mismo ambiente,
música. Lo que falte no se inventa.

## 1. Estudiar las fotos (gratis, con Read)
- Numerarlas (Foto 1, Foto 2…). Por cada una: qué se ve, profundidad (primer plano / fondo), puertas, luz, si la
  composición es fuerte.
- Comparar las que se parecen: dos ángulos no son dos ambientes. No deducir cantidad de dormitorios ni plano de la
  casa.

## 2. Elegir tomas como un editor
- Elegir las mejores, no animar todas. Ahorro: 6–8 tomas. Calidad: las que haga falta para cubrir lo importante.
- Abrir con la composición más atractiva (no necesariamente la entrada) y cerrar con una toma memorable.
- Priorizar lo que vende: luz, arquitectura, materiales, vista, carácter. Saltear placares, teles apagadas y baños
  repetidos.
- Duración total 25–40 s (unos 28–30 s para algo chico); cada toma recortada a 3–6 s, de largos variados.
- Orientación: fotos verticales → 9:16; horizontales → 16:9. No inventar los costados para llenar el cuadro.

## 3. Un movimiento con propósito por toma
Antes de cada toma: qué tiene que notar quien mira, qué movimiento lo revela y dónde termina el encuadre.
- Deslizamiento corto lateral si hay un mueble o arco en primer plano que dé profundidad.
- Avance lento (dolly-in) hacia la cama, un detalle arquitectónico, la vista o un material.
- Paneo suave desde un punto fijo en un ambiente chico.
- Elevación corta si el techo o un elemento alto lo justifica.
Prohibido: cámara en mano, balanceo, paneos bruscos, rampas de velocidad, órbitas o alejamientos que muestren lo
que la foto no muestra, atravesar puertas.

## 4. Generación
- Cada toma: `generate_video` con la foto mejorada como `start_image`.
- Ahorro: `seedance_2_0_mini`, `resolution: "720p"`, `duration: 5`, `generate_audio: false`.
- Calidad: `seedance_2_5`, `resolution: "1080p"`, `duration: 5`, `generate_audio: false` (probar con
  `draft: true` primero). Entrega a 24 fps.
- Una toma de prueba (la de apertura), revisarla y después el resto en lote.

Prompt por toma (completar las llaves):
```
Architectural cinematography of the room shown in the start frame: {qué se ve}.
Camera: {un movimiento: slow dolly-in toward the bed | short lateral slide past the armchair in the foreground |
gentle pan from a fixed position from left to right | small vertical rise toward the ceiling beams}, smooth,
professionally operated, ending framed on {encuadre final}.
Only the camera moves. The scene is rigid and still: furniture, counters, fixtures, beds, mirrors, curtains,
towels and objects keep their exact position, shape, size, count, material and colour; counters stay attached to
walls and floors; nothing slides across the floor.
Stay inside this photographed space: do not go through doorways, do not reveal unseen areas or adjoining rooms.
No people, pets, flowers, candles, steam, running water or moving curtains. Same light, weather, time of day and
window view as the photo. True colours, clean whites, detailed shadows, no filters, no fake golden hour.
No handheld shake, no sway, no whip pans, no speed ramps, no exaggerated wide-angle distortion.
```

## 5. Revisión de cada toma (cuadros al inicio, la mitad y el final contra la foto)
Rechazar si: un objeto se mueve solo, cambia la unión de una mesada o un artefacto, la geometría se deforma,
cambia la cantidad de cosas, aparece una vista inventada, cambia el ambiente, titilan texturas o la cámara "salta".
Un recorte o un cambio de perspectiva normal no es una deformación. Si falla: un movimiento más acotado o
otra foto de ese ambiente. Si no se logra: decirlo y pedir un clip real de ese ambiente (nunca reemplazarlo en
silencio por un zoom sobre la foto).

## 6. Música y armado (local, gratis)
- Música instrumental tranquila acorde al lugar (ej.: acústica cálida para algo rústico, piano mínimo para un
  depto moderno). Sin voces ni narración. Ver SKILL.md para de dónde sale.
- `scripts/armar.py` con las tomas en orden, cada una recortada (`desde`/`hasta`), música con fundido al final, sin
  títulos ni logos salvo que los pidan. 1080p (720p en ahorro) a 24 fps.

## Entrega
`final/recorrido.mp4` + lista de tomas (foto, movimiento, duración) + qué tomas no salieron y por qué.
