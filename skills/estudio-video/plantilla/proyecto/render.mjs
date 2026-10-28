// Renderiza la pieza (pieza.html) en cada variante de video.json.
//   node render.mjs                     todas las variantes -> ../entregas/<slug>-<v>.mp4
//   node render.mjs A C                 solo esas
//   node render.mjs --stills 1,4.5 [B]  cuadros sueltos -> out/stills/<v>/
//   node render.mjs --hoja [A B]        hoja de revisión: una fila por variante -> out/stills/hoja.jpg
//   node render.mjs --portada 0.4 [A]   portada a resolución completa -> ../entregas/<slug>-<v>-portada.jpg
//   node render.mjs --audio [A]         solo la mezcla -> out/audio/<v>.wav
//   node render.mjs --preview           escribe out/datos.js; abrí pieza.html?play&v=A en el navegador
//   node render.mjs --borrador [A]      a media resolución y rápido -> out/borrador/ (para revisar el movimiento)
// "escala": 2 en video.json dibuja en w×h y saca el doble (4K desde un diseño 1920×1080).
// Requiere Node 18+, ffmpeg, Python 3 (numpy scipy pillow) y Chrome/Edge/Chromium.
// El navegador se busca solo; para forzar uno: NAVEGADOR=/ruta/al/chrome node render.mjs
import puppeteer from "puppeteer-core";
import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";

const DIR = path.dirname(fileURLToPath(import.meta.url));
process.chdir(DIR);
const PY = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
const ESTILOS = ["house", "lofi", "marimba", "synthwave", "cine", "noticiero", "minimal"];
const VIDEO = JSON.parse(readFileSync("video.json", "utf8"));

// ---------------------------------------------------------------- argumentos
const args = process.argv.slice(2);
const opt = n => { const i = args.indexOf(n); return i > -1 ? args.splice(i, 2)[1] ?? true : null; };
const flag = n => { const i = args.indexOf(n); return i > -1 ? (args.splice(i, 1), true) : false; };
const oStills = opt("--stills"), oPortada = opt("--portada");
const oHoja = flag("--hoja"), oAudio = flag("--audio"), oPreview = flag("--preview"), oBorrador = flag("--borrador");
const ids = args.length ? args : Object.keys(VIDEO.variantes);
for (const id of ids) if (!VIDEO.variantes[id]) { console.error(`No existe la variante "${id}". Hay: ${Object.keys(VIDEO.variantes).join(", ")}`); process.exit(1); }

function run(cmd, a, quiet) {
  const r = spawnSync(cmd, a, { stdio: quiet ? "pipe" : "inherit", encoding: "utf8" });
  if (r.status !== 0) throw new Error(`${cmd} ${a.slice(0, 3).join(" ")}… falló (${r.status})\n${r.stderr || ""}`);
  return r;
}

function navegador() {
  const c = [
    process.env.NAVEGADOR,
    // Chrome antes que Edge: Edge, a mitad de una actualización, se cierra apenas arranca.
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
  ];
  if (existsSync("/opt/pw-browsers"))
    for (const d of readdirSync("/opt/pw-browsers").filter(d => d.startsWith("chromium-")))
      c.push(`/opt/pw-browsers/${d}/chrome-linux/chrome`);
  const n = c.find(p => p && existsSync(p));
  if (!n) throw new Error("No encontré Chrome/Edge/Chromium. Indicá la ruta con NAVEGADOR=...");
  return n;
}

// ---------------------------------------------------------------- variantes
const esObj = x => x && typeof x === "object" && !Array.isArray(x);
function mezclar(a, b) {
  const o = { ...a };
  for (const [k, v] of Object.entries(b || {})) o[k] = esObj(v) && esObj(a?.[k]) ? mezclar(a[k], v) : v;
  return o;
}
// Cada variante = base + lo que cambia. musica, voz, dur y subtitulos pueden ir en cualquiera de los dos.
function variante(id) {
  const v = mezclar(VIDEO.base, VIDEO.variantes[id]);
  v.dur ??= VIDEO.dur;
  v.musica = v.musica === undefined ? VIDEO.musica : v.musica;
  v.voz = v.voz === undefined ? VIDEO.voz : v.voz;
  v.subtitulos ??= VIDEO.subtitulos ?? false;
  v.palabras = v.subtitulos && v.voz ? palabras(v.voz, v.voz_desde || 0) : [];
  return v;
}

// Tiempos por palabra de la voz: out/palabras/<nombre>.json (los escribe voz.py, o palabras.py con Whisper)
function palabras(voz, desde) {
  const f = `out/palabras/${path.parse(voz).name}.json`;
  if (!existsSync(f)) run(PY, ["scripts/palabras.py", voz, f]);
  return JSON.parse(readFileSync(f, "utf8")).map(p => ({ ...p, s: p.s + desde, e: p.e + desde }));
}

function datos() {
  const clips = existsSync("out/frames/clips.json") ? readFileSync("out/frames/clips.json", "utf8") : "{}";
  const vars = Object.fromEntries(Object.keys(VIDEO.variantes).map(id => [id, variante(id)]));
  const { w, h, fps, dur, titulo } = VIDEO;
  mkdirSync("out", { recursive: true });
  writeFileSync("out/datos.js",
    `// Generado por render.mjs a partir de video.json. No editar a mano.\n` +
    `window.VIDEO = ${JSON.stringify({ w, h, fps, dur, titulo })};\n` +
    `window.VARIANTES = ${JSON.stringify(vars, null, 1)};\n` +
    `window.CLIPS = ${clips};\n`);
  return vars;
}

// ---------------------------------------------------------------- audio
function musica(m, dur) {
  if (!m) return null;
  if (!ESTILOS.includes(m)) {
    if (!existsSync(m)) throw new Error(`No existe la música ${m}`);
    return m;
  }
  const f = `out/musica/${m}-${dur}.wav`;
  mkdirSync("out/musica", { recursive: true });
  if (!existsSync(f)) run(PY, ["scripts/musica.py", m, f, String(dur)]);
  return f;
}

// Voz + música con la música agachándose cuando hay voz, normalizado a VIDEO.lufs (dos pasadas).
function audio(id, V) {
  const out = `out/audio/${id}.wav`;
  mkdirSync("out/audio", { recursive: true });
  const D = V.dur, mus = musica(V.musica, D), voz = V.voz;
  if (voz && !existsSync(voz)) throw new Error(`No existe la voz ${voz}`);
  const ins = [], g = [];
  if (voz) ins.push("-i", voz);
  if (mus) ins.push("-stream_loop", "-1", "-i", mus);
  if (!voz && !mus) {
    run("ffmpeg", ["-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", String(D), out]);
    return out;
  }
  const iv = 0, im = voz ? 1 : 0;
  const fin = `afade=t=out:st=${Math.max(0, D - 0.8)}:d=0.8`;
  if (mus) g.push(`[${im}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:${D},asetpts=PTS-STARTPTS,volume=${V.musica_db ?? (voz ? -15 : 0)}dB,${fin}[mus]`);
  if (voz) {
    const ms = Math.round((V.voz_desde || 0) * 1000);
    g.push(`[${iv}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=${ms}|${ms},apad,atrim=0:${D},equalizer=f=3000:t=o:w=1.5:g=2${mus ? ",asplit=2[voz][llave]" : "[mix]"}`);
    if (mus) g.push(`[mus][llave]sidechaincompress=threshold=0.08:ratio=4:attack=15:release=300[duck]`, `[voz][duck]amix=inputs=2:duration=first:normalize=0[mix]`);
  } else g.push(`[mus]anull[mix]`);
  const LN = `I=${VIDEO.lufs ?? -14}:TP=-1.5:LRA=11`;
  const ff = extra => run("ffmpeg", ["-hide_banner", ...ins, ...extra], true);
  const m = ff(["-filter_complex", [...g, `[mix]loudnorm=${LN}:print_format=json[o]`].join(";"), "-map", "[o]", "-t", String(D), "-f", "null", "-"]);
  const j = JSON.parse(m.stderr.slice(m.stderr.lastIndexOf("{"), m.stderr.lastIndexOf("}") + 1));
  const ln = `${LN}:measured_I=${j.input_i}:measured_TP=${j.input_tp}:measured_LRA=${j.input_lra}:measured_thresh=${j.input_thresh}:offset=${j.target_offset}:linear=true`;
  ff(["-y", "-filter_complex", [...g, `[mix]loudnorm=${ln},aresample=48000[o]`].join(";"), "-map", "[o]", "-t", String(D), "-c:a", "pcm_s16le", out]);
  return out;
}

// ---------------------------------------------------------------- navegador
async function abrir(id, escala = VIDEO.escala || 1) {
  const browser = await puppeteer.launch({
    executablePath: navegador(), headless: true,
    userDataDir: path.resolve(`out/perfiles/${id}-${process.pid}`),
    // swiftshader: si no hay placa de video, WebGL (bases 3D y shader) sigue andando por software
    args: ["--allow-file-access-from-files", "--disable-web-security", "--hide-scrollbars", "--force-color-profile=srgb", "--enable-unsafe-swiftshader",
      ...(process.getuid?.() === 0 ? ["--no-sandbox"] : [])],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: VIDEO.w, height: VIDEO.h, deviceScaleFactor: escala });
  page.on("pageerror", e => console.error(`[${id}] error en la pieza:`, e.message));
  page.on("console", m => m.type() === "error" && console.error(`[${id}]`, m.text()));
  await page.goto(pathToFileURL(path.resolve("pieza.html")).href + `?v=${encodeURIComponent(id)}`, { waitUntil: "load" });
  await page.waitForFunction("window.READY === true", { timeout: 120000 });
  const cdp = await page.createCDPSession();
  const cuadro = async (t, formato = "jpeg", q = 94) => {
    await page.evaluate(tt => window.seek(tt), t);
    const { data } = await cdp.send("Page.captureScreenshot", { format: formato, quality: formato === "jpeg" ? q : undefined, optimizeForSpeed: true });
    return Buffer.from(data, "base64");
  };
  return { browser, cuadro };
}

async function video(id, V) {
  const wav = audio(id, V);
  const dir = oBorrador ? "out/borrador" : "../entregas";
  mkdirSync(dir, { recursive: true });
  const nombre = Object.keys(VIDEO.variantes).length > 1 ? `${VIDEO.slug}-${id}` : VIDEO.slug;
  const out = path.resolve(`${dir}/${nombre}.mp4`);
  // borrador: la mitad de la resolución (un cuarto de los píxeles) y codificación rápida
  const esc = (VIDEO.escala || 1) * (oBorrador ? 0.5 : 1);
  const { browser, cuadro } = await abrir(id, esc);
  const fps = VIDEO.fps, N = Math.round(V.dur * fps);
  const ff = spawn("ffmpeg", [
    "-y", "-hide_banner", "-loglevel", "error",
    "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-",
    "-i", wav, "-map", "0:v", "-map", "1:a",
    "-c:v", "libx264", "-preset", oBorrador ? "veryfast" : "slow", "-crf", VIDEO.w * VIDEO.h * (VIDEO.escala || 1) ** 2 > 1920 * 1080 ? "19" : "17", "-profile:v", "high",
    // techo de bitrate: el grano o el ruido de los clips no inflan el archivo
    "-pix_fmt", "yuv420p", "-g", String(fps * 2), "-maxrate", (VIDEO.escala || 1) > 1 ? "40M" : "14M", "-bufsize", (VIDEO.escala || 1) > 1 ? "80M" : "28M",
    // tamaño de salida explícito: Chrome no siempre respeta la escala en la captura
    "-vf", `scale=${Math.round(VIDEO.w * esc / 2) * 2}:${Math.round(VIDEO.h * esc / 2) * 2}:flags=lanczos,setsar=1`, "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", String(V.dur), "-movflags", "+faststart", out,
  ], { stdio: ["pipe", "inherit", "inherit"] });
  const fin = new Promise((res, rej) => ff.on("close", c => (c === 0 ? res() : rej(new Error("ffmpeg " + c)))));
  const t0 = Date.now();
  for (let f = 0; f < N; f++) {
    const buf = await cuadro(f / fps);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    if (f % (fps * 5) === 0) console.log(`[${id}] ${(f / fps).toFixed(0)} s / ${V.dur}  (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
  }
  ff.stdin.end();
  await fin;
  await browser.close();
  console.log(`[${id}] OK -> ${out}  (${((Date.now() - t0) / 60000).toFixed(1)} min)`);
}

async function stills(id, tiempos, dir = `out/stills/${id}`) {
  const { browser, cuadro } = await abrir(id);
  mkdirSync(dir, { recursive: true });
  const files = [];
  for (const t of tiempos) {
    const f = `${dir}/t${t.toFixed(2).padStart(5, "0")}.jpg`;
    writeFileSync(f, await cuadro(t, "jpeg", 90));
    files.push(f);
  }
  await browser.close();
  return files;
}

// ---------------------------------------------------------------- principal
const vars = datos();
if (oPreview) {
  console.log("Listo out/datos.js. Abrí en el navegador:");
  for (const id of ids) console.log(`  ${pathToFileURL(path.resolve("pieza.html")).href}?play&v=${id}`);
} else if (oAudio) {
  for (const id of ids) console.log(audio(id, vars[id]));
} else if (oStills) {
  for (const id of ids) (await stills(id, String(oStills).split(",").map(Number))).forEach(f => console.log(f));
} else if (oPortada) {
  mkdirSync("../entregas", { recursive: true });
  for (const id of ids) {
    const { browser, cuadro } = await abrir(id);
    const f = `../entregas/${VIDEO.slug}${ids.length > 1 || Object.keys(VIDEO.variantes).length > 1 ? "-" + id : ""}-portada.jpg`;
    writeFileSync(f, await cuadro(Number(oPortada), "jpeg", 95));
    await browser.close();
    console.log(f);
  }
} else if (oHoja) {
  // misma grilla de tiempos para todas: las variantes se comparan fila contra fila
  const D = Math.min(...ids.map(id => vars[id].dur)), n = 6;
  const tiempos = Array.from({ length: n }, (_, i) => +(0.4 + (i * (D - 0.8)) / (n - 1)).toFixed(2));
  const filas = [];
  for (const id of ids) filas.push(id, ...(await stills(id, tiempos)));
  run(PY, ["-c", `
import sys
from PIL import Image, ImageDraw
out, n, args = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
filas = [args[i:i + n + 1] for i in range(0, len(args), n + 1)]
ims = [[Image.open(f) for f in fila[1:]] for fila in filas]
w = 300; h = int(ims[0][0].height * w / ims[0][0].width); m = 56
hoja = Image.new("RGB", (m + n * w, len(filas) * h), "white"); d = ImageDraw.Draw(hoja)
for r, fila in enumerate(filas):
    d.text((14, r * h + h // 2 - 8), fila[0], fill="black", font_size=28)
    for c, im in enumerate(ims[r]):
        hoja.paste(im.resize((w, h)), (m + c * w, r * h))
hoja.save(out, quality=85)`, "out/stills/hoja.jpg", String(n), ...filas]);
  console.log(`out/stills/hoja.jpg  (tiempos: ${tiempos.join(", ")} s)`);
} else {
  const cola = [...ids];
  await Promise.all(Array.from({ length: Math.min(2, cola.length) }, async () => { while (cola.length) { const id = cola.shift(); await video(id, vars[id]); } }));
}
