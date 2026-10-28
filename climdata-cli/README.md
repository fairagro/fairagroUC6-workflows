# climdata Command-Line Interface

A small CLI around the [climdata](https://github.com/Kaushikreddym/climdata) package ([docs](https://kaushikreddym.github.io/climdata/)) that supplies complementary weather data to the UC6 crop-modelling workflow. It backs the CWL tools in [`workflows/climdataTools/`](../workflows/climdataTools/), which replace the NASA POWER-only `get-weather-data` / `convert-nasa-data-icasa` steps.

| Command | CWL tool | Description |
| --- | --- | --- |
| `get-climdata-weather` | `get-climdata-weather.cwl` | Retrieve a daily point weather series from a climdata provider |
| `convert-climdata-weather-icasa` | `convert-climdata-weather-icasa.cwl` | Convert that series to ICASA JSON |

## Providers

| Dataset | Coverage | Credentials |
| --- | --- | --- |
| `POWER` (default) | Global, 1981–present | – |
| `DWD` | German stations (averaged within 30 km, as climdata's `DWD.format()` does); few stations measure radiation, so `rsds` may be unavailable | – |
| `HYRAS` | Germany, gridded, 1951–present | – |
| `HOSTRADA` | Germany, hourly grids (limited variables) | – |
| `MSWX` | Global, 0.1°, 1979–present | Google service account (`--google-service-account`) |
| `ERA5` | Global, 0.25°, 1940–present | Copernicus CDS key (`--cds-key`, `.cdsapirc` format) |
| `W5E5` | Global, 1979–2019 | – |
| `CMIP`, `CMIP_W5E5`, `NEXGDDP` | Climate projections | – (pick model/scenario with `--override source_id=… --override experiment_id=…`) |
| `AGRI_ISIMIP` | ISIMIP agricultural forcing | – |

For ERA5, `--cds-key` takes a file in the `.cdsapirc` format from climdata's setup instructions (`url:` and `key:` lines). The CLI writes it to `~/.cdsapirc` with mode 600 if no such file exists (and never overwrites an existing one), and also exports `CDSAPI_RC`/`CDSAPI_URL`/`CDSAPI_KEY`. Use the current endpoint `https://cds.climate.copernicus.eu/api`; the legacy `/api/v2` was shut down in 2024.

ERA5 is not part of climdata's `ClimData` workflow (it is a global Zarr mirror). The CLI drives `climdata.ERA5` directly, overriding its monthly request to fetch only a 0.5° box around the field and the daily mean/max/min it needs. ERA5 supports `tas, tasmax, tasmin, pr, rsds`.

### Workarounds for climdata 1.0.1

The CLI patches two upstream issues at runtime (see `_patch_dwd` in `climdata_cli.py`):

- `DWD.get_stations()` indexes stations by row number rather than `station_id` with current wetterdienst, so no station matches and the result is empty. The CLI re-indexes the station table by `station_id`.
- DWD `rsds` is mapped to diffuse shortwave radiation; the CLI overrides it to `radiation_global`, which corresponds to ICASA `solar_radiation`.

ERA5 requests are sent one at a time, because the CDS rejects the concurrent requests `ERA5Mirror` makes by default.

## Variables

climdata variables are converted to ICASA as follows:

| climdata | ICASA header | ICASA unit |
| --- | --- | --- |
| `tas` | `dry_bulb_temper_avg_day` | °C |
| `tasmax` | `maximum_temperature` | °C |
| `tasmin` | `minimum_temperature` | °C |
| `rsds` | `solar_radiation` | MJ m⁻² d⁻¹ |
| `pr` | `precipitation` | mm d⁻¹ |
| `hurs` | `realtive_humidity_avg` (spelling as in csmTools' mapping) | % |
| `sfcWind` | `wind_speed_daily` | km d⁻¹ |

The default variable set is `tas,tasmax,tasmin,pr,rsds`, which reproduces the columns of the NASA POWER ICASA dataset.

## Usage

```bash
# Retrieve (season file from identify-production-season)
python climdata_cli.py get-climdata-weather \
  --lon 10.645269 --lat 49.20868 \
  --season-file production_season.json \
  --dataset POWER \
  --output weather_climdata.csv

# ERA5 with the CDS key
python climdata_cli.py get-climdata-weather \
  --lon 10.645269 --lat 49.20868 --start-date 2024-10-22 --end-date 2025-08-09 \
  --dataset ERA5 --cds-key ../config/.cdsapirc

# Convert to ICASA
python climdata_cli.py convert-climdata-weather-icasa \
  --input weather_climdata.csv --output weather_climdata_icasa.json
```

The intermediate CSV is climdata's long format (`time, lat, lon, variable, value, units, source`), in the units climdata reports (e.g. `rsds` in W m⁻²); unit conversion to ICASA happens in the convert step via xclim.

## Docker

climdata's own dependency list includes a Qt GUI, ML, plotting and notebook tooling, which gives a ~4.3 GB image. The Dockerfile installs climdata with `--no-deps` and adds only the packages its weather providers import at runtime, giving ~2.8 GB (~620 MB compressed download). If a provider later needs a missing package, add it to the `micromamba install` list.

```bash
./build_docker.sh                          # builds joemureithi/climdata-cli:latest
docker run --rm joemureithi/climdata-cli:latest get-climdata-weather --help
docker push joemureithi/climdata-cli:latest  # the CWL tools pull this image
```
