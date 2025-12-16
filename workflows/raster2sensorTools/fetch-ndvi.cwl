#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

requirements:
  ShellCommandRequirement: {}
  InlineJavascriptRequirement: {}

inputs:
- id: trial_id
  type: string
  default: "Goetheweg-2024"
- id: sensorthingsapi_url
  type: string
  default: "https://tuzehez-fairagro.srv.mwn.de/frost/v1.1"
- id: ndvi_file
  type: string
  default: "data/ndvi_goetheweg_2024.csv"

outputs:
- id: ndvi_timeseries
  type: File
  outputBinding:
    glob: 'ndvi_timeseries.csv'

arguments:
- shellQuote: false
  valueFrom: |
    mkdir -p data && raster2sensor plots fetch-ndvi --trial-id "$(inputs.trial_id)" --sensorthingsapi-url "$(inputs.sensorthingsapi_url)" --ndvi-file "$(inputs.ndvi_file)" && cp data/ndvi_*.csv ndvi_timeseries.csv
