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
    location: data/ndvi_timeseries.csv
- id: geojson_file
  type: File
  default:
    class: File
    location: data/field_location.geojson
- id: sowing_date
  type: string
  default: "03.10.2023"
- id: harvest_date
  type: string
  default: "30.07.2024"
 
outputs:
- id: phenology_results_csv
  type: File
  outputBinding:
    glob: 'phenology_results.csv'
- id: phenology_results_png
  type: File
  outputBinding:
    glob: 'phenology_analysis.png'

arguments:
- shellQuote: false
  valueFrom: |
    phenocover phenology-analyzer --ndvi-file "$(inputs.ndvi_file.basename)" --geojson-file "$(inputs.geojson_file.basename)" --sowing-date "$(inputs.sowing_date)" --harvest-date "$(inputs.harvest_date)" --output-dir results --visualization-png phenology_analysis.png --results-csv phenology_results.csv && mv results/phenology_results.csv phenology_results.csv && mv results/phenology_analysis.png phenology_analysis.png
