# Jira Escalation Flow - Setup Guide

This Logic App creates Jira tickets for payment escalations from the Treasury Shock Day demo.

## Prerequisites

1. **Jira Cloud** account with API access
2. **Azure subscription** with Logic Apps Standard support
3. A **Jira project** to create issues in

## Step 1: Create Jira API Token

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Name it: `treasury-demo-escalation`
4. Copy the token (you won't see it again)

## Step 2: Generate Base64 Auth Token

The Jira REST API uses Basic authentication with `email:api_token` encoded in Base64.

```bash
# Replace with your values
EMAIL="your-email@example.com"
API_TOKEN="your-api-token-here"

# Generate Base64 token
echo -n "${EMAIL}:${API_TOKEN}" | base64
```

Save this Base64 string - you'll need it for deployment.

## Step 3: Get Your Jira Details

| Setting | Example | How to Find |
|---------|---------|-------------|
| Site URL | `https://yoursite.atlassian.net` | Your Jira Cloud URL |
| Project Key | `TREAS` | Project sidebar → Project settings → Details |

## Step 4: Deploy to Azure

### Option A: Azure CLI

```bash
# Set variables
RESOURCE_GROUP="rg-treasury-demo"
LOCATION="uksouth"
JIRA_SITE_URL="https://yoursite.atlassian.net"
JIRA_PROJECT_KEY="TREAS"
JIRA_AUTH_TOKEN="<base64-token-from-step-2>"

# Deploy
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file deploy.json \
  --parameters \
    jiraSiteUrl=$JIRA_SITE_URL \
    jiraProjectKey=$JIRA_PROJECT_KEY \
    jiraAuthToken=$JIRA_AUTH_TOKEN
```

### Option B: Azure Portal

1. Go to Azure Portal → Create a resource → Logic App (Standard)
2. After creation, go to **Workflows** → Create new workflow
3. Upload `workflow.json`
4. Add App Settings for `JIRA_SITE_URL`, `JIRA_PROJECT_KEY`, `JIRA_AUTH_TOKEN`

## Step 5: Get the Trigger URL

After deployment:

```bash
# Get workflow callback URL
az rest --method post \
  --uri "https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Web/sites/jira-escalation-flow/hostruntime/runtime/webhooks/workflow/api/management/workflows/JiraEscalationFlow/triggers/When_a_HTTP_request_is_received/listCallbackUrl?api-version=2022-03-01"
```

Or in the Portal: Logic App → Workflows → JiraEscalationFlow → Overview → Workflow URL

## Step 6: Test the Workflow

```bash
# Test creating an escalation ticket
curl -X POST "<YOUR_TRIGGER_URL>" \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "[HOLD] Payment TXN-EMRG-001 breaches liquidity buffer",
    "description": "Emergency payment to ACME Trading LLC requires treasury review due to buffer breach.",
    "priority": "High",
    "source": "liquidity_gate",
    "payment": {
      "payment_id": "TXN-EMRG-001",
      "amount": 250000,
      "currency": "USD",
      "beneficiary": "ACME Trading LLC",
      "account_id": "ACC-BAN-001",
      "entity": "BankSubsidiary_TR"
    },
    "decision": {
      "action": "HOLD",
      "reason": "Payment would breach buffer by $50,000.00",
      "gap": 50000
    }
  }'
```

Expected response:
```json
{
  "status": "created",
  "issue": {
    "key": "TREAS-123",
    "url": "https://yoursite.atlassian.net/browse/TREAS-123"
  }
}
```

## Integration with Demo

### From Liquidity Gate Agent

When the Liquidity Gate returns `HOLD`, the agent can call this workflow:

```json
{
  "summary": "[HOLD] Payment {payment_id} breaches liquidity buffer",
  "source": "liquidity_gate",
  "payment": { /* from liquidity gate response */ },
  "decision": { /* from liquidity gate recommendation */ }
}
```

### From Sanctions Screening Agent

When Sanctions Screening returns `ESCALATE`:

```json
{
  "summary": "[ESCALATE] Counterparty {name} requires sanctions review",
  "source": "sanctions_screening",
  "payment": { /* payment context */ },
  "decision": {
    "action": "ESCALATE",
    "reason": "Fuzzy match on OFAC SDN list",
    "confidence": 75
  }
}
```

## Exposing as MCP Tool

To use this in Azure AI Foundry:

1. **Custom Tool (HTTP)**: Add as a custom tool with the trigger URL
2. **Logic Apps Connector**: If Foundry supports Logic Apps connectors natively

### Tool Schema for Foundry

```json
{
  "name": "create_escalation_ticket",
  "description": "Create a Jira ticket for payment escalations requiring manual review",
  "parameters": {
    "summary": { "type": "string", "required": true },
    "description": { "type": "string" },
    "priority": { "type": "string", "enum": ["Highest", "High", "Medium", "Low"] },
    "source": { "type": "string", "enum": ["liquidity_gate", "sanctions_screening", "manual"] },
    "payment": { "type": "object" },
    "decision": { "type": "object" }
  }
}
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Bad API token | Regenerate token, re-encode Base64 |
| 404 Project not found | Wrong project key | Check project key in Jira settings |
| 400 Bad Request | Invalid field | Check issue type exists in project |

## Labels Created

Each escalation ticket gets these labels:
- `treasury-demo` - Identifies demo tickets
- `escalation` - Marks as escalation
- `{source}` - Source system (liquidity_gate, sanctions_screening)
- `{action}` - Decision action (hold, block, escalate)
