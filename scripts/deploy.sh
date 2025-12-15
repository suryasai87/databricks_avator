#!/bin/bash

# Deploy Databricks Avatar Assistant to Databricks Apps
# Cost-optimized deployment script

set -e

echo "========================================="
echo "Databricks Avatar Assistant Deployment"
echo "Cost-Optimized Configuration"
echo "========================================="

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v databricks &> /dev/null; then
    echo "Error: Databricks CLI not found. Please install it:"
    echo "  curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "Error: npm not found. Please install Node.js first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install it first."
    exit 1
fi

# Set environment
ENVIRONMENT=${1:-dev}
echo "Deploying to environment: $ENVIRONMENT"

# Authenticate with Databricks
echo ""
echo "Authenticating with Databricks..."
if [ -z "$DATABRICKS_HOST" ] || [ -z "$DATABRICKS_TOKEN" ]; then
    echo "Please set DATABRICKS_HOST and DATABRICKS_TOKEN environment variables"
    exit 1
fi

# Build frontend
echo ""
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Install backend dependencies
echo ""
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Validate bundle
echo ""
echo "Validating Databricks Asset Bundle..."
databricks bundle validate -t $ENVIRONMENT

# Deploy
echo ""
echo "Deploying to Databricks..."
databricks bundle deploy -t $ENVIRONMENT

echo ""
echo "========================================="
echo "Deployment complete!"
echo "========================================="

# Get app URL
echo ""
echo "Fetching app URL..."
databricks bundle summary -t $ENVIRONMENT

echo ""
echo "Cost Optimization Features Enabled:"
echo "  - Edge-TTS (FREE) for text-to-speech"
echo "  - Foundation Model API (pay-per-token)"
echo "  - Response caching (reduces API calls)"
echo "  - Text-based emotion detection (CPU)"
echo "  - Client-side speech recognition (FREE)"
echo ""
echo "Estimated monthly cost: \$100-280"
echo "(vs \$1,500-3,500 with original architecture)"
echo ""
