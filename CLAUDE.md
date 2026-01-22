# Claude Code Instructions for Treasury Shock Day Demo

## CRITICAL - Liquidity Gate Function Protection

**DO NOT modify the following files without explicit user approval:**
- `functions/LiquidityGate/function_app.py`
- `functions/LiquidityGate/host.json`
- `functions/LiquidityGate/requirements.txt`

The MCP tool trigger configuration is fragile and has been carefully tuned to work with Azure Functions Experimental Extension Bundle.

## If Liquidity Gate Function Stops Working

### Step 1: Check if it's an infrastructure issue (most likely)

```bash
# Check function host status
az rest --method get --url "https://management.azure.com/subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-openai/providers/Microsoft.Web/sites/liquidity-gate-func/hostruntime/admin/host/status?api-version=2022-03-01" --query "{state:state,errors:errors[0]}"
```

### Step 2: If "AuthorizationFailure" on storage - Fix storage permissions

```bash
# Enable public network access on storage
az storage account update --name stliquidityfunc01 --resource-group rg-openai --public-network-access Enabled

# Get function app identity
PRINCIPAL_ID=$(az functionapp identity show --name liquidity-gate-func --resource-group rg-openai --query principalId -o tsv)

# Assign RBAC roles
STORAGE_ID="/subscriptions/a20bc194-9787-44ee-9c7f-7c3130e651b6/resourceGroups/rg-openai/providers/Microsoft.Storage/storageAccounts/stliquidityfunc01"
az role assignment create --assignee $PRINCIPAL_ID --role "Storage Blob Data Owner" --scope $STORAGE_ID
az role assignment create --assignee $PRINCIPAL_ID --role "Storage Queue Data Contributor" --scope $STORAGE_ID
az role assignment create --assignee $PRINCIPAL_ID --role "Storage Table Data Contributor" --scope $STORAGE_ID

# Restart function app
az functionapp restart --name liquidity-gate-func --resource-group rg-openai
```

### Step 3: If database connection timeout - Start PostgreSQL

```bash
az postgres flexible-server start --resource-group rg-openai --name treasurydb
```

### Step 4: If code was accidentally modified - Restore from git tag

```bash
# Restore to known working state
git checkout mcp-working-v1 -- functions/LiquidityGate/

# Redeploy
cd functions/LiquidityGate
zip -r ../liquidity-gate.zip . -x "*.pyc" -x "__pycache__/*" -x ".funcignore" -x "local.settings.json"
az functionapp deployment source config-zip --name liquidity-gate-func --resource-group rg-openai --src ../liquidity-gate.zip --build-remote true
```

### Step 5: Verify endpoints work

```bash
# Test ping
curl https://liquidity-gate-func.azurewebsites.net/api/ping

# Test health
curl https://liquidity-gate-func.azurewebsites.net/api/health

# Get MCP key
MCP_KEY=$(az functionapp keys list --name liquidity-gate-func --resource-group rg-openai --query "systemKeys.mcp_extension" -o tsv)

# Test MCP SSE
curl "https://liquidity-gate-func.azurewebsites.net/runtime/webhooks/mcp/sse?code=$MCP_KEY"
```

## Key Points

1. **The mcpToolTrigger decorator MUST remain in function_app.py** - it's required for MCP integration
2. **The Experimental Extension Bundle in host.json is required** - do not change to standard bundle
3. **Storage account must have public network access enabled** - this was the root cause of the Jan 2026 outage
4. **PostgreSQL database may be stopped for cost savings** - start it if needed

## Git Tags

- `mcp-working-v1` - Known working state with MCP trigger (Jan 22, 2026)

## Azure Resources

| Resource | Name | Resource Group |
|----------|------|----------------|
| Function App | liquidity-gate-func | rg-openai |
| Storage Account | stliquidityfunc01 | rg-openai |
| PostgreSQL | treasurydb | rg-openai |
