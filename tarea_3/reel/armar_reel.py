"""Reel 1080x1920 con voz clonada, un gráfico o mapa por escena, subtítulos y música de fondo.

Reutiliza el motor de la Sesión 15 (reel_sesion15.py: Qwen3-TTS o VoxCPM2 + Whisper) y le agrega:
  * la imagen de cada escena (campo "imagen" de guion.json) sobre la cifra,
  * música de fondo a volumen bajo (recursos/musica.wav), mezclada debajo de la voz.

Uso (con su voz; la primera corrida baja ~4 GB de modelos):
    python reel/armar_reel.py --voz mi_voz.m4a
    python reel/armar_reel.py --voz mi_voz.m4a --motor voxcpm --velocidad 1.08   # alternativa
Vista previa sin voz (para revisar diseño y tiempos):
    python reel/armar_reel.py --vista-previa
Salidas en reel/salidas/: reel.mp4, reel.srt (subtítulos), portada.png
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import reel_sesion15 as reel  # noqa: E402

AUTOR = "Fiorella Becerril Mercado"
FUENTE = "Informes técnicos SERVIR-GDSRH (2014–2026) · Música: pista propia (CC0)"


def escena_con_imagen(e):
    """Reemplaza reel._escena: gráfico arriba, cifra y etiqueta debajo."""
    capa = Image.new("RGBA", (reel.ANCHO, reel.ALTO), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    ancho = reel.ANCHO - 2 * reel.MARGEN
    y_img_fin = 400
    if e.get("imagen"):
        img = Image.open(AQUI / e["imagen"]).convert("RGBA")
        img.thumbnail((ancho, 520))
        capa.paste(img, (reel.MARGEN + (ancho - img.width) // 2, 400), img)
        y_img_fin = 400 + img.height
    y = y_img_fin + 40
    if e.get("cifra"):
        f = reel._ajustar(d, e["cifra"], "Oswald", 700, ancho, 130, minimo=70)
        y += f.size
        d.text((reel.MARGEN, y), e["cifra"], font=f, fill=reel.ACENTO, anchor="ls")
        y += 18
    fe = reel._fuente("PublicSans", 44 if e.get("cifra") else 80, 600)
    for linea in reel._envolver(d, e["etiqueta"], fe, ancho):
        y += int(fe.size * 1.15)
        d.text((reel.MARGEN, y), linea, font=fe, fill=reel.TEXTO if not e.get("cifra") else reel.SUAVE, anchor="ls")
    return capa


def base_sin_superponer(titulo, fuente_datos, autor):
    """Igual que reel._base, pero el pie va bajo los subtítulos para no chocar con las imágenes."""
    img = Image.new("RGB", (reel.ANCHO, reel.ALTO), reel.FONDO)
    d = ImageDraw.Draw(img)
    d.text((reel.MARGEN, 250), titulo.upper(), font=reel._fuente("PublicSans", 40, 800), fill=reel.ACENTO)
    aviso = "VOZ GENERADA CON IA A PARTIR DE MI VOZ"
    f = reel._fuente("PublicSans", 26, 700)
    x1 = reel.MARGEN + d.textlength(aviso, font=f) + 36
    d.rounded_rectangle((reel.MARGEN, 312, x1, 360), radius=24, outline=reel.SUAVE, width=2)
    d.text((reel.MARGEN + 18, 336), aviso, font=f, fill=reel.SUAVE, anchor="lm")
    pie = reel._fuente("PublicSans", 28, 500)
    for i, linea in enumerate(reel._envolver(d, f"{autor} · Fuente: {fuente_datos}", pie, reel.ANCHO - 2 * reel.MARGEN)):
        d.text((reel.MARGEN, 1560 + i * 40), linea, font=pie, fill=reel.SUAVE)
    return img


def narracion_simulada(guion, sr=24000, palabras_por_s=2.7):
    """Para la vista previa: tiempos estimados por palabra, audio en silencio."""
    t, escenas, palabras = reel.INICIO, [], []
    for e in guion["escenas"]:
        ws = e["frase"].split()
        dur = len(ws) / palabras_por_s
        for k, w in enumerate(ws):
            palabras.append((t + k * dur / len(ws), t + (k + 1) * dur / len(ws) - 0.02, w))
        escenas.append((t, t + dur))
        t += dur + reel.PAUSA
    total = t + reel.FINAL
    return reel.Narracion(np.zeros(int(total * sr), np.float32), sr, escenas, palabras)


def mezclar_musica(video, musica, salida, volumen=0.10):
    cmd = [reel.FFMPEG, "-y", "-v", "error", "-i", str(video), "-stream_loop", "-1", "-i", str(musica),
           "-filter_complex",
           f"[1:a]volume={volumen},afade=t=out:st=0:d=0[m0];[m0]apad[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
           "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", str(salida)]
    subprocess.run(cmd, check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--voz", help="15 a 25 s de su propia voz (wav, m4a, ogg, opus)")
    p.add_argument("--motor", default="qwen", choices=["qwen", "voxcpm"])
    p.add_argument("--tts", default="Qwen/Qwen3-TTS-12Hz-0.6B-Base")
    p.add_argument("--device", default="cpu", help="cpu, cuda (Colab) o mps (Mac)")
    p.add_argument("--velocidad", type=float, default=1.0)
    p.add_argument("--vista-previa", action="store_true", help="sin voz: revisa diseño y tiempos")
    a = p.parse_args()

    sal = AQUI / "salidas"
    sal.mkdir(exist_ok=True)
    guion = json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))
    reel._escena = escena_con_imagen
    reel._base = base_sin_superponer

    if a.vista_previa:
        narr = narracion_simulada(guion)
        nombre = "reel_vista_previa"
    else:
        if not a.voz:
            sys.exit("Falta --voz (o use --vista-previa)")
        voz = (reel.VozExpresiva(a.voz, device=a.device) if a.motor == "voxcpm"
               else reel.Voz(a.voz, modelo=a.tts, device=a.device))
        print("Referencia transcrita:", voz.texto_ref)
        narr = reel.narrar(voz, guion, velocidad=a.velocidad)
        print("WER por escena:", [round(e["wer"], 2) for e in guion["escenas"]])
        reel.subtitulos(narr, guion)
        nombre = "reel"
        (sal / "guion_con_wer.json").write_text(json.dumps(guion, ensure_ascii=False, indent=2), encoding="utf-8")

    reel.a_srt(narr, sal / f"{nombre}.srt")
    solo_voz = reel.video(guion, narr, sal / f"{nombre}_solo_voz.mp4", FUENTE, AUTOR)
    mezclar_musica(solo_voz, AQUI / "recursos" / "musica.mp3", sal / f"{nombre}.mp4",
                   volumen=0.35 if a.vista_previa else 0.10)
    reel.portada(guion, narr, sal / "portada.png", FUENTE, AUTOR, escena=0)
    if not a.vista_previa:
        shutil.copy(sal / "reel.srt", AQUI / "subtitulos.srt")
        shutil.copy(sal / "reel.mp4", AQUI / "reel.mp4")
    print(f"Listo: {sal / (nombre + '.mp4')}  ({narr.duracion:.1f} s)")


if __name__ == "__main__":
    main()
