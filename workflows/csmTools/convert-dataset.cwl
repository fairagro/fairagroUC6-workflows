#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

doc: |
  Convert dataset between different model formats (user, icasa, nasa-power to icasa/dssat).
  Uses csmTools R package for data model conversion.

requirements:
  DockerRequirement:
    dockerPull: rocker/r-ver:4.3
  InitialWorkDirRequirement:
    listing:
      - $(inputs.input_file)

inputs:
- id: input_file
  type: File
  doc: Input dataset file (JSON format)
  inputBinding:
    prefix: --input
    valueFrom: $(self.basename)

- id: input_model
  type: string
  default: "user"
  doc: Input model format (user, icasa, nasa-power, bonares)
  inputBinding:
    prefix: --from

- id: output_model
  type: string
  default: "icasa"
  doc: Output model format (icasa, dssat)
  inputBinding:
    prefix: --to

- id: output_filename
  type: string
  default: "converted_data.json"
  doc: Output filename
  inputBinding:
    prefix: --output

outputs:
- id: converted_data
  type: File
  outputBinding:
    glob: $(inputs.output_filename)

baseCommand: [Rscript, workflows/cli/csmtools_cli.R, convert]
