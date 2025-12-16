#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

doc: |
  Assemble multiple dataset components into a single integrated dataset.
  Supports merging, appending, and replacing data from multiple sources.

requirements:
  DockerRequirement:
    dockerPull: rocker/r-ver:4.3
  InitialWorkDirRequirement:
    listing: $(inputs.component_files)

inputs:
- id: component_files
  type: File[]
  doc: Array of component JSON files to assemble
  inputBinding:
    prefix: --components
    itemSeparator: " "
    valueFrom: |
      ${
        var basenames = [];
        for (var i = 0; i < self.length; i++) {
          basenames.push(self[i].basename);
        }
        return basenames.join(" ");
      }

- id: action
  type: string
  default: "merge_properties"
  doc: Assembly action (merge_properties, append_rows, replace_section)
  inputBinding:
    prefix: --action

- id: output_filename
  type: string
  default: "assembled_data.json"
  doc: Output filename
  inputBinding:
    prefix: --output

outputs:
- id: assembled_data
  type: File
  outputBinding:
    glob: $(inputs.output_filename)

baseCommand: [Rscript, /opt/csmtools_cli.R, assemble]
