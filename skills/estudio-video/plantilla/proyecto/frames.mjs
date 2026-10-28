// Extrae los clips de video declarados en video.json ("clips") como secuencias
// de JPG (out/frames/<clip>/0001.jpg …) y escribe out/frames/clips.json.
// La pieza muestra el cuadro que corresponde a cada t con M.clip(): render exacto.
//   node frames.mjs            solo los que faltan
//   node frames.mjs --forzar   todos de nuevo
// Campos de cada clip: src (ruta), in (s), dur (s), w/h (por defecto, los del video),
// cx/cy (0..1, centro de interés para el recorte), speed (0.5 = cámara lenta),
// interp (true: interpola cuadros para la cámara lenta), filtro (filtros de ffmpeg extra).
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

process.chdir(path.dirname(fileURLToPath(import.meta.url)));
const VIDEO = JSON.parse(readFileSync("video.json", "utf8"));
const forzar = process.argv.includes("--forzar");
const meta = {};

for (const [id, c] of Object.entries(VIDEO.clips || {})) {
  const dir = `out/frames/${id}`;
  const fps = c.fps || VIDEO.fps;
  const W = c.w || VIDEO.w, H = c.h || VIDEO.h;
  if (forzar || !existsSync(dir) || readdirSync(dir).length === 0) {
    mkdirSync(dir, { recursive: true });
    const cx = c.cx ?? 0.5, cy = c.cy ?? 0.5;
    // cubrir la caja W×H y recortar alrededor del centro de interés (cx, cy)
    let vf = `scale=${W}:${H}:force_original_aspect_ratio=increase:flags=lanczos,crop=${W}:${H}:(iw-${W})*${cx}:(ih-${H})*${cy}`;
    if (c.interp) vf = `minterpolate=fps=${Math.round(fps / (c.speed || 1))}:mi_mode=mci:mc_mode=aobmc:vsbmc=1,` + vf;
    else vf = `fps=${fps},` + vf;
    if (c.filtro) vf += "," + c.filtro;
    console.log(`${id} ← ${path.basename(c.src)} (${c.in ?? 0}s +${c.dur}s) ${W}×${H}`);
    const r = spawnSync("ffmpeg", ["-v", "error", "-y", "-ss", String(c.in ?? 0), "-t", String(c.dur), "-i", path.resolve(c.src),
      "-vf", vf, "-q:v", "3", `${dir}/%04d.jpg`], { stdio: "inherit" });
    if (r.status !== 0) process.exit(1);
  }
  const count = readdirSync(dir).filter(f => f.endsWith(".jpg")).length;
  // con interpolación, los cuadros ya están a la velocidad final: se leen a 1×
  meta[id] = { fps: c.interp ? Math.round(fps / (c.speed || 1)) : fps, count, speed: c.speed || 1 };
}
mkdirSync("out/frames", { recursive: true });
writeFileSync("out/frames/clips.json", JSON.stringify(meta, null, 1));
console.log("clips:", Object.keys(meta).length);
