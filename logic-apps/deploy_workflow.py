#!/usr/bin/env python3
"""
Deploy SanctionsScreeningFlow to Azure Logic Apps Standard.

This script provides multiple deployment options:
1. Using Azure CLI (recommended)
2. Using REST API directly
3. Manual instructions

Usage:
    python deploy_workflow.py --resource-group <rg> --logic-app <name>
"""

import json
import os
import subprocess
import argparse
from pathlib import Path


def load_workflow_definition():
    """Load the workflow.json file."""
    script_dir = Path(__file__).parent
    workflow_path = script_dir / "SanctionsScreeningFlow" / "workflow.json"

    with open(workflow_path, "r") as f:
        return json.load(f)


def deploy_via_cli(resource_group: str, logic_app_name: str, workflow_name: str = "SanctionsScreeningFlow"):
    """Deploy using Azure CLI."""
    print(f"\nDeploying {workflow_name} to {logic_app_name}...")

    # Check if az CLI is available
    try:
        subprocess.run(["az", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Azure CLI not found. Please install it first.")
        return False

    # Check login status
    result = subprocess.run(["az", "account", "show"], capture_output=True)
    if result.returncode != 0:
        print("Error: Not logged in to Azure. Run 'az login' first.")
        return False

    script_dir = Path(__file__).parent

    # Create zip package
    import tempfile
    import shutil

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Copy files
        shutil.copy(script_dir / "host.json", temp_path / "host.json")
        shutil.copytree(
            script_dir / workflow_name,
            temp_path / workflow_name
        )

        # Create zip
        zip_path = temp_path / "deployment.zip"
        shutil.make_archive(str(zip_path).replace('.zip', ''), 'zip', temp_path)

        # Deploy
        result = subprocess.run([
            "az", "logicapp", "deployment", "source", "config-zip",
            "--resource-group", resource_group,
            "--name", logic_app_name,
            "--src", str(zip_path)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Deployment failed: {result.stderr}")
            return False

        print("Deployment successful!")
        return True


def print_manual_instructions(resource_group: str = None, logic_app_name: str = None):
    """Print manual deployment instructions."""
    workflow = load_workflow_definition()

    print("""
╔══════════════════════════════════════════════════════════════════╗
║         MANUAL DEPLOYMENT INSTRUCTIONS                          ║
╚══════════════════════════════════════════════════════════════════╝

If automated deployment doesn't work, follow these steps in Azure Portal:

1. CREATE LOGIC APP STANDARD (if not exists)
   ─────────────────────────────────────────
   • Go to Azure Portal > Create a resource > Logic App
   • Choose "Standard" plan (Workflow Service Plan)
   • Name: sanctions-screening-app (or your preferred name)
   • Region: Same as your Azure AI Search
   • Create

2. CONFIGURE APP SETTINGS
   ─────────────────────────────────────────
   • Go to Logic App > Configuration > Application settings
   • Add new setting:
     - Name: AZURE_SEARCH_API_KEY
     - Value: <your Azure AI Search API key>
   • Save

3. CREATE THE WORKFLOW
   ─────────────────────────────────────────
   • Go to Logic App > Workflows > + Add
   • Name: SanctionsScreeningFlow
   • State type: Stateful
   • Create

4. OPEN DESIGNER AND ADD COMPONENTS
   ─────────────────────────────────────────

   TRIGGER: HTTP Request
   • Search "Request" > "When a HTTP request is received"
   • Request Body JSON Schema:
""")

    # Print the schema
    trigger_schema = workflow["definition"]["triggers"]["When_a_HTTP_request_is_received"]["inputs"]["schema"]
    print(f"     {json.dumps(trigger_schema, indent=6)}")

    print("""
   ACTIONS (in order):

   a) Initialize variable "decision" (String) = "CLEAR"
   b) Initialize variable "bestScore" (Integer) = 0
   c) Initialize variable "bestMatch" (Object) = {}

   d) Compose "Normalize_Name":
      Expression: toUpper(trim(triggerBody()?['name']))

   e) HTTP action "Query_Azure_AI_Search":
      • Method: POST
      • URI: https://chatops-ozguler.search.windows.net/indexes/idx-ofac-sdn-v1/docs/search?api-version=2023-11-01
      • Headers:
        - Content-Type: application/json
        - api-key: @appsetting('AZURE_SEARCH_API_KEY')
      • Body:
        {
          "search": "@{outputs('Normalize_Name')}",
          "top": 5,
          "queryType": "simple",
          "searchFields": "primary_name,aka_names",
          "select": "uid,primary_name,aka_names,programs,entity_type,snapshot_date"
        }

   f) Parse JSON "Parse_Search_Results":
      • Content: @body('Query_Azure_AI_Search')
      • Generate schema from sample Azure Search response

   g) Condition "Check_If_Results_Exist":
      • length(body('Parse_Search_Results')?['value']) > 0

      If YES:
        - For Each over body('Parse_Search_Results')?['value']
          - Check exact match → Set decision=BLOCK, bestScore=95
          - Else check partial → Set decision=ESCALATE, bestScore=80

   h) Response:
      • Status: 200
      • Body: (see workflow.json for full response structure)

5. SAVE AND TEST
   ─────────────────────────────────────────
   • Save the workflow
   • Copy the HTTP POST URL from the trigger
   • Test with:
     curl -X POST "<url>" -H "Content-Type: application/json" \\
       -d '{"name": "BANK MASKAN"}'

═══════════════════════════════════════════════════════════════════
""")


def print_workflow_json():
    """Print the full workflow JSON for copy-paste into Azure Portal."""
    workflow = load_workflow_definition()
    print("\n" + "="*60)
    print("FULL WORKFLOW JSON (for Code View in Azure Portal)")
    print("="*60 + "\n")
    print(json.dumps(workflow, indent=2))
    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="Deploy SanctionsScreeningFlow Logic App")
    parser.add_argument("--resource-group", "-g", help="Azure resource group name")
    parser.add_argument("--logic-app", "-n", help="Logic App name")
    parser.add_argument("--manual", action="store_true", help="Print manual deployment instructions")
    parser.add_argument("--json", action="store_true", help="Print workflow JSON for code view")

    args = parser.parse_args()

    if args.json:
        print_workflow_json()
        return

    if args.manual or not (args.resource_group and args.logic_app):
        print_manual_instructions(args.resource_group, args.logic_app)
        return

    success = deploy_via_cli(args.resource_group, args.logic_app)

    if success:
        print(f"""
Next steps:
1. Go to Azure Portal > Logic Apps > {args.logic_app}
2. Navigate to Workflows > SanctionsScreeningFlow
3. Get the HTTP trigger URL
4. Test with: curl -X POST "<url>" -H "Content-Type: application/json" -d '{{"name": "BANK MASKAN"}}'
""")


if __name__ == "__main__":
    main()
