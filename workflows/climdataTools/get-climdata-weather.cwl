#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

doc: |
  Downloads complementary daily weather data for the full production season
  using the climdata package, which offers one interface to eleven climate
  data providers: MSWX, CMIP, POWER, DWD, HYRAS, HOSTRADA, W5E5, CMIP_W5E5,
  NEXGDDP, AGRI_ISIMIP and ERA5. The date range is taken from the
  production_season.json file produced by identify-production-season.
  Gridded/station results are reduced to a single series at the field
  location and written as a long-form CSV
  (time, lat, lon, variable, value, units, source).
  Replaces csmTools/get-weather-data.cwl (NASA POWER only).

  Credentials:
    - MSWX needs a Google service-account JSON (google_service_account)
    - ERA5 needs a Copernicus CDS key file in .cdsapirc format (cds_key)

requirements:
  DockerRequirement:
    dockerPull: joemureithi/climdata-cli:latest
  NetworkAccess:
    networkAccess: true
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    # Credentials are optional. Stage them under fixed names; when omitted an
    # empty placeholder is written instead (the CLI flag is then not passed).
    listing:
      - $(inputs.season_file)
      - entryname: google_service_account.json
        entry: "$(inputs.google_service_account ? inputs.google_service_account.path : '')"
      - entryname: cdsapirc
        entry: "$(inputs.cds_key ? inputs.cds_key.path : '')"

inputs:
- id: lon
  type: float
  doc: Longitude of the field location
  inputBinding:
    prefix: --lon
- id: lat
  type: float
  doc: Latitude of the field location
  inputBinding:
    prefix: --lat
- id: season_file
  type: File
  doc: JSON file from identify-production-season with start_date/end_date fields
  inputBinding:
    prefix: --season-file
    valueFrom: $(self.basename)
- id: climdata_dataset
  type: string
  default: "POWER"
  doc: |
    climdata provider: MSWX, CMIP, POWER, DWD, HYRAS, HOSTRADA, W5E5,
    CMIP_W5E5, NEXGDDP, AGRI_ISIMIP or ERA5
  inputBinding:
    prefix: --dataset
- id: climdata_variables
  type: string
  default: "tas,tasmax,tasmin,pr,rsds"
  doc: |
    Comma-separated climdata variables. tas/tasmax/tasmin/pr/rsds map to the
    ICASA daily weather variables; hurs and sfcWind are also converted.
  inputBinding:
    prefix: --variables
- id: climdata_overrides
  type: string[]?
  doc: |
    Extra Hydra overrides for climdata, e.g. source_id=MPI-ESM1-2-HR or
    experiment_id=ssp585 for CMIP/NEXGDDP/CMIP_W5E5.
  inputBinding:
    prefix: --override
- id: google_service_account
  type: File?
  doc: Google Drive service-account JSON (required for MSWX)
  inputBinding:
    prefix: --google-service-account
    valueFrom: google_service_account.json
- id: cds_key
  type: File?
  doc: Copernicus CDS API key file, .cdsapirc format (required for ERA5)
  inputBinding:
    prefix: --cds-key
    valueFrom: cdsapirc
- id: climdata_data_output
  type: string
  default: "weather_climdata.csv"
  doc: Output file name for the raw climdata weather series (long-form CSV)
  inputBinding:
    prefix: --output

baseCommand:
  - get-climdata-weather

outputs:
- id: climdata_data
  type: File
  outputBinding:
    glob: $(inputs.climdata_data_output)
