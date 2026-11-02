"""Extrae de la matriz consolidada de SERVIR (Excel interno de la DDSRH) solo los campos
públicos de los informes técnicos y del maestro de entidades. No se exportan nombres de
personal, comentarios internos ni registros de asistencia técnica.

Uso: python scripts/obtener_datos.py ruta/equivalencias_y_maestro_todo_revisado.xlsx
"""
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
ORIG = BASE / "datos" / "originales"
ORIG.mkdir(parents=True, exist_ok=True)


def main(xlsx):
    c = pd.read_excel(xlsx, sheet_name="CONSOLIDADO DE INFORMES")
    c = c.rename(columns={
        "ID_FINAL": "id_entidad", "INSTRUMENTO O DOCUMENTO": "instrumento", "AÑO": "anio",
        "MES": "mes", "NOMBRE": "nombre", "NIVEL DE GOBIERNO": "nivel",
        "TIPO DE ENTIDAD": "tipo_entidad", "SECTOR": "sector", "REGIÓN": "region",
        "TIPO DE OPINIÓN": "opinion", "OPORTUNIDAD DE OPINIÓN": "oportunidad",
        "N° DE INFORME ": "n_informe", "FECHA DEL INFORME ": "fecha_informe",
    })
    keep = ["id_entidad", "instrumento", "anio", "mes", "nombre", "nivel", "tipo_entidad",
            "sector", "region", "opinion", "oportunidad", "n_informe", "fecha_informe"]
    c[keep].to_csv(ORIG / "consolidado_informes.csv", index=False, encoding="utf-8")

    m = pd.read_excel(xlsx, sheet_name="Maestro", header=1)
    m = m.rename(columns={"ID_FINAL N": "id_entidad", "ENTIDAD": "entidad_final",
                          "UBIGEO": "ubigeo", "DEPARTAMENTO": "departamento",
                          "LATITUD": "lat", "LONGITUD": "lon"})
    m[["id_entidad", "entidad_final", "ubigeo", "departamento", "lat", "lon"]].to_csv(
        ORIG / "maestro_entidades.csv", index=False, encoding="utf-8")
    print(len(c), "informes;", len(m), "entidades")


if __name__ == "__main__":
    main(sys.argv[1])
