#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

doc: |
  Get weather data from NASA POWER database for crop modeling.
  Downloads daily weather time series for specified location and time period.

requirements:
  DockerRequirement:
    dockerPull: rocker/r-ver:4.3
  NetworkAccess:
    networkAccess: true

inputs:
- id: longitude
  type: double
  doc: Longitude coordinate
  inputBinding:
    prefix: --lon

- id: latitude
  type: double
  doc: Latitude coordinate
  inputBinding:
    prefix: --lat

- id: start_date
  type: string
  doc: Start date (YYYY-MM-DD)
  inputBinding:
    prefix: --from

- id: end_date
  type: string
  doc: End date (YYYY-MM-DD)
  inputBinding:
    prefix: --to

- id: output_filename
  type: string
  default: "weather_nasapower.json"
  doc: Output filename
  inputBinding:
    prefix: --output

outputs:
- id: weather_data
  type: File
  outputBinding:
    glob: $(inputs.output_filename)

baseCommand: [Rscript, workflows/cli/csmtools_cli.R, get-weather]
