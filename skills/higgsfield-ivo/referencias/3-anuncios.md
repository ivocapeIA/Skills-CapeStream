# Método 2 — Tres anuncios nuevos a partir de uno existente (AI Ads)

Objetivo: entender el negocio con un anuncio existente (video o grabación de pantalla) y crear TRES anuncios de
video originales para Facebook/Instagram que busquen la misma acción del cliente. No es pulir el original: el
original solo aporta información sobre el negocio, no el guion, el estilo ni la estructura.

## Entrada
- El anuncio (archivo local o URL de YouTube).
- Opcional: nombre, web/redes, qué vende, cliente objetivo, zona, acción buscada (comprar, reservar, llamar,
  escribir, pedir presupuesto) y adónde lleva, oferta y condiciones vigentes, razones verificadas para elegirlo,
  pruebas (reseñas aprobadas, certificaciones), material disponible (logo, fotos, tomas), qué evitar, textos
  legales obligatorios, ubicación (Reels / Stories / Feed), si el guion se reescribe libre o se respeta textual.
  Un campo vacío NO autoriza a inventar.

## 1. Entender el negocio (gratis)
- Video local: cuadros cada 1–2 s con ffmpeg (`ffmpeg -i anuncio.mp4 -vf fps=1 cuadros/%03d.jpg`) + audio a texto
  si hace falta. Recortar controles del reproductor, bordes y repeticiones. Alternativa: `video_analysis_create`.
- Extraer: quién es, qué vende, servicios y beneficios explícitos, oferta, precios y fechas, zona, contacto, destino
  de la conversión, afirmaciones y textos legales, marca visible, mensaje central y acción buscada.
- No adivinar texto ilegible ni audio confuso.

## 2. Fijar los hechos ("Facts Lock")
Investigar web y redes oficiales (WebSearch/WebFetch) y clasificar cada dato: confirmado en el anuncio / dado por el
usuario / corroborado en fuente oficial / inferido o sin resolver. Que el anuncio lo diga no lo prueba.
Nunca inventar ni agrandar: resultados, garantías, credenciales, comparaciones, reseñas, cantidad de clientes,
precios, descuentos, escasez, plazos, productos, sucursales o contactos. No reusar una oferta vencida. Si algo de
esto queda en duda, una sola tanda de preguntas antes de producir.

## 3. Oportunidad y tres hipótesis
Quién es más probable que le importe, qué necesidad real cubre, la razón más fuerte y sostenida para elegirlo, qué
lo haría frenar el scroll, qué tiene que entender, sentir y hacer.
Tres conceptos REALMENTE distintos, cada uno con su gancho, idea central, guion, lenguaje visual, ritmo de edición,
voz/música/sonido y forma de mostrar el llamado a la acción. No tres versiones cosméticas de lo mismo, y no caer por
defecto en: tomas "cinematográficas" genéricas, cabeza parlante, tarjetas animadas, montaje de stock, el mismo
guion problema–solución, música corporativa y locutor. "Cinematográfico", "UGC" y "animado" son ejecuciones, no ideas.

## 4. Guiones
- ~30 s cada uno (ajustar solo si el mensaje o la ubicación lo justifican). Gancho entendible en 1–2 s.
- Lenguaje hablado natural (en el idioma del público), sin superlativos vacíos. Hechos y textos legales exactos.
- Si se pidió respetar el guion textual: mismas palabras en el mismo orden.
- Un solo llamado a la acción al final, con tiempo para leerlo. El mensaje central se entiende sin sonido.
- Son hipótesis para testear, no ganadores garantizados.

## 5. Mostrar antes de generar
Resumen del negocio, Facts Lock con dudas, objetivo/público/formato/duración, los 3 conceptos y por qué difieren,
los 3 guiones, la lista de tomas de cada uno y la cotización (`get_cost` por clip, imagen y voz). Seguir según el tope.

## 6. Producir
- 9:16 (1080×1920 en calidad, 720p en ahorro), márgenes seguros para la interfaz de Reels/Stories.
- Clips: ahorro `seedance_2_0_mini` 720p sin audio, 2–6 clips por anuncio que sumen su duración; calidad
  `seedance_2_5` 1080p. Imágenes de arranque solo si un clip lo necesita (`gpt_image_2_5` medium). Usar el
  material real del usuario cuando sirva (fotos como `start_image`).
- Voz: `seed_audio`, una toma por anuncio con el guion aprobado textual. Música: una pista instrumental para los tres.
- **Nunca generar dentro del video** nombre, logo, precios, teléfono, web ni llamado a la acción: van como texto en
  `armar.py`. Si no hay logo limpio, el nombre bien escrito en tipografía simple.
- Material generado o de stock no puede pasar por trabajos, sucursales, empleados o clientes reales del negocio;
  si podría confundirse, sumar una aclaración.
- Subtítulos legibles cuando el audio lleva información clave (`textos` en `armar.py`, sincronizados con la voz).

## 7. Revisar y entregar
Ver y escuchar cada anuncio armado: guion y pronunciación, nombre, oferta, teléfono, web y CTA correctos,
afirmaciones y textos legales, ortografía, marca, sin manos deformes ni texto ilegible, sonido equilibrado,
encuadre seguro, duración y tiempo del CTA, y que los tres sean distintos de verdad. Un render terminado no es
automáticamente un anuncio aceptable.
Entregar `final/anuncio-1.mp4`, `-2`, `-3`, cada uno con una línea sobre la hipótesis y la limitación que quede.
