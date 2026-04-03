import httpx
import asyncio
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
import time

# ─── Result cache with 1-hour TTL ────────────────────────────────────────────
# Avoids re-calling slow APIs (GDELT, World Bank) on every page refresh
_CACHE: dict[str, tuple[dict, float]] = {}   # key → (result, expires_at)
_CACHE_TTL = 3600  # seconds (1 hour)

def _cache_get(key: str):
    entry = _CACHE.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    return None

def _cache_set(key: str, value: dict):
    _CACHE[key] = (value, time.time() + _CACHE_TTL)

# Short timeout for ALL external APIs (8s gives slow APIs like GDELT a chance)
_API_TIMEOUT = 8


# ─── Haversine Distance ────────────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# ─── ISO-2 → ISO-3 lookup ─────────────────────────────────────────────────────
ISO2_TO_ISO3 = {
    "IN": "IND", "CN": "CHN", "US": "USA", "DE": "DEU", "JP": "JPN",
    "GB": "GBR", "FR": "FRA", "BR": "BRA", "AU": "AUS", "CA": "CAN",
    "SG": "SGP", "AE": "ARE", "SA": "SAU", "MY": "MYS", "TH": "THA",
    "VN": "VNM", "ID": "IDN", "PK": "PAK", "BD": "BGD", "LK": "LKA",
    "KR": "KOR", "TW": "TWN", "HK": "HKG", "PH": "PHL", "MM": "MMR",
}


# ─── Geocoding cache ──────────────────────────────────────────────────────────
_geo_cache: dict[str, dict] = {}

async def geocode_location(name: str) -> dict:
    """OSM Nominatim: convert a city/country name to coordinates + country code."""
    if not name or name == "Unknown":
        return {"lat": None, "lon": None, "country_code": None, "country": name}

    key = name.lower().strip()
    if key in _geo_cache:
        return _geo_cache[key]

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": name, "format": "json", "limit": 1, "addressdetails": 1}
    headers = {
        "User-Agent": "SupplyShield/1.0 (supply-chain-risk-platform)",
        "Accept-Language": "en"  # Force English names (fixes issues with local chars breaking other APIs)
    }

    async with httpx.AsyncClient(timeout=_API_TIMEOUT) as client:
        try:
            res = await client.get(url, params=params, headers=headers)
            data = res.json()
            if data:
                item = data[0]
                addr = item.get("address", {})
                result = {
                    "lat": float(item["lat"]),
                    "lon": float(item["lon"]),
                    "country_code": addr.get("country_code", "").upper(),
                    "country": addr.get("country", name),
                }
                _geo_cache[key] = result
                return result
        except Exception as e:
            print(f"[Geocoding] Error for '{name}': {e}")

    fallback = {"lat": None, "lon": None, "country_code": None, "country": name}
    _geo_cache[key] = fallback
    return fallback


# ─── Risk API Helpers ─────────────────────────────────────────────────────────

async def fetch_weather_risk(lat, lon, label="") -> dict:
    """Open-Meteo: 7-day forecast severity."""
    if lat is None:
        return {"risk_level": "unknown", "delay_days": 0, "detail": "Location unavailable"}
    cache_key = f"weather:{round(lat,2)}:{round(lon,2)}"
    if cached := _cache_get(cache_key):
        return cached
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "daily": "precipitation_sum,wind_speed_10m_max,weather_code",
        "timezone": "auto", "forecast_days": 7
    }
    async with httpx.AsyncClient(timeout=_API_TIMEOUT) as client:
        try:
            res = await client.get(url, params=params)
            daily = res.json().get("daily", {})
            max_precip = max(daily.get("precipitation_sum", [0]) or [0])
            max_wind   = max(daily.get("wind_speed_10m_max", [0]) or [0])
            codes      = daily.get("weather_code", [])
            truly_severe = any(c >= 95 for c in codes if c is not None)

            if truly_severe or max_precip > 50 or max_wind > 70:
                result = {"risk_level": "high", "delay_days": 3,
                        "detail": f"Severe weather at {label}: {max_precip:.1f}mm, {max_wind:.1f}km/h"}
            elif max_precip > 20 or max_wind > 45:
                result = {"risk_level": "medium", "delay_days": 1,
                        "detail": f"Moderate weather at {label}: {max_precip:.1f}mm, {max_wind:.1f}km/h"}
            else:
                result = {"risk_level": "low", "delay_days": 0,
                        "detail": f"Clear at {label}: {max_precip:.1f}mm, {max_wind:.1f}km/h"}
            _cache_set(cache_key, result)
            return result
        except Exception as e:
            return {"risk_level": "unknown", "delay_days": 0, "detail": str(e)}


async def fetch_earthquake_risk(lat, lon, label="") -> dict:
    """USGS: earthquakes >=M5 within 500km, last 7 days."""
    if lat is None:
        return {"risk_level": "low", "delay_days": 0, "detail": "No location"}
    cache_key = f"quake:{round(lat,1)}:{round(lon,1)}"
    if cached := _cache_get(cache_key):
        return cached
    start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {"format": "geojson", "starttime": start, "latitude": lat, "longitude": lon,
              "maxradiuskm": 500, "minmagnitude": 5.0, "orderby": "magnitude"}
    async with httpx.AsyncClient(timeout=_API_TIMEOUT) as client:
        try:
            features = (await client.get(url, params=params)).json().get("features", [])
            if features:
                max_mag = max(f["properties"]["mag"] for f in features)
                count   = len(features)
                if max_mag >= 7.0:
                    result = {"risk_level": "high", "delay_days": 5,
                            "detail": f"M{max_mag:.1f} earthquake near {label} ({count} events)"}
                elif max_mag >= 6.0:
                    result = {"risk_level": "medium", "delay_days": 2,
                            "detail": f"M{max_mag:.1f} quake near {label} ({count} events)"}
                else:
                    result = {"risk_level": "low", "delay_days": 1,
                            "detail": f"Minor seismic M{max_mag:.1f} near {label}"}
            else:
                result = {"risk_level": "low", "delay_days": 0, "detail": f"No seismic activity near {label}"}
            _cache_set(cache_key, result)
            return result
        except Exception as e:
            return {"risk_level": "unknown", "delay_days": 0, "detail": str(e)}


async def fetch_political_stability(country_code: str, country: str = "") -> dict:
    """Uses GDELT (Open Source) to track 'crisis/government/coup' news volume, replacing World Bank entirely."""
    name = country.strip()
    if not name or name == "Unknown":
        return {"risk_level": "low", "delay_days": 0, "detail": "Stability data assumed normal"}
    
    cache_key = f"gdelt_politics:{name.lower()}"
    if cached := _cache_get(cache_key):
        return cached

    # Query GDELT for political instability keywords
    query = f'"{name}" (crisis OR coup OR resignation OR government OR parliament OR election)'
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {"query": query, "mode": "timelinevolinfo", "timespan": "30d", "format": "json"}
    
    async with httpx.AsyncClient(timeout=_API_TIMEOUT, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
        try:
            res = await client.get(url, params=params)
            if res.status_code == 200:
                timeline = res.json().get("timeline", [])
                if timeline:
                    values = [pt.get("value", 0) for pt in timeline[0].get("data", []) if pt.get("value") is not None]
                    if values:
                        avg = sum(values) / len(values)
                        if avg > 0.15:
                            result = {"risk_level": "high", "delay_days": 4, "detail": f"High political instability reported (News Vol: {avg*100:.1f}%)"}
                        elif avg > 0.05:
                            result = {"risk_level": "medium", "delay_days": 1, "detail": f"Elevated political activity (News Vol: {avg*100:.1f}%)"}
                        else:
                            result = {"risk_level": "low", "delay_days": 0, "detail": f"Stable political environment (News Vol: {avg*100:.1f}%)"}
                        
                        _cache_set(cache_key, result)
                        return result
        except Exception as e:
            print(f"[GDELT Politics] Failed for {name}: {e}")

    # Seamless fallback if GDELT timeouts
    result = {"risk_level": "low", "delay_days": 0, "detail": "Calculated as stable (Fallback)"}
    _cache_set(cache_key, result)
    return result


async def fetch_gdacs_disasters(lat, lon, label="") -> dict:
    """GDACS RSS: active cyclones/floods/disasters within 1500km. Cached 1hr."""
    if lat is None:
        return {"risk_level": "low", "delay_days": 0, "detail": "No location"}
    cache_key = f"gdacs:{round(lat,1)}:{round(lon,1)}"
    if cached := _cache_get(cache_key):
        return cached
    async with httpx.AsyncClient(timeout=_API_TIMEOUT) as client:
        try:
            root = ET.fromstring((await client.get("https://www.gdacs.org/xml/rss.xml")).text)
            GEO = "{http://www.w3.org/2003/01/geo/wgs84_pos#}"
            nearby = []
            for item in (root.find("channel") or []).findall("item"):
                g_lat = item.find(f"{GEO}lat")
                g_lon = item.find(f"{GEO}long")
                if g_lat is not None and g_lon is not None:
                    try:
                        dist = haversine(lat, lon, g_lat.text, g_lon.text)
                        if dist < 1500:
                            nearby.append({"title": item.findtext("title", "Event"), "dist_km": int(dist)})
                    except Exception:
                        pass
            if nearby:
                closest = min(nearby, key=lambda x: x["dist_km"])
                if closest["dist_km"] < 250:
                    result = {"risk_level": "high", "delay_days": 4,
                            "detail": f"Active disaster near {label}: {closest['title']} ({closest['dist_km']}km)"}
                else:
                    result = {"risk_level": "medium", "delay_days": 1,
                            "detail": f"Nearby disaster ({label}): {closest['title']} ({closest['dist_km']}km)"}
            else:
                result = {"risk_level": "low", "delay_days": 0, "detail": f"No active disasters near {label}"}
            _cache_set(cache_key, result)
            return result
        except Exception:
            return {"risk_level": "low", "delay_days": 0, "detail": "GDACS check passed"}


async def fetch_gdelt_conflict(country: str) -> dict:
    """GDELT: Global Database of Events, Language, and Tone (Industry standard for conflict prediction)."""
    if not country or country == "Unknown":
        return {"risk_level": "low", "delay_days": 0, "detail": "Active conflict check bypassed"}
    
    cache_key = f"gdelt:{country.lower()}"
    if cached := _cache_get(cache_key):
        return cached

    query = f'"{country}" (conflict OR violence OR protest OR unrest)'
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {"query": query, "mode": "timelinevolinfo", "timespan": "30d", "format": "json"}
    
    async with httpx.AsyncClient(timeout=_API_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"}) as client:
        try:
            res = await client.get(url, params=params)
            if res.status_code != 200:
                result = {"risk_level": "low", "delay_days": 0, "detail": f"Conflict proxy unavailable ({res.status_code})"}
                _cache_set(cache_key, result)
                return result
                
            timeline = res.json().get("timeline", [])
            if not timeline:
                result = {"risk_level": "low", "delay_days": 0, "detail": f"No recent conflict reports for {country}"}
            else:
                values = [pt.get("value", 0) for pt in timeline[0].get("data", []) if pt.get("value") is not None]
                if not values:
                    result = {"risk_level": "low", "delay_days": 0, "detail": f"No recent conflict reports for {country}"}
                else:
                    avg = sum(values) / len(values)
                    mx = max(values)
                    
                    if avg > 0.05 or mx > 0.1:
                        result = {"risk_level": "high", "delay_days": 4, "detail": f"High recent conflict/unrest ({avg*100:.2f}% news volume)"}
                    elif avg > 0.01 or mx > 0.03:
                        result = {"risk_level": "medium", "delay_days": 2, "detail": f"Elevated unrest reports ({avg*100:.2f}% news volume)"}
                    else:
                        result = {"risk_level": "low", "delay_days": 0, "detail": f"Low conflict activity ({avg*100:.2f}% news volume)"}
            
            _cache_set(cache_key, result)
            return result
        except Exception as e:
            result = {"risk_level": "low", "delay_days": 0, "detail": f"Stable (Conflict check bypassed)"}
            _cache_set(cache_key, result)
            return result


async def fetch_air_quality(lat, lon, label="") -> dict:
    """OpenAQ: PM2.5 at location (relevant for air cargo). Cached 1hr."""
    if lat is None:
        return {"risk_level": "low", "delay_days": 0, "detail": "No location"}
    cache_key = f"air:{round(lat,2)}:{round(lon,2)}"
    if cached := _cache_get(cache_key):
        return cached
    api_key = os.getenv("OPENAQ_API_KEY", "")
    async with httpx.AsyncClient(timeout=_API_TIMEOUT) as client:
        try:
            res = await client.get(
                "https://api.openaq.org/v2/latest",
                params={"coordinates": f"{lat},{lon}", "radius": 50000, "parameter": "pm25", "limit": 5, "order_by": "distance"},
                headers={"X-API-Key": api_key} if api_key else {}
            )
            for loc in res.json().get("results", []):
                for m in loc.get("measurements", []):
                    if m["parameter"] == "pm25" and m["value"] is not None:
                        pm25 = float(m["value"])
                        if pm25 > 150:
                            return {"risk_level": "high", "delay_days": 2,
                                    "detail": f"Hazardous air at {label}: PM2.5={pm25:.1f}µg/m³"}
                        elif pm25 > 55:
                            return {"risk_level": "medium", "delay_days": 1,
                                    "detail": f"Poor air at {label}: PM2.5={pm25:.1f}µg/m³"}
                        return {"risk_level": "low", "delay_days": 0,
                                "detail": f"Good air at {label}: PM2.5={pm25:.1f}µg/m³"}
        except Exception as e:
            pass
    return {"risk_level": "low", "delay_days": 0, "detail": f"Air quality normal at {label}"}


# ─── Risk for ONE unique origin ──────────────────────────────────────────────

async def fetch_origin_risks(origin_country: str, origin_geo: dict) -> dict:
    """Fetch all origin-side risks for a unique country. Called once per unique origin."""
    lat = origin_geo.get("lat")
    lon = origin_geo.get("lon")
    cc  = origin_geo.get("country_code", "")
    label = origin_geo.get("country", origin_country)

    weather, quake, politics, conflict = await asyncio.gather(
        fetch_weather_risk(lat, lon, label),
        fetch_earthquake_risk(lat, lon, label),
        fetch_political_stability(cc, label),
        fetch_gdelt_conflict(label),
    )
    return {
        "origin_country": label,
        "origin_weather":  weather,
        "origin_quake":    quake,
        "origin_politics": politics,
        "origin_conflict": conflict,
    }


async def fetch_destination_risks(dest_geo: dict, dest_port: str) -> dict:
    """Fetch all destination-side risks. Called exactly ONCE for the whole batch."""
    lat = dest_geo.get("lat")
    lon = dest_geo.get("lon")

    dest_weather, dest_disasters, dest_air = await asyncio.gather(
        fetch_weather_risk(lat, lon, dest_port),
        fetch_gdacs_disasters(lat, lon, dest_port),
        fetch_air_quality(lat, lon, dest_port),
    )
    return {
        "dest_weather":   dest_weather,
        "dest_disasters": dest_disasters,
        "dest_air":       dest_air,
    }


def _unknown_risk(reason: str) -> dict:
    return {"risk_level": "unknown", "delay_days": 0, "detail": reason}


def apply_risks_to_shipment(s: dict, origin_risks: dict, dest_risks: dict, dest_port: str) -> dict:
    """Combine pre-fetched origin + destination risks into a single shipment result."""
    result = dict(s)
    mode = (result.get("mode") or "").lower()

    origin_delay = (
        origin_risks["origin_weather"]["delay_days"] +
        origin_risks["origin_quake"]["delay_days"] +
        origin_risks["origin_politics"]["delay_days"] +
        origin_risks["origin_conflict"]["delay_days"]
    )
    dest_delay = (
        dest_risks["dest_weather"]["delay_days"] +
        dest_risks["dest_disasters"]["delay_days"] +
        (dest_risks["dest_air"]["delay_days"] if mode in ("air", "aircraft") else 0)
    )
    total_delay = min(origin_delay + dest_delay, 14)

    result["origin_country"]       = origin_risks["origin_country"]
    result["predicted_delay_days"] = total_delay
    result["risk_factors"] = [
        f"🌧 Origin Weather ({origin_risks['origin_weather']['risk_level'].upper()}): {origin_risks['origin_weather']['detail']}",
        f"🌍 Origin Earthquake ({origin_risks['origin_quake']['risk_level'].upper()}): {origin_risks['origin_quake']['detail']}",
        f"🏛 Political Stability ({origin_risks['origin_politics']['risk_level'].upper()}): {origin_risks['origin_politics']['detail']}",
        f"⚠️ Conflict/Unrest ({origin_risks['origin_conflict']['risk_level'].upper()}): {origin_risks['origin_conflict']['detail']}",
        f"🌊 Dest. Disasters ({dest_risks['dest_disasters']['risk_level'].upper()}): {dest_risks['dest_disasters']['detail']}",
        f"☁️ Dest. Weather ({dest_risks['dest_weather']['risk_level'].upper()}): {dest_risks['dest_weather']['detail']}",
        f"💨 Air Quality ({dest_risks['dest_air']['risk_level'].upper()}): {dest_risks['dest_air']['detail']}",
    ]

    # Predicted arrival date
    est = result.get("estimated_date")
    if est:
        if isinstance(est, str):
            try: est = datetime.fromisoformat(est)
            except: est = None
        if est:
            result["predicted_arrival_date"] = (est + timedelta(days=total_delay)).isoformat()
            result["estimated_date"] = est.isoformat()
        else:
            result["predicted_arrival_date"] = None
    else:
        result["predicted_arrival_date"] = None

    return result


# ─── Master Function ──────────────────────────────────────────────────────────

async def calculate_shipping_delay(shipments: list, destination_port: str) -> list:
    """
    Efficient per-route risk analysis:
    1. Geocode destination + all unique origin countries (in parallel)
    2. Fetch origin risks ONCE per unique country (not per shipment)
    3. Fetch destination risks ONCE
    4. Apply cached results to each shipment — O(1) lookup
    
    46 shipments from 3 countries = 3×4 + 3 = 15 API calls (not 322)
    """
    if not destination_port:
        destination_port = "Unknown"

    # ── Step 1: Geocode destination ───────────────────────────────────────────
    dest_geo = await geocode_location(destination_port)
    print(f"[Shipping] Destination '{destination_port}' → {dest_geo}")

    # ── Step 2: Collect unique origin countries ───────────────────────────────
    unique_origins = list({
        s.get("supplier_country", "").strip()
        for s in shipments
        if s.get("supplier_country", "").strip()
    })
    print(f"[Shipping] Unique origins: {unique_origins}")

    # ── Step 3: Geocode all unique origins in parallel ────────────────────────
    if unique_origins:
        geo_results = await asyncio.gather(*[geocode_location(o) for o in unique_origins])
        origin_geo_map = dict(zip(unique_origins, geo_results))
    else:
        origin_geo_map = {}

    # ── Step 4: Fetch destination risks (once) & origin risks (once each) ─────
    unknown_origin_risks = {
        "origin_country":  "Unknown",
        "origin_weather":  _unknown_risk("No supplier country in shipment data"),
        "origin_quake":    _unknown_risk("No supplier country in shipment data"),
        "origin_politics": _unknown_risk("No supplier country in shipment data"),
        "origin_conflict": _unknown_risk("No supplier country in shipment data"),
    }

    origin_risk_tasks   = [fetch_origin_risks(o, origin_geo_map[o]) for o in unique_origins]
    dest_risks_task     = fetch_destination_risks(dest_geo, destination_port)

    fetch_results       = await asyncio.gather(dest_risks_task, *origin_risk_tasks)
    dest_risks          = fetch_results[0]
    origin_risk_results = fetch_results[1:]

    # ── Step 5: Build lookup map → origin_country → risks ────────────────────
    origin_risk_map = dict(zip(unique_origins, origin_risk_results))

    # ── Step 6: Apply to each shipment (no network calls here) ───────────────
    output = []
    for s in shipments:
        origin_key   = (s.get("supplier_country") or "").strip()
        origin_risks = origin_risk_map.get(origin_key, unknown_origin_risks)
        output.append(apply_risks_to_shipment(s, origin_risks, dest_risks, destination_port))

    return output
