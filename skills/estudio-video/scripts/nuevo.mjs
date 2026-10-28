// Crea un proyecto de video nuevo en videos/NN-nombre/ a partir de la plantilla.
//   node ~/.claude/skills/estudio-video/scripts/nuevo.mjs <nombre> [opciones]   (desde la raíz del proyecto)
// Opciones: --w 1080 --h 1920 --fps 30 --dur 20 --musica house|lofi|…|ninguna
//           --titulo "Texto" --slug nombre-archivo --variantes A,B,C
//           --base texto|3d|shader   (punto de partida de pieza.html; ver plantilla/bases/)
// El número NN sale solo (el siguiente libre en videos/). No instala nada:
// al final imprime los comandos que faltan.
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SKILL = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RAIZ = process.cwd(); // el proyecto donde se está trabajando, no donde vive la skill
const VIDEOS = path.join(RAIZ, "videos");
const args = process.argv.slice(2);
const opt = (n, d) => { const i = args.indexOf("--" + n); return i > -1 ? args.splice(i, 2)[1] : d; };
const w = +opt("w", 1080), h = +opt("h", 1920), fps = +opt("fps", 30), dur = +opt("dur", 20);
const musica = opt("musica", "house"), titulo = opt("titulo"), slugOpt = opt("slug");
const base = opt("base", "texto");
const variantes = opt("variantes", "A,B").split(",").map(s => s.trim()).filter(Boolean);
let nombre = args[0];
const original = nombre;
if (!nombre) { console.error("Uso: node nuevo.mjs <nombre> [--w --h --fps --dur --musica --titulo --slug --variantes]"); process.exit(1); }

mkdirSync(VIDEOS, { recursive: true });
nombre = nombre.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
if (!/^\d+-/.test(nombre)) {
  const nums = readdirSync(VIDEOS).map(d => parseInt(d, 10)).filter(n => !isNaN(n));
  nombre = `${String(Math.max(0, ...nums) + 1).padStart(2, "0")}-${nombre}`;
}
const destino = path.join(VIDEOS, nombre);
if (existsSync(destino)) { console.error(`Ya existe ${destino}`); process.exit(1); }
const baseHtml = base === "texto" ? null : path.join(SKILL, `plantilla/bases/${base}.html`);
if (baseHtml && !existsSync(baseHtml)) {
  console.error(`No existe la base "${base}". Hay: texto, ${readdirSync(path.join(SKILL, "plantilla/bases")).map(f => f.replace(".html", "")).join(", ")}`);
  process.exit(1);
}

cpSync(path.join(SKILL, "plantilla/proyecto"), path.join(destino, "proyecto"), {
  recursive: true, filter: s => !/node_modules|[\\/]out([\\/]|$)/.test(s),
});
cpSync(path.join(SKILL, "plantilla/gitignore"), path.join(destino, ".gitignore"));
if (baseHtml) cpSync(baseHtml, path.join(destino, "proyecto/pieza.html"));
for (const d of ["material/voz", "material/tomas", "material/fotos", "entregas"]) mkdirSync(path.join(destino, d), { recursive: true });

const vj = path.join(destino, "proyecto/video.json");
const v = JSON.parse(readFileSync(vj, "utf8"));
const slug = slugOpt || nombre.replace(/^\d+-/, "");
if (base !== "texto") v.base.colores.acento2 ??= "#7a5cff";   // segundo color de luz o de mancha
if (base === "3d") Object.assign(v.base, { forma: "blob" });
if (base === "shader") Object.assign(v.base, { shader: "malla" });
Object.assign(v, { slug, titulo: titulo || original, w, h, fps, dur, musica: musica === "ninguna" ? null : musica });
v.variantes = Object.fromEntries(variantes.map((id, i) => [id, { nota: i === 0 ? "Control" : "Qué cambia y por qué (hipótesis)" }]));
writeFileSync(vj, JSON.stringify(v, null, 2) + "\n");

const rel = path.relative(RAIZ, destino).replaceAll("\\", "/");
console.log(`Listo: ${rel}/
  proyecto/   pieza.html, video.json, render.mjs, frames.mjs, scripts/
  material/   voz/, tomas/, fotos/ (no se suben a git)
  entregas/   lo que se publica

Siguiente:
  cd ${rel}/proyecto
  npm install
  pip install numpy scipy pillow edge-tts faster-whisper
  node render.mjs --hoja          # hoja de revisión de las variantes`);
