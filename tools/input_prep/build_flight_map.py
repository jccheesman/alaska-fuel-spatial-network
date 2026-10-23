"""Match flight paths to airports and produce a combined CSV + interactive HTML map.

Uses the Alaska DOT&PF airports dataset (NAME, FAA_ID, ICAO, LAT_DD, LONG_DD, ...).
"""
import json
import re
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
AIRPORTS_CSV = BASE / "airports_ak_dotpf.csv"   # AK DOT&PF registry — provenance for flight_paths_combined.csv
FLIGHTS_XLSX = BASE / "Flight Paths.xlsx"
OUT_CSV = BASE / "flight_paths_combined.csv"
OUT_MAP = BASE / "flight_map.html"
OUT_UNMATCHED = BASE / "unmatched_locations.csv"

# Manual overrides for source names that don't match cleanly.
# Map: normalized location name -> FAA_ID in airports.csv
MANUAL_OVERRIDES = {
    "atmauluak": "4A2",   # Atmautluak (typo)
    "husila": "HLA",      # Huslia (typo)
    "kivilina": "KVL",    # Kivalina (typo)
    "shugnak": "SHG",     # Shungnak (typo)
    "nunpitchuk": "16A",  # Nunapitchuk (typo)
    "metarvik": "EWU",    # Mertavik (relocated Newtok village)
    "nondalton runway": "5NN",
    "little diomede": "DM2",
    "barter island": "BTI",
    "deadhorse": "SCC",
    "st marys": "KSM",
    "st michael": "SMK",
    "king salmon": "AKN",
    "anaktuvuk pass": "AKP",
    "arctic village": "ARC",
    "fort yukon": "FYU",
    "point hope": "PHO",
}

# Locations not present in the DOT&PF dataset (e.g. military) — hard-coded.
# Map: normalized name -> synthetic airport record
HARDCODED_AIRPORTS = {
    "tin city": {
        "NAME": "Tin City LRRS Airport",
        "FAA_ID": "TNC",
        "ICAO": "PATC",
        "STATUS": "Other",
        "REGION": "Northern",
        "OWNER": "US Air Force",
        "LAT_DD": 65.5634,
        "LONG_DD": -167.9217,
    },
}


def normalize(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.replace("’", "'").replace("‘", "'")
    s = s.lower()
    # "saint" -> "st" so both forms collapse
    s = re.sub(r"\bsaint\b", "st", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


SUFFIXES = (" apt", " spb", " heliport", " airport", " runway",
            " long range radar station", " lrrs")


def base_name(name: str) -> str:
    n = normalize(name)
    changed = True
    while changed:
        changed = False
        for suf in SUFFIXES:
            if n.endswith(suf):
                n = n[: -len(suf)].strip()
                changed = True
    return n


def load_airports() -> pd.DataFrame:
    df = pd.read_csv(AIRPORTS_CSV, encoding="utf-8-sig", low_memory=False)
    df = df.rename(columns=str.strip)
    keep = ["NAME", "OWNER", "STATUS", "REGION", "LAT_DD", "LONG_DD", "FAA_ID", "ICAO"]
    df = df[keep].copy()
    df["LAT_DD"] = pd.to_numeric(df["LAT_DD"], errors="coerce")
    df["LONG_DD"] = pd.to_numeric(df["LONG_DD"], errors="coerce")
    df = df.dropna(subset=["LAT_DD", "LONG_DD"])
    return df


def build_lookup(airports: pd.DataFrame):
    """Return (faa_lookup, name_lookup)."""
    faa = {}
    # Prefer Standard status when an FAA_ID is duplicated (e.g., AKN apt vs SPB)
    status_rank = {"Standard": 0, "SubStandard": 1, "Sea Plane Base": 2,
                   "Other Sea Plane Base": 3, "Other": 4}
    a = airports.copy()
    a["_srank"] = a["STATUS"].map(status_rank).fillna(9)
    a = a.sort_values("_srank")
    for _, r in a.iterrows():
        code = str(r["FAA_ID"]).strip().upper() if isinstance(r["FAA_ID"], str) else ""
        if code and code not in faa:
            faa[code] = r

    name_lookup = {}
    for _, r in a.iterrows():
        key = base_name(r["NAME"])
        if key and key not in name_lookup:
            name_lookup[key] = r

    return faa, name_lookup


def match_location(name, faa_lookup, name_lookup):
    if not isinstance(name, str) or not name.strip():
        return None
    raw = name.strip()
    norm = normalize(raw)

    # 0. Hard-coded airports not present in the authoritative dataset
    if norm in HARDCODED_AIRPORTS:
        return pd.Series(HARDCODED_AIRPORTS[norm])

    # 1. Manual override
    if norm in MANUAL_OVERRIDES:
        key = MANUAL_OVERRIDES[norm].upper()
        if key in faa_lookup:
            return faa_lookup[key]

    # 2. 3-letter all-caps code -> FAA_ID
    if len(raw) == 3 and raw.isupper() and raw in faa_lookup:
        return faa_lookup[raw]

    # 3. Direct base-name match
    if norm in name_lookup:
        return name_lookup[norm]

    # 4. Strip common suffix from input and retry
    bn = base_name(raw)
    if bn in name_lookup:
        return name_lookup[bn]

    # 5. Loose containment (only if input is a substring of an airport base name
    #    or vice versa, with min length to avoid false hits)
    if len(bn) >= 4:
        for key, row in name_lookup.items():
            if key == bn:
                return row
            if bn in key.split() or key in bn.split():
                return row

    return None


def to_dict(r):
    if r is None:
        return None
    return {
        "name": r["NAME"],
        "faa": r["FAA_ID"] if isinstance(r["FAA_ID"], str) else "",
        "icao": r["ICAO"] if isinstance(r["ICAO"], str) else "",
        "status": r["STATUS"] if isinstance(r["STATUS"], str) else "",
        "region": r["REGION"] if isinstance(r["REGION"], str) else "",
        "owner": r["OWNER"] if isinstance(r["OWNER"], str) else "",
        "lat": float(r["LAT_DD"]),
        "lon": float(r["LONG_DD"]),
    }


def main():
    print("Loading airports...")
    airports = load_airports()
    faa_lookup, name_lookup = build_lookup(airports)
    print(f"  {len(airports)} airports, {len(faa_lookup)} FAA codes, "
          f"{len(name_lookup)} unique base names")

    print("Loading flight paths...")
    flights = pd.read_excel(FLIGHTS_XLSX)
    print(f"  {len(flights)} flight rows")

    combined_rows = []
    unmatched = set()
    for _, fr in flights.iterrows():
        o_name, d_name = fr["Origin"], fr["Destination"]
        o_air = match_location(o_name, faa_lookup, name_lookup)
        d_air = match_location(d_name, faa_lookup, name_lookup)
        if o_air is None:
            unmatched.add(str(o_name))
        if d_air is None:
            unmatched.add(str(d_name))

        row = {
            "Origin": o_name,
            "Destination": d_name,
            "Carrier": fr.get("Carrier", ""),
            "Notes": fr.get("Notes", ""),
            "Source": fr.get("Source", ""),
        }
        for prefix, air in (("Origin", o_air), ("Destination", d_air)):
            d = to_dict(air) or {}
            row[f"{prefix}_Airport_Name"] = d.get("name", "")
            row[f"{prefix}_FAA_ID"] = d.get("faa", "")
            row[f"{prefix}_ICAO"] = d.get("icao", "")
            row[f"{prefix}_Status"] = d.get("status", "")
            row[f"{prefix}_Region"] = d.get("region", "")
            row[f"{prefix}_Owner"] = d.get("owner", "")
            row[f"{prefix}_Lat"] = d.get("lat", "")
            row[f"{prefix}_Lon"] = d.get("lon", "")
        combined_rows.append(row)

    combined = pd.DataFrame(combined_rows)
    combined.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV.name}  ({len(combined)} rows)")

    if unmatched:
        pd.DataFrame({"unmatched": sorted(unmatched)}).to_csv(OUT_UNMATCHED, index=False)
        print(f"  WARNING: {len(unmatched)} unmatched -> {OUT_UNMATCHED.name}")
        for u in sorted(unmatched):
            print(f"    - {u}")
    else:
        # Clean up any stale unmatched file
        if OUT_UNMATCHED.exists():
            OUT_UNMATCHED.unlink()

    # Build map data
    airport_points = {}
    paths = []
    for _, r in combined.iterrows():
        if r["Origin_Lat"] == "" or r["Destination_Lat"] == "":
            continue
        for prefix in ("Origin", "Destination"):
            key = r[f"{prefix}_Airport_Name"]
            if key and key not in airport_points:
                airport_points[key] = {
                    "name": r[f"{prefix}_Airport_Name"],
                    "faa":  r[f"{prefix}_FAA_ID"],
                    "icao": r[f"{prefix}_ICAO"],
                    "status": r[f"{prefix}_Status"],
                    "region": r[f"{prefix}_Region"],
                    "owner":  r[f"{prefix}_Owner"],
                    "lat": float(r[f"{prefix}_Lat"]),
                    "lon": float(r[f"{prefix}_Lon"]),
                    "roles": set(),
                }
            if key:
                airport_points[key]["roles"].add(prefix.lower())
        paths.append({
            "from": [float(r["Origin_Lat"]), float(r["Origin_Lon"])],
            "to":   [float(r["Destination_Lat"]), float(r["Destination_Lon"])],
            "origin": r["Origin"], "destination": r["Destination"],
            "carrier": r["Carrier"], "notes": r["Notes"], "source": r["Source"],
        })

    for v in airport_points.values():
        v["roles"] = sorted(v["roles"])

    map_data = {"airports": list(airport_points.values()), "paths": paths}
    write_html(map_data)
    print(f"Wrote {OUT_MAP.name}  ({len(map_data['airports'])} airports, {len(paths)} paths)")


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Alaska Flight Paths</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
  html, body, #map { height: 100%; margin: 0; }
  .legend {
    background: white; padding: 8px 10px; font: 13px/1.4 sans-serif;
    border-radius: 4px; box-shadow: 0 1px 4px rgba(0,0,0,.3);
  }
  .legend .dot { display:inline-block; width:10px; height:10px; border-radius:50%;
                 margin-right:6px; vertical-align:middle; }
  .popup { font: 13px/1.4 sans-serif; }
  .popup b { font-size: 14px; }
</style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA = __DATA__;

const map = L.map('map').setView([64.5, -155], 4);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

const pathLayer = L.layerGroup().addTo(map);
const airportLayer = L.layerGroup().addTo(map);

DATA.paths.forEach(p => {
  const line = L.polyline([p.from, p.to], {
    color: '#1f77b4', weight: 1.5, opacity: 0.55
  });
  line.bindPopup(`<div class="popup">
    <b>${p.origin} &rarr; ${p.destination}</b><br>
    <b>Carrier:</b> ${p.carrier || ''}<br>
    <b>Notes:</b> ${p.notes || ''}<br>
    <b>Source:</b> ${p.source || ''}
  </div>`);
  pathLayer.addLayer(line);
});

DATA.airports.forEach(a => {
  const isOrigin = a.roles.includes('origin');
  const color = isOrigin ? '#d62728' : '#2ca02c';
  const marker = L.circleMarker([a.lat, a.lon], {
    radius: isOrigin ? 7 : 5,
    color: color, fillColor: color, fillOpacity: 0.85, weight: 1
  });
  marker.bindPopup(`<div class="popup">
    <b>${a.name}</b><br>
    <b>FAA:</b> ${a.faa || '-'} &nbsp; <b>ICAO:</b> ${a.icao || '-'}<br>
    <b>Status:</b> ${a.status || '-'}<br>
    <b>Region:</b> ${a.region || '-'}<br>
    <b>Owner:</b> ${a.owner || '-'}<br>
    <b>Role:</b> ${a.roles.join(', ')}
  </div>`);
  airportLayer.addLayer(marker);
});

const legend = L.control({position: 'bottomright'});
legend.onAdd = function() {
  const div = L.DomUtil.create('div', 'legend');
  div.innerHTML = `
    <div><span class="dot" style="background:#d62728"></span>Origin (hub)</div>
    <div><span class="dot" style="background:#2ca02c"></span>Destination</div>
    <div style="margin-top:4px;"><span style="display:inline-block;width:18px;height:2px;background:#1f77b4;vertical-align:middle;margin-right:6px"></span>Flight path</div>
    <div style="margin-top:6px;color:#666;">Click markers/lines for details</div>
  `;
  return div;
};
legend.addTo(map);

if (DATA.airports.length) {
  const bounds = L.latLngBounds(DATA.airports.map(a => [a.lat, a.lon]));
  map.fitBounds(bounds, { padding: [30, 30] });
}
</script>
</body>
</html>
"""


def write_html(data):
    OUT_MAP.write_text(HTML_TEMPLATE.replace("__DATA__", json.dumps(data)))


if __name__ == "__main__":
    main()
