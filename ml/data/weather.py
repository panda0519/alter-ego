"""NASA POWER daily weather and Hargreaves reference ET0.

PRECTOTCORR, T2M_MAX and T2M_MIN are requested for representative cells, not for
an independent rain gauge at every well. MERRA-2 native spacing is about
0.5 degrees latitude by 0.625 degrees longitude. Wells that share a cell share
one cached response. ET0 is a reference estimate, not measured aquifer
evapotranspiration. Ra is converted from MJ/m2/day to mm/day by multiplying by
0.408 before the Hargreaves equation.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import requests

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
LAT_STEP = 0.5
LON_STEP = 0.625
GSC = 0.0820
RA_MJ_TO_MM = 0.408


def representative_cell(latitude: float, longitude: float) -> tuple[float, float]:
    lat_c = math.floor(latitude / LAT_STEP) * LAT_STEP + LAT_STEP / 2
    lon_c = math.floor(longitude / LON_STEP) * LON_STEP + LON_STEP / 2
    return round(lat_c, 4), round(lon_c, 4)


def fetch_power_cell(latitude: float, longitude: float, dates: pd.DatetimeIndex, cache_dir: Path) -> dict:
    cache_dir.mkdir(parents=True, exist_ok=True)
    start = dates[0].strftime("%Y%m%d")
    end = dates[-1].strftime("%Y%m%d")
    path = cache_dir / f"power_{latitude:.4f}_{longitude:.4f}_{start}_{end}.json"
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        source = "cache"
    else:
        payload = _download(latitude, longitude, start, end)
        path.write_text(json.dumps(payload), encoding="utf-8")
        source = "download"
    parsed = parse_power_payload(payload, dates)
    parsed["cache_path"] = str(path)
    parsed["retrieval"] = source
    parsed["request_latitude"] = latitude
    parsed["request_longitude"] = longitude
    return parsed


def parse_power_payload(payload: dict, dates: pd.DatetimeIndex) -> dict:
    header = payload.get("header") or {}
    parameters = payload.get("parameters") or {}
    fill = header.get("fill_value")
    if fill is None:
        raise ValueError("POWER payload has no fill_value")
    units = {
        "PRECTOTCORR": _unit(parameters, "PRECTOTCORR"),
        "T2M_MAX": _unit(parameters, "T2M_MAX"),
        "T2M_MIN": _unit(parameters, "T2M_MIN"),
    }
    if units["PRECTOTCORR"].lower() != "mm/day":
        raise ValueError(f"unexpected PRECTOTCORR unit: {units['PRECTOTCORR']}")
    if units["T2M_MAX"].upper() not in {"C", "DEG C", "°C"} or units["T2M_MIN"].upper() not in {"C", "DEG C", "°C"}:
        raise ValueError(f"unexpected temperature units: {units}")
    if header.get("time_standard") != "LST":
        raise ValueError("POWER time_standard is not LST")
    series = payload["properties"]["parameter"]
    precip = np.full(len(dates), np.nan, dtype=np.float64)
    tmax = np.full(len(dates), np.nan, dtype=np.float64)
    tmin = np.full(len(dates), np.nan, dtype=np.float64)
    for position, day in enumerate(dates):
        key = day.strftime("%Y%m%d")
        precip[position] = _measurement(series["PRECTOTCORR"].get(key), fill)
        tmax[position] = _measurement(series["T2M_MAX"].get(key), fill)
        tmin[position] = _measurement(series["T2M_MIN"].get(key), fill)
    geometry = (payload.get("geometry") or {}).get("coordinates") or [None, None, None]
    return {
        "precip_mm": precip,
        "tmax_c": tmax,
        "tmin_c": tmin,
        "units": units,
        "fill_value": fill,
        "api_version": (header.get("api") or {}).get("version"),
        "title": header.get("title"),
        "response_longitude": geometry[0],
        "response_latitude": geometry[1],
        "response_elevation_m": geometry[2] if len(geometry) > 2 else None,
        "missing_days": int(np.isnan(precip).sum() + np.isnan(tmax).sum() + np.isnan(tmin).sum()),
    }


def hargreaves_et0_mm(latitude_deg: np.ndarray, day_of_year: np.ndarray, tmax_c: np.ndarray, tmin_c: np.ndarray) -> np.ndarray:
    """ET0 in mm/day. latitude is per well, day/temperature arrays are broadcastable."""
    phi = np.radians(np.asarray(latitude_deg, dtype=np.float64))
    jay = np.asarray(day_of_year, dtype=np.float64)
    dr = 1 + 0.033 * np.cos(2 * np.pi * jay / 365.0)
    delta = 0.409 * np.sin(2 * np.pi * jay / 365.0 - 1.39)
    argument = np.clip(-np.tan(phi) * np.tan(delta), -1.0, 1.0)
    sunset = np.arccos(argument)
    ra_mj = (24 * 60 / np.pi) * GSC * dr * (
        sunset * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(sunset)
    )
    ra_mm = ra_mj * RA_MJ_TO_MM
    tmean = (tmax_c + tmin_c) / 2.0
    span = tmax_c - tmin_c
    et0 = 0.0023 * (tmean + 17.8) * np.sqrt(np.maximum(span, 0.0)) * ra_mm
    invalid = ~np.isfinite(tmax_c) | ~np.isfinite(tmin_c) | (tmax_c < tmin_c) | ~np.isfinite(et0)
    return np.where(invalid, np.nan, et0)


def weather_for_wells(latitude: np.ndarray, longitude: np.ndarray, dates: pd.DatetimeIndex, cache_dir: Path) -> dict:
    cells: dict[tuple[float, float], list[int]] = {}
    assignment = []
    for index, (lat, lon) in enumerate(zip(latitude, longitude)):
        cell = representative_cell(float(lat), float(lon))
        cells.setdefault(cell, []).append(index)
        assignment.append(cell)
    n_days = len(dates)
    n_wells = len(latitude)
    precip_mm = np.full((n_days, n_wells), np.nan, dtype=np.float64)
    tmax = np.full((n_days, n_wells), np.nan, dtype=np.float64)
    tmin = np.full((n_days, n_wells), np.nan, dtype=np.float64)
    reports = []
    for (lat_c, lon_c), members in cells.items():
        parsed = fetch_power_cell(lat_c, lon_c, dates, cache_dir)
        member_index = np.array(members, dtype=int)
        precip_mm[:, member_index] = parsed["precip_mm"][:, None]
        tmax[:, member_index] = parsed["tmax_c"][:, None]
        tmin[:, member_index] = parsed["tmin_c"][:, None]
        reports.append(
            {
                "request_latitude": lat_c,
                "request_longitude": lon_c,
                "n_wells": len(members),
                "units": parsed["units"],
                "fill_value": parsed["fill_value"],
                "api_version": parsed["api_version"],
                "title": parsed["title"],
                "response_latitude": parsed["response_latitude"],
                "response_longitude": parsed["response_longitude"],
                "response_elevation_m": parsed["response_elevation_m"],
                "missing_parameter_days": parsed["missing_days"],
                "cache_path": parsed["cache_path"],
                "retrieval": parsed["retrieval"],
                "resolution_note": "representative MERRA-2-scale cell, not a gauge at the well",
            }
        )
    doy = np.array([day.day_of_year for day in dates], dtype=np.float64)[:, None]
    et0_mm = hargreaves_et0_mm(latitude[None, :], doy, tmax, tmin)
    weather_valid = np.isfinite(precip_mm) & np.isfinite(et0_mm)
    return {
        "precip_mm": precip_mm,
        "precip_m_per_day": precip_mm / 1000.0,
        "tmax_c": tmax,
        "tmin_c": tmin,
        "et0_mm": et0_mm,
        "et0_m_per_day": et0_mm / 1000.0,
        "weather_valid": weather_valid,
        "cells": reports,
        "cell_of_well": assignment,
    }


def _download(latitude: float, longitude: float, start: str, end: str) -> dict:
    response = requests.get(
        POWER_URL,
        params={
            "parameters": "PRECTOTCORR,T2M_MAX,T2M_MIN",
            "community": "AG",
            "longitude": f"{longitude:.4f}",
            "latitude": f"{latitude:.4f}",
            "start": start,
            "end": end,
            "format": "JSON",
            "time-standard": "LST",
        },
        timeout=180,
    )
    response.raise_for_status()
    payload = response.json()
    if "properties" not in payload:
        raise ValueError("POWER response has no properties")
    return payload


def _unit(parameters: dict, name: str) -> str:
    try:
        return str(parameters[name]["units"])
    except KeyError as exc:
        raise ValueError(f"POWER payload is missing unit for {name}") from exc


def _measurement(value, fill) -> float:
    if value is None:
        return math.nan
    number = float(value)
    if number == float(fill) or not math.isfinite(number):
        return math.nan
    return number
