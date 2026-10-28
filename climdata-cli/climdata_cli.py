#!/usr/bin/env python3
"""Command-line interface wrapping the climdata package for the UC6 CWL workflow.

Subcommands
-----------
get-climdata-weather
    Retrieve a daily point weather series for a field location from any of the
    eleven climate data providers offered by climdata (MSWX, CMIP, POWER, DWD,
    HYRAS, HOSTRADA, W5E5, CMIP_W5E5, NEXGDDP, AGRI_ISIMIP and ERA5) and write it
    as a long-form CSV (time, lat, lon, variable, value, units, source).

convert-climdata-weather-icasa
    Convert that long-form CSV into the ICASA JSON layout used by the other
    weather datasets in the workflow (WEATHER_METADATA + WEATHER_DAILY).

Examples
--------
    climdata_cli.py get-climdata-weather --lon 10.645 --lat 49.208 \
        --season-file production_season.json --dataset POWER \
        --output weather_climdata.csv

    climdata_cli.py convert-climdata-weather-icasa \
        --input weather_climdata.csv --output weather_climdata_icasa.json
"""

import argparse
import datetime
import json
import math
import os
import sys
import tempfile

import numpy as np
import pandas as pd

# Providers driven through climdata.ClimData(...).extract()
WORKFLOW_DATASETS = (
    "MSWX", "CMIP", "POWER", "DWD", "HYRAS", "HOSTRADA",
    "W5E5", "CMIP_W5E5", "NEXGDDP", "AGRI_ISIMIP",
)
# ERA5 is a Zarr mirror in climdata and is driven directly (see _extract_era5)
ALL_DATASETS = WORKFLOW_DATASETS + ("ERA5",)

DEFAULT_VARIABLES = "tas,tasmax,tasmin,pr,rsds"

# climdata variable -> (ICASA header, target unit). Order defines column order.
ICASA_DAILY = {
    "tas": ("dry_bulb_temper_avg_day", "degC"),
    "tasmax": ("maximum_temperature", "degC"),
    "tasmin": ("minimum_temperature", "degC"),
    "rsds": ("solar_radiation", "MJ m-2 d-1"),
    "pr": ("precipitation", "mm d-1"),
    # Spelling follows csmTools' ICASA mappings (map_icasa_dssat.yaml: RHUM)
    "hurs": ("realtive_humidity_avg", "%"),
    "sfcWind": ("wind_speed_daily", "km d-1"),
}

# Nominal wind measurement height (m) per provider, written to
# ref_height_windsp_meas when wind is present. Unknown providers omit it.
WIND_HEIGHT_M = {
    "POWER": 2, "DWD": 10, "HOSTRADA": 10, "CMIP": 10, "W5E5": 10,
    "CMIP_W5E5": 10, "NEXGDDP": 10, "ERA5": 10,
}

# ERA5 (CDS derived daily statistics): CF variable -> request + unit handling.
# Accumulated fields are averaged from hourly steps and rescaled to daily values.
ERA5_VARIABLES = {
    "tas": {"cds": "2m_temperature", "stat": "daily_mean", "units": "K"},
    "tasmax": {"cds": "2m_temperature", "stat": "daily_maximum", "units": "K"},
    "tasmin": {"cds": "2m_temperature", "stat": "daily_minimum", "units": "K"},
    # mean hourly accumulation (m) * 24 h * 1000 -> mm/day
    "pr": {"cds": "total_precipitation", "stat": "daily_mean",
           "scale": 24 * 1000.0, "units": "mm/day"},
    # mean hourly accumulation (J m-2) / 3600 s -> W m-2
    "rsds": {"cds": "surface_solar_radiation_downwards", "stat": "daily_mean",
             "scale": 1 / 3600.0, "units": "W m-2"},
}

ICASA_CLASS = {"_class_attribute": ["tbl_df", "tbl", "data.frame"]}


def log(msg):
    print(f"[climdata-cli] {msg}", file=sys.stderr, flush=True)


# =============================================================================
# get-climdata-weather
# =============================================================================

def _resolve_dates(args):
    start, end = args.start_date, args.end_date
    if args.season_file:
        with open(args.season_file) as f:
            season = json.load(f)
        start = start or season.get("start_date")
        end = end or season.get("end_date")
    if not start or not end:
        sys.exit("ERROR: provide --season-file or both --start-date and --end-date")
    # Normalise and validate (YYYY-MM-DD)
    start = datetime.date.fromisoformat(str(start)[:10])
    end = datetime.date.fromisoformat(str(end)[:10])
    if end < start:
        sys.exit(f"ERROR: end date {end} is before start date {start}")
    return start, end


def _canonical_dataset(name):
    for ds in ALL_DATASETS:
        if ds.lower() == name.lower():
            return ds
    sys.exit(f"ERROR: unknown dataset '{name}'. Choose one of: {', '.join(ALL_DATASETS)}")


def _setup_credentials(args):
    """Expose credential files to the libraries that read them."""
    if args.cds_key:
        # climdata's ERA5 setup expects ~/.cdsapirc ("url: ..." / "key: ...",
        # mode 600). Write it from the supplied key file unless the user already
        # has one, and also export CDSAPI_RC/URL/KEY, which cdsapi prefers.
        cds = {}
        with open(args.cds_key) as f:
            for line in f:
                key, _, value = line.partition(":")
                if key.strip() in ("url", "key"):
                    cds[key.strip()] = value.strip()
        if not {"url", "key"} <= cds.keys():
            sys.exit(f"ERROR: {args.cds_key} must contain 'url:' and 'key:' lines")
        rc = os.path.expanduser("~/.cdsapirc")
        if not os.path.exists(rc):
            with open(rc, "w") as f:
                f.write(f"url: {cds['url']}\nkey: {cds['key']}\n")
            os.chmod(rc, 0o600)
            log(f"Wrote CDS credentials to {rc}")
        os.environ["CDSAPI_RC"] = os.path.abspath(args.cds_key)
        os.environ["CDSAPI_URL"] = cds["url"]
        os.environ["CDSAPI_KEY"] = cds["key"]
    if args.google_service_account:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(
            args.google_service_account)


def _check_variables(cfg, dataset, variables):
    """Fail early (and readably) on variables the provider does not offer."""
    dsinfo = {k.upper(): k for k in cfg.dsinfo.keys()}
    key = dsinfo.get(dataset.upper())
    if key is None or "variables" not in cfg.dsinfo[key]:
        return
    available = list(cfg.dsinfo[key].variables.keys())
    missing = [v for v in variables if v not in available]
    if missing:
        sys.exit(f"ERROR: {dataset} does not provide {missing}. "
                 f"Available variables: {', '.join(available)}")


def _nearest_point(ds, lon, lat):
    """Reduce any spatial layout returned by a provider to one point series.

    - station networks (DWD: dim ``station_id``) are averaged across the
      selected stations, mirroring climdata's own ``DWD.format()``;
    - 1-D lat/lon grids are sampled at the nearest cell;
    - curvilinear grids (2-D lat/lon coords on y/x) use the nearest cell by
      great-circle-ish distance;
    - leftover length-1 dimensions are squeezed.
    Returns (dataset, point_lon, point_lat).
    """
    lat_name = next((n for n in ("lat", "latitude") if n in ds.coords), None)
    lon_name = next((n for n in ("lon", "longitude") if n in ds.coords), None)

    if "station_id" in ds.dims:
        ds = ds.mean("station_id", skipna=True, keep_attrs=True)
        return ds, lon, lat

    if lat_name and lon_name:
        la, lo = ds[lat_name], ds[lon_name]
        if la.ndim == 1 and lo.ndim == 1 and la.dims != lo.dims:
            ds = ds.sel({lat_name: lat, lon_name: lon}, method="nearest")
        elif la.ndim >= 1:
            dist = (la - lat) ** 2 + ((lo - lon) * math.cos(math.radians(lat))) ** 2
            idx = np.unravel_index(int(dist.argmin()), dist.shape)
            ds = ds.isel({d: int(i) for d, i in zip(dist.dims, idx)})

    extra = [d for d in ds.dims if d != "time"]
    for d in extra:
        if ds.sizes[d] == 1:
            ds = ds.isel({d: 0})
        else:
            sys.exit(f"ERROR: could not reduce dimension '{d}' (size {ds.sizes[d]}) "
                     "to a single point")

    p_lat = float(ds[lat_name]) if lat_name and ds[lat_name].ndim == 0 else lat
    p_lon = float(ds[lon_name]) if lon_name and ds[lon_name].ndim == 0 else lon
    return ds, p_lon, p_lat


def _patch_dwd():
    """Work around climdata 1.0.1's DWD station lookup with current wetterdienst.

    ``DWDmirror.get_stations`` returns ``request.all().df.to_pandas()``, whose
    index is a plain RangeIndex, while ``extract`` uses that index as station
    ids -- so no station ever matches and the result is empty. Re-index the
    station table by its ``station_id`` column.
    """
    from climdata.datasets import DWD as dwd_module

    cls = dwd_module.DWDmirror
    if getattr(cls, "_uc6_patched", False):
        return
    original = cls.get_stations

    def get_stations(self, variable="pr"):
        stations = original(self, variable)
        if "station_id" in stations.columns:
            stations = stations.set_index("station_id")
            dataset = self.param_mapping.DWD.variables[variable]["dataset"]
            self._stations_cache[dataset] = stations
            self.stations = stations
        return stations

    cls.get_stations = get_stations
    cls._uc6_patched = True


def _extract_era5(cfg, variables, lon, lat, start, end, data_dir):
    """ERA5 via climdata's ERA5Mirror, restricted to a small box around the point.

    climdata.ERA5 mirrors whole global months of daily means. For a field-scale
    series we keep its mirroring/journal logic but override the per-month
    request to (a) cut a 0.5 deg box around the field and (b) request the daily
    statistic each variable needs (mean/max/min) from hourly data.
    """
    import climdata
    import xarray as xr
    import cdsapi

    unsupported = [v for v in variables if v not in ERA5_VARIABLES]
    if unsupported:
        sys.exit(f"ERROR: ERA5 support covers {', '.join(ERA5_VARIABLES)}; "
                 f"not available: {unsupported}")

    area = [lat + 0.25, lon - 0.25, lat - 0.25, lon + 0.25]  # N, W, S, E

    class PointERA5(climdata.ERA5):
        # Mirror keys look like "<cds_variable>__<daily_statistic>"
        def download_chunk(self, variable, year, month, pressure_level=None):
            import calendar
            cds_var, stat = variable.split("__")
            days = calendar.monthrange(year, month)[1]
            out = os.path.join(tempfile.mkdtemp(dir=data_dir),
                               f"{cds_var}_{stat}_{year}_{month:02d}.nc")
            cdsapi.Client(quiet=True).retrieve(
                "derived-era5-single-levels-daily-statistics",
                {
                    "product_type": "reanalysis",
                    "variable": [cds_var],
                    "year": str(year),
                    "month": f"{month:02d}",
                    "day": [f"{d:02d}" for d in range(1, days + 1)],
                    "daily_statistic": stat,
                    "time_zone": "utc+00:00",
                    "frequency": "1_hourly",
                    "area": area,
                    "data_format": "netcdf",
                },
                out,
            )
            return xr.open_dataset(out).load()

    mirror_dir = os.path.join(data_dir, f"era5_LAT{lat:.3f}_LON{lon:.3f}")
    mirror = PointERA5(mirror_dir)
    keys = {v: f"{ERA5_VARIABLES[v]['cds']}__{ERA5_VARIABLES[v]['stat']}" for v in variables}
    # ERA5Mirror submits months/variables concurrently through dask; the CDS
    # rejects that ("Maximum number queued requests ... request data
    # sequentially"), so force the synchronous scheduler.
    import dask
    with dask.config.set(scheduler="synchronous"):
        paths = mirror.download(sorted(set(keys.values())), (start, end))
    stores = dict(zip(sorted(set(keys.values())), paths))

    data = {}
    for v in variables:
        spec = ERA5_VARIABLES[v]
        z = xr.open_zarr(stores[keys[v]])
        da = z[next(iter(z.data_vars))]
        da = da.sel(time=slice(str(start), str(end))) * spec.get("scale", 1.0)
        da.attrs = {"units": spec["units"]}
        data[v] = da
    ds = xr.Dataset(data)
    for k in ("number", "expver"):
        if k in ds.coords:
            ds = ds.drop_vars(k)
    return ds


def cmd_get_climdata_weather(args):
    import climdata
    import xclim

    dataset = _canonical_dataset(args.dataset)
    variables = [v.strip() for v in args.variables.split(",") if v.strip()]
    start, end = _resolve_dates(args)
    # Resolve credential paths before changing into the climdata workdir
    for attr in ("google_service_account", "cds_key"):
        if getattr(args, attr):
            setattr(args, attr, os.path.abspath(getattr(args, attr)))
    _setup_credentials(args)

    data_dir = os.path.abspath(args.data_dir)
    os.makedirs(data_dir, exist_ok=True)

    # climdata copies its Hydra conf/ into the CWD; keep that out of the output
    # directory (and away from read-only working dirs) by running in a temp dir.
    workdir = tempfile.mkdtemp(prefix="climdata_", dir=data_dir)
    output = os.path.abspath(args.output)
    cwd = os.getcwd()
    os.chdir(workdir)
    try:
        overrides = [
            f"dataset={dataset}",
            f"lat={args.lat}",
            f"lon={args.lon}",
            f"variables=[{','.join(variables)}]",
            f"time_range.start_date={start.isoformat()}",
            f"time_range.end_date={end.isoformat()}",
            f"data_dir={data_dir}",
            "output.fair.enabled=false",
        ]
        if args.google_service_account:
            overrides.append("dsinfo.MSWX.params.google_service_account="
                             f"{args.google_service_account}")
        if dataset == "DWD":
            _patch_dwd()
            # climdata 1.0.1 maps rsds to *diffuse* radiation; ICASA SRAD is global
            overrides.append("dsinfo.DWD.variables.rsds.name=radiation_global")
        overrides += args.override or []

        log(f"Retrieving {variables} from {dataset} for "
            f"({args.lat}, {args.lon}) {start} .. {end}")
        extractor = climdata.ClimData(overrides=overrides)

        if dataset == "ERA5":
            ds = _extract_era5(extractor.cfg, variables, args.lon, args.lat,
                               start, end, data_dir)
            for v in variables:
                ds[v] = xclim.core.units.convert_units_to(
                    ds[v], extractor.cfg.varinfo[v].units, context="hydro")
        else:
            _check_variables(extractor.cfg, dataset, variables)
            ds = extractor.extract()
        ds = ds[[v for v in variables if v in ds.data_vars]]

        ds, p_lon, p_lat = _nearest_point(ds, args.lon, args.lat)
        ds = ds.load()
        # Normalise coordinates so to_dataframe() always emits lat/lon columns
        ds = ds.drop_vars([c for c in ds.coords if c != "time"])
        ds = ds.assign_coords(lat=p_lat, lon=p_lon)
        # Some providers (e.g. MSWX, parallel per-day downloads) return days
        # out of order; sort and de-duplicate before slicing.
        ds = ds.sortby("time")
        ds = ds.isel(time=~ds.get_index("time").duplicated())
        ds = ds.sel(time=slice(str(start), str(end)))

        df = extractor.to_dataframe(ds)
        df["source"] = dataset
        df = df[["time", "lat", "lon", "variable", "value", "units", "source"]]
    finally:
        os.chdir(cwd)

    # POWER encodes gaps as -999
    df.loc[df["value"] <= -999, "value"] = np.nan
    df["time"] = pd.to_datetime(df["time"]).dt.strftime("%Y-%m-%d")
    df.to_csv(output, index=False)
    log(f"Wrote {len(df)} rows ({df['time'].nunique()} days) to {output}")


# =============================================================================
# convert-climdata-weather-icasa
# =============================================================================

def _to_unit(values, units, target):
    import xarray as xr
    import xclim
    da = xr.DataArray(values.astype(float), attrs={"units": units})
    return xclim.core.units.convert_units_to(da, target, context="hydro").values


def _json_list(values, digits):
    return [None if (v is None or (isinstance(v, float) and math.isnan(v)))
            else round(float(v), digits) for v in values]


def cmd_convert_climdata_weather_icasa(args):
    df = pd.read_csv(args.input)
    required = {"time", "lat", "lon", "variable", "value", "units"}
    if not required.issubset(df.columns):
        sys.exit(f"ERROR: input lacks columns {sorted(required - set(df.columns))}")

    source = str(df["source"].iloc[0]) if "source" in df.columns and len(df) else None
    wide = df.pivot_table(index="time", columns="variable", values="value",
                          aggfunc="mean", dropna=False).sort_index()
    units = df.groupby("variable")["units"].first().to_dict()

    daily = {
        "year": [int(t[:4]) for t in wide.index],
        "weather_date": list(wide.index),
    }
    for var, (header, target) in ICASA_DAILY.items():
        if var in wide.columns:
            values = _to_unit(wide[var].values, units[var], target)
            daily[header] = _json_list(values, args.digits)

    unknown = sorted(set(wide.columns) - set(ICASA_DAILY))
    if unknown:
        log(f"Skipping variables without an ICASA mapping: {unknown}")

    metadata = {
        "weather_sta_longitude": round(float(df["lon"].iloc[0]), 4),
        "weather_sta_latitude": round(float(df["lat"].iloc[0]), 4),
        "temperature_sensor_ht": 2,
    }
    if "sfcWind" in wide.columns and source in WIND_HEIGHT_M:
        metadata["ref_height_windsp_meas"] = WIND_HEIGHT_M[source]

    icasa = {
        "WEATHER_METADATA": {"data": metadata, "attributes": ICASA_CLASS},
        "WEATHER_DAILY": {"data": daily, "attributes": ICASA_CLASS},
    }
    with open(args.output, "w") as f:
        json.dump(icasa, f, indent=2)
    log(f"Wrote ICASA weather ({len(wide)} days, "
        f"{len(daily) - 2} variables) to {args.output}")


# =============================================================================
# Argument parsing
# =============================================================================

def build_parser():
    parser = argparse.ArgumentParser(
        prog="climdata-cli",
        description="climdata weather retrieval and ICASA conversion for the UC6 workflow")
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("get-climdata-weather",
                       help="Retrieve a daily point weather series via climdata")
    g.add_argument("--lon", type=float, required=True, help="Field longitude")
    g.add_argument("--lat", type=float, required=True, help="Field latitude")
    g.add_argument("--season-file",
                   help="JSON with start_date/end_date (identify-production-season output)")
    g.add_argument("--start-date", help="Start date YYYY-MM-DD (overrides season file)")
    g.add_argument("--end-date", help="End date YYYY-MM-DD (overrides season file)")
    g.add_argument("--dataset", default="POWER",
                   help=f"climdata provider: {', '.join(ALL_DATASETS)} (default POWER)")
    g.add_argument("--variables", default=DEFAULT_VARIABLES,
                   help=f"Comma-separated climdata variables (default {DEFAULT_VARIABLES})")
    g.add_argument("--google-service-account",
                   help="Google service-account JSON (needed for MSWX)")
    g.add_argument("--cds-key",
                   help="Copernicus CDS key file in .cdsapirc format (needed for ERA5)")
    g.add_argument("--data-dir",
                   default=os.path.join(tempfile.gettempdir(), "climdata_cache"),
                   help="Download/cache directory for provider files "
                        "(default: $TMPDIR/climdata_cache, kept out of the CWL outputs)")
    g.add_argument("--override", action="extend", nargs="+",
                   help="Extra Hydra override(s) passed to climdata, e.g. "
                        "source_id=MPI-ESM1-2-HR experiment_id=historical")
    g.add_argument("--output", default="weather_climdata.csv",
                   help="Output long-form CSV")
    g.set_defaults(func=cmd_get_climdata_weather)

    c = sub.add_parser("convert-climdata-weather-icasa",
                       help="Convert climdata long-form CSV to ICASA JSON")
    c.add_argument("--input", required=True, help="CSV from get-climdata-weather")
    c.add_argument("--output", default="weather_climdata_icasa.json",
                   help="Output ICASA JSON")
    c.add_argument("--digits", type=int, default=2, help="Decimal places (default 2)")
    c.set_defaults(func=cmd_convert_climdata_weather_icasa)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
