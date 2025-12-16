# csmTools Command-Line Interface

A command-line interface for the [csmTools](https://github.com/leroy-bml/uc6_csmTools) package that allows you to run crop modeling workflows from the terminal. `csmTools` should be installed in your R environment before running this CLI tool.

## Installation

First, install the required package:

```R
install.packages("argparse")
```

Make the CLI executable:

```bash
chmod +x csmtools_cli.R
```

## Usage

The CLI is organized into subcommands for different workflow steps:

### Workflow Steps

1. **extract-field** - Extract field data from ICASA template
2. **get-weather** - Download weather data (NASA POWER)
3. **get-sensor** - Download sensor data (FROST server)
4. **get-soil** - Extract soil profile (SoilGrids)
5. **assemble** - Combine data components
6. **convert** - Convert between formats (ICASA ↔ DSSAT)
7. **build-inputs** - Generate DSSAT input files
8. **simulate** - Run DSSAT simulation

### 1. Extract Field Data

Extract field data from an ICASA template:

```bash
Rscript csmtools_cli.R extract-field \
  --path inst/extdata/template_icasa_vba.xlsm \
  --exp-id HWOC2501 \
  --output archive/field_data.json
```

### 2. Download Weather Data

Get weather data from NASA POWER:

```bash
Rscript csmtools_cli.R get-weather \
  --lon 10.645269 \
  --lat 49.20868 \
  --from 2024-01-01 \
  --to 2025-08-09 \
  --output archive/weather_nasa.json
```

### 3. Download Sensor Data

Get sensor data from FROST server (requires credentials in `.Renviron`):

```bash
Rscript csmtools_cli.R get-sensor \
  --lon 10.645269 \
  --lat 49.20868 \
  --from 2024-01-01 \
  --to 2025-12-31 \
  --radius 10 \
  --vars "air_temperature,solar_radiation,volume_of_hydrological_precipitation" \
  --output archive/sensor_data.json
```

### 4. Get Soil Profile

Extract soil profile from SoilGrids:

```bash
Rscript csmtools_cli.R get-soil \
  --lon 10.645269 \
  --lat 49.20868 \
  --output archive/soil_data.json
```

### 5. Assemble Dataset

Combine multiple data components:

```bash
Rscript csmtools_cli.R assemble \
  --components archive/field_data.json archive/weather_nasa.json archive/soil_data.json \
  --output archive/icasa_dataset.json \
  --action merge_properties
```

### 6. Convert Dataset Format

Convert between different data formats:

```bash
Rscript csmtools_cli.R convert \
  --input archive/icasa_dataset.json \
  --from icasa \
  --to dssat \
  --output archive/dssat_dataset.json
```

### 7. Build Simulation Inputs

Build DSSAT input files:

```bash
Rscript csmtools_cli.R build-inputs \
  --input archive/dssat_dataset.json \
  --write-dssat-dir
```

### 8. Run Simulation

Run DSSAT crop simulation:

```bash
Rscript csmtools_cli.R simulate \
  --filex ~/dssat/Wheat/HWOC2501.WHX \
  --treatments 1,3,7 \
  --dssat-dir ~/dssat \
  --output-dir ./simulations
```

## Complete Workflow Example

### Complete workflow using the CLI:

```bash
#!/bin/bash
# Complete csmTools CLI workflow

# Set up environment
export WORKDIR="archive"
mkdir -p $WORKDIR

# Step 1: Extract field data
Rscript csmtools_cli.R extract-field \
  --path inst/extdata/template_icasa_vba.xlsm \
  --exp-id HWOC2501 \
  --output $WORKDIR/field.json

# Step 2: Get weather data
Rscript csmtools_cli.R get-weather \
  --lon 10.645269 --lat 49.20868 \
  --from 2024-01-01 --to 2025-08-09 \
  --output $WORKDIR/weather.json

# Step 3: Get soil data
Rscript csmtools_cli.R get-soil \
  --lon 10.645269 --lat 49.20868 \
  --output $WORKDIR/soil.json

# Step 4: Assemble into ICASA format
Rscript csmtools_cli.R assemble \
  --components $WORKDIR/field.json $WORKDIR/weather.json $WORKDIR/soil.json \
  --output $WORKDIR/icasa.json

# Step 5: Convert to DSSAT format
Rscript csmtools_cli.R convert \
  --input $WORKDIR/icasa.json \
  --from icasa --to dssat \
  --output $WORKDIR/dssat.json

# Step 6: Build DSSAT inputs
Rscript csmtools_cli.R build-inputs \
  --input $WORKDIR/dssat.json \
  --write-dssat-dir

# Step 7: Run simulation
Rscript csmtools_cli.R simulate \
  --filex ~/dssat/Wheat/HWOC2501.WHX \
  --treatments 1,3,7 \
  --output-dir ./simulations

echo "✓ Workflow complete!"
```

### Using the Shell Script

```bash
# Run complete workflow
bash run_workflow.sh
```

### Comparison

| Approach | Best For | Pros | Cons |
|----------|----------|------|------|
| **CLI Script** | Individual steps, debugging | Flexible, detailed control | Requires writing commands |
| **Shell Script** | Complete automated runs | Simple to execute | Less flexible |

## Help

Get help for any command:

```bash
# General help
Rscript csmtools_cli.R --help

# Command-specific help
Rscript csmtools_cli.R extract-field --help
Rscript csmtools_cli.R get-weather --help
Rscript csmtools_cli.R assemble --help
```

## Environment Variables

For FROST server access, set these in `.Renviron`:

```
FROST_CLIENT_ID=your_client_id
FROST_CLIENT_SECRET=your_client_secret
FROST_USERNAME=your_username
FROST_PASSWORD=your_password
FROST_USER_URL=https://your-frost-server/v1.0/
```

## Features

- **Modular**: Each workflow step is a separate command
- **Composable**: Chain commands together using shell scripts
- **Progress tracking**: Clear feedback on each step
- **Error handling**: Informative error messages
- **Flexible**: Override defaults with command-line arguments
