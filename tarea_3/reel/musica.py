"""Pista de fondo propia (ambiente suave en Do mayor) generada con numpy. Uso libre (CC0)."""
import numpy as np, soundfile as sf
from pathlib import Path
sr, dur = 48000, 80
t = np.arange(int(sr * dur)) / sr
acordes = [[261.6, 329.6, 392.0], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [196.0, 246.9, 293.7]]
y = np.zeros_like(t)
seg = 5.0
for k in range(int(dur / seg) + 1):
    notas = acordes[k % 4]
    a, b = int(k * seg * sr), int(min(dur, (k + 1) * seg + 1.5) * sr)
    tt = t[a:b] - k * seg
    env = np.minimum(1, tt / 1.2) * np.exp(-np.maximum(0, tt - seg) / 0.6)
    for f in notas:
        y[a:b] += env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) / 6
    # pulso suave de bajo
    y[a:b] += 0.18 * env * np.sin(2 * np.pi * notas[0] / 2 * tt) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.0 * tt))
y *= 0.6 / np.abs(y).max()
fade = int(3 * sr); y[-fade:] *= np.linspace(1, 0, fade); y[:sr] *= np.linspace(0, 1, sr)
sf.write(Path(__file__).parent / "recursos" / "musica.wav", np.stack([y, y], 1).astype(np.float32), sr)
import subprocess, imageio_ffmpeg
w = Path(__file__).parent / "recursos" / "musica.wav"
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-y", "-i", str(w), "-b:a", "128k", str(w.with_suffix(".mp3"))], check=True)
w.unlink()
print("musica.mp3", dur, "s")
