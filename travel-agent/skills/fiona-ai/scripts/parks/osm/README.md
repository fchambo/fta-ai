# Park maps from OpenStreetMap

Each `<park>.json` here holds a park's outline, water, green areas, plazas, buildings, attraction
footprints and walkway network, extracted from OpenStreetMap by `tools/osm_park.py` (see the `osm`
block in `../<park>.json`). Patty uses it for walking times and to draw the real park map in the PDF.

Map data © OpenStreetMap contributors, available under the Open Database License (ODbL 1.0):
https://www.openstreetmap.org/copyright. Every map drawn from it shows "© OpenStreetMap contributors".

To refresh a park: `python3 tools/osm_park.py <park>` (downloads the area from the OSM API).
