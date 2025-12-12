#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

inputs:
- id: config
  type: File
  default: 
    class: File
    location: '../config/raster2sensor_config.yml'
  inputBinding:
    position: 0
    prefix: '--config'

outputs:
- id: ndvi_timeseries
  type: File
  outputBinding:
    glob: 'data/ndvi_*.csv'

baseCommand:
- raster2sensor
- plots
- fetch-ndvi