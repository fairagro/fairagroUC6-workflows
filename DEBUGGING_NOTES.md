# Debugging Notes: CWL File Path Handling

## Issue
The workflow `s4n execute local ./workflows/demo/demo.cwl` was failing with:
```
❌ Error: Failed to copy file from "data/ndvi_timeseries.csv" to "/tmp/.tmpH3Jht2/data/ndvi_timeseries.csv": No such file or directory
```

## Root Cause
The CWL tools were trying to output files to a `data/` subdirectory that didn't exist in the CWL working directory. CWL creates temporary working directories for each tool execution, and subdirectories must be explicitly created or files should be output directly to the working directory.

## Solution: Understanding InitialWorkDirRequirement

### What is InitialWorkDirRequirement?
`InitialWorkDirRequirement` is a CWL feature that stages input files into the tool's working directory before execution. This is crucial when:
1. Tools expect input files to be in the current directory (not with full paths)
2. You need to reference files by their basename rather than full path
3. Input files need to be copied/staged before processing

### Example from phenology-analyzer.cwl
```yaml
requirements:
  InitialWorkDirRequirement:
    listing:
      - $(inputs.geojson_file)
      - $(inputs.ndvi_file)
```

This stages the input files in the working directory, allowing the command to reference them using:
```yaml
$(inputs.ndvi_file.basename)  # Just the filename, e.g., "ndvi_timeseries.csv"
```

Instead of:
```yaml
$(inputs.ndvi_file.path)  # Full path, e.g., "/tmp/xyz/ndvi_timeseries.csv"
```

## Changes Made

### 1. fetch-ndvi.cwl
**Before:**
```yaml
outputs:
- id: ndvi_timeseries
  type: File
  outputBinding:
    glob: 'data/ndvi_timeseries.csv'

arguments:
- shellQuote: false
  valueFrom: |
    mkdir -p data && raster2sensor plots fetch-ndvi ... && cp ndvi_*.csv data/ndvi_timeseries.csv
```

**After:**
```yaml
outputs:
- id: ndvi_timeseries
  type: File
  outputBinding:
    glob: 'ndvi_timeseries.csv'

arguments:
- shellQuote: false
  valueFrom: |
    raster2sensor plots fetch-ndvi ... && mv "$(inputs.ndvi_file)" ndvi_timeseries.csv
```

**Changes:**
- Removed `data/` subdirectory creation
- Output file directly in working directory
- Use `mv` instead of `cp` to rename the generated file

### 2. phenology-analyzer.cwl
**Before:**
```yaml
outputs:
- id: phenology_results_csv
  type: File
  outputBinding:
    glob: 'data/phenology_results.csv'

arguments:
- shellQuote: false
  valueFrom: |
    phenocover phenology-analyzer ... && cp results/phenology_results.csv data/phenology_results.csv
```

**After:**
```yaml
outputs:
- id: phenology_results_csv
  type: File
  outputBinding:
    glob: 'phenology_results.csv'

arguments:
- shellQuote: false
  valueFrom: |
    phenocover phenology-analyzer ... && mv results/phenology_results.csv phenology_results.csv
```

**Changes:**
- Removed `data/` subdirectory references
- Output files directly in working directory
- Use `mv` instead of `cp` to move files from `results/` to working directory

## Best Practices Learned

### 1. Output Files in Working Directory
Always output files directly to the CWL working directory, not subdirectories:
```yaml
outputBinding:
  glob: 'output.csv'  # ✓ Good
  # glob: 'data/output.csv'  # ✗ Bad (unless you explicitly create data/)
```

### 2. Use InitialWorkDirRequirement for Input Staging
When tools expect files in the current directory:
```yaml
requirements:
  InitialWorkDirRequirement:
    listing:
      - $(inputs.input_file)
```

Then reference with:
```yaml
valueFrom: |
  tool --input "$(inputs.input_file.basename)"
```

### 3. File Path Properties
CWL provides several properties for file inputs:
- `$(inputs.file)` - Full File object
- `$(inputs.file.path)` - Full filesystem path
- `$(inputs.file.basename)` - Just the filename
- `$(inputs.file.dirname)` - Directory path
- `$(inputs.file.nameroot)` - Filename without extension
- `$(inputs.file.nameext)` - File extension

### 4. Creating Subdirectories (if needed)
If you must use subdirectories:
```yaml
arguments:
- shellQuote: false
  valueFrom: |
    mkdir -p output && tool --output output/file.csv
    
outputs:
- id: result
  type: File
  outputBinding:
    glob: 'output/file.csv'  # Match the path exactly
```

## References
From the [fairagro/m4.4_sciwin_client_demo](https://github.com/fairagro/m4.4_sciwin_client_demo) examples:
- Tools output directly to working directory
- Input files are staged using InitialWorkDirRequirement when needed
- Commands reference files by basename after staging

## Result
✅ Workflow now executes successfully:
```bash
s4n execute local ./workflows/demo/demo.cwl
```

All three output files are generated correctly:
- `ndvi_timeseries.csv`
- `phenology_results.csv`
- `phenology_analysis.png`

## FAQ: Organizing Outputs in a data/ Directory

### Q: Can I keep outputs in a `data/` subdirectory?

**Short answer:** It's tricky with CWL file outputs. The recommended approach is to output files to the root directory during workflow execution, then organize them afterwards.

**Why the limitation?**
When CWL collects output files, it needs to copy them from the temporary execution directory to the final output location. If you specify `glob: 'data/file.csv'`, CWL expects to find `data/file.csv` in the execution directory AND needs to create the same `data/` structure in the output location. Different CWL runners handle this differently, and some (like s4n) may fail if the destination directory doesn't exist.

### Solutions:

#### Option 1: Post-workflow organization (Recommended)
Output files to root during execution, organize after completion:

```bash
# Run workflow
s4n execute local ./workflows/demo/demo.cwl

# Organize outputs
./organize_outputs.sh
```

The `organize_outputs.sh` script moves all output files to a `data/` directory for you.

#### Option 2: Output Directory instead of individual Files
Change your tool to output a Directory containing all files:

```yaml
outputs:
- id: results
  type: Directory
  outputBinding:
    glob: 'data'

arguments:
- shellQuote: false
  valueFrom: |
    mkdir -p data && 
    tool --output data/file1.csv &&
    tool --output data/file2.png
```

This way CWL collects the entire `data/` directory as one output.

#### Option 3: Use workflow-level organization
Create a workflow that runs your analysis tools, then adds a final step to organize outputs:

```yaml
steps:
- id: analyze
  run: phenology-analyzer.cwl
  out: [results_csv, results_png]
  
- id: organize
  run: organize-outputs.cwl  # A tool that moves files to data/
  in:
    files: [analyze/results_csv, analyze/results_png]
  out: [data_directory]
```

### Recommendation
For simplicity and portability across CWL runners, **output files to the root directory** and use a post-processing script to organize them. This avoids CWL implementation differences and keeps your workflow portable.
