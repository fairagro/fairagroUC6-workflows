#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: Workflow

inputs:
  fetch_config:
    type: File
    default:
      class: File
      location: 'config/raster2sensor_workflow_config.yml'
  geojson_file:
    type: File
    default:
      class: File
      location: '../data/field_location.geojson'

outputs:
  ndvi_timeseries:
    type: File
    outputSource: fetch_ndvi/ndvi_timeseries
  phenology_results_csv:
    type: File
    outputSource: analyze_phenology/phenology_results_csv
  phenology_results_png:
    type: File
    outputSource: analyze_phenology/phenology_results_png

steps:
  fetch_ndvi:
    run: fetch-ndvi/fetch-ndvi.cwl
    in:
      config: fetch_config
    out: [ndvi_timeseries]

  analyze_phenology:
    run: phenology-analyzer/phenology-analyzer.cwl
    in:
      ndvi_file: fetch_ndvi/ndvi_timeseries
      geojson_file: geojson_file
    out: [phenology_results_csv, phenology_results_png]
