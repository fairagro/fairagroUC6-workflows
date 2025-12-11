#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

inputs:
- id: config
  type: File
  default: 
    class: File
    location: '../config/config.yml'
  inputBinding:
    position: 0
    prefix: '--config'

- id: ndvi_file
  type: string
  default: '../../data/ndvi_results.csv'
  inputBinding:
    position: 0
    prefix: '--ndvi-file'


outputs:
- id: out
  type: File
  outputBinding:
    glob: $(inputs.ndvi_file)

baseCommand:
- raster2sensor
- plots
- fetch-ndvi