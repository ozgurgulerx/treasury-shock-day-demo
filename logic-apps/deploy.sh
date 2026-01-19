#!/bin/bash
# Deploy SanctionsScreeningFlow Logic App to Azure
#
# Prerequisites:
# - Azure CLI installed and logged in (az login)
# - An existing Logic App Standard resource
#
# Usage: ./deploy.sh <resource-group> <logic-app-name>

set -e

RESOURCE_GROUP="${1:-your-resource-group}"
LOGIC_APP_NAME="${2:-sanctions-screening-app}"
WORKFLOW_NAME="SanctionsScreeningFlow"

echo "=============================================="
echo "Deploying SanctionsScreeningFlow Logic App"
echo "=============================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Logic App: $LOGIC_APP_NAME"
echo "Workflow: $WORKFLOW_NAME"
echo ""

# Check if logged in
echo "Checking Azure CLI login..."
az account show > /dev/null 2>&1 || { echo "Please run 'az login' first"; exit 1; }

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Option 1: Deploy via ZIP deployment (recommended for Logic Apps Standard)
echo ""
echo "Creating deployment package..."

# Create a temporary directory for the zip
TEMP_DIR=$(mktemp -d)
cp -r "$SCRIPT_DIR/host.json" "$TEMP_DIR/"
cp -r "$SCRIPT_DIR/$WORKFLOW_NAME" "$TEMP_DIR/"

# Create the zip file
cd "$TEMP_DIR"
zip -r deployment.zip . > /dev/null

echo "Deploying to Azure..."
az logicapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP" \
    --name "$LOGIC_APP_NAME" \
    --src deployment.zip

# Clean up
rm -rf "$TEMP_DIR"

echo ""
echo "=============================================="
echo "Deployment complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Go to Azure Portal > Logic Apps > $LOGIC_APP_NAME"
echo "2. Navigate to Workflows > $WORKFLOW_NAME"
echo "3. Open the workflow designer to verify"
echo "4. Get the HTTP trigger URL from the workflow"
echo ""
echo "Configure app settings (if not already done):"
echo "  az logicapp config appsettings set \\"
echo "    --resource-group $RESOURCE_GROUP \\"
echo "    --name $LOGIC_APP_NAME \\"
echo "    --settings AZURE_SEARCH_API_KEY=<your-key>"
echo ""
