# Variantes A/B de bajo costo

## Lo incómodo primero

- **Publicar A el lunes y B el jueves no es un test.** Cambian el día, la hora, lo que pasa en el feed y el humor del algoritmo. Cualquier diferencia de menos del doble es ruido.
- **Con pocos seguidores, la muestra no alcanza.** Con 300 reproducciones por variante, solo se ven las diferencias enormes.
- **Si cambian dos cosas, no sabés cuál funcionó.** Un test tiene una sola variable.

Qué hacer en su lugar:

1. **Reels de prueba de Instagram** (cuentas profesionales): el reel se muestra primero a gente que no te sigue y después se ven sus métricas para decidir si se comparte con los seguidores. Es la forma gratis más limpia: se suben A y B como prueba el mismo día, a la misma hora. Revisá en la app que la opción esté disponible en la cuenta.
2. **Experimento A/B de Meta Ads:** el mismo presupuesto chico para cada variante, con el público repartido sin superponerse. Es lo más riguroso; con poca plata por variante ya da datos de retención y clics.
3. **Sin ninguna de las dos:** usá las variantes como **banco de contenido** (se publica B semanas después como "otra versión") y no saques conclusiones de una sola comparación.

## Qué variar (de más a menos impacto por peso invertido)

| Variable | Por qué importa | Costo con la plantilla | Métrica para decidir |
|---|---|---|---|
| **Hook** (texto o primera toma, 0–2 s) | Decide si alguien se queda | Cambiar `textos.hook` o la primera toma | Retención a 3 s / tasa de salteo |
| **Portada** | Decide el clic desde el perfil y la grilla | `--portada <t>` en otro instante, o un texto distinto | Reproducciones desde el perfil |
| **Duración** (corta/larga) | Más corta = más vistas completas | `dur` + `tiempos` en la variante | % de vistas completas, repeticiones |
| **CTA** | Decide la acción | `textos.cierre` / `textos.boton` | Mensajes, visitas al perfil, clics |
| **Música / ritmo** | Clima y energía | `musica: "lofi"` en la variante | Retención media |
| **Paleta / estilo** | Reconocimiento de marca | `colores` en la variante | Casi nunca se mide bien: no la testees primero |

## Cómo se arma

En `video.json`, `base` tiene todo y cada variante solo **lo que cambia**:

```json
"variantes": {
  "A": { "nota": "Control: hook con pregunta" },
  "B": { "nota": "Hook con dato", "textos": { "hook": "El *80 %* pasa de largo en 3 segundos" } },
  "C": { "nota": "Versión corta", "dur": 9, "tiempos": { "cierre": 2.5 } }
}
```

`musica`, `voz`, `voz_desde`, `dur` y `subtitulos` también se pueden pisar por variante.

**Si hay voz y la variante cambia el hook, la voz del hook también tiene que cambiar.** Si no, el subtítulo y la locución dicen una cosa y el texto en pantalla, otra. Ejemplo: la variante B usa otra toma de voz (`"voz": "out/voz/hook-B.mp3"`), hecha con `scripts/voz.py` o grabada aparte.

Flujo:

1. `node render.mjs --hoja`: una fila por variante, en los mismos instantes. Se ve la diferencia de un vistazo **antes** de renderizar.
2. `node render.mjs`: todas las variantes → `entregas/<slug>-A.mp4`, `-B.mp4`…
3. Las variantes comparten la música, los clips y la pieza; cada una suma solo su tiempo de render (unos 20–40 s por cada 15 s de video).

## Registro (va al README del proyecto)

```markdown
## Test A/B
| Variante | Hipótesis | Publicada | Alcance | Retención 3 s | Vistas completas | Guardados | Compartidos | Mensajes |
|---|---|---|---|---|---|---|---|---|
| A | Control | 2026-10-07 (prueba) | | | | | | |
| B | El dato retiene más que la pregunta | 2026-10-07 (prueba) | | | | | | |

**Resultado:** <ganadora y por cuánto> · **Aprendizaje:** <qué se aplica al próximo video>
```

Regla de decisión: la ganadora tiene que sacar **al menos un 20 % más** en la métrica elegida y una base de unas 1000 reproducciones por variante. Si no, es empate: quedate con la que más te guste y testeá otra variable.

## Git

Las variantes que se publican (o se suben como prueba) son entregas y se commitean. Las que se descartan en la hoja de revisión no se renderizan; las que se renderizaron y no se van a publicar se borran de `entregas/` antes del commit (el `CLAUDE.md` del repo no deja subir versiones alternativas).
