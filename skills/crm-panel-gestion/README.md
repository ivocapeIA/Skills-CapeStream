# Skill `crm-panel-gestion` — instalación y uso

Skill portable para construir un CRM / panel de gestión completo (Next.js 15 + Supabase +
Tailwind + Vercel) con landing, integraciones y endurecimiento de seguridad, a partir de una
descripción del negocio.

Es **agnóstica de herramienta**: son archivos Markdown. Funciona en Claude Code, Cursor,
Codex, Windsurf o leyéndola a mano.

```
crm-panel-gestion/
├── SKILL.md                     ← el workflow (empezar acá)
├── README.md                    ← este archivo
└── references/
    ├── 00-intake-y-plan.md      · cuestionario, defaults, plantilla de PLAN.md
    ├── 01-stack-y-arquitectura.md
    ├── 02-datos-rls-migraciones.md
    ├── 03-seguridad.md
    ├── 04-diseno-frontend.md
    ├── 05-integraciones.md      · WhatsApp, correo IMAP, Instagram, iCal, IA, pagos
    ├── 06-landing-y-legales.md
    ├── 07-errores-conocidos.md  ← ~50 fallas reales, con su regla
    ├── 08-entrega-y-verificacion.md
    └── 09-rendimiento.md        ← que se sienta tan fluido como el sistema de referencia
```

---

## Claude Code

**Por proyecto** (queda versionada con el repo):

```
<repo>/.claude/skills/crm-panel-gestion/
```

**Personal** (disponible en todos los proyectos):

```
~/.claude/skills/crm-panel-gestion/
```

Se carga sola cuando el pedido matchea la `description` del frontmatter, o a mano:

```
/crm-panel-gestion
```

o simplemente: *"quiero un CRM para mi negocio de …"*.

---

## Cursor

Cursor no lee `SKILL.md` por sí solo, así que hay dos puentes ya incluidos en este repo:

1. **Regla** — `.cursor/rules/crm-panel-gestion.mdc`
   Regla de tipo *Agent Requested*: Cursor la ofrece cuando el pedido tiene que ver con
   construir un CRM/panel, y su contenido le indica leer `SKILL.md` y las referencias.

2. **Comando** — `.cursor/commands/crm.md`
   Escribiendo `/crm` en el chat de Cursor arranca el workflow (Fase 0 en modo Plan).

Para usarla en **otro** proyecto desde Cursor, copiar estas tres cosas al repo nuevo:

```
.claude/skills/crm-panel-gestion/     (los archivos de la skill)
.cursor/rules/crm-panel-gestion.mdc
.cursor/commands/crm.md
```

> Si tu versión de Cursor soporta Agent Skills nativas, alcanza con copiar la carpeta a
> `.cursor/skills/crm-panel-gestion/`; los puentes siguen funcionando igual.

---

## Otros agentes (Codex, Windsurf, Gemini CLI…)

Agregar al `AGENTS.md` del repo:

```markdown
## Construir un CRM / panel de gestión
Si el pedido es crear un CRM, panel administrativo o sistema de gestión desde cero,
leer y seguir `.claude/skills/crm-panel-gestion/SKILL.md` antes de escribir nada.
```

---

## Cómo se usa

1. Contale al agente **qué es el negocio, cómo opera hoy, qué estilo visual querés y qué
   apps querés conectar**. Si falta algo, lo pregunta en una sola ronda (incluido el
   **nombre del negocio**, que es obligatorio).
2. Devuelve un **plan** (`docs/PLAN.md`) con sugerencias y recomendaciones explícitas.
   Se revisa y se aprueba.
3. A partir de ahí ejecuta **en modo auto, sin preguntar**: esqueleto → base de datos con
   RLS → auth y navegación → módulos → estadísticas → integraciones → landing y legales →
   endurecimiento y deploy. Lo que decide sin consultar queda en `docs/DECISIONES.md`.
4. Solo se frena si falta un secreto que únicamente vos podés dar (una API key, una
   credencial) o ante una acción destructiva sobre datos reales.

---

## De dónde sale

Del sistema **Manager** (gestión de alquileres temporarios, en producción): multi-tenant con
RLS, WhatsApp bidireccional multi-proveedor con chatbot de contexto en capas, ingesta de
correo por IMAP con extractores e IA, calendarios iCal en ambas direcciones, finanzas con
importador, estadísticas con cross-filtering en el navegador, vitrina pública sobre vistas de
la misma base operativa y landing con verificación de empresa.

`references/07-errores-conocidos.md` es el destilado de su `HISTORIAL.md`: ~50 fallas reales
—incluidas las que llegaron a producción— con la regla que las evita.
