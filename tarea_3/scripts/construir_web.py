"""Inserta los datos procesados y el GeoJSON en la plantilla y genera web/index.html
(un solo archivo autocontenido, listo para GitHub Pages)."""
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
tpl = (BASE / "web" / "plantilla.html").read_text(encoding="utf-8")
data = (BASE / "web" / "data" / "informes.json").read_text(encoding="utf-8")
geo = (BASE / "web" / "data" / "departamentos.geojson").read_text(encoding="utf-8")
html = tpl.replace("__DATA__", data.replace("</", "<\\/")).replace("__GEO__", geo.replace("</", "<\\/"))
(BASE / "web" / "index.html").write_text(html, encoding="utf-8")
print("web/index.html", round(len(html) / 1024), "KB")
