#!/bin/bash
# Build the climdata-cli Docker image used by workflows/climdataTools/*.cwl
set -euo pipefail

IMAGE="${IMAGE:-joemureithi/climdata-cli:latest}"

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

cd "$(dirname "$0")"
docker build --platform linux/amd64 -t "$IMAGE" .

echo ""
echo "✓ Docker image built: $IMAGE"
echo ""
echo "Test it:"
echo "  docker run --rm $IMAGE get-climdata-weather --help"
echo "  docker run --rm $IMAGE convert-climdata-weather-icasa --help"
echo ""
echo "Publish it (CWL tools pull $IMAGE):"
echo "  docker push $IMAGE"
