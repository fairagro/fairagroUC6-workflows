#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

inputs:
- id: process_images
  type: string
  default: process-images
  inputBinding:
    position: 0
- id: config
  type: File
  default: 
    class: File
    location: '../config/config.yml'
  inputBinding:
    position: 1
    prefix: '--config'
- id: dry-run
  type: boolean
  default: false
  inputBinding:
    position: 2
    prefix: '--dry-run'

outputs: []
baseCommand:
- python
- -m
- raster2sensor
