#!/bin/bash
# Quick setup script for csmTools namespace

echo "=========================================="
echo "csmTools CWL Setup"
echo "=========================================="
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✓ Docker is installed"
echo ""

# Prompt user for approach
echo "Choose setup approach:"
echo "  1. Build custom Docker image (recommended for production)"
echo "  2. Use runtime installation (for testing)"
echo "  3. Exit"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "Building custom Docker image..."
        cd "$(dirname "$0")"
        
        # Check if csmtools_cli.R exists
        if [ ! -f "../scripts/csmtools_cli.R" ]; then
            echo "❌ csmtools_cli.R not found at ../scripts/csmtools_cli.R"
            exit 1
        fi
        
        # Copy CLI script
        cp ../scripts/csmtools_cli.R .
        
        # Build image
        docker build -t fairagro/csmtools:latest .
        
        # Clean up
        rm csmtools_cli.R
        
        echo ""
        echo "✓ Docker image built: fairagro/csmtools:latest"
        echo ""
        echo "Next steps:"
        echo "  1. Test the image:"
        echo "     docker run --rm fairagro/csmtools:latest Rscript /opt/csmtools_cli.R --help"
        echo ""
        echo "  2. Update CWL tools to use fairagro/csmtools:latest"
        echo "     See DOCKER_SETUP.md for details"
        echo ""
        echo "  3. (Optional) Push to Docker Hub:"
        echo "     docker push fairagro/csmtools:latest"
        ;;
        
    2)
        echo ""
        echo "Using runtime installation approach..."
        echo ""
        echo "The CWL tools will install csmTools during execution."
        echo "This is slower but requires no setup."
        echo ""
        echo "Use the *-runtime.cwl versions of tools, e.g.:"
        echo "  convert-dataset-runtime.cwl"
        echo ""
        echo "Note: This requires network access during workflow execution."
        ;;
        
    3)
        echo "Exiting..."
        exit 0
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
