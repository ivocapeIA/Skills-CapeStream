"""Pistas originales sintetizadas desde cero (sin samples ni derechos de terceros).
Copia del generador de videos/10-carteleria-monitor, con la duración como parámetro.

    python musica.py <estilo> <salida.wav> [segundos]   estilos: house lofi marimba synthwave cine noticiero minimal

Cada estilo tiene su tempo, armonía e instrumentos. La forma es la misma para todos
(intro, entrada, cuerpo, respiro, final, cola) y cae en compases, así el video
puede cortar en los tiempos fuertes: el tempo de cada estilo está en BPM más abajo
y en videos.json.
"""
import sys
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
DUR = float(sys.argv[3]) if len(sys.argv) > 3 else 45.0
N = int(DUR * SR)

BPM = {"house": 122, "lofi": 84, "marimba": 104, "synthwave": 110, "cine": 72, "noticiero": 124, "minimal": 96}


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def tt(d):
    return np.arange(int(d * SR)) / SR


def filt(x, kind, fc, order=2):
    return sosfilt(butter(order, fc, btype=kind, fs=SR, output="sos"), x)


class Mix:
    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)
        self.bus = {}

    def add(self, name, t0, sig, pan=0.0):
        if name not in self.bus:
            self.bus[name] = np.zeros((2, N))
        i = int(t0 * SR)
        if i >= N or i < 0:
            return
        j = min(N, i + len(sig))
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.bus[name][0, i:j] += sig[: j - i] * l * 1.414
        self.bus[name][1, i:j] += sig[: j - i] * r * 1.414

    def noise(self, d):
        return self.rng.standard_normal(int(d * SR))


# ---------------------------------------------------------------- instrumentos
def kick(m, punch=1.0, d=0.5, f_end=46):
    t = tt(d)
    f = f_end + 120 * punch * np.exp(-t * 32)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5)
    s[:120] += m.noise(120 / SR) * 0.25 * np.linspace(1, 0, 120)
    return np.tanh(s * 1.4)


def snare(m, d=0.28, tone=190, bright=1.0):
    t = tt(d)
    n = filt(m.noise(d), "band", [1200, 7000 * bright]) * np.exp(-t * 18)
    b = np.sin(2 * np.pi * tone * t) * np.exp(-t * 30) * 0.6
    return (n + b) * 0.55


def clap(m):
    t = tt(0.3)
    n = filt(m.noise(0.3), "band", [900, 4800])
    env = sum((t >= o) * np.exp(-np.maximum(t - o, 0) * (70 if o < 0.02 else 15)) for o in (0, 0.012, 0.024))
    return n * env * 0.45


def hat(m, d=0.05, level=0.3):
    return filt(m.noise(d), "high", 7500) * np.exp(-tt(d) / d * 5) * level


def shaker(m, d=0.09):
    t = tt(d)
    return filt(m.noise(d), "band", [4000, 11000]) * np.sin(np.pi * t / d) ** 2 * 0.18


def crackle(m, d):
    x = np.zeros(int(d * SR))
    k = m.rng.integers(0, len(x), int(d * 35))
    x[k] = m.rng.standard_normal(len(k)) * 0.5
    return filt(x, "band", [1500, 9000]) + filt(m.noise(d), "band", [300, 3000]) * 0.012


def saw(f, t, detune=0.0, voices=1):
    out = np.zeros_like(t)
    for v in range(voices):
        dv = (v - (voices - 1) / 2) * detune
        ff = f * 2 ** (dv / 1200)
        out += 2 * ((ff * t + v * 0.37) % 1.0) - 1
    return out / voices


def adsr(t, a, dcy, s, r, length):
    env = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(dcy, 1e-4)))
    rel = np.clip((length - t) / max(r, 1e-4), 0, 1)
    return env * np.minimum(1, rel) * (t <= length + r)


def pad(f, d, voices=5, detune=14, cutoff=1800, a=0.6, r=0.8):
    t = tt(d + r)
    s = saw(f, t, detune, voices) + 0.5 * saw(f / 2, t, detune * 0.7, 3)
    s = filt(s, "low", cutoff)
    return s * adsr(t, a, 1.0, 0.85, r, d) * 0.35


def pluck(f, d=0.4, bright=3000, decay=9):
    t = tt(d)
    s = saw(f, t, 8, 2)
    return filt(s, "low", bright) * np.exp(-t * decay) * 0.5


def marimba(f, d=0.6):
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t * 25) + 0.15 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t * 60)
    return s * np.exp(-t * 7) * (1 - np.exp(-t * 900)) * 0.45


def epiano(f, d=1.2):
    t = tt(d)
    mod = np.sin(2 * np.pi * f * 1.0 * t) * 1.6 * np.exp(-t * 4)
    s = np.sin(2 * np.pi * f * t + mod) + 0.25 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 3)
    trem = 1 + 0.08 * np.sin(2 * np.pi * 4.5 * t)
    return s * np.exp(-t * 2.2) * (1 - np.exp(-t * 400)) * trem * 0.3


def piano(f, d=2.5, vel=1.0):
    t = tt(d)
    s = np.zeros_like(t)
    for h, (amp, dec) in enumerate([(1, 2.2), (0.55, 3.0), (0.3, 4.2), (0.18, 5.5), (0.1, 7), (0.06, 9)], start=1):
        inh = h * (1 + 0.0004 * h * h)
        s += amp * np.sin(2 * np.pi * f * inh * t) * np.exp(-t * dec * (0.6 + f / 900))
    hammer = filt(np.random.default_rng(int(f)).standard_normal(len(t)), "band", [800, 5000]) * np.exp(-t * 120) * 0.08
    return (s + hammer) * (1 - np.exp(-t * 600)) * 0.28 * vel


def bass(f, d, kind="saw", cutoff=500):
    t = tt(d + 0.03)
    if kind == "sine":
        s = np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t)
    else:
        s = filt(saw(f, t, 6, 2), "low", cutoff) * 1.4 + 0.6 * np.sin(2 * np.pi * f * t)
    return s * adsr(t, 0.005, 0.25, 0.7, 0.03, d) * 0.5


def strings(f, d, cutoff=2600):
    t = tt(d + 1.2)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t)
    s = np.zeros_like(t)
    for k in range(6):
        ph = 2 * np.pi * np.cumsum(f * vib * 2 ** ((k - 2.5) * 6 / 1200)) / SR
        s += 2 * ((ph / (2 * np.pi) + k * 0.21) % 1.0) - 1
    s = filt(s / 6, "low", cutoff)
    return s * adsr(t, 1.4, 2.0, 0.9, 1.2, d) * 0.3


def riser(m, d):
    t = tt(d)
    n = m.noise(d)
    out = np.zeros_like(n)
    blk = 2048
    for s in range(0, len(n), blk):
        fc = 400 * (12000 / 400) ** (s / len(n))
        out[s:s + blk] = filt(n[s:s + blk], "band", [fc * 0.7, min(fc * 1.3, 20000)])
    return out * (t / d) ** 2 * 0.25


def impact(m, d=2.5):
    t = tt(d)
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t * 8)) / SR) * np.exp(-t * 1.6)
    return (boom + filt(m.noise(d), "low", 1200) * np.exp(-t * 4) * 0.4) * 0.7


def tick(f=2400):
    t = tt(0.04)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 140) * 0.35


# ---------------------------------------------------------------- utilidades de mezcla
def reverb(x, seconds=2.2, wet=0.25, seed=7):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.empty_like(x)
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 6.9 / seconds)
        ir = filt(ir, "low", 6000)
        ir[: int(0.012 * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        out[ch] = fftconvolve(x[ch], ir)[: x.shape[1]]
    return x + out * wet


def delay(x, time, fb=0.35, wet=0.3):
    d = int(time * SR)
    out = x.copy()
    tap = x.copy()
    for k in range(1, 6):
        tap = np.roll(tap, d, axis=1)
        tap[:, :d] = 0
        tap = tap * fb
        if k % 2:
            tap = tap[::-1]  # ping-pong
        out += tap * wet / fb
    return out


def sidechain(beats, depth=0.6, rel=0.18):
    env = np.ones(N)
    t = tt(rel * 3)
    shape = 1 - depth * np.exp(-t / rel * 2.2)
    for b in beats:
        i = int(b * SR)
        j = min(N, i + len(shape))
        if i < N:
            env[i:j] = np.minimum(env[i:j], shape[: j - i])
    return env


def gate(a, b, curve=1.0):
    """Envelope de nivel por tramo: rampa entre segundos a y b."""
    t = np.arange(N) / SR
    return np.clip((t - a) / max(b - a, 1e-3), 0, 1) ** curve


def chord_notes(root, kind):
    iv = {"maj": [0, 4, 7], "min": [0, 3, 7], "maj7": [0, 4, 7, 11], "min7": [0, 3, 7, 10], "dom7": [0, 4, 7, 10],
          "min9": [0, 3, 7, 10, 14], "maj9": [0, 4, 7, 11, 14], "13": [0, 4, 10, 14, 21], "7b9": [0, 4, 7, 10, 13],
          "sus2": [0, 2, 7], "add9": [0, 4, 7, 14]}[kind]
    return [root + i for i in iv]


# ---------------------------------------------------------------- estilos
def estilo_house(m):
    bpm = BPM["house"]; b = 60 / bpm; bar = 4 * b
    prog = [(57, "min7"), (53, "maj7"), (48, "maj"), (55, "add9")]
    nb = int(DUR / bar) + 1
    kicks = []
    for k in range(nb):
        t0 = k * bar
        root, kind = prog[k % 4]
        notes = chord_notes(root, kind)
        intro, drop_out = k < 2, 12 <= k < 14
        for q in range(4):
            tq = t0 + q * b
            if not intro and not drop_out and tq < DUR - 2.5:
                m.add("kick", tq, kick(m)); kicks.append(tq)
            m.add("hat", tq + b / 2, hat(m, 0.07, 0.32 if k >= 2 else 0.15), pan=0.25)
            if k >= 4:
                m.add("hat", tq + b / 4, hat(m, 0.03, 0.12), pan=-0.3)
                m.add("hat", tq + 3 * b / 4, hat(m, 0.03, 0.12), pan=-0.3)
            if q % 2 == 1 and k >= 2 and not drop_out:
                m.add("clap", tq, clap(m))
        # acordes stab en contratiempo (estilo deep house)
        for q in (0.5, 1.5, 2.75, 3.5):
            for n in notes:
                m.add("stab", t0 + q * b, pluck(midi(n + 12), 0.35, 2600 if k >= 4 else 1200, 10), pan=(n % 5 - 2) * 0.15)
        m.add("pad", t0, pad(midi(notes[0]), bar, cutoff=900) + pad(midi(notes[1]), bar, cutoff=900) + pad(midi(notes[2]), bar, cutoff=900))
        if k >= 2 and not drop_out:
            for i, q in enumerate([0, 0.75, 1.5, 2.5, 3, 3.5]):
                m.add("bass", t0 + q * b, bass(midi(root - 24 + (7 if i == 4 else 0)), b * 0.45, cutoff=420))
    m.add("fx", 12 * bar - 0.1, impact(m))
    m.add("fx", 14 * bar - 2 * bar, riser(m, 2 * bar))
    m.add("fx", 14 * bar, impact(m))
    return dict(kicks=kicks, sc=0.55, delay=b * 0.75, rev=1.8, levels=dict(kick=1, clap=0.7, hat=0.8, stab=0.55, pad=0.4, bass=0.9, fx=0.5))


def estilo_lofi(m):
    bpm = BPM["lofi"]; b = 60 / bpm; bar = 4 * b
    prog = [(50, "min9"), (43, "13"), (48, "maj9"), (45, "7b9")]
    nb = int(DUR / bar) + 1
    sw = b * 0.12  # swing
    kicks = []
    m.add("vinyl", 0, crackle(m, DUR))
    for k in range(nb):
        t0 = k * bar
        root, kind = prog[k % 4]
        notes = chord_notes(root, kind)
        for i, n in enumerate(notes):
            m.add("keys", t0 + i * 0.018, epiano(midi(n + 12), bar * 0.9), pan=(i - 2) * 0.2)
            m.add("keys", t0 + 2.5 * b + i * 0.02, epiano(midi(n + 12), b * 1.2) * 0.5, pan=(i - 2) * 0.2)
        if k >= 1 and t0 < DUR - 3:
            for q in (0, 1.5, 2.25):
                m.add("kick", t0 + q * b, kick(m, 0.6, 0.4, 50) * 0.9); kicks.append(t0 + q * b)
            for q in (1, 3):
                m.add("snare", t0 + q * b + 0.01, snare(m, 0.22, 180, 0.6))
            for e in range(8):
                m.add("hat", t0 + e * b / 2 + (sw if e % 2 else 0), hat(m, 0.04, 0.16 if e % 2 else 0.22), pan=0.3)
            m.add("bass", t0, bass(midi(root - 12), b * 1.4, "sine"))
            m.add("bass", t0 + 2.5 * b, bass(midi(root - 12 + 7), b * 0.9, "sine"))
        if k >= 4 and k % 2 == 0:
            mel = [notes[-1] + 12, notes[-2] + 12, notes[2] + 12, notes[-1] + 10]
            for i, n in enumerate(mel):
                m.add("lead", t0 + (i * 0.75 + 0.5) * b, marimba(midi(n), 0.7) * 0.5, pan=-0.3)
    return dict(kicks=kicks, sc=0.25, delay=b * 0.5, rev=2.4, lofi=True, levels=dict(vinyl=0.5, keys=0.75, kick=0.8, snare=0.6, hat=0.6, bass=0.8, lead=0.5))


def estilo_marimba(m):
    bpm = BPM["marimba"]; b = 60 / bpm; bar = 4 * b
    prog = [(60, "maj"), (55, "maj"), (57, "min"), (53, "maj")]
    nb = int(DUR / bar) + 1
    kicks = []
    for k in range(nb):
        t0 = k * bar
        root, kind = prog[k % 4]
        notes = chord_notes(root, kind)
        patt = [0, 1, 2, 1, 2, 0, 1, 2]
        for e in range(8):
            n = notes[patt[e]] + (12 if e in (2, 6) else 0)
            m.add("mar", t0 + e * b / 2, marimba(midi(n + 12)), pan=(-0.4 if e % 2 else 0.4))
        m.add("pad", t0, sum(pad(midi(n), bar, voices=3, cutoff=1400, a=0.3) for n in notes) * 0.6)
        if k >= 2 and t0 < DUR - 2.5:
            for q in range(4):
                m.add("kick", t0 + q * b, kick(m, 0.7) * (1 if q % 2 == 0 else 0.6)); kicks.append(t0 + q * b)
                if q % 2:
                    m.add("clap", t0 + q * b, clap(m) * 0.8)
                m.add("shaker", t0 + q * b + b / 2, shaker(m), pan=0.35)
                m.add("shaker", t0 + q * b + b / 4, shaker(m) * 0.5, pan=0.35)
            for q, iv in ((0, 0), (1.5, 0), (2, 7), (3, 12), (3.5, 7)):
                m.add("bass", t0 + q * b, bass(midi(root - 24 + iv), b * 0.4, cutoff=700))
        if k >= 6 and k % 2 == 1:
            mel = [notes[2] + 24, notes[1] + 24, notes[0] + 24, notes[1] + 24, notes[2] + 26]
            for i, n in enumerate(mel):
                m.add("lead", t0 + i * b * 0.5 + b, pluck(midi(n), 0.3, 5000, 12) * 0.6, pan=0.1)
    m.add("fx", 2 * bar - bar, riser(m, bar))
    return dict(kicks=kicks, sc=0.3, delay=b * 0.75, rev=1.6, levels=dict(mar=0.8, pad=0.35, kick=0.85, clap=0.6, shaker=0.7, bass=0.8, lead=0.5, fx=0.4))


def estilo_synthwave(m):
    bpm = BPM["synthwave"]; b = 60 / bpm; bar = 4 * b
    prog = [(57, "min"), (53, "maj"), (48, "maj"), (55, "maj")]
    nb = int(DUR / bar) + 1
    kicks = []
    for k in range(nb):
        t0 = k * bar
        root, kind = prog[k % 4]
        notes = chord_notes(root, kind)
        m.add("pad", t0, sum(pad(midi(n), bar, voices=7, detune=18, cutoff=2400, a=0.05, r=0.3) for n in notes))
        arp = [notes[0], notes[1], notes[2], notes[1] + 12]
        for e in range(16):
            if k >= 1:
                m.add("arp", t0 + e * b / 4, pluck(midi(arp[e % 4] + 12), 0.2, 2000 + 2500 * min(1, k / 8), 14), pan=0.3 * np.sin(e))
        if k >= 2 and not (10 <= k < 12) and t0 < DUR - 2.5:
            for q in range(4):
                m.add("kick", t0 + q * b, kick(m, 1.1)); kicks.append(t0 + q * b)
                if q % 2:
                    m.add("snare", t0 + q * b, snare(m, 0.45, 200, 1.0) * 1.2)
                m.add("hat", t0 + q * b + b / 2, hat(m, 0.05, 0.25))
        if k >= 2:
            for e in range(8):
                m.add("bass", t0 + e * b / 2, bass(midi(root - 24 + (12 if e % 2 else 0)), b * 0.42, cutoff=650))
    m.add("fx", 2 * bar - bar, riser(m, bar))
    m.add("fx", 12 * bar - bar, riser(m, bar))
    m.add("fx", 12 * bar, impact(m))
    return dict(kicks=kicks, sc=0.6, delay=b * 0.75, rev=2.6, levels=dict(pad=0.45, arp=0.5, kick=1, snare=0.75, hat=0.5, bass=0.75, fx=0.5))


def estilo_cine(m):
    bpm = BPM["cine"]; b = 60 / bpm; bar = 4 * b
    prog = [(50, "min"), (46, "maj"), (53, "maj"), (48, "sus2"), (50, "min"), (46, "maj"), (41, "maj"), (45, "maj")]
    nb = int(DUR / bar) + 1
    kicks = []
    mel = [74, 72, 69, 72, 74, 77, 76, 72]
    for k in range(nb):
        t0 = k * bar
        root, kind = prog[k % 8]
        notes = chord_notes(root, kind)
        m.add("str", t0, sum(strings(midi(n), bar) for n in notes) + strings(midi(root - 12), bar, 900))
        # piano: arpegio lento que se va llenando
        arp = [notes[0], notes[2], notes[1] + 12, notes[2]]
        for e in range(4 if k < 4 else 8):
            step = b if k < 4 else b / 2
            m.add("piano", t0 + e * step, piano(midi(arp[e % 4] + 12), 2.5, 0.8), pan=-0.2)
        if k >= 2:
            m.add("piano", t0, piano(midi(mel[k % 8]), 3.5, 1.1), pan=0.15)
        if k >= 4 and t0 < DUR - 4:
            for q in (0, 1.5, 2, 3):  # ostinato de timbales graves
                m.add("drum", t0 + q * b, kick(m, 0.4, 0.9, 60) * (1 if q == 0 else 0.55)); kicks.append(t0 + q * b)
            if k >= 6:
                for e in range(8):
                    m.add("drum", t0 + e * b / 2, hat(m, 0.03, 0.1), pan=0.4)
    for at in (0.0, 4 * bar, 8 * bar):
        m.add("fx", at, impact(m, 3.5) * 0.8)
    return dict(kicks=kicks, sc=0.0, delay=b, rev=3.4, levels=dict(str=0.5, piano=0.9, drum=0.6, fx=0.5))


def estilo_noticiero(m):
    bpm = BPM["noticiero"]; b = 60 / bpm; bar = 4 * b
    prog = [(52, "min"), (48, "maj"), (55, "maj"), (50, "maj")]
    nb = int(DUR / bar) + 1
    kicks = []
    for k in range(nb):
        t0 = k * bar
        root, kind = prog[k % 4]
        notes = chord_notes(root, kind)
        for e in range(16):  # pulso de 16avos en la tónica: el "tic tac" del noticiero
            m.add("pulse", t0 + e * b / 4, pluck(midi(root - 12 + (12 if e % 4 == 2 else 0)), 0.14, 1400, 22), pan=0.0)
        if k % 2 == 0:
            m.add("bell", t0, sum(marimba(midi(n + 24), 1.2) for n in notes[:3]) * 0.6, pan=0.3)
        m.add("pad", t0, sum(pad(midi(n), bar, voices=5, cutoff=1300, a=0.4) for n in notes) * 0.7)
        if k >= 1 and t0 < DUR - 2.5:
            for q in range(4):
                m.add("kick", t0 + q * b, kick(m, 0.9)); kicks.append(t0 + q * b)
                m.add("hat", t0 + q * b + b / 2, hat(m, 0.05, 0.25), pan=0.3)
                m.add("tick", t0 + q * b + b / 4, tick(3200) * 0.4, pan=-0.4)
                if q % 2:
                    m.add("snare", t0 + q * b, snare(m, 0.2, 220, 1.2) * 0.8)
        if k % 4 == 3:
            m.add("fx", t0 + bar - b, riser(m, b))
    for at in (0, 4 * bar, 8 * bar, 12 * bar, 16 * bar):
        m.add("fx", at, impact(m, 1.8) * 0.6)
    return dict(kicks=kicks, sc=0.35, delay=b * 0.5, rev=1.5, levels=dict(pulse=0.55, bell=0.55, pad=0.35, kick=0.9, hat=0.6, tick=0.5, snare=0.6, fx=0.45))


def estilo_minimal(m):
    bpm = BPM["minimal"]; b = 60 / bpm; bar = 4 * b
    prog = [(53, "maj7"), (57, "min7"), (50, "min7"), (46, "maj7")]
    nb = int(DUR / bar) + 1
    kicks = []
    for k in range(nb):
        t0 = k * bar
        root, kind = prog[k % 4]
        notes = chord_notes(root, kind)
        # patrón de piano en corcheas al estilo minimalista (Reich/Glass livianito)
        patt = [0, 2, 1, 3, 2, 1, 3, 2]
        for e in range(8):
            m.add("piano", t0 + e * b / 2, piano(midi(notes[patt[e]] + 12), 1.6, 0.7 + 0.25 * (e % 4 == 0)), pan=0.25 * np.sin(e * 0.9))
        m.add("piano", t0, piano(midi(root - 12), 3.0, 0.9))
        if k >= 2:
            m.add("pad", t0, sum(pad(midi(n), bar, voices=3, cutoff=1100, a=0.8) for n in notes) * 0.5)
        if k >= 4 and t0 < DUR - 3:
            for q in range(4):
                m.add("kick", t0 + q * b, kick(m, 0.5, 0.35) * 0.7); kicks.append(t0 + q * b)
                m.add("shaker", t0 + q * b + b / 2, shaker(m), pan=0.3)
            m.add("bass", t0, bass(midi(root - 24), bar * 0.9, "sine"))
        if k >= 8 and k % 2 == 0:
            for i, n in enumerate([notes[3] + 24, notes[2] + 24, notes[1] + 24]):
                m.add("mar", t0 + 2 * b + i * b / 2, marimba(midi(n), 0.9) * 0.6, pan=-0.3)
    return dict(kicks=kicks, sc=0.2, delay=b * 0.75, rev=2.8, levels=dict(piano=0.9, pad=0.4, kick=0.7, shaker=0.6, bass=0.7, mar=0.5))


ESTILOS = dict(house=estilo_house, lofi=estilo_lofi, marimba=estilo_marimba, synthwave=estilo_synthwave,
               cine=estilo_cine, noticiero=estilo_noticiero, minimal=estilo_minimal)


def render(nombre, out):
    m = Mix(seed=sum(map(ord, nombre)))
    info = ESTILOS[nombre](m)
    lv = info["levels"]
    sc = sidechain(info["kicks"], info["sc"]) if info["sc"] else np.ones(N)
    dry = np.zeros((2, N)); send = np.zeros((2, N))
    for name, x in m.bus.items():
        g = lv.get(name, 0.6)
        if name not in ("kick", "snare", "clap", "drum", "vinyl"):
            x = x * sc
        dry += x * g
        if name not in ("kick", "vinyl", "bass"):
            send += x * g
    wet = reverb(send, info["rev"], 0.3) - send
    echo = delay(send * 0.5, info["delay"], 0.35, 0.25) - send * 0.5
    mix = dry + wet + echo * 0.6
    mix = filt(mix, "high", 30)
    if info.get("lofi"):
        mix = filt(mix, "low", 9000) * 1.0
    # forma: entrada suave y cola para que el loop en pantalla no corte seco
    env = np.minimum(gate(0, 0.25), 1 - gate(DUR - 2.2, DUR, 1.3))
    mix *= env
    mix = np.tanh(mix / (np.max(np.abs(mix)) + 1e-9) * 1.6) * 0.85
    wavfile.write(out, SR, (mix.T * 32767).astype(np.int16))


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
    print("OK", sys.argv[1], "->", sys.argv[2])
