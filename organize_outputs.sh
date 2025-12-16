#!/bin/bash
# Script to organize workflow outputs into a data/ directory

echo "Organizing workflow outputs..."

# Create data directory if it doesn't exist
mkdir -p data

# Move output files to data directory
if [ -f "ndvi_timeseries.csv" ]; then
    mv ndvi_timeseries.csv data/
    echo "✓ Moved ndvi_timeseries.csv to data/"
fi

if [ -f "phenology_results.csv" ]; then
    mv phenology_results.csv data/
    echo "✓ Moved phenology_results.csv to data/"
fi

if [ -f "phenology_analysis.png" ]; then
    mv phenology_analysis.png data/
    echo "✓ Moved phenology_analysis.png to data/"
fi

echo "✓ Outputs organized in data/ directory"
ls -lh data/
