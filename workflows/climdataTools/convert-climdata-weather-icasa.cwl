#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

doc: |
  Converts the long-form climdata weather series (output of
  get-climdata-weather) into ICASA format (WEATHER_METADATA + WEATHER_DAILY)
  so it can be assembled with the other ICASA datasets.
  Units are converted from those reported by climdata to ICASA units:
    tas/tasmax/tasmin -> degC   (dry_bulb_temper_avg_day, maximum/minimum_temperature)
    rsds              -> MJ/m2/d (solar_radiation)
    pr                -> mm/d    (precipitation)
    hurs              -> %       (realtive_humidity_avg)
    sfcWind           -> km/d    (wind_speed_daily)
  Replaces csmTools/convert-nasa-data-icasa.cwl.

requirements:
  DockerRequirement:
    dockerPull: joemureithi/climdata-cli:latest
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    listing:
      - $(inputs.climdata_data)

inputs:
- id: climdata_data
  type: File
  doc: Long-form CSV weather series from get-climdata-weather
  inputBinding:
    prefix: --input
    valueFrom: $(self.basename)
- id: climdata_icasa_output
  type: string
  default: "weather_climdata_icasa.json"
  doc: Output file name for the ICASA-formatted weather data
  inputBinding:
    prefix: --output

baseCommand:
  - convert-climdata-weather-icasa

outputs:
- id: climdata_data_icasa
  type: File
  outputBinding:
    glob: $(inputs.climdata_icasa_output)
