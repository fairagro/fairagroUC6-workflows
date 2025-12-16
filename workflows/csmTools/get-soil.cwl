#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

doc: |
  Extract soil profile data from SoilGrids database.
  Downloads standardized soil profile for specified coordinates.

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

- id: output_filename
  type: string
  default: "soil_profile.json"
  doc: Output filename
  inputBinding:
    prefix: --output

outputs:
- id: soil_data
  type: File
  outputBinding:
    glob: $(inputs.output_filename)

baseCommand: [Rscript, workflows/cli/csmtools_cli.R, get-soil]
