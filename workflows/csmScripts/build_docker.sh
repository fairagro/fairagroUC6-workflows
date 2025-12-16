#!/bin/bash
# Build and tag the csmTools Docker image

cd "$(dirname "$0")"

# Copy the CLI script to this directory
cp csmtools_cli.R .

# Build the image
docker build -t fairagro/csmtools:latest .

# Clean up
rm csmtools_cli.R

echo "✓ Docker image built: fairagro/csmtools:latest"
echo ""
echo "To push to Docker Hub (requires login):"
echo "  docker push fairagro/csmtools:latest"
echo ""
echo "To test the image:"
echo "  docker run --rm fairagro/csmtools:latest Rscript /opt/csmtools_cli.R --help"
