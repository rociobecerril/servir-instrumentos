"""Genera las imágenes de cada escena del reel (900x700, fondo oscuro) a partir de los datos procesados."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Polygon

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "reel" / "recursos"
OUT.mkdir(parents=True, exist_ok=True)
FONDO, TEXTO, SUAVE = "#1C1A17", "#F7F3EC", "#B8AE9F"
CAPP, CPE, MPP, OBS = "#5aa6d6", "#e57a63", "#86b866", "#F08A4B"

c = pd.read_csv(BASE / "datos" / "procesados" / "informes.csv")
plt.rcParams.update({"font.size": 22, "text.color": TEXTO, "axes.labelcolor": SUAVE, "xtick.color": SUAVE,
                     "ytick.color": SUAVE, "axes.edgecolor": "#3a362f", "font.family": "DejaVu Sans"})


def lienzo():
    fig, ax = plt.subplots(figsize=(9, 7), dpi=100)
    fig.patch.set_facecolor(FONDO); ax.set_facecolor(FONDO)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    return fig, ax


def guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(OUT / nombre, facecolor=FONDO)
    plt.close(fig)


# 1. Opiniones por año e instrumento
fig, ax = lienzo()
t = c.pivot_table(index="anio", columns="instrumento", aggfunc="size", fill_value=0)
bottom = 0
for inst, col in [("CAP-P", CAPP), ("CPE", CPE), ("MPP", MPP)]:
    ax.bar(t.index, t[inst], bottom=bottom, color=col, label=inst if inst != "CAP-P" else "CAP Provisional")
    bottom = bottom + t[inst]
ax.set_xticks([2014, 2017, 2020, 2023, 2026])
ax.legend(frameon=False, labelcolor=TEXTO, fontsize=18, loc="upper left", bbox_to_anchor=(0, 1.02), ncol=3)
ax.set_ylim(0, t.sum(axis=1).max() * 1.22)
ax.set_title("Opiniones técnicas por año", color=TEXTO, loc="left", fontsize=26, pad=14)
guardar(fig, "e1_anios.png")

# 2. Participación por instrumento
fig, ax = lienzo()
s = c["instrumento"].value_counts().reindex(["CAP-P", "CPE", "MPP"])
ax.barh(["MPP", "CPE", "CAP Provisional"], s[::-1].values, color=[MPP, CPE, CAPP])
for i, v in enumerate(s[::-1].values):
    ax.text(v + 40, i, f"{v:,}", va="center", color=TEXTO, fontsize=24)
ax.set_xlim(0, s.max() * 1.25); ax.set_xticks([])
ax.spines["bottom"].set_visible(False)
ax.set_title("Opiniones por instrumento", color=TEXTO, loc="left", fontsize=26, pad=14)
guardar(fig, "e2_instrumentos.png")

# 3. Primera propuesta vs. modificación (CAP-P favorable)
fav = c[(c.instrumento == "CAP-P") & (c.opinion == "FAVORABLE")]["momento"].value_counts()
fig, ax = lienzo()
ax.pie([fav["Modificación"], fav["Primera propuesta"]], colors=[OBS, CAPP], startangle=90, counterclock=False,
       wedgeprops={"width": 0.38, "edgecolor": FONDO, "linewidth": 3})
ax.text(0, 0.08, f"{fav['Modificación']:,}", ha="center", fontsize=44, weight="bold")
ax.text(0, -0.2, "modificaciones", ha="center", fontsize=22, color=SUAVE)
ax.legend(["Modificación", "Primera propuesta"], frameon=False, labelcolor=TEXTO, loc="lower center",
          bbox_to_anchor=(0.5, -0.08), ncol=2, fontsize=20)
ax.set_title("CAP Provisional: informes favorables", color=TEXTO, loc="left", fontsize=26)
guardar(fig, "e3_modificaciones.png")

# 4. Tasa de observación por nivel
fig, ax = lienzo()
niv = ["NACIONAL", "REGIONAL", "LOCAL"]
r = c.groupby("nivel")["opinion"].apply(lambda x: (x == "OBSERVADO").mean() * 100).reindex(niv)
ax.bar(["Nacional", "Regional", "Local"], r.values, color=[SUAVE, SUAVE, OBS], width=0.6)
for i, v in enumerate(r.values):
    ax.text(i, v + 2, f"{v:.0f} %", ha="center", fontsize=28, weight="bold")
ax.set_ylim(0, 90); ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.set_title("Propuestas observadas por nivel de gobierno", color=TEXTO, loc="left", fontsize=24, pad=14)
guardar(fig, "e4_nivel.png")

# 5. Tasa local en el tiempo
fig, ax = lienzo()
loc = c[c.nivel == "LOCAL"].groupby("anio")["opinion"].agg(n="size", obs=lambda x: (x == "OBSERVADO").mean() * 100)
loc = loc[loc.n >= 10]
ax.plot(loc.index, loc.obs, color=OBS, lw=5, marker="o", ms=10)
ult = loc.index.max()
ax.annotate(f"{loc.obs.iloc[-1]:.0f} %", (ult, loc.obs.iloc[-1]), xytext=(-10, -46), textcoords="offset points",
            fontsize=30, weight="bold", ha="right", color=TEXTO)
ax.set_ylim(0, 105); ax.set_yticks([0, 50, 100]); ax.set_yticklabels(["0 %", "50 %", "100 %"])
ax.grid(axis="y", color="#3a362f")
ax.set_title("Municipalidades: tasa de observación", color=TEXTO, loc="left", fontsize=26, pad=14)
guardar(fig, "e5_local_tiempo.png")
print("local 2026:", loc.tail(3).round(1).to_dict())

# 6. Entidades con favorable: CAP-P vs CPE
fig, ax = lienzo()
f = c[c.opinion == "FAVORABLE"]
ents = [f[f.instrumento == i].id_entidad.nunique() for i in ["CAP-P", "CPE"]]
ax.bar(["Con CAP Provisional\nfavorable", "Con CPE\nfavorable"], ents, color=[CAPP, CPE], width=0.55)
for i, v in enumerate(ents):
    ax.text(i, v + 20, f"{v:,}", ha="center", fontsize=34, weight="bold")
ax.set_ylim(0, max(ents) * 1.2); ax.set_yticks([]); ax.spines["left"].set_visible(False)
ax.set_title("Entidades: régimen antiguo vs. nuevo", color=TEXTO, loc="left", fontsize=26, pad=14)
guardar(fig, "e6_transito.png")

# 7. Mapa de opiniones por región
geo = json.loads((BASE / "web" / "data" / "departamentos.geojson").read_text(encoding="utf-8"))
cnt = c["region_mapa"].value_counts()
fig, ax = plt.subplots(figsize=(9, 7), dpi=100); fig.patch.set_facecolor(FONDO); ax.set_facecolor(FONDO)
import numpy as np
mx = np.log1p(cnt.max())
cmap = matplotlib.colormaps["YlOrBr"]
for feat in geo["features"]:
    v = cnt.get(feat["properties"]["NOMBDEP"], 0)
    col = cmap(0.15 + 0.8 * np.log1p(v) / mx)
    g = feat["geometry"]
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for p in polys:
        ax.add_patch(Polygon(p[0], closed=True, fc=col, ec=FONDO, lw=1.2))
ax.set_xlim(-82, -68); ax.set_ylim(-21.6, 0.2); ax.set_aspect("equal"); ax.axis("off")
ax.text(-81.8, -19.9, f"Lima: {cnt['LIMA']:,}", fontsize=24, weight="bold")
ax.text(-81.8, -21.0, "opiniones (más oscuro = más)", fontsize=18, color=SUAVE)
ax.set_title("Opiniones técnicas por región", color=TEXTO, loc="left", fontsize=26)
guardar(fig, "e7_mapa.png")
print("listo:", sorted(p.name for p in OUT.glob("e*.png")))
