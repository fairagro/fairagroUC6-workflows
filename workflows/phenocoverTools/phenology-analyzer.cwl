#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

requirements:
  ShellCommandRequirement: {}
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    listing:
      - $(inputs.geojson_file)
      - $(inputs.ndvi_file)

inputs:
- id: ndvi_file
  type: File
  default:
    class: File
    location: ndvi_timeseries.csv
  inputBinding:
    prefix: --ndvi-file
- id: geojson_file
  type: File
  default:
    class: File
    location: data/field_location.geojson

- id: sowing_date
  type: string
  default: "03.10.2023"
  inputBinding:
    prefix: --sowing-date
- id: harvest_date
  type: string
  default: "30.07.2024"
  inputBinding:
    prefix: --harvest-date
- id: output_dir
  type: string
  default: "results"
  inputBinding:
    prefix: --output-dir
- id: results_csv
  type: string
  default: "phenology_results.csv"
  inputBinding:
    prefix: --results-csv
- id: visualization_png
  type: string
  default: "phenology_analysis.png"
  inputBinding:
    prefix: --visualization-png
 
outputs:
- id: phenology_results_csv
  type: File
  outputBinding:
    glob: phenology_results.csv
- id: phenology_results_png
  type: File
  outputBinding:
    glob: phenology_analysis.png

arguments:
- shellQuote: false
  valueFrom: |
    phenocover phenology-analyzer --ndvi-file "$(inputs.ndvi_file.basename)" --geojson-file "$(inputs.geojson_file.basename)" --sowing-date "$(inputs.sowing_date)" --harvest-date "$(inputs.harvest_date)" --output-dir results --visualization-png phenology_analysis.png --results-csv phenology_results.csv && cp results/phenology_results.csv phenology_results.csv && cp results/phenology_analysis.png phenology_analysis.png
