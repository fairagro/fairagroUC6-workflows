#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

inputs:
- id: config
  type: File
  default: 
    class: File
    location: '../config/phenocover_config.yml'
  inputBinding:
    position: 0
    prefix: '--config'
- id: ndvi_file
  type: File
  default:
    class: File
    location: '../../data/ndvi_goetheweg_2024.csv'
  inputBinding:
    position: 1
    prefix: '--ndvi-file'
- id: geojson_file
  type: File
  default:
    class: File
    location: '../../data/field_location.geojson'
  inputBinding:
    position: 2
    prefix: '--geojson-file'
 
outputs:
- id: phenology_results_csv
  type: File
  outputBinding:
    glob: 'data/phenology_*.csv'
- id: phenology_results_png
  type: File
  outputBinding:
    glob: 'data/phenology_*.png'

baseCommand:
- phenocover
- phenology-analyzer
