#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

doc: |
  Reads and processes field experiment data from an Excel template, 
  converting it to ICASA-compliant format..

inputs:
- id: path
  type: string
  default: "data/template_icasa_vba.xlsm"
  doc: Path to template file
  inputBinding:
    prefix: --path
- id: exp-id
  type: string
  default: "HWOC2501"
  doc: Experiment ID
  inputBinding:
    prefix: --exp-id
- id: headers
  type: string
  default: "long"
  doc: Header format
  inputBinding:
    prefix: --headers
- id: output
  type: string
  default: "data/field_data_icasa.json"
  inputBinding:
    prefix: --output

outputs:
- id: field_data
  type: File
  outputBinding:
    glob: $(inputs.output)


baseCommand: [Rscript, workflows/scripts/csmtools_cli.R, extract-field-data]
