#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

inputs:
- id: ndvi_file
  type: string
  default: '../../data/ndvi_results.csv'
  inputBinding:
    prefix: '--ndvi-file'
    
- id: config
  type: File
  default: 
    class: File
    location: '../config/config.yml'
  inputBinding:
    prefix: '--config'




outputs:
- id: out
  type: File
  outputBinding:
    glob: '../../data/ndvi_results.csv'

baseCommand:
- raster2sensor
- plots
- fetch-ndvi