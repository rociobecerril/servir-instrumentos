"""Procesa el consolidado de informes técnicos de SERVIR (CAP Provisional, CPE, MPP)
y genera los archivos que consume el dashboard.

Entrada : datos/originales/consolidado_informes.csv  (extracto sin datos personales)
          datos/originales/maestro_entidades.csv
Salida  : datos/procesados/informes.csv
          web/data/informes.json, web/data/entidades.json, web/data/resumen.json
"""
import json
import unicodedata
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
ORIG = BASE / "datos" / "originales"
PROC = BASE / "datos" / "procesados"
WEB = BASE / "web" / "data"
PROC.mkdir(parents=True, exist_ok=True)
WEB.mkdir(parents=True, exist_ok=True)

INSTRUMENTOS = {"CAP Provisional": "CAP-P", "CPE": "CPE", "MPP": "MPP"}


def sin_tildes(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).upper().strip()


def main():
    c = pd.read_csv(ORIG / "consolidado_informes.csv", dtype=str)
    m = pd.read_csv(ORIG / "maestro_entidades.csv", dtype=str)

    n0 = len(c)
    # 1. Solo los tres instrumentos centrales del sistema
    c = c[c["instrumento"].isin(INSTRUMENTOS)].copy()
    c["instrumento"] = c["instrumento"].map(INSTRUMENTOS)
    # 2. Normalización de textos
    c["nivel"] = c["nivel"].str.strip().str.upper()
    c["opinion"] = c["opinion"].str.strip().str.upper()
    c["region"] = c["region"].map(sin_tildes)
    c.loc[c["region"].isin(["LIMA REGION", "LIMA"]), "region"] = "LIMA PROVINCIAS"
    c["anio"] = pd.to_numeric(c["anio"], errors="coerce").astype("Int64")
    # 3. Solo opiniones de fondo: favorable u observado
    c = c[c["opinion"].isin(["FAVORABLE", "OBSERVADO"])]
    c = c[c["anio"].between(2014, 2026)]
    # 4. Duplicados exactos por número de informe y entidad
    c = c.drop_duplicates(subset=["n_informe", "id_entidad", "instrumento"])
    # 5. Tipo de pronunciamiento (primera propuesta vs. modificación)
    op = c["oportunidad"].fillna("").str.lower()
    c["momento"] = "Sin dato"
    c.loc[op.str.contains("primer") & ~op.str.contains("modific"), "momento"] = "Primera propuesta"
    c.loc[op.str.contains("modific"), "momento"] = "Modificación"

    # 6. Cruce con el maestro de entidades (ubigeo y coordenadas)
    m = m.drop_duplicates("id_entidad")
    c = c.merge(m[["id_entidad", "entidad_final", "ubigeo", "departamento", "lat", "lon"]],
                on="id_entidad", how="left")
    c["region_mapa"] = c["region"].where(~c["region"].isin(["LIMA METROPOLITANA", "LIMA PROVINCIAS"]), "LIMA")
    c["region_mapa"] = c["region_mapa"].replace({"NACIONAL": None})

    cols = ["id_entidad", "entidad_final", "nombre", "instrumento", "anio", "nivel", "region",
            "region_mapa", "tipo_entidad", "opinion", "momento", "n_informe", "ubigeo", "lat", "lon"]
    c = c[cols].sort_values(["anio", "instrumento"])
    c.to_csv(PROC / "informes.csv", index=False, encoding="utf-8")

    # JSON compacto para la web
    reg = c.assign(entidad=c["entidad_final"].fillna(c["nombre"]))
    reg = reg[["id_entidad", "entidad", "instrumento", "anio", "nivel", "region", "region_mapa",
               "tipo_entidad", "opinion", "momento", "lat", "lon"]]
    reg["lat"] = pd.to_numeric(reg["lat"], errors="coerce").round(4)
    reg["lon"] = pd.to_numeric(reg["lon"], errors="coerce").round(4)
    reg["anio"] = reg["anio"].astype(int)
    rows = reg.where(reg.notna(), None).values.tolist()
    (WEB / "informes.json").write_text(
        json.dumps({"cols": list(reg.columns), "rows": rows}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")

    resumen = {
        "registros_originales": n0,
        "registros_analizados": len(c),
        "entidades": int(c["id_entidad"].nunique()),
        "con_coordenadas": int(pd.to_numeric(c["lat"], errors="coerce").notna().sum()),
        "anio_min": int(c["anio"].min()), "anio_max": int(c["anio"].max()),
    }
    (WEB / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(resumen)


if __name__ == "__main__":
    main()
