#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

doc: |
  Lookup growth stage dates from phenology results CSV.
  Takes the phenology analysis output and extracts specific growth stage dates
  (e.g., Zadoks 65 for anthesis, 87 for maturity) for crop modeling.

requirements:
  DockerRequirement:
    dockerPull: rocker/r-ver:4.3
  InitialWorkDirRequirement:
    listing:
      - entryname: lookup_gs_dates.R
        entry: |
          #!/usr/bin/env Rscript
          suppressPackageStartupMessages({
            library(dplyr)
            library(readr)
            library(jsonlite)
          })
          
          args <- commandArgs(trailingOnly = TRUE)
          
          # Parse arguments
          phenology_csv <- args[1]
          gs_scale <- args[2]
          gs_codes <- as.numeric(strsplit(args[3], ",")[[1]])
          date_rule <- args[4]
          output_file <- args[5]
          
          # Load phenology data
          pheno_data <- read_csv(phenology_csv, show_col_types = FALSE)
          
          # Map growth stages to dates
          # This is a simplified version - actual implementation depends on phenology CSV structure
          gs_dates <- list()
          
          if ("date" %in% names(pheno_data) && "growth_stage" %in% names(pheno_data)) {
            for (code in gs_codes) {
              stage_data <- pheno_data %>%
                filter(growth_stage == code)
              
              if (nrow(stage_data) > 0) {
                selected_date <- switch(date_rule,
                  "first" = min(stage_data$date),
                  "last" = max(stage_data$date),
                  "median" = median(as.Date(stage_data$date)),
                  median(as.Date(stage_data$date))
                )
                gs_dates[[paste0("gs_", code)]] <- as.character(selected_date)
              }
            }
          }
          
          # Create output JSON
          output_data <- list(
            growth_stage_scale = gs_scale,
            growth_stage_dates = gs_dates,
            date_selection_rule = date_rule
          )
          
          # Write to file
          write_json(output_data, output_file, pretty = TRUE, auto_unbox = TRUE)
          
          cat("✓ Growth stage dates saved to:", output_file, "\n")

inputs:
- id: phenology_results
  type: File
  doc: Phenology results CSV from phenology-analyzer
  inputBinding:
    position: 1
  default:
    class: File
    location: 'phenology_results.csv'

- id: gs_scale
  type: string
  default: "zadoks"
  doc: Growth stage scale (e.g., zadoks, bbch)
  inputBinding:
    position: 2

- id: gs_codes
  type: string
  default: "65,87"
  doc: Comma-separated growth stage codes (e.g., 65 for anthesis, 87 for maturity)
  inputBinding:
    position: 3

- id: date_select_rule
  type: string
  default: "median"
  doc: Rule for selecting dates (first, last, median)
  inputBinding:
    position: 4

outputs:
- id: phenology_json
  type: File
  outputBinding:
    glob: phenology_dates.json

arguments:
- position: 5
  valueFrom: phenology_dates.json
- prefix: ""
  position: 0
  valueFrom: Rscript lookup_gs_dates.R

baseCommand: []
